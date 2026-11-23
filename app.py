import json
import os
import re
import secrets
import sqlite3
import subprocess
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PANEL_DB", "/var/lib/ocserv-panel/panel.db"))
HELPER = "/usr/local/sbin/ocserv-panel-helper"
LOGIN_TRIES = {}

app = Flask(__name__)
secret_path = Path("/etc/ocserv-panel/secret_key")
app.secret_key = secret_path.read_text().strip() if secret_path.exists() else os.environ.get("PANEL_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set /etc/ocserv-panel/secret_key before starting the panel.")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE="Strict", PERMANENT_SESSION_LIFETIME=3600)


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS admins (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)")
    con.commit()
    return con


def helper(payload):
    p = subprocess.run(["sudo", "-n", HELPER], input=json.dumps(payload), text=True, capture_output=True, timeout=45)
    try:
        data = json.loads(p.stdout)
    except Exception:
        raise RuntimeError((p.stderr or p.stdout or "The privileged helper returned an invalid response.").strip())
    if p.returncode or not data.get("ok"):
        raise RuntimeError(data.get("error", "Operation failed."))
    return data["data"]


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


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return jsonify(error="Please sign in again."), 401
        return fn(*args, **kwargs)
    return wrapped


@app.get("/")
def index():
    if not session.get("admin"):
        return redirect(url_for("login"))
    return render_template("index.html", csrf=csrf_token(), username=session["admin"])


@app.get("/login")
def login():
    return render_template("login.html", csrf=csrf_token())


@app.post("/login")
def login_post():
    ip = request.remote_addr or "unknown"
    current = LOGIN_TRIES.get(ip, {"n": 0, "until": 0})
    if current["until"] > time.time():
        return render_template("login.html", csrf=csrf_token(), error="Too many attempts. Try again later."), 429
    username = request.form.get("username", "")[:64]
    password = request.form.get("password", "")[:256]
    con = db()
    row = con.execute("SELECT username,password_hash FROM admins WHERE username=?", (username,)).fetchone()
    con.close()
    if row and check_password_hash(row["password_hash"], password):
        LOGIN_TRIES.pop(ip, None)
        session.clear()
        session["admin"] = username
        csrf_token()
        session.permanent = True
        return redirect(url_for("index"))
    current["n"] += 1
    if current["n"] >= 5:
        current.update(n=0, until=time.time() + 900)
    LOGIN_TRIES[ip] = current
    return render_template("login.html", csrf=csrf_token(), error="Username or password is incorrect."), 401


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/state")
@login_required
def api_state():
    try:
        return jsonify(helper({"op": "state"}))
    except Exception as exc:
        return jsonify(error=str(exc)), 500


@app.post("/api/users")
@login_required
def api_add_user():
    try:
        body = request.get_json(force=True)
        return jsonify(helper({"op": "add_user", "username": body.get("username", ""), "password": body.get("password", "")}))
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.delete("/api/users/<username>")
@login_required
def api_delete_user(username):
    try:
        return jsonify(helper({"op": "delete_user", "username": username}))
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/dns")
@login_required
def api_dns():
    try:
        body = request.get_json(force=True)
        return jsonify(helper({"op": "save_dns", "dns": body.get("dns", [])}))
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/restart")
@login_required
def api_restart():
    try:
        return jsonify(helper({"op": "restart"}))
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/check")
@login_required
def api_check():
    try:
        return jsonify(helper({"op": "check"}))
    except Exception as exc:
        return jsonify(error=str(exc)), 400


def bootstrap():
    import getpass
    username = input("Panel admin username: ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", username):
        raise SystemExit("Use 3–32 letters, numbers, underscore or hyphen.")
    password = getpass.getpass("Panel admin password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    con = db()
    con.execute("INSERT OR REPLACE INTO admins(username,password_hash) VALUES(?,?)", (username, generate_password_hash(password)))
    con.commit()
    con.close()
    print("Admin account saved.")


if __name__ == "__main__" and len(os.sys.argv) > 1 and os.sys.argv[1] == "bootstrap":
    bootstrap()
