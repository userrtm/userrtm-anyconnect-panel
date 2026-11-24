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

    def test_installer_aligns_vpn_auth_and_certificate_with_panel(self):
        self.assertIn('plain[passwd=/etc/ocserv/ocpasswd]', self.source)
        self.assertIn('fullchain.pem', self.source)
        self.assertIn('privkey.pem', self.source)
        self.assertIn('/etc/ocserv-panel/vpn-domain', self.source)

    def test_existing_server_is_migrated_to_full_tunnel(self):
        self.assertIn("lines.append('route = default')", self.source)
        self.assertIn('server-key|route|no-route', self.source)

    def test_nat_uses_the_configured_vpn_pool(self):
        self.assertIn("ipaddress.ip_network(f'{network}/{mask}', strict=False)", self.source)
        self.assertNotIn('10.20.30.0/24 -o "$WAN_IF"', self.source)


if __name__ == "__main__":
    unittest.main()
