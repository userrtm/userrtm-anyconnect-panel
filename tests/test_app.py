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
        with self.client.session_transaction(base_url=self.base) as session:
            return session["csrf"]

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

    def test_admin_can_change_to_a_simple_password(self):
        csrf = self.sign_in()
        response = self.client.post("/api/admin/password", base_url=self.base, json={
            "current": "correct-horse-battery", "new": "123",
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(response.status_code, 200)
        con = panel.db()
        row = con.execute("SELECT password_hash FROM admins WHERE username='admin'").fetchone()
        con.close()
        self.assertTrue(panel.check_password_hash(row["password_hash"], "123"))

    def test_customer_profile_url_serves_their_server_profile(self):
        profile = {"username": "alice", "endpoints": [{"host": "vpn.example.com", "port": 443}]}
        with patch.object(panel, "helper", return_value=profile):
            response = self.client.get("/customer-profile/" + "A" * 43 + ".xml", base_url=self.base)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"vpn.example.com", response.data)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_create_and_copy_use_the_primary_subscription_url_even_after_switching_vpn(self):
        csrf = self.sign_in()
        token = "A" * 43
        sub_base = "https://sub.example.test:8443"
        profile_path = f"/customer-profile/{token}.xml"
        vpn_host = "vpn-primary.example.test"

        def helper(payload):
            if payload["op"] == "network":
                return {"subscription_base_url": sub_base}
            if payload["op"] == "add_user":
                return {"profile_token": token}
            if payload["op"] == "state":
                return {
                    "settings": {"subscription_base_url": sub_base, "primary_host": vpn_host},
                    "users": [{"username": "alice", "profile_token": token}],
                }
            if payload["op"] == "customer_profile":
                return {"username": "alice", "endpoints": [{"host": vpn_host, "port": 443}]}
            self.fail(f"Unexpected helper operation: {payload['op']}")

        credentials = {"username": "alice", "password": "test-password"}
        token_file = SimpleNamespace(read_text=lambda **kwargs: "test-token")
        with patch.object(panel, "helper", side_effect=helper), patch.object(panel, "API_TOKEN_FILE", token_file):
            sellers = {"Authorization": "Bearer test-token"}
            for path, headers in [("/api/users", {"X-CSRF-Token": csrf}), ("/api/v1/customers", sellers)]:
                response = self.client.post(path, base_url=self.base, json=credentials, headers=headers)
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.get_json()["profile_url"], sub_base + profile_path)

            vpn_host = "vpn-backup.example.test"
            for path, key, headers in [("/api/state", "users", {}), ("/api/v1/customers", "customers", sellers)]:
                response = self.client.get(path, base_url=self.base, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json()[key][0]["profile_url"], sub_base + profile_path)
            result = self.client.get(profile_path, base_url=sub_base)
            self.assertEqual(result.status_code, 200)
            self.assertIn(b"vpn-backup.example.test", result.data)

    def test_missing_primary_subscription_is_reported_before_creating_customer(self):
        csrf = self.sign_in()
        with patch.object(panel, "helper", return_value={"subscription_base_url": ""}) as helper:
            response = self.client.post("/api/users", base_url=self.base, headers={"X-CSRF-Token": csrf}, json={
                "username": "alice", "password": "test-password",
            })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "subscription_not_configured")
        helper.assert_called_once_with({"op": "network"})

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
