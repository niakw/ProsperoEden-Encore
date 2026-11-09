# Eden Encore — Fejlfinding · Dansk

[Overblik](README.da-DK.md) · [Installation og opdatering](INSTALL.da-DK.md) · [Indstillinger](SETTINGS.da-DK.md) · [Fejlfinding](TROUBLESHOOTING.da-DK.md) · [Support](SUPPORT.da-DK.md) · [Tilgængelighed](ACCESSIBILITY.da-DK.md) · [🌐](../../LANGUAGES.md)

Starter appen ikke, så kontrollér eboot.bin, sce_sys og ui/lang i den korrekte mappe. Manglende spil findes ofte under en anden valgt lagerrod end roms. Hvis sproget bliver engelsk, skal oversættelsesfilerne kontrolleres. Safe Launch kan nulstille ét spils indstillinger uden at slette gemte data.

## Installation og opdatering

Hent en faktisk offentliggjort pakke fra Releases, og sikkerhedskopiér app og data først. Ved ZIP/FTP kopieres hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Bland ikke ZIP/FTP med FFPFSC/ShadowMountPlus, og kontrollér SHA-256, hvis en kontrolsum er tilgængelig.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## Indstillinger

Den anbefalede startprofil bruger Vulkan, tv-output på 1440p, intern spilskala 1.25x, FSR 1 med 50 % skarphed, FXAA og 60 Hz. Tv-output og spillets interne opløsning er ikke det samme. Billedgenerering øger ikke selve spillets simuleringshastighed.

## Support

Oplys Encore-version, PS5-firmware, trin til at genskabe fejlen, relevante indstillinger og rensede logs i en GitHub Issue. Del aldrig nøgler, private gemte data eller personlige oplysninger.

Slet aldrig /data/prosperoeden/; mappen kan indeholde gemte spil, indstillinger og nøgler. Lav også en kopi af eventuel ekstern lagerplads.

---

Den seneste offentligt kompilerede PS5-pakke er fra 15. oktober 2026. Udgivelsen den 30. oktober var en kopi. Det nye udkast indeholder ingen binære filer eller verificerede spil fra anden generation på konsollen.

[English](../../TROUBLESHOOTING.md) · [Installation og opdatering](INSTALL.da-DK.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
