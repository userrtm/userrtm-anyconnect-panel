#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then echo "Run as root: sudo bash install.sh"; exit 1; fi
if ! grep -qi ubuntu /etc/os-release; then echo "This installer supports Ubuntu only."; exit 1; fi

APP_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VPN_PORT=443
PANEL_PORT=8443
read -rp "VPN domain (for example vpn.example.com): " DOMAIN
read -rp "Let's Encrypt email: " EMAIL

if [[ ! "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]]; then echo "Invalid domain."; exit 1; fi

echo "Installing packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get -o Acquire::Retries=3 -o Acquire::ForceIPv4=true update
apt-get install -y ocserv certbot iptables python3 python3-venv python3-pip sudo

systemctl stop ocserv-panel.service 2>/dev/null || true
if ss -H -lntup "sport = :${VPN_PORT}" 2>/dev/null | grep -q .; then
  if ! ss -H -lntup "sport = :${VPN_PORT}" 2>/dev/null | grep -q ocserv; then
    echo "Port 443 is already used by another service. Resolve the conflict before installing."
    ss -lntup "sport = :${VPN_PORT}"
    exit 1
  fi
fi

if [[ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
  if ss -H -lnt 'sport = :80' 2>/dev/null | grep -q .; then
    echo "Port 80 is in use; stop its service before requesting the certificate."
    exit 1
  fi
  certbot certonly --standalone --non-interactive --agree-tos --email "$EMAIL" -d "$DOMAIN"
else
  echo "Using existing Let's Encrypt certificate for ${DOMAIN}."
fi

if ss -H -lnt "sport = :${PANEL_PORT}" 2>/dev/null | grep -q .; then
  echo "Panel port ${PANEL_PORT} is already in use. Resolve the conflict and rerun."
  exit 1
fi

mkdir -p /etc/ocserv
if [[ -f /etc/ocserv/ocserv.conf ]]; then
  cp /etc/ocserv/ocserv.conf "/etc/ocserv/ocserv.conf.backup.$(date +%Y%m%d%H%M%S)"
  echo "Existing ocserv config backed up and preserved."
  # The panel writes customer credentials to this password file. Keep ocserv's
  # plain authentication source aligned with the file the panel manages.
  if [[ -s /etc/ocserv/passwd && ! -s /etc/ocserv/ocpasswd ]]; then
    install -m 0600 /etc/ocserv/passwd /etc/ocserv/ocpasswd
  fi
  python3 - /etc/ocserv/ocserv.conf "$DOMAIN" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
domain = sys.argv[2]
lines = path.read_text(encoding='utf-8').splitlines()
settings = {
    'auth': 'auth = "plain[passwd=/etc/ocserv/ocpasswd]"',
    'server-cert': f'server-cert = /etc/letsencrypt/live/{domain}/fullchain.pem',
    'server-key': f'server-key = /etc/letsencrypt/live/{domain}/privkey.pem',
    'config-per-user': 'config-per-user = /etc/ocserv/config-per-user/',
    'max-same-clients': 'max-same-clients = 1',
}
found = set()
for index, line in enumerate(lines):
    match = re.match(r'^\s*(auth|server-cert|server-key|config-per-user|max-same-clients|route|no-route)\s*=', line)
    if match:
        key = match.group(1)
        if key in ('route', 'no-route'):
            # Existing split routes bypass ordinary Internet traffic.
            lines[index] = ''
        elif key not in found:
            lines[index] = settings[key]
            found.add(key)
        else:
            lines[index] = ''
for key, value in settings.items():
    if key not in found:
        lines.append(value)
lines = [line for line in lines if line]
lines.append('route = default')
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY
  if ! grep -Eq '^\s*device\s*=' /etc/ocserv/ocserv.conf; then
    printf '\ndevice = vpns\n' >> /etc/ocserv/ocserv.conf
  fi
else
cat > /etc/ocserv/ocserv.conf <<CONF
auth = "plain[passwd=/etc/ocserv/ocpasswd]"
tcp-port = ${VPN_PORT}
udp-port = ${VPN_PORT}
run-as-user = nobody
run-as-group = nogroup
socket-file = /run/ocserv-socket
server-cert = /etc/letsencrypt/live/${DOMAIN}/fullchain.pem
server-key = /etc/letsencrypt/live/${DOMAIN}/privkey.pem
device = vpns
max-clients = 100
config-per-user = /etc/ocserv/config-per-user/
max-same-clients = 1
keepalive = 32400
dpd = 90
mobile-dpd = 1800
try-mtu-discovery = false
ipv4-network = 10.20.30.0
ipv4-netmask = 255.255.255.0
dns = 1.1.1.1
dns = 8.8.8.8
route = default
tunnel-all-dns = true
CONF
fi

if [[ ! -e /etc/ocserv/ocpasswd ]]; then
  install -m 0600 /dev/null /etc/ocserv/ocpasswd
fi
chmod 0600 /etc/ocserv/ocpasswd
install -d -o root -g root -m 0750 /etc/ocserv/config-per-user

cat > /etc/sysctl.d/99-ocserv.conf <<'SYSCTL'
net.ipv4.ip_forward=1
SYSCTL
sysctl --system >/dev/null

install -m 0755 "$APP_SRC/helper/ocserv-panel-helper" /usr/local/sbin/ocserv-panel-helper
cat > /etc/sudoers.d/ocserv-panel <<'SUDOERS'
ocserv-panel ALL=(root) NOPASSWD: /usr/local/sbin/ocserv-panel-helper
SUDOERS
chmod 0440 /etc/sudoers.d/ocserv-panel
visudo -cf /etc/sudoers.d/ocserv-panel

id -u ocserv-panel >/dev/null 2>&1 || useradd --system --home-dir /var/lib/ocserv-panel --create-home --shell /usr/sbin/nologin ocserv-panel
getent group ssl-cert >/dev/null 2>&1 && usermod -aG ssl-cert ocserv-panel || true
install -d -o ocserv-panel -g ocserv-panel -m 0750 /var/lib/ocserv-panel
install -d -o root -g ocserv-panel -m 0750 /etc/ocserv-panel
install -d -o root -g ocserv-panel -m 0750 /etc/ocserv-panel/tls
printf '%s\n' "$DOMAIN" > /etc/ocserv-panel/vpn-domain
chown root:ocserv-panel /etc/ocserv-panel/vpn-domain
chmod 0640 /etc/ocserv-panel/vpn-domain
cat > /usr/local/sbin/ocserv-panel-sync-cert <<'SYNC_CERT'
#!/usr/bin/env bash
set -Eeuo pipefail
LINEAGE="${1:?Usage: ocserv-panel-sync-cert /etc/letsencrypt/live/<domain>}"
[[ -r "$LINEAGE/fullchain.pem" && -r "$LINEAGE/privkey.pem" ]] || {
  echo "Certificate or private key is unavailable in $LINEAGE" >&2
  exit 1
}
install -o root -g ocserv-panel -m 0640 "$LINEAGE/fullchain.pem" /etc/ocserv-panel/tls/fullchain.pem
install -o root -g ocserv-panel -m 0640 "$LINEAGE/privkey.pem" /etc/ocserv-panel/tls/privkey.pem
SYNC_CERT
chmod 0750 /usr/local/sbin/ocserv-panel-sync-cert
/usr/local/sbin/ocserv-panel-sync-cert "/etc/letsencrypt/live/${DOMAIN}"
if [[ ! -f /etc/ocserv-panel/secret_key ]]; then
  umask 027
  openssl rand -hex 48 > /etc/ocserv-panel/secret_key
fi
chown root:ocserv-panel /etc/ocserv-panel/secret_key
chmod 0640 /etc/ocserv-panel/secret_key

install -d -o root -g root -m 0755 /opt/ocserv-panel
cp -a "$APP_SRC/app.py" "$APP_SRC/VERSION" "$APP_SRC/requirements.txt" "$APP_SRC/templates" "$APP_SRC/static" /opt/ocserv-panel/
python3 -m venv /opt/ocserv-panel/.venv
/opt/ocserv-panel/.venv/bin/pip install --upgrade pip
/opt/ocserv-panel/.venv/bin/pip install -r /opt/ocserv-panel/requirements.txt
chown -R root:root /opt/ocserv-panel
# The panel service account must be able to traverse and execute the venv.
chmod -R a+rX /opt/ocserv-panel
chmod 0755 /opt/ocserv-panel/.venv/bin/python /opt/ocserv-panel/.venv/bin/gunicorn

cat > /usr/local/sbin/ocserv-nat <<'NAT'
#!/usr/bin/env bash
set -e
WAN_IF="$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
test -n "$WAN_IF"
VPN_SUBNET="$(python3 - <<'PY'
from pathlib import Path
import ipaddress
import re
text = Path('/etc/ocserv/ocserv.conf').read_text(encoding='utf-8')
def setting(name):
    matches = re.findall(r'^\s*' + name + r'\s*=\s*([^#\s]+)', text, re.M)
    return matches[-1] if matches else None
network, mask = setting('ipv4-network'), setting('ipv4-netmask')
if not network or not mask:
    raise SystemExit('ocserv ipv4-network or ipv4-netmask is missing')
print(ipaddress.ip_network(f'{network}/{mask}', strict=False))
PY
 )"
iptables -C FORWARD -s "$VPN_SUBNET" -o "$WAN_IF" -j ACCEPT 2>/dev/null || iptables -A FORWARD -s "$VPN_SUBNET" -o "$WAN_IF" -j ACCEPT
iptables -C FORWARD -d "$VPN_SUBNET" -i "$WAN_IF" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || iptables -A FORWARD -d "$VPN_SUBNET" -i "$WAN_IF" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -t nat -C POSTROUTING -s "$VPN_SUBNET" -o "$WAN_IF" -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s "$VPN_SUBNET" -o "$WAN_IF" -j MASQUERADE
NAT
chmod 0750 /usr/local/sbin/ocserv-nat

cat > /etc/systemd/system/ocserv-panel-expire.service <<'UNIT'
[Unit]
Description=Expire overdue ocserv customer accounts
After=ocserv.service
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/ocserv-panel-helper --expire
UNIT

cat > /etc/systemd/system/ocserv-panel-expire.timer <<'TIMER'
[Unit]
Description=Check ocserv customer expiry every five minutes
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true
[Install]
WantedBy=timers.target
TIMER

cat > /etc/systemd/system/ocserv-nat.service <<'UNIT'
[Unit]
Description=Network rules for ocserv
After=network-online.target
Wants=network-online.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/ocserv-nat
[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/systemd/system/ocserv-panel.service <<UNIT
[Unit]
Description=OpenConnect administration panel
After=network-online.target ocserv.service
Wants=network-online.target
[Service]
User=ocserv-panel
Group=ocserv-panel
WorkingDirectory=/opt/ocserv-panel
ExecStart=/opt/ocserv-panel/.venv/bin/gunicorn --workers 2 --bind 0.0.0.0:${PANEL_PORT} --certfile /etc/ocserv-panel/tls/fullchain.pem --keyfile /etc/ocserv-panel/tls/privkey.pem app:app
Restart=on-failure
RestartSec=3
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/ocserv-panel /etc/ocserv /etc/ocserv-panel /run
[Install]
WantedBy=multi-user.target
UNIT

mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/restart-ocserv-services <<HOOK
#!/bin/sh
set -eu
if [ "\${RENEWED_LINEAGE:-}" = "/etc/letsencrypt/live/${DOMAIN}" ]; then
  /usr/local/sbin/ocserv-panel-sync-cert "\$RENEWED_LINEAGE"
fi
systemctl restart ocserv.service ocserv-panel.service
HOOK
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/restart-ocserv-services

echo "Checking ocserv configuration..."
ocserv -t -c /etc/ocserv/ocserv.conf

echo "Set the panel administrator account."
cd /opt/ocserv-panel
/opt/ocserv-panel/.venv/bin/python app.py bootstrap
chown -R ocserv-panel:ocserv-panel /var/lib/ocserv-panel

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw allow 443/udp
  ufw allow 8443/tcp
fi

systemctl daemon-reload
systemctl enable --now ocserv-nat.service
systemctl restart ocserv-nat.service
systemctl enable --now ocserv.service
systemctl restart ocserv.service
systemctl enable --now ocserv-panel.service
systemctl enable --now ocserv-panel-expire.timer

echo
echo "Installation complete."
echo "Panel: https://${DOMAIN}:${PANEL_PORT}"
echo "VPN: ${DOMAIN}:${VPN_PORT} (TCP/UDP)"
echo "Next: sign in to the web panel and add VPN customers there. Each customer gets a personal Cisco profile URL."
echo "Open 80/TCP, 443/TCP+UDP and 8443/TCP in the VPS provider firewall."
