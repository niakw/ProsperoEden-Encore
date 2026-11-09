# Eden Encore — Áttekintés · Magyar

[Áttekintés](README.hu-HU.md) · [Telepítés és frissítés](INSTALL.hu-HU.md) · [Beállítások](SETTINGS.hu-HU.md) · [Hibaelhárítás](TROUBLESHOOTING.hu-HU.md) · [Támogatás](SUPPORT.hu-HU.md) · [Akadálymentesség](ACCESSIBILITY.hu-HU.md) · [🌐](../../LANGUAGES.md)

Az Eden Encore nem hivatalos, közösségi PS5-emulátorprojekt, amely közös forráskódon dolgozik az első és második generációs játékokhoz. A felületet tévéhez és kontrollerhez tervezték. A forráskód- és gazdagép-tesztek sikere nem bizonyítja, hogy egy játék működik a konzolon.

## Telepítés és frissítés

A valóban közzétett csomagot a Releases oldalról töltsd le, előtte mentsd a programot és az adataidat. ZIP/FTP telepítésnél a teljes PPSA99008 mappát másold a /data/homebrew/PPSA99008/ helyre. Ne keverd a ZIP/FTP és FFPFSC/ShadowMountPlus módszert; ellenőrizd az SHA-256 összeget, ha rendelkezésre áll.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/updates/
/data/prosperoeden/firmware/
/data/prosperoeden/keys/
```

[Telepítés és frissítés](./INSTALL.hu-HU.md) · [R1 — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Beállítások

Az ajánlott kezdőprofil Vulkan renderelést, 1440p tévékimenetet, 1.25x belső játékfelbontást, 50%-os élességű FSR 1-et, FXAA-t és 60 Hz-et használ. A tévékimenet különbözik a játék belső felbontásától. A képkockagenerálás nem gyorsítja a játék szimulációját.

**Vulkan** · **FSR 1 (EASU/RCAS)** · **FXAA** · **60 Hz** · `Minimum` / `Recommended` / `High`

## Beállítások · Touchpad

A Touchpad rövid megnyomásával játék közben megnyitható az Encore gyorsbeállítási menüje. A központi rendszergomb a konzolé. Itt találhatók a grafikai, gombkiosztási, FPS- és diagnosztikai lehetőségek. Egyes változtatásokhoz újra kell indítani a játékot. A nyelv a Settings → Language alatt választható, de nem minden fordítás szerepel a menüben.

## Akadálymentesség

A nagyobb szöveg, nagy kontraszt és csökkentett mozgás külön kapcsolható be az akadálymentességi menüben, alapállapotban ki vannak kapcsolva. A menü akadálymentessége nem garantálja az egyes játékok akadálymentességét.

## Hibaelhárítás

Ha a program nem indul, ellenőrizd az eboot.bin, sce_sys és ui/lang állományokat. Hiányzó játékoknál ellenőrizd a kiválasztott tárhely roms könyvtárát. Angol menük esetén nézd meg a fordítási fájlokat. A Safe Launch visszaállítja egy játék beállításait a mentések törlése nélkül.

## Támogatás

Hibabejelentéshez add meg az Encore verzióját, a PS5 firmware-t, a pontos reprodukciós lépéseket, a beállításokat és a személyes adatokat nem tartalmazó naplókat. A GitHub Issues felületet használd; kulcsokat és mentéseket ne ossz meg.

Soha ne töröld a /data/prosperoeden/ mappát: mentések, beállítások és kulcsok lehetnek benne. A külső tárhelyet is mentsd.

---

Az utolsó ténylegesen lefordított nyilvános PS5-csomag 2026. október 15-i. Az október 30-i kiadás másolat volt. Az új előzetes vázlat nem tartalmaz binárisokat vagy bizonyított második generációs konzolos kompatibilitást.

[English — complete README](../../README.md) · [English — full settings reference](../../SETTINGS.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
