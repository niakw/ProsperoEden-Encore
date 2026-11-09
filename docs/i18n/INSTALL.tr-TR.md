# Eden Encore — Kurulum ve güncelleme · Türkçe

[Genel bakış](README.tr-TR.md) · [Kurulum ve güncelleme](INSTALL.tr-TR.md) · [Ayarlar](SETTINGS.tr-TR.md) · [Sorun giderme](TROUBLESHOOTING.tr-TR.md) · [Destek](SUPPORT.tr-TR.md) · [Erişilebilirlik](ACCESSIBILITY.tr-TR.md) · [Languages](../../LANGUAGES.md)

Gerçekten yayımlanmış paketi Releases sayfasından indirin ve önce uygulama ile verilerinizi yedekleyin. ZIP/FTP için PPSA99008 klasörünün tamamını /data/homebrew/PPSA99008/ dizinine kopyalayın. ZIP/FTP ile FFPFSC/ShadowMountPlus yöntemlerini karıştırmayın; varsa SHA-256 doğrulaması yapın.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

/data/prosperoeden/ klasörünü asla silmeyin; kayıtları, ayarları ve anahtarları içerebilir. Harici depolamayı da yedekleyin.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Sorun giderme

Uygulama açılmıyorsa eboot.bin, sce_sys ve ui/lang dosyalarını kontrol edin. Oyunlar görünmüyorsa seçili depolama kökündeki roms klasörünü kontrol edin. Menü İngilizce kalıyorsa çeviri dosyalarını doğrulayın. Safe Launch oyun kayıtlarını silmeden yalnızca ilgili oyunun ayarlarını geri alır.

Gerçekten derlenmiş son herkese açık PS5 paketi 15 Ekim 2026 tarihlidir; 30 Ekim yayını bir kopyadır. Yeni ön sürüm taslağı ikili dosya ya da konsolda doğrulanmış ikinci nesil oyun desteği içermez.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)