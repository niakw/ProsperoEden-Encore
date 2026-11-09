# Eden Encore — Ayarlar · Türkçe

[Genel bakış](README.tr-TR.md) · [Kurulum ve güncelleme](INSTALL.tr-TR.md) · [Ayarlar](SETTINGS.tr-TR.md) · [Sorun giderme](TROUBLESHOOTING.tr-TR.md) · [Destek](SUPPORT.tr-TR.md) · [Erişilebilirlik](ACCESSIBILITY.tr-TR.md) · [Languages](../../LANGUAGES.md)

Önerilen başlangıç profili Vulkan, 1440p TV çıkışı, 1.25x iç oyun ölçeği, %50 keskinlikte uzamsal FSR 1, FXAA ve 60 Hz kullanır. TV çıkışı oyun içi çözünürlükten ayrıdır. Kare üretimi oyunun simülasyon hızını artırmaz.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Önerilen başlangıç profili Vulkan, 1440p TV çıkışı, 1.25x iç oyun ölçeği, %50 keskinlikte uzamsal FSR 1, FXAA ve 60 Hz kullanır. TV çıkışı oyun içi çözünürlükten ayrıdır. Kare üretimi oyunun simülasyon hızını artırmaz.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Erişilebilirlik

Büyük metin, yüksek karşıtlık ve azaltılmış hareket seçenekleri Erişilebilirlik altında ayrı ayrı açılır; varsayılan olarak kapalıdır. Başlatıcı erişilebilirliği her oyunun erişilebilir olduğu anlamına gelmez.

## Sorun giderme

Uygulama açılmıyorsa eboot.bin, sce_sys ve ui/lang dosyalarını kontrol edin. Oyunlar görünmüyorsa seçili depolama kökündeki roms klasörünü kontrol edin. Menü İngilizce kalıyorsa çeviri dosyalarını doğrulayın. Safe Launch oyun kayıtlarını silmeden yalnızca ilgili oyunun ayarlarını geri alır.

/data/prosperoeden/ klasörünü asla silmeyin; kayıtları, ayarları ve anahtarları içerebilir. Harici depolamayı da yedekleyin.

---

Gerçekten derlenmiş son herkese açık PS5 paketi 15 Ekim 2026 tarihlidir; 30 Ekim yayını bir kopyadır. Yeni ön sürüm taslağı ikili dosya ya da konsolda doğrulanmış ikinci nesil oyun desteği içermez.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)