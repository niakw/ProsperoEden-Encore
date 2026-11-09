# Eden Encore — Genel bakış · Türkçe

[Genel bakış](README.tr-TR.md) · [Kurulum ve güncelleme](INSTALL.tr-TR.md) · [Ayarlar](SETTINGS.tr-TR.md) · [Sorun giderme](TROUBLESHOOTING.tr-TR.md) · [Destek](SUPPORT.tr-TR.md) · [Erişilebilirlik](ACCESSIBILITY.tr-TR.md) · [Languages](../../LANGUAGES.md)

Eden Encore, birinci ve ikinci nesil konuk oyunlar için ortak motor geliştiren, PS5'e yönelik resmî olmayan bir topluluk projesidir. Arayüz televizyon ve kontrolcü için tasarlanmıştır. Kaynak kodu ve ana sistem testlerinin başarılı olması oyunların konsolda çalıştığını kanıtlamaz.

## Kurulum ve güncelleme

Gerçekten yayımlanmış paketi Releases sayfasından indirin ve önce uygulama ile verilerinizi yedekleyin. ZIP/FTP için PPSA99008 klasörünün tamamını /data/homebrew/PPSA99008/ dizinine kopyalayın. ZIP/FTP ile FFPFSC/ShadowMountPlus yöntemlerini karıştırmayın; varsa SHA-256 doğrulaması yapın.

[Actual R1 package — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Ayarlar

Önerilen başlangıç profili Vulkan, 1440p TV çıkışı, 1.25x iç oyun ölçeği, %50 keskinlikte uzamsal FSR 1, FXAA ve 60 Hz kullanır. TV çıkışı oyun içi çözünürlükten ayrıdır. Kare üretimi oyunun simülasyon hızını artırmaz.

## Sorun giderme

Uygulama açılmıyorsa eboot.bin, sce_sys ve ui/lang dosyalarını kontrol edin. Oyunlar görünmüyorsa seçili depolama kökündeki roms klasörünü kontrol edin. Menü İngilizce kalıyorsa çeviri dosyalarını doğrulayın. Safe Launch oyun kayıtlarını silmeden yalnızca ilgili oyunun ayarlarını geri alır.

## Destek

GitHub Issues üzerinde Encore sürümü, PS5 yazılımı, hatayı yeniden oluşturma adımları, ilgili ayarlar ve kişisel bilgileri temizlenmiş günlüklerle rapor verin. Anahtarları, kayıt dosyalarını veya özel bilgileri yayımlamayın.

## Erişilebilirlik

Büyük metin, yüksek karşıtlık ve azaltılmış hareket seçenekleri Erişilebilirlik altında ayrı ayrı açılır; varsayılan olarak kapalıdır. Başlatıcı erişilebilirliği her oyunun erişilebilir olduğu anlamına gelmez.

/data/prosperoeden/ klasörünü asla silmeyin; kayıtları, ayarları ve anahtarları içerebilir. Harici depolamayı da yedekleyin.

---

Gerçekten derlenmiş son herkese açık PS5 paketi 15 Ekim 2026 tarihlidir; 30 Ekim yayını bir kopyadır. Yeni ön sürüm taslağı ikili dosya ya da konsolda doğrulanmış ikinci nesil oyun desteği içermez.

[Full English reference](../../README.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)