# UserrTM AnyConnect Panel

Ubuntu VPS üzerinde OpenConnect (`ocserv`) sunucusunu ve VPN müşteri hesaplarını web panelinden yönetir. Yönetim ekranı masaüstü ve telefonda çalışır; açık ve koyu görünüm sunar.

## Tek komutla kurulum

Ubuntu VPS'e root olarak SSH ile bağlan ve şu komutu çalıştır:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/userrtm/userrtm-anyconnect-panel/main/install.sh)
```

Kurulum alan adını, Let's Encrypt e-posta adresini ve isteğe bağlı ilk VPN müşterisini sorar. Sonra panel yöneticisi için kullanıcı adı ve güçlü bir parola belirletir. İşlem tamamlanınca panel adresini terminalde gösterir:

```text
https://ALAN_ADIN:8443
```

Alan adının A kaydı VPS IP'sine yönlenmelidir. VPS sağlayıcısının güvenlik duvarında 80/TCP (sertifika), 443/TCP ve 443/UDP (VPN), 8443/TCP (web paneli) açık olmalıdır. Kurulum sunucuya doğrudan `ocserv` ve panel servislerini yükler.

## Panel özellikleri

- VPN müşterisi ekleme, kalıcı silme, geçici olarak devre dışı bırakma ve yeniden etkinleştirme
- 1–3650 gün süreli hesap veya sınırsız hesap oluşturma; abonelik bitişini değiştirme
- Süresi dolan hesabı otomatik devre dışı bırakma (beş dakikada bir denetim)
- Müşteri VPN şifresini yenileme
- `ocserv` servis durumu, yapılandırma kontrolü, yeniden başlatma ve son günlük kayıtları
- DNS sunucularını değiştirme; değişiklikten önce yedek alma ve yapılandırma doğrulama
- Yönetici panel parolasını değiştirme
- Cisco Secure Client için sunucu listesini içeren XML profili ve URI ile içe aktarma adresi
- Açık/koyu tema ve telefon ekranına uyumlu görünüm

Cisco Secure Client uygulamasında **Profile Management → Import Profile → Network Location (URI)** seçeneğini aç ve panelde gösterilen `https://ALAN_ADIN:8443/profile.xml` adresini gir. Profil VPN sunucu adresini ekler; müşteri kullanıcı adı ve şifresi yine uygulamada ayrıca girilir.

## Güvenlik ve sınırlar

Panel root olarak web isteği çalıştırmaz. Ayrı servis kullanıcısı, CSRF koruması ve yalnızca tanımlı `ocserv-panel-helper` işlemlerine izin veren sudo kuralı kullanır. VPN parola dosyası ve müşteri durumu root tarafından korunur. Panel TLS'i Let's Encrypt ile sağlanır; sertifika yenilendiğinde VPN ve panel servisleri yeniden başlatılır.

Bu sürüm kullanıcı kotası, cihaz/HWID sınırı, ödeme alma, bayi/alt yönetici rolleri, uygulama içinden otomatik abonelik ödemesi veya farklı sunucuları tek merkezden yönetme özelliklerini içermez. Paneli yalnızca güvendiğin yöneticilerle paylaş; 8443/TCP erişimini sağlayıcı güvenlik duvarında kısıtlayabiliyorsan yönetici IP'lerine sınırla.

## Geliştirme ve kontroller

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app.py helper/ocserv-panel-helper
bash -n install.sh scripts/install-core.sh
node --check static/app.js
```
