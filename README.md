# UserrTM AnyConnect Panel

**Sürüm: 1.4.1**

Ubuntu VPS üzerinde OpenConnect (`ocserv`) sunucusunu ve müşteri hesaplarını web panelinden yönetir. Panel telefon ve masaüstüne uyumludur; açık/koyu tema sunar.

## Tek komutla kurulum

Ubuntu VPS'e root olarak SSH ile bağlan:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/userrtm/userrtm-anyconnect-panel/main/install.sh)
```

Kurulum VPN domain'ini, sabit profil/abonelik hostname'ini, Let's Encrypt e-postasını ve panel yöneticisi hesabını sorar. Abonelik hostname'i müşteriye vereceğin sabit adres içindir. Bu domain'in A kaydı profil panelini çalıştıran VPS'e yönlenmeli; TLS sertifikası VPN domain'i ve abonelik domain'i için alınır. Kurulum mevcut kullanıcı verisini korur.

Sağlayıcı güvenlik duvarında 80/TCP (Let's Encrypt), VPN için 443/TCP ve 443/UDP, web paneli için 8443/TCP açık olmalı. Kurulum, VPN IP havuzuna göre NAT/FORWARD kurallarını servisin her açılışında uygular.

## Sürüm 1.4.0

- Yeni müşterinin süresi gün sayısıyla veya takvimden bitiş tarihi seçerek ayarlanabilir; sınırsız seçenek de bulunur.
- Müşterinin süresi sonradan aynı seçeneklerle değiştirilebilir.
- Panel dili Türkçe, Rusça veya İngilizce seçilebilir ve seçim tarayıcıda saklanır.
- Paneldeki işlemler içerikleri arka planda günceller; tam sayfa yenilemesi gerekmez. Panelde açılış, modal, müşteri satırı ve işlem bekleme animasyonları bulunur.
- Sürüm numarası statik dosya adreslerine eklenir; yeni kurulumdan sonra tarayıcının eski arayüz dosyalarını kullanma ihtimali azaltılır.

Takvimde seçilen tarih, paneli açan yöneticinin yerel saatine göre o günün sonuna kadar geçerlidir. Gün sayısı 1–3650 aralığındadır.

## Sürüm 1.3.0

- Ayrı, sabit abonelik taban adresi: müşteri profil linkleri panel alan adı/VPN uç domain'inden bağımsız kalır.
- Birincil ve yedek VPN domain/IP ile port tanımlama; XML profilinde ikisi de gösterilir, seçilen aktif uç ilk sırada yer alır.
- Token korumalı REST API: bayi/satıcı panelinden müşteri ve AnyConnect sunucusu yönetimi.
- `sudo any` terminal menüsü: durum, uç/abonelik ayarları, panel yönetici adı/şifresi, web portu, API tokenı ve kaldırma.
- Panel sürümü arayüzde ve `VERSION` dosyasında tutulur.

## Sabit abonelik ve yedek VPN

Web panelinde **Ayarlar → Sabit abonelik ve VPN sunucuları** bölümünde şunları gir:

- Ana abonelik adresi, örneğin `https://userrtm.sub.com:8443`
- Birincil ve yedek VPN domain/IP ve portları
- Profilde önce gösterilecek aktif uç

Sabit abonelik domain'i profil XML'ini sunan bu panele gitmeli. Alan adının TLS sertifikasında yoksa `sudo any` menüsünde **Birincil/yedek VPN ve abonelik URL ayarla** seçeneği sertifikayı Let's Encrypt ile genişletir; DNS kaydı önce bu VPS'e yönlenmeli ve doğrulama sırasında TCP 80 boş olmalı.

Panel ve bayi API'si, yeni müşterinin profil linkini kayıtlı ana abonelik adresiyle oluşturur. Müşteri listesinden kopyalanan link de aynı adresi kullanır. Adres kaydedilene kadar yeni müşteri oluşturulamaz.

VPN ucu değiştiğinde müşteri linki sabit kalır. Link açıldığında XML en son kayıtlı aktif VPN ucunu ve varsa yedek ucu gösterir. Aktif ucu panelden değiştirdikten sonra müşteri aynı URL'yi yeniden içe aktarmalıdır. Profilde iki sunucu da önceden varsa müşteri AnyConnect sunucu listesinden yedeği seçebilir.

Yeni VPS'te aynı müşterinin bağlanabilmesi için o kullanıcı adı ve VPN şifresi yeni VPS'teki AnyConnect sunucusunda da bulunmalıdır. Bu API her paneldeki yerel `ocserv` hesaplarını yönetir; sunucular arasında parola veritabanını kendiliğinden çoğaltmaz. Bayi paneli aynı müşteri hesabını primary ve backup VPS'lerde ayrı ayrı oluşturup yönetmelidir.

## Satıcı/bayi API'si

API tokenı yerel terminalde yönetilir:

```bash
sudo any
```

Menüden **Seller API tokenını göster** seçeneği tokenı ekrana verir; **yenile** eski tokenı hemen geçersiz kılar. Tokenı yalnızca bayi panelinin gizli sunucu ayarına kaydet; URL, tarayıcı kodu, GitHub veya müşteri profil linkine koyma. API isteklerinde `Authorization: Bearer TOKEN` başlığını kullan.

Temel adres: `https://PANEL-DOMAIN:8443/api/v1`

| İşlem | Yöntem ve uç |
|---|---|
| Bağlantı/sürüm/uç durumu | `GET /health` |
| Birincil/yedek ağ ayarları | `GET /network` |
| Uç ayarlarını değiştir | `POST /network` |
| Müşteri listesi | `GET /customers` |
| Müşteri oluştur | `POST /customers` |
| Müşteriyi sil | `DELETE /customers/{username}` |
| Etkin/devre dışı | `POST /customers/{username}/status` |
| Süre | `POST /customers/{username}/expiry` |
| Cihaz limiti (1–4) | `POST /customers/{username}/limit` |
| VPN parolası | `POST /customers/{username}/password` |

Müşteri oluşturma örnek gövdesi:

```json
{"username":"musteri01","password":"vpn-secret","days":30,"max_same_clients":1}
```

`days: null` sınırsız süre demektir. Müşteri oluşturma cevabı `profile_url` döndürür. Tokenı yalnızca TLS üzerinden, güvenilir bayi paneli sunucusunda sakla; bayi panelindeki AnyConnect panel adresi olarak `https://PANEL-DOMAIN:8443`, token olarak `sudo any` menüsünden aldığın değeri kullan.

Müşteri ekleme veya süre güncelleme isteğinde gün yerine `expires_at` alanıyla Unix zaman damgası gönderilebilir; `expires_at: null` süresiz erişim verir.

## Terminal menüsü

`sudo any` seçenekleri panel/VPN durumunu gösterir; primary/backup VPN uçlarını ve sabit abonelik URL'sini ayarlar; panel kullanıcı adı/şifresi ile web portunu değiştirir; API tokenını gösterir veya yeniler. Kaldırma seçeneği ayrıca `DELETE ANYCONNECT PANEL` yazılı onayı ister ve bu VPS'teki paneli, `ocserv` yapılandırmasını ve VPN hesap verilerini siler.

## Profil ve oturum limiti

Müşteri oluşturulduğunda panel kişiye özel, iptal edilebilir XML profil URL'sini üretir. Cisco Secure Client'ta **Profile Management → Import Profile → Network Location (URI)** yoluyla eklenir. Cisco Android uygulaması kullanıcı adı ve şifreyi bu XML profilinden almaz ve parolayı kalıcı kaydetmez; müşteri VPN giriş bilgilerini bağlantı sırasında girer. Profil URL'si bağlantı bilgisi içermeyen, erişim anahtarı niteliğinde özel bir linktir.

1–4 eşzamanlı oturum sınırı müşteri başına uygulanır. Bu fiziksel cihaz/HWID kilidi değildir. Hesap devre dışı bırakılır, süresi dolar veya silinirse kişisel profil linki geçersizleşir.

## Güvenlik

Web servisi ayrı, yetkileri sınırlı kullanıcıyla çalışır; root işlemleri sabit izinli helper üzerinden yapılır. API tokenı `/etc/ocserv-panel/api-token` içinde `root:ocserv-panel`, `0640` izinleriyle tutulur. Paneli yalnızca güvendiğin yöneticiler ve bayi sistemleriyle kullan. Mümkünse 8443/TCP'yi sağlayıcı güvenlik duvarında yönetici IP'lerine sınırla.

## Geliştirme

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app.py helper/ocserv-panel-helper
bash -n install.sh scripts/install-core.sh scripts/any-menu.sh
node --check static/app.js
```
