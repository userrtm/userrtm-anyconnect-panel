import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


HELPER_PATH = Path(__file__).resolve().parents[1] / "helper" / "ocserv-panel-helper"
loader = importlib.machinery.SourceFileLoader("ocserv_panel_helper", str(HELPER_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
helper = importlib.util.module_from_spec(spec)
loader.exec_module(helper)


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        helper.CONFIG = root / "ocserv.conf"
        helper.PASSWD = root / "ocpasswd"
        helper.META = root / "panel" / "users.json"
        helper.VPN_DOMAIN = root / "panel" / "vpn-domain"
        helper.CONFIG.write_text(
            "server-cert = /etc/letsencrypt/live/vpn.example.com/fullchain.pem\n"
            "server-key = /etc/letsencrypt/live/vpn.example.com/privkey.pem\n"
            "tcp-port = 443\ndns = 1.1.1.1\nroute = default\n",
            encoding="utf-8",
        )
        self.original_run = helper.run
        helper.run = self.fake_run

    def tearDown(self):
        helper.run = self.original_run
        self.temp.cleanup()

    def fake_run(self, args, input_text=None, timeout=30):
        if args[0] == "ocpasswd":
            passwd = Path(args[args.index("-c") + 1])
            username = args[-1]
            lines = passwd.read_text().splitlines() if passwd.exists() else []
            entries = {line.split(":", 1)[0]: line.split(":", 1)[1] for line in lines}
            if "-d" in args:
                entries.pop(username, None)
            elif "-l" in args:
                entries[username] = "!" + entries[username].lstrip("!")
            elif "-u" in args:
                entries[username] = entries[username].lstrip("!")
            else:
                entries[username] = "testhash"
            passwd.write_text("".join(f"{name}:{value}\n" for name, value in entries.items()))
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if args[0] == "ocserv":
            return SimpleNamespace(returncode=0, stdout="valid", stderr="")
        if args[0] == "systemctl":
            return SimpleNamespace(returncode=0, stdout="active\n", stderr="")
        if args[0] == "journalctl":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        self.fail(f"Unexpected command: {args}")

    def test_customer_lifecycle_and_locking(self):
        helper.action({"op": "add_user", "username": "customer_1", "password": "long-password", "days": 30})
        self.assertEqual(helper.snapshot(helper.load_meta())[0]["status"], "active")
        helper.action({"op": "disable_user", "username": "customer_1"})
        self.assertIn("!testhash", helper.PASSWD.read_text())
        self.assertEqual(helper.snapshot(helper.load_meta())[0]["status"], "disabled")
        helper.action({"op": "enable_user", "username": "customer_1"})
        self.assertEqual(helper.PASSWD.read_text().strip(), "customer_1:testhash")
        helper.action({"op": "delete_user", "username": "customer_1"})
        self.assertEqual(helper.PASSWD.read_text(), "")
        self.assertEqual(helper.snapshot(helper.load_meta()), [])

    def test_expiration_locks_account(self):
        helper.action({"op": "add_user", "username": "monthly", "password": "long-password", "days": 30})
        meta = helper.load_meta()
        meta["users"]["monthly"]["expires_at"] = 1
        helper.save_meta(meta)
        self.assertEqual(helper.action({"op": "expire"})["expired"], ["monthly"])
        self.assertIn("!testhash", helper.PASSWD.read_text())
        self.assertEqual(helper.snapshot(helper.load_meta())[0]["status"], "expired")

    def test_invalid_dns_does_not_change_config(self):
        original = helper.CONFIG.read_text()
        with self.assertRaises(ValueError):
            helper.action({"op": "save_dns", "dns": ["not-an-ip"]})
        self.assertEqual(helper.CONFIG.read_text(), original)

    def test_valid_dns_is_applied_after_config_check(self):
        helper.action({"op": "save_dns", "dns": ["1.1.1.1", "2001:4860:4860::8888"]})
        contents = helper.CONFIG.read_text()
        self.assertIn("dns = 1.1.1.1\n", contents)
        self.assertIn("dns = 2001:4860:4860::8888\n", contents)
        self.assertEqual(contents.count("dns ="), 2)

    def test_profile_url_uses_vpn_certificate_hostname(self):
        self.assertEqual(helper.action({"op": "profile"}), {"host": "vpn.example.com", "port": "443"})

    def test_profile_hostname_handles_quoted_certificate_path(self):
        helper.CONFIG.write_text(
            'server-cert = "/opt/certs/server.pem"\n'
            'server-key = "/opt/certs/server-key.pem"\n'
            'tcp-port = 443\n',
            encoding="utf-8",
        )
        helper.VPN_DOMAIN.parent.mkdir(parents=True, exist_ok=True)
        helper.VPN_DOMAIN.write_text("vpn.example.com\n", encoding="utf-8")
        self.assertEqual(helper.action({"op": "profile"}), {"host": "vpn.example.com", "port": "443"})

    def test_reports_actual_password_file_from_auth_config(self):
        helper.CONFIG.write_text(
            'auth = "plain[passwd=/etc/ocserv/passwd]"\n'
            'server-cert = /etc/letsencrypt/live/vpn.example.com/fullchain.pem\n'
            'tcp-port = 443\n',
            encoding="utf-8",
        )
        settings = helper.get_settings()
        self.assertEqual(settings["auth_passwd"], "/etc/ocserv/passwd")
        self.assertFalse(settings["auth_file_exists"])

    def test_config_check_detects_missing_vpn_password_file(self):
        helper.CONFIG.write_text(
            'auth = "plain[passwd=/missing/ocserv/passwd]"\n'
            'server-cert = /etc/letsencrypt/live/vpn.example.com/fullchain.pem\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeError, "password file is missing"):
            helper.config_check()

    def test_each_customer_gets_a_private_profile_url(self):
        helper.action({"op": "add_user", "username": "alice", "password": "long-password-a"})
        helper.action({"op": "add_user", "username": "bob", "password": "long-password-b"})
        rows = {row["username"]: row for row in helper.snapshot(helper.load_meta())}
        self.assertNotEqual(rows["alice"]["profile_token"], rows["bob"]["profile_token"])
        self.assertEqual(
            helper.action({"op": "customer_profile", "token": rows["alice"]["profile_token"]}),
            {"username": "alice", "host": "vpn.example.com", "port": "443"},
        )
        helper.action({"op": "disable_user", "username": "alice"})
        with self.assertRaises(ValueError):
            helper.action({"op": "customer_profile", "token": rows["alice"]["profile_token"]})

    def test_profile_url_is_revoked_on_customer_delete(self):
        helper.action({"op": "add_user", "username": "revoke", "password": "long-password"})
        token = helper.snapshot(helper.load_meta())[0]["profile_token"]
        helper.action({"op": "delete_user", "username": "revoke"})
        with self.assertRaises(ValueError):
            helper.action({"op": "customer_profile", "token": token})

    def test_profile_url_is_unavailable_after_expiry(self):
        helper.action({"op": "add_user", "username": "expired", "password": "long-password"})
        meta = helper.load_meta()
        token = meta["users"]["expired"]["profile_token"]
        meta["users"]["expired"]["expires_at"] = 1
        helper.save_meta(meta)
        with self.assertRaises(ValueError):
            helper.action({"op": "customer_profile", "token": token})


if __name__ == "__main__":
    unittest.main()
