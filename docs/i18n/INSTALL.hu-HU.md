# Eden Encore — Telepítés és frissítés · Magyar

[Áttekintés](README.hu-HU.md) · [Telepítés és frissítés](INSTALL.hu-HU.md) · [Beállítások](SETTINGS.hu-HU.md) · [Hibaelhárítás](TROUBLESHOOTING.hu-HU.md) · [Támogatás](SUPPORT.hu-HU.md) · [Akadálymentesség](ACCESSIBILITY.hu-HU.md) · [Languages](../../LANGUAGES.md)

A valóban közzétett csomagot a Releases oldalról töltsd le, előtte mentsd a programot és az adataidat. ZIP/FTP telepítésnél a teljes PPSA99008 mappát másold a /data/homebrew/PPSA99008/ helyre. Ne keverd a ZIP/FTP és FFPFSC/ShadowMountPlus módszert; ellenőrizd az SHA-256 összeget, ha rendelkezésre áll.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Soha ne töröld a /data/prosperoeden/ mappát: mentések, beállítások és kulcsok lehetnek benne. A külső tárhelyet is mentsd.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Hibaelhárítás

Ha a program nem indul, ellenőrizd az eboot.bin, sce_sys és ui/lang állományokat. Hiányzó játékoknál ellenőrizd a kiválasztott tárhely roms könyvtárát. Angol menük esetén nézd meg a fordítási fájlokat. A Safe Launch visszaállítja egy játék beállításait a mentések törlése nélkül.

Az utolsó ténylegesen lefordított nyilvános PS5-csomag 2026. október 15-i. Az október 30-i kiadás másolat volt. Az új előzetes vázlat nem tartalmaz binárisokat vagy bizonyított második generációs konzolos kompatibilitást.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)