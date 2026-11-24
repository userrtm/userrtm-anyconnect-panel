import importlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

TEMP = tempfile.TemporaryDirectory()
os.environ["PANEL_DB"] = str(Path(TEMP.name) / "panel.db")
os.environ["PANEL_SECRET_KEY"] = "test-only-secret-key"
try:
    from werkzeug.security import generate_password_hash
    panel = importlib.import_module("app")
    FLASK_AVAILABLE = True
except ModuleNotFoundError:
    FLASK_AVAILABLE = False


@unittest.skipUnless(FLASK_AVAILABLE, "Flask/Werkzeug dependencies are not installed in this test environment")
class PanelRouteTests(unittest.TestCase):
    def setUp(self):
        con = panel.db()
        con.execute("DELETE FROM admins")
        con.execute("DELETE FROM login_attempts")
        con.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)", ("admin", generate_password_hash("correct-horse-battery")))
        con.commit()
        con.close()
        self.client = panel.app.test_client()
        self.base = "https://panel.example.test"

    def sign_in(self):
        page = self.client.get("/login", base_url=self.base)
        with self.client.session_transaction(base_url=self.base) as session:
            csrf = session["csrf"]
        response = self.client.post("/login", base_url=self.base, data={
            "username": "admin", "password": "correct-horse-battery", "csrf": csrf,
        })
        self.assertEqual(response.status_code, 302)
        return csrf

    def test_login_and_authentication_required(self):
        response = self.client.get("/api/state", base_url=self.base)
        self.assertEqual(response.status_code, 401)
        csrf = self.sign_in()
        response = self.client.get("/", base_url=self.base)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"M\xc3\xbc\xc5\x9fteriler", response.data)
        self.assertTrue(csrf)

    def test_csrf_rejects_mutation(self):
        self.sign_in()
        response = self.client.post("/api/users", base_url=self.base, json={"username": "valid", "password": "long-password"})
        self.assertEqual(response.status_code, 400)

    def test_password_change_requires_current_password(self):
        csrf = self.sign_in()
        response = self.client.post("/api/admin/password", base_url=self.base, json={
            "current": "wrong", "new": "replacement-password",
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Mevcut", response.get_json()["error"])

    def test_customer_profile_url_serves_their_server_profile(self):
        with patch.object(panel, "helper", return_value={"username": "alice", "host": "vpn.example.com", "port": "443"}):
            response = self.client.get("/customer-profile/" + "A" * 43 + ".xml", base_url=self.base)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"UserrTM - alice", response.data)
        self.assertIn(b"vpn.example.com", response.data)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_customer_profile_rejects_revoked_urls(self):
        helper_response = SimpleNamespace(
            returncode=1,
            stdout=json.dumps({"ok": False, "error": "Profile is inactive or expired."}),
            stderr="",
        )
        with patch.object(panel.subprocess, "run", return_value=helper_response):
            response = self.client.get("/customer-profile/" + "A" * 43 + ".xml", base_url=self.base)
        self.assertEqual(response.status_code, 404)

    def test_customer_profile_hides_internal_errors(self):
        with patch.object(panel, "helper", side_effect=RuntimeError("/etc/private/path")):
            response = self.client.get("/customer-profile/" + "A" * 43 + ".xml", base_url=self.base)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"/etc/private/path", response.data)


if __name__ == "__main__":
    unittest.main()
