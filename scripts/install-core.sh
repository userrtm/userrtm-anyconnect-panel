#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then echo "Run as root: sudo bash install.sh"; exit 1; fi
if ! grep -qi ubuntu /etc/os-release; then echo "This installer supports Ubuntu only."; exit 1; fi

APP_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VPN_PORT=443
PANEL_PORT=8443
read -rp "VPN domain (for example vpn.example.com): " DOMAIN
read -rp "Let's Encrypt email: " EMAIL
read -rp "First VPN customer username (leave blank to skip): " FIRST_USER

if [[ ! "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]]; then echo "Invalid domain."; exit 1; fi
if [[ -n "$FIRST_USER" && ! "$FIRST_USER" =~ ^[A-Za-z0-9_-]{1,32}$ ]]; then echo "Invalid username."; exit 1; fi

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
  if ! grep -Eq '^\s*device\s*=' /etc/ocserv/ocserv.conf; then
    printf '\n# Added by the panel installer\ndevice = vpns\n' >> /etc/ocserv/ocserv.conf
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
max-same-clients = 2
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

if [[ -n "$FIRST_USER" ]]; then
  echo "Create or update the VPN account; enter its password twice."
  ocpasswd -c /etc/ocserv/ocpasswd "$FIRST_USER"
  chmod 600 /etc/ocserv/ocpasswd
fi

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
if [[ ! -f /etc/ocserv-panel/secret_key ]]; then
  umask 027
  openssl rand -hex 48 > /etc/ocserv-panel/secret_key
fi
chown root:ocserv-panel /etc/ocserv-panel/secret_key
chmod 0640 /etc/ocserv-panel/secret_key

install -d -o root -g root -m 0755 /opt/ocserv-panel
cp -a "$APP_SRC/app.py" "$APP_SRC/requirements.txt" "$APP_SRC/templates" "$APP_SRC/static" /opt/ocserv-panel/
python3 -m venv /opt/ocserv-panel/.venv
/opt/ocserv-panel/.venv/bin/pip install --upgrade pip
/opt/ocserv-panel/.venv/bin/pip install -r /opt/ocserv-panel/requirements.txt
chown -R root:root /opt/ocserv-panel

cat > /usr/local/sbin/ocserv-nat <<'NAT'
#!/usr/bin/env bash
set -e
WAN_IF="$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
test -n "$WAN_IF"
iptables -C FORWARD -s 10.20.30.0/24 -o "$WAN_IF" -j ACCEPT 2>/dev/null || iptables -A FORWARD -s 10.20.30.0/24 -o "$WAN_IF" -j ACCEPT
iptables -C FORWARD -d 10.20.30.0/24 -i "$WAN_IF" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || iptables -A FORWARD -d 10.20.30.0/24 -i "$WAN_IF" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -t nat -C POSTROUTING -s 10.20.30.0/24 -o "$WAN_IF" -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s 10.20.30.0/24 -o "$WAN_IF" -j MASQUERADE
NAT
chmod 0750 /usr/local/sbin/ocserv-nat

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
ExecStart=/opt/ocserv-panel/.venv/bin/gunicorn --workers 2 --bind 0.0.0.0:${PANEL_PORT} --certfile /etc/letsencrypt/live/${DOMAIN}/fullchain.pem --keyfile /etc/letsencrypt/live/${DOMAIN}/privkey.pem app:app
Restart=on-failure
RestartSec=3
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/ocserv-panel /etc/ocserv /run
[Install]
WantedBy=multi-user.target
UNIT

mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/restart-ocserv-services <<'HOOK'
#!/bin/sh
systemctl restart ocserv.service ocserv-panel.service
HOOK
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/restart-ocserv-services

echo "Checking ocserv configuration..."
ocserv -t -c /etc/ocserv/ocserv.conf

echo "Set the panel administrator account."
cd /opt/ocserv-panel
sudo -u ocserv-panel /opt/ocserv-panel/.venv/bin/python app.py bootstrap

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw allow 443/udp
  ufw allow 8443/tcp
fi

systemctl daemon-reload
systemctl enable --now ocserv-nat.service
systemctl enable --now ocserv.service
systemctl restart ocserv.service
systemctl enable --now ocserv-panel.service

echo
echo "Installation complete."
echo "Panel: https://${DOMAIN}:${PANEL_PORT}"
echo "VPN: ${DOMAIN}:${VPN_PORT} (TCP/UDP)"
echo "Open 80/TCP, 443/TCP+UDP and 8443/TCP in the VPS provider firewall."
