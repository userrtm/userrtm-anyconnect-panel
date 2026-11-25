#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Root gerekli: sudo any"
  exit 1
fi

APP_DIR=/opt/ocserv-panel
DB_PATH=/var/lib/ocserv-panel/panel.db
NETWORK=/var/lib/ocserv-panel/network.json
API_TOKEN=/etc/ocserv-panel/api-token
UNIT=/etc/systemd/system/ocserv-panel.service

pause() { read -rp "Devam etmek için Enter..." _; }
panel_port() {
  sed -n 's/.*--bind 0\.0\.0\.0:\([0-9][0-9]*\).*/\1/p' "$UNIT" | head -n1
}
show_status() {
  echo "AnyConnect panel: $(systemctl is-active ocserv-panel.service 2>/dev/null || true)"
  echo "ocserv VPN:      $(systemctl is-active ocserv.service 2>/dev/null || true)"
  echo "Panel portu:     $(panel_port)"
  if [[ -f $NETWORK ]]; then
    python3 - "$NETWORK" <<'PY'
import json, sys
try:
    d=json.load(open(sys.argv[1], encoding='utf-8'))
    print('Birincil VPN:    %s:%s' % (d.get('primary_host',''), d.get('primary_port',443)))
    print('Yedek VPN:       %s' % ((d.get('backup_host','') + ':' + str(d.get('backup_port',443))) if d.get('backup_host') else 'ayarlı değil'))
    print('Aktif profil:    %s' % d.get('active_endpoint','primary'))
    print('Abonelik URL:    %s' % (d.get('subscription_base_url') or 'panel adresinden üretiliyor'))
except Exception:
    print('Profil ayarları okunamadı.')
PY
  fi
  echo
}
admin_python() {
  "$APP_DIR/.venv/bin/python" - "$DB_PATH" "$@" <<'PY'
import getpass, grp, os, re, secrets, sqlite3, sys
from werkzeug.security import generate_password_hash
from pathlib import Path
db=sys.argv[1]
mode=sys.argv[2]
con=sqlite3.connect(db)
def invalidate_sessions():
    p=Path('/etc/ocserv-panel/secret_key')
    p.write_text(secrets.token_hex(48)+'\n',encoding='utf-8')
    os.chown(p,0,grp.getgrnam('ocserv-panel').gr_gid)
    os.chmod(p,0o640)
if mode == 'username':
    old=input('Mevcut yönetici kullanıcı adı: ').strip()
    new=input('Yeni yönetici kullanıcı adı: ').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,32}', new):
        raise SystemExit('Kullanıcı adı 3–32 karakter olmalı; harf, rakam, _ veya - kullan.')
    cur=con.execute('UPDATE admins SET username=? WHERE username=?', (new, old))
    if cur.rowcount != 1:
        raise SystemExit('Yönetici hesabı bulunamadı.')
    con.commit()
    invalidate_sessions()
    print('Yönetici kullanıcı adı güncellendi.')
elif mode == 'password':
    username=input('Yönetici kullanıcı adı: ').strip()
    first=getpass.getpass('Yeni panel şifresi: ')
    second=getpass.getpass('Yeni panel şifresini tekrar yaz: ')
    if not first or len(first)>256 or '\n' in first or '\r' in first:
        raise SystemExit('Şifre boş olamaz; en fazla 256 karakter olabilir.')
    if first != second:
        raise SystemExit('Şifreler eşleşmiyor.')
    cur=con.execute('UPDATE admins SET password_hash=? WHERE username=?', (generate_password_hash(first), username))
    if cur.rowcount != 1:
        raise SystemExit('Yönetici hesabı bulunamadı.')
    con.commit()
    invalidate_sessions()
    print('Panel şifresi güncellendi.')
else:
    raise SystemExit('Bilinmeyen işlem.')
con.close()
PY
}
rotate_api_token() {
  local confirm token
  read -rp "API token değişecek; bayi panelindeki eski token çalışmayı durdurur. Devam için ROTATE yaz: " confirm
  [[ $confirm == ROTATE ]] || { echo "İptal edildi."; return; }
  token="$(openssl rand -hex 32)"
  install -o root -g ocserv-panel -m 0640 /dev/null "$API_TOKEN"
  printf '%s\n' "$token" > "$API_TOKEN"
  chown root:ocserv-panel "$API_TOKEN"
  chmod 0640 "$API_TOKEN"
  echo "Yeni API token (bir kez kopyala, seller paneline kaydet):"
  echo "$token"
}
show_api_token() {
  if [[ ! -s $API_TOKEN ]]; then echo "API token bulunamadı."; return 1; fi
  echo "API token: $(cat "$API_TOKEN")"
  local base
  base="$(python3 - "$NETWORK" "$(cat /etc/ocserv-panel/vpn-domain 2>/dev/null || hostname)" "$(panel_port)" <<'PY'
import json,sys
from pathlib import Path
try: d=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
except Exception: d={}
print(d.get('subscription_base_url') or f'https://{sys.argv[2]}:{sys.argv[3]}')
PY
)"
  echo "API temel adresi: ${base%/}/api/v1"
}
ensure_subscription_cert() {
  local base="$1" host vpn_domain email
  [[ -n $base ]] || return 0
  host="$(python3 - "$base" <<'PY'
import sys
from urllib.parse import urlsplit
print(urlsplit(sys.argv[1]).hostname or '')
PY
)"
  [[ -n $host ]] || { echo "Abonelik adresinden hostname alınamadı."; return 1; }
  vpn_domain="$(cat /etc/ocserv-panel/vpn-domain 2>/dev/null || true)"
  [[ -n $vpn_domain && -f "/etc/letsencrypt/live/$vpn_domain/fullchain.pem" ]] || { echo "VPN sertifikası bulunamadı."; return 1; }
  openssl x509 -in "/etc/letsencrypt/live/$vpn_domain/fullchain.pem" -noout -checkhost "$host" >/dev/null 2>&1 && return 0
  if python3 - "$host" <<'PY' >/dev/null 2>&1
import ipaddress,sys
ipaddress.ip_address(sys.argv[1])
PY
  then echo "Sabit HTTPS aboneliği için sertifikalı bir domain kullan; bu host IP adresi."; return 1; fi
  if ss -H -lnt 'sport = :80' 2>/dev/null | grep -q .; then
    echo "Sertifikayı genişletmek için Let's Encrypt doğrulama sırasında TCP 80 boş olmalı."; return 1
  fi
  read -rp "Let's Encrypt e-posta adresi: " email
  [[ $email == *@*.* ]] || { echo "E-posta adresi geçersiz."; return 1; }
  mapfile -t domains < <(openssl x509 -in "/etc/letsencrypt/live/$vpn_domain/fullchain.pem" -noout -ext subjectAltName | grep -oE 'DNS:[A-Za-z0-9.-]+' | cut -d: -f2 | sort -u)
  [[ ${#domains[@]} -gt 0 ]] || domains=("$vpn_domain")
  if [[ ! " ${domains[*]} " =~ " ${host} " ]]; then domains+=("$host"); fi
  local -a cert_args=()
  for d in "${domains[@]}"; do cert_args+=(-d "$d"); done
  certbot certonly --standalone --non-interactive --agree-tos --email "$email" --expand --cert-name "$vpn_domain" "${cert_args[@]}" || return 1
  /usr/local/sbin/ocserv-panel-sync-cert "/etc/letsencrypt/live/$vpn_domain"
  systemctl restart ocserv.service ocserv-panel.service
}
save_network() {
  local primary_host primary_port backup_host backup_port active base payload result
  read -rp "Birincil VPN domain/IP: " primary_host
  read -rp "Birincil VPN portu [443]: " primary_port; primary_port=${primary_port:-443}
  read -rp "Yedek VPN domain/IP (boş bırakılabilir): " backup_host
  read -rp "Yedek VPN portu [443]: " backup_port; backup_port=${backup_port:-443}
  read -rp "Profilde önce gösterilecek uç (primary/backup) [primary]: " active; active=${active:-primary}
  read -rp "Sabit HTTPS abonelik taban adresi (boş=bu panel adresi): " base
  ensure_subscription_cert "$base" || return 1
  payload="$(python3 - "$primary_host" "$primary_port" "$backup_host" "$backup_port" "$active" "$base" <<'PY'
import json, sys
print(json.dumps({'op':'save_network','primary_host':sys.argv[1],'primary_port':int(sys.argv[2]),'backup_host':sys.argv[3],'backup_port':int(sys.argv[4]),'active_endpoint':sys.argv[5],'subscription_base_url':sys.argv[6]}))
PY
)"
  result="$(printf '%s' "$payload" | /usr/local/sbin/ocserv-panel-helper)"
  echo "$result" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("data",{}).get("message") or d.get("error"))'
  if [[ $base == https://* ]]; then
    echo "Not: Sabit abonelik alan adının DNS'i bu panel VPS'ine yönlenmeli; TLS sertifikası bu adı içermeli."
  fi
}
change_panel_port() {
  local old new
  old="$(panel_port)"
  read -rp "Yeni panel TCP portu (1024–65535): " new
  [[ $new =~ ^[0-9]+$ ]] && (( new >= 1024 && new <= 65535 )) || { echo "Geçersiz port."; return 1; }
  if [[ $new != "$old" ]] && ss -H -lnt "sport = :$new" 2>/dev/null | grep -q .; then
    echo "Port $new kullanımda."; return 1
  fi
  sed -i "s/--bind 0.0.0.0:${old}/--bind 0.0.0.0:${new}/" "$UNIT"
  if [[ -f $NETWORK ]]; then
    python3 - "$NETWORK" "$old" "$new" <<'PY'
import json, os, sys, tempfile
from pathlib import Path
p=Path(sys.argv[1]); data=json.loads(p.read_text(encoding='utf-8'))
old,new=int(sys.argv[2]),int(sys.argv[3]); base=data.get('subscription_base_url','')
if base:
    from urllib.parse import urlsplit
    from urllib.parse import urlunsplit
    u=urlsplit(base)
    if u.port == old:
        host='['+u.hostname+']' if ':' in u.hostname else u.hostname
        data['subscription_base_url']=urlunsplit((u.scheme,host+':'+str(new),u.path,u.query,u.fragment))
fd,name=tempfile.mkstemp(prefix='.network.',dir=str(p.parent),text=True)
with os.fdopen(fd,'w',encoding='utf-8') as f:
    json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
os.chmod(name,0o640); os.replace(name,p)
PY
  fi
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -q 'Status: active'; then ufw allow "$new/tcp"; fi
  systemctl daemon-reload
  systemctl restart ocserv-panel.service
  echo "Panel portu $new olarak değiştirildi. Sağlayıcı güvenlik duvarında da TCP $new açılmalı."
  echo "Panel: https://$(hostname -f 2>/dev/null || hostname):$new"
}
uninstall_panel() {
  local confirm
  echo "Bu işlem AnyConnect panelini, ocserv VPN servisini ve bu sunucudaki VPN kullanıcı/veri dosyalarını kaldırır."
  read -rp "Devam etmek için DELETE ANYCONNECT PANEL yaz: " confirm
  [[ $confirm == 'DELETE ANYCONNECT PANEL' ]] || { echo "İptal edildi."; return; }
  if [[ -f /etc/ocserv/ocserv.conf ]]; then
    local wan subnet
    wan="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
    subnet="$(python3 - <<'PY'
import ipaddress,re
from pathlib import Path
p=Path('/etc/ocserv/ocserv.conf')
if p.exists():
    t=p.read_text(encoding='utf-8')
    def v(n):
        m=re.findall(r'^\s*'+n+r'\s*=\s*([^#\s]+)',t,re.M); return m[-1] if m else ''
    if v('ipv4-network') and v('ipv4-netmask'):
        print(ipaddress.ip_network(v('ipv4-network')+'/'+v('ipv4-netmask'),strict=False))
PY
)"
    if [[ -n $wan && -n $subnet ]]; then
      iptables -D FORWARD -s "$subnet" -o "$wan" -j ACCEPT 2>/dev/null || true
      iptables -D FORWARD -d "$subnet" -i "$wan" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
      iptables -t nat -D POSTROUTING -s "$subnet" -o "$wan" -j MASQUERADE 2>/dev/null || true
    fi
  fi
  local old_port; old_port="$(panel_port)"
  systemctl disable --now ocserv-panel-expire.timer ocserv-panel.service ocserv-nat.service ocserv.service 2>/dev/null || true
  rm -f /etc/systemd/system/ocserv-panel.service /etc/systemd/system/ocserv-panel-expire.service /etc/systemd/system/ocserv-panel-expire.timer /etc/systemd/system/ocserv-nat.service
  rm -f /usr/local/sbin/ocserv-panel-helper /usr/local/sbin/ocserv-nat /usr/local/sbin/ocserv-panel-sync-cert /usr/local/bin/any /etc/sudoers.d/ocserv-panel
  rm -rf /opt/ocserv-panel /etc/ocserv-panel /var/lib/ocserv-panel /etc/ocserv/config-per-user
  rm -f /etc/ocserv/ocserv.conf /etc/ocserv/ocpasswd /etc/ocserv/passwd
  rm -f /etc/sysctl.d/99-ocserv.conf /etc/letsencrypt/renewal-hooks/deploy/restart-ocserv-services
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -q 'Status: active'; then
    [[ -n $old_port ]] && ufw delete allow "$old_port/tcp" || true
    ufw delete allow 443/tcp || true
    ufw delete allow 443/udp || true
  fi
  systemctl daemon-reload
  apt-get purge -y ocserv >/dev/null 2>&1 || true
  echo "AnyConnect panel and its local ocserv data were removed. Review provider firewall and old DNS records manually."
  exit 0
}

while true; do
  clear || true
  echo "UserrTM AnyConnect Panel · $(cat /opt/ocserv-panel/VERSION 2>/dev/null || echo unknown)"
  echo "1) Durum ve sunucu uçları"
  echo "2) Birincil/yedek VPN ve abonelik URL ayarla"
  echo "3) Panel yöneticisi kullanıcı adını değiştir"
  echo "4) Panel yöneticisi parolasını değiştir"
  echo "5) Web panel portunu değiştir"
  echo "6) Seller API tokenını göster"
  echo "7) Seller API tokenını yenile"
  echo "8) AnyConnect panelini ve yerel VPN kullanıcılarını kaldır"
  echo "0) Çıkış"
  read -rp "Seçim: " choice
  case "$choice" in
    1) show_status; pause ;;
    2) save_network || true; pause ;;
    3) admin_python username && systemctl restart ocserv-panel.service; pause ;;
    4) admin_python password && systemctl restart ocserv-panel.service; pause ;;
    5) change_panel_port; pause ;;
    6) show_api_token; pause ;;
    7) rotate_api_token; pause ;;
    8) uninstall_panel ;;
    0) exit 0 ;;
    *) echo "Geçersiz seçim."; pause ;;
  esac
done
