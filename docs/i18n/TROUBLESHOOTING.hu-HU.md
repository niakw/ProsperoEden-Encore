# Eden Encore — Hibaelhárítás · Magyar

[Áttekintés](README.hu-HU.md) · [Telepítés és frissítés](INSTALL.hu-HU.md) · [Beállítások](SETTINGS.hu-HU.md) · [Hibaelhárítás](TROUBLESHOOTING.hu-HU.md) · [Támogatás](SUPPORT.hu-HU.md) · [Akadálymentesség](ACCESSIBILITY.hu-HU.md) · [Languages](../../LANGUAGES.md)

Ha a program nem indul, ellenőrizd az eboot.bin, sce_sys és ui/lang állományokat. Hiányzó játékoknál ellenőrizd a kiválasztott tárhely roms könyvtárát. Angol menük esetén nézd meg a fordítási fájlokat. A Safe Launch visszaállítja egy játék beállításait a mentések törlése nélkül.

## Telepítés és frissítés

A valóban közzétett csomagot a Releases oldalról töltsd le, előtte mentsd a programot és az adataidat. ZIP/FTP telepítésnél a teljes PPSA99008 mappát másold a /data/homebrew/PPSA99008/ helyre. Ne keverd a ZIP/FTP és FFPFSC/ShadowMountPlus módszert; ellenőrizd az SHA-256 összeget, ha rendelkezésre áll.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Beállítások

Az ajánlott kezdőprofil Vulkan renderelést, 1440p tévékimenetet, 1.25x belső játékfelbontást, 50%-os élességű FSR 1-et, FXAA-t és 60 Hz-et használ. A tévékimenet különbözik a játék belső felbontásától. A képkockagenerálás nem gyorsítja a játék szimulációját.

## Támogatás

Hibabejelentéshez add meg az Encore verzióját, a PS5 firmware-t, a pontos reprodukciós lépéseket, a beállításokat és a személyes adatokat nem tartalmazó naplókat. A GitHub Issues felületet használd; kulcsokat és mentéseket ne ossz meg.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Soha ne töröld a /data/prosperoeden/ mappát: mentések, beállítások és kulcsok lehetnek benne. A külső tárhelyet is mentsd.

---

Az utolsó ténylegesen lefordított nyilvános PS5-csomag 2026. október 15-i. Az október 30-i kiadás másolat volt. Az új előzetes vázlat nem tartalmaz binárisokat vagy bizonyított második generációs konzolos kompatibilitást.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)