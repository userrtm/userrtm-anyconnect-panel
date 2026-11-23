# OpenConnect / AnyConnect Sunucu Paneli

Ubuntu üzerinde `ocserv` hesaplarını ve temel sunucu ayarlarını yönetmek için web paneli. Bu ilk sürümde yönetici girişi, müşteri ekleme/silme, servis durumu ve yeniden başlatma, DNS ayarları, son kayıtlar ve açık/koyu tema bulunur.

## Gereksinimler

- Ubuntu 24.04 veya daha yeni
- VPS IP adresine yönlenen bir alan adı A kaydı
- Dış güvenlik duvarında 80/TCP, 443/TCP, 443/UDP ve 8443/TCP erişimi
- Root SSH erişimi

## Kurulum

Bu klasörü VPS'e yükle ve klasörün içinden çalıştır:

```bash
sudo bash install.sh
```

Kurulum alan adını, Let's Encrypt e-posta adresini, ilk VPN kullanıcı hesabını ve panel yöneticisini sorar. Panel `https://ALAN_ADIN:8443` adresinden açılır.

Panel genel bir terminal açmaz. Root işlemleri sadece izinleri sınırlandırılmış `ocserv-panel-helper` üzerinden yürütülür.

## Güvenlik

Gerçek parolaları, özel anahtarları, `.env` dosyalarını veya `/etc/letsencrypt` içeriğini GitHub'a yükleme. Depoda üretim kimlik bilgileri bulunmamalı.

## Sınırlamalar

- DNS değişikliklerinden önce yapılandırmanın yedeği alınır ve `ocserv -t` ile kontrol edilir.
- Panel 8443/TCP'de çalışır; VPN 443/TCP ve 443/UDP kullanır.
- Sağlayıcının VPS dış güvenlik duvarında da gerekli portları aç.
- Bu ilk sürümde süre sonu takibi, bayi/alt yönetici rolleri ve kullanım kotası yönetimi bulunmuyor; sonraki geliştirme aşamalarına eklenebilir.
