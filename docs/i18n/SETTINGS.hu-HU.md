# Eden Encore — Beállítások · Magyar

[Áttekintés](README.hu-HU.md) · [Telepítés és frissítés](INSTALL.hu-HU.md) · [Beállítások](SETTINGS.hu-HU.md) · [Hibaelhárítás](TROUBLESHOOTING.hu-HU.md) · [Támogatás](SUPPORT.hu-HU.md) · [Akadálymentesség](ACCESSIBILITY.hu-HU.md) · [Languages](../../LANGUAGES.md)

Az ajánlott kezdőprofil Vulkan renderelést, 1440p tévékimenetet, 1.25x belső játékfelbontást, 50%-os élességű FSR 1-et, FXAA-t és 60 Hz-et használ. A tévékimenet különbözik a játék belső felbontásától. A képkockagenerálás nem gyorsítja a játék szimulációját.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Az ajánlott kezdőprofil Vulkan renderelést, 1440p tévékimenetet, 1.25x belső játékfelbontást, 50%-os élességű FSR 1-et, FXAA-t és 60 Hz-et használ. A tévékimenet különbözik a játék belső felbontásától. A képkockagenerálás nem gyorsítja a játék szimulációját.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Akadálymentesség

A nagyobb szöveg, nagy kontraszt és csökkentett mozgás külön kapcsolható be az akadálymentességi menüben, alapállapotban ki vannak kapcsolva. A menü akadálymentessége nem garantálja az egyes játékok akadálymentességét.

## Hibaelhárítás

Ha a program nem indul, ellenőrizd az eboot.bin, sce_sys és ui/lang állományokat. Hiányzó játékoknál ellenőrizd a kiválasztott tárhely roms könyvtárát. Angol menük esetén nézd meg a fordítási fájlokat. A Safe Launch visszaállítja egy játék beállításait a mentések törlése nélkül.

Soha ne töröld a /data/prosperoeden/ mappát: mentések, beállítások és kulcsok lehetnek benne. A külső tárhelyet is mentsd.

---

Az utolsó ténylegesen lefordított nyilvános PS5-csomag 2026. október 15-i. Az október 30-i kiadás másolat volt. Az új előzetes vázlat nem tartalmaz binárisokat vagy bizonyított második generációs konzolos kompatibilitást.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)