"""Web administration UI for an ocserv server."""
import json
import os
import re
import secrets
import sqlite3
import subprocess
import time
import xml.etree.ElementTree as ET
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(os.environ.get("PANEL_DB", "/var/lib/ocserv-panel/panel.db"))
HELPER = "/usr/local/sbin/ocserv-panel-helper"
USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

app = Flask(__name__)
secret_path = Path("/etc/ocserv-panel/secret_key")
app.secret_key = secret_path.read_text().strip() if secret_path.exists() else os.environ.get("PANEL_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set /etc/ocserv-panel/secret_key before starting the panel.")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=3600,
    MAX_CONTENT_LENGTH=16 * 1024,
)


class CustomerProfileNotFound(LookupError):
    """A customer profile URL is unknown, disabled, deleted, or expired."""


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS admins (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS login_attempts (ip TEXT PRIMARY KEY, failures INTEGER NOT NULL, locked_until REAL NOT NULL, updated_at REAL NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS admin_events (id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, created_at REAL NOT NULL)")
    con.commit()
    return con


EVENT_LABELS = {
    "add_user": "Müşteri oluşturuldu",
    "delete_user": "Müşteri silindi",
    "disable_user": "Müşteri durduruldu",
    "enable_user": "Müşteri etkinleştirildi",
    "set_expiry": "Abonelik süresi güncellendi",
    "reset_password": "VPN parolası yenilendi",
    "save_dns": "DNS ayarları değiştirildi",
    "restart": "VPN servisi yeniden başlatıldı",
}


def record_event(payload):
    op = payload.get("op")
    label = EVENT_LABELS.get(op)
    if not label:
        return
    username = payload.get("username", "")
    detail = f"Kullanıcı: {username}" if username else ""
    if op == "set_expiry":
        days = payload.get("days")
        detail += f" · Süre: {'sınırsız' if days in (None, '') else str(days) + ' gün'}"
    con = db()
    try:
        con.execute("INSERT INTO admin_events(actor,action,detail,created_at) VALUES(?,?,?,?)", (session.get("admin", "admin"), label, detail, time.time()))
        con.commit()
    finally:
        con.close()


def recent_events(limit=50):
    con = db()
    try:
        rows = con.execute("SELECT actor,action,detail,created_at FROM admin_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def helper(payload):
    p = subprocess.run(
        ["sudo", "-n", HELPER], input=json.dumps(payload), text=True,
        capture_output=True, timeout=45,
    )
    try:
        data = json.loads(p.stdout)
    except (ValueError, TypeError):
        raise RuntimeError((p.stderr or p.stdout or "The privileged helper returned an invalid response.").strip())
    if p.returncode or not data.get("ok"):
        message = data.get("error", "Operation failed.")
        if payload.get("op") == "customer_profile" and message in {
            "Profile not found.",
            "Profile is inactive or expired.",
        }:
            raise CustomerProfileNotFound(message)
        raise RuntimeError(message)
    result = data["data"]
    if payload.get("op") != "state":
        try:
            record_event(payload)
        except sqlite3.Error:
            app.logger.exception("Could not record panel activity")
    return result


def csrf_token():
    token = session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


@app.before_request
def protect_posts():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected = session.get("csrf", "")
        supplied = request.headers.get("X-CSRF-Token", "")
        if request.method == "POST" and not supplied:
            supplied = request.form.get("csrf", "")
        if not expected or not secrets.compare_digest(expected, supplied):
            return jsonify(error="Invalid request token. Reload the page and try again."), 400


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
    return response


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return jsonify(error="Please sign in again."), 401
        return fn(*args, **kwargs)
    return wrapped


def json_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Request body must be a JSON object.")
    return body


def api_operation(payload):
    try:
        return jsonify(helper(payload))
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        return jsonify(error=str(exc)), 400


@app.get("/")
def index():
    if not session.get("admin"):
        return redirect(url_for("login"))
    return render_template("index.html", csrf=csrf_token(), username=session["admin"])


@app.get("/login")
def login():
    if session.get("admin"):
        return redirect(url_for("index"))
    return render_template("login.html", csrf=csrf_token())


@app.get("/profile.xml")
def client_profile():
    """Serve a minimal Cisco Secure Client server-list profile for URI import."""
    try:
        details = helper({"op": "profile"})
        body = build_profile(details["host"], details.get("port", "443"), details["host"])
        return Response(body, mimetype="application/xml", headers={"Cache-Control": "no-store", "Content-Disposition": 'inline; filename="UserrTM-AnyConnect.xml"'})
    except (RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        return Response(str(exc), status=503, mimetype="text/plain", headers={"Cache-Control": "no-store"})


def build_profile(host, port, display_name):
    namespace = "http://schemas.xmlsoap.org/encoding/"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}AnyConnectProfile")
    servers = ET.SubElement(root, f"{{{namespace}}}ServerList")
    entry = ET.SubElement(servers, f"{{{namespace}}}HostEntry")
    ET.SubElement(entry, f"{{{namespace}}}HostName").text = display_name
    port = str(port)
    ET.SubElement(entry, f"{{{namespace}}}HostAddress").text = host if port == "443" else f"{host}:{port}"
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")


@app.get("/customer-profile/<token>.xml")
def customer_profile(token):
    """Serve a private, revocable Cisco Secure Client profile URL per customer."""
    try:
        details = helper({"op": "customer_profile", "token": token})
        body = build_profile(details["host"], details.get("port", "443"), details["host"])
        return Response(body, mimetype="application/xml", headers={
            "Cache-Control": "no-store, private",
            "Content-Disposition": f'inline; filename="{details["username"]}.xml"',
        })
    except CustomerProfileNotFound:
        return Response("Profile not found or inactive.", status=404, mimetype="text/plain", headers={"Cache-Control": "no-store"})
    except (RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        app.logger.exception("Unable to serve customer profile")
        return Response("Profile temporarily unavailable.", status=503, mimetype="text/plain", headers={"Cache-Control": "no-store"})


@app.post("/login")
def login_post():
    now = time.time()
    ip = request.remote_addr or "unknown"
    con = db()
    con.execute("DELETE FROM login_attempts WHERE updated_at < ?", (now - 86400,))
    state = con.execute("SELECT failures,locked_until FROM login_attempts WHERE ip=?", (ip,)).fetchone()
    if state and state["locked_until"] > now:
        con.close()
        return render_template("login.html", csrf=csrf_token(), error="Çok fazla deneme. 15 dakika sonra tekrar deneyin."), 429
    username = request.form.get("username", "")[:32]
    password = request.form.get("password", "")[:256]
    row = con.execute("SELECT username,password_hash FROM admins WHERE username=?", (username,)).fetchone()
    if row and check_password_hash(row["password_hash"], password):
        con.execute("DELETE FROM login_attempts WHERE ip=?", (ip,))
        con.commit()
        con.close()
        session.clear()
        session["admin"] = username
        session["csrf"] = secrets.token_urlsafe(32)
        session.permanent = True
        return redirect(url_for("index"))
    failures = (state["failures"] if state else 0) + 1
    locked_until = now + 900 if failures >= 5 else 0
    con.execute("INSERT INTO login_attempts(ip,failures,locked_until,updated_at) VALUES(?,?,?,?) ON CONFLICT(ip) DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until,updated_at=excluded.updated_at", (ip, 0 if locked_until else failures, locked_until, now))
    con.commit()
    con.close()
    return render_template("login.html", csrf=csrf_token(), error="Kullanıcı adı veya şifre yanlış."), 401


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/state")
@login_required
def api_state():
    try:
        result = helper({"op": "state"})
        result["events"] = recent_events()
        return jsonify(result)
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, sqlite3.Error) as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/users")
@login_required
def api_add_user():
    try:
        body = json_body()
        username = body.get("username", "")
        if not isinstance(username, str) or not USERNAME_RE.fullmatch(username):
            raise ValueError("Kullanıcı adı 1–32 karakter olmalı; harf, rakam, _ ve - kullanın.")
        password = body.get("password", "")
        if not isinstance(password, str) or len(password) < 10 or len(password) > 128:
            raise ValueError("VPN şifresi 10–128 karakter olmalı.")
        return api_operation({"op": "add_user", "username": username, "password": password, "days": body.get("days")})
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.delete("/api/users/<username>")
@login_required
def api_delete_user(username):
    return api_operation({"op": "delete_user", "username": username})


@app.post("/api/users/<username>/status")
@login_required
def api_user_status(username):
    try:
        body = json_body()
        if not isinstance(body.get("active"), bool):
            raise ValueError("active alanı true veya false olmalı.")
        return api_operation({"op": "enable_user" if body["active"] else "disable_user", "username": username})
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/users/<username>/expiry")
@login_required
def api_user_expiry(username):
    try:
        body = json_body()
        days = body.get("days")
        if days is not None and days != "" and (not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 3650):
            raise ValueError("Süre 1–3650 gün arasında veya sınırsız olmalı.")
        return api_operation({"op": "set_expiry", "username": username, "days": days})
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/users/<username>/password")
@login_required
def api_user_password(username):
    try:
        body = json_body()
        password = body.get("password", "")
        if not isinstance(password, str) or len(password) < 10 or len(password) > 128:
            raise ValueError("VPN şifresi 10–128 karakter olmalı.")
        return api_operation({"op": "reset_password", "username": username, "password": password})
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/admin/password")
@login_required
def api_admin_password():
    try:
        body = json_body()
        current, new = body.get("current", ""), body.get("new", "")
        if not isinstance(current, str) or not isinstance(new, str) or len(new) < 12 or len(new) > 256:
            raise ValueError("Yeni panel şifresi 12–256 karakter olmalı.")
        con = db()
        try:
            row = con.execute("SELECT password_hash FROM admins WHERE username=?", (session["admin"],)).fetchone()
            if not row or not check_password_hash(row["password_hash"], current):
                raise ValueError("Mevcut panel şifresi hatalı.")
            con.execute("UPDATE admins SET password_hash=? WHERE username=?", (generate_password_hash(new), session["admin"]))
            con.commit()
        finally:
            con.close()
        session.clear()
        return jsonify(message="Şifre değiştirildi. Güvenlik için yeniden giriş yapın.", logout=True)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/dns")
@login_required
def api_dns():
    try:
        body = json_body()
        return api_operation({"op": "save_dns", "dns": body.get("dns", [])})
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/restart")
@login_required
def api_restart():
    return api_operation({"op": "restart"})


@app.post("/api/check")
@login_required
def api_check():
    return api_operation({"op": "check"})


def bootstrap():
    import getpass
    username = input("Panel admin username: ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", username):
        raise SystemExit("Use 3–32 letters, numbers, underscore or hyphen.")
    password = getpass.getpass("Panel admin password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    con = db()
    try:
        con.execute("INSERT INTO admins(username,password_hash) VALUES(?,?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash", (username, generate_password_hash(password)))
        con.commit()
    finally:
        con.close()
    print("Admin account saved.")


if __name__ == "__main__" and len(os.sys.argv) > 1 and os.sys.argv[1] == "bootstrap":
    bootstrap()
