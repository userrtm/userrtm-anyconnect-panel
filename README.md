# UserrTM AnyConnect Panel

**Sürüm: 1.2.0**

Ubuntu VPS üzerinde OpenConnect (`ocserv`) sunucusunu ve VPN müşteri hesaplarını web panelinden yönetir. Yönetim ekranı masaüstü ve telefonda çalışır; açık ve koyu görünüm sunar.

## Tek komutla kurulum

Ubuntu VPS'e root olarak SSH ile bağlan ve şu komutu çalıştır:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/userrtm/userrtm-anyconnect-panel/main/install.sh)
```

Kurulum yalnızca VPN servisini ve yönetim panelini kurar; müşteri hesabı kurulum sırasında oluşturulmaz. Kurulum alan adını, Let's Encrypt e-posta adresini ve panel yöneticisi için kullanıcı adı ile parolayı sorar. Boş parola kabul edilmez; başka bir minimum karakter zorunluluğu yoktur. Panel açıldıktan sonra müşterileri **Müşteriler → Müşteri ekle** bölümünden oluşturursun. İstersen panel güvenli VPN şifresi üretir. İşlem tamamlanınca panel adresini terminalde gösterir:

```text
https://ALAN_ADIN:8443
```

Alan adının A kaydı VPS IP'sine yönlenmelidir. VPS sağlayıcısının güvenlik duvarında 80/TCP (sertifika), 443/TCP ve 443/UDP (VPN), 8443/TCP (web paneli) açık olmalıdır. Güncelleme mevcut ocserv ayarını yedekler; panelin kullandığı VPN parola dosyası ile ocserv ayarını ve VPN sertifika alan adını eşitler. NAT ve yönlendirme kuralları ocserv'deki VPN IP havuzundan otomatik hesaplanır, servis her başladığında tekrar uygulanır. Panelin kurulu sürümü sol menüde ve sayfa altında görünür; her yayın için `VERSION` dosyası güncellenir.

## Sürüm 1.2.0

- VPN IP havuzundan hesaplanan NAT ve FORWARD kuralları her sunucu başlangıcında uygulanır.
- Her müşteri için 1–4 eşzamanlı AnyConnect bağlantısı seçilebilir ve panelden değiştirilebilir.
- Panel sürümü arayüzde gösterilir.

## Panel özellikleri

- VPN müşterisi ekleme, kalıcı silme, geçici olarak devre dışı bırakma ve yeniden etkinleştirme
- 1–3650 gün süreli hesap veya sınırsız hesap oluşturma; abonelik bitişini değiştirme
- Süresi dolan hesabı otomatik devre dışı bırakma (beş dakikada bir denetim)
- Müşteri VPN şifresini yenileme (boş olmayan, en fazla 128 karakter)
- `ocserv` servis durumu, yapılandırma kontrolü, yeniden başlatma ve son günlük kayıtları
- DNS sunucularını değiştirme; değişiklikten önce yedek alma ve yapılandırma doğrulama
- Yönetici panel parolasını değiştirme
- Her müşteri için 1–4 arası eşzamanlı bağlantı sınırı; kullanıcı oluştururken seçilebilir ve sonradan değiştirilebilir
- Her müşteri için ayrı, rastgele korunan ve hesap devre dışı bırakılınca veya silinince geçersiz olan Cisco Secure Client XML profil URL'si
- Müşteri eklerken VPN şifresi üretme; müşteri profil adresini panelden kopyalama
- Müşteri oluşturma tamamlanınca listeyi anında yenileme, satırı vurgulama ve yönetici hareketini kaydetme
- Ayrı içerikli gezinme menüleri, son yönetici hareketleri ve VPN günlükleri
- Eksik VPN parola dosyası veya tanınmayan sertifika alan adı için panel uyarısı
- Açık/koyu tema ve telefon ekranına uyumlu görünüm

Müşteri oluşturulduktan sonra satırındaki **URI'yi kopyala** düğmesine bas. Müşteri Cisco Secure Client uygulamasında **Profile Management → Import Profile → Network Location (URI)** yolunu izleyip kendisine gönderdiğin bu özel adresi ekler. Profil VPN sunucu adresini ekler; bağlanırken kendi müşteri kullanıcı adı ve VPN şifresini ayrıca girer. Panel yöneticisi parolası Cisco Secure Client’ta kullanılmaz. Hesap devre dışı bırakılır, süresi biter veya silinirse özel profil URL'si çalışmaz. `/profile.xml` yönetici genel profilidir; müşterilere kişiye özel URL gönder.

## Güvenlik ve sınırlar

Panel root olarak web isteği çalıştırmaz. Ayrı servis kullanıcısı, CSRF koruması ve yalnızca tanımlı `ocserv-panel-helper` işlemlerine izin veren sudo kuralı kullanır. VPN parola dosyası ve müşteri durumu root tarafından korunur. Profilde görünen sunucu adı VPN sertifikasındaki alan adıyla eşleşir. Panel TLS'i Let's Encrypt ile sağlanır; sertifika yenilendiğinde VPN ve panel servisleri yeniden başlatılır.

Cihaz sınırı aynı kullanıcı hesabıyla izin verilen eşzamanlı VPN oturumu sayısını kontrol eder. Örneğin sınır 1 ise ikinci bağlantı reddedilir; ilk cihazın bağlantısı kapandıktan sonra başka bir cihaz bağlanabilir. Bu özellik fiziksel cihaz/HWID kaydı değildir. Panel kullanıcı kotası, ödeme alma, bayi/alt yönetici rolleri, uygulama içinden otomatik abonelik ödemesi veya farklı sunucuları tek merkezden yönetme özelliklerini içermez. Paneli yalnızca güvendiğin yöneticilerle paylaş; 8443/TCP erişimini sağlayıcı güvenlik duvarında kısıtlayabiliyorsan yönetici IP'lerine sınırla.

## Geliştirme ve kontroller

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app.py helper/ocserv-panel-helper
bash -n install.sh scripts/install-core.sh
node --check static/app.js
```
