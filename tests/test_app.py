import importlib
import os
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
