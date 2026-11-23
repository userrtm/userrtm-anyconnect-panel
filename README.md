# OpenConnect / AnyConnect Sunucu Paneli

Ubuntu üzerinde `ocserv` hesaplarını ve temel sunucu ayarlarını yönetmek için web paneli. İlk sürümde yönetici girişi, müşteri ekleme/silme, servis durumu ve yeniden başlatma, DNS ayarları, son kayıtlar ve açık/koyu tema bulunur.

## Kurulum

Ubuntu VPS'te root hesabıyla bu tek komutu çalıştır. Bu biçim, kurulum sorularının SSH terminalinden yanıtlanmasını sağlar:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/userrtm/userrtm-anyconnect-panel/main/install.sh)
```

Kurulum betiği GitHub'daki kaynak paketini geçici bir klasöre indirir ve kurulum sihirbazını başlatır. Alan adını, Let's Encrypt e-posta adresini, ilk VPN kullanıcı hesabını ve panel yöneticisini sorar. Panel `https://ALAN_ADIN:8443` adresinden açılır.

> GitHub deposunun herkese açık olması gerekir ki VPS oturum açmadan `curl` ile dosyayı indirebilsin.

## Gereksinimler

- Ubuntu 24.04 veya daha yeni
- VPS IP adresine yönlenen alan adı A kaydı
- Dış güvenlik duvarında 80/TCP, 443/TCP, 443/UDP ve 8443/TCP erişimi
- Root SSH erişimi

Panel genel bir terminal açmaz. Root işlemleri sadece izinleri sınırlandırılmış `ocserv-panel-helper` üzerinden yürütülür.

## Güvenlik ve sınırlamalar

Gerçek parolaları, özel anahtarları, `.env` dosyalarını veya `/etc/letsencrypt` içeriğini depoya yükleme. DNS değişikliklerinden önce yapılandırmanın yedeği alınır ve `ocserv -t` ile kontrol edilir. Bu ilk sürümde süre sonu takibi, bayi/alt yönetici rolleri ve kullanım kotası yönetimi bulunmuyor.
