import re
import unittest
from pathlib import Path


INSTALLER = Path(__file__).resolve().parents[1] / "scripts" / "install-core.sh"


class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INSTALLER.read_text(encoding="utf-8")

    def test_installer_does_not_create_a_vpn_customer(self):
        self.assertNotIn("First VPN customer", self.source)
        self.assertIn('app.py bootstrap', self.source)
        self.assertIn('add VPN customers there', self.source)

    def test_sandbox_allows_privileged_helper_metadata_writes(self):
        match = re.search(r"^ReadWritePaths=(.*)$", self.source, re.MULTILINE)
        self.assertIsNotNone(match)
        writable = set(match.group(1).split())
        self.assertTrue({"/var/lib/ocserv-panel", "/etc/ocserv", "/etc/ocserv-panel", "/run"}.issubset(writable))


if __name__ == "__main__":
    unittest.main()
