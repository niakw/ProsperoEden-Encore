# Eden Encore — Overblik · Dansk

[Overblik](README.da-DK.md) · [Installation og opdatering](INSTALL.da-DK.md) · [Indstillinger](SETTINGS.da-DK.md) · [Fejlfinding](TROUBLESHOOTING.da-DK.md) · [Support](SUPPORT.da-DK.md) · [Tilgængelighed](ACCESSIBILITY.da-DK.md) · [🌐](../../LANGUAGES.md)

Eden Encore er en uofficiel fællesskabsudviklet emulator til PS5 med fælles kode til første og anden generation af gæstespil. Brugerfladen er lavet til tv og controller. Vellykkede kildekode- og værtstests er ikke bevis for, at et spil virker på konsollen.

## Installation og opdatering

Hent en faktisk offentliggjort pakke fra Releases, og sikkerhedskopiér app og data først. Ved ZIP/FTP kopieres hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Bland ikke ZIP/FTP med FFPFSC/ShadowMountPlus, og kontrollér SHA-256, hvis en kontrolsum er tilgængelig.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/updates/
/data/prosperoeden/firmware/
/data/prosperoeden/keys/
```

[Installation og opdatering](./INSTALL.da-DK.md) · [R1 — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Indstillinger

Den anbefalede startprofil bruger Vulkan, tv-output på 1440p, intern spilskala 1.25x, FSR 1 med 50 % skarphed, FXAA og 60 Hz. Tv-output og spillets interne opløsning er ikke det samme. Billedgenerering øger ikke selve spillets simuleringshastighed.

**Vulkan** · **FSR 1 (EASU/RCAS)** · **FXAA** · **60 Hz** · `Minimum` / `Recommended` / `High`

## Indstillinger · Touchpad

Et kort tryk på Touchpad åbner Encores hurtigindstillinger under spillet. Den centrale systemknap er reserveret til konsollen. Her findes grafik, knapopsætning, FPS og diagnostik. Nogle ændringer kræver genstart af spillet. Sprog vælges under Settings → Language; ikke alle oversættelseskataloger kan vælges i menuen.

## Tilgængelighed

Større tekst, høj kontrast og reduceret bevægelse kan slås til enkeltvis under Tilgængelighed; alle er slået fra som standard. Launcherens fokuserede kontrol betyder ikke automatisk tilgængelighed inde i hvert spil.

## Fejlfinding

Starter appen ikke, så kontrollér eboot.bin, sce_sys og ui/lang i den korrekte mappe. Manglende spil findes ofte under en anden valgt lagerrod end roms. Hvis sproget bliver engelsk, skal oversættelsesfilerne kontrolleres. Safe Launch kan nulstille ét spils indstillinger uden at slette gemte data.

## Support

Oplys Encore-version, PS5-firmware, trin til at genskabe fejlen, relevante indstillinger og rensede logs i en GitHub Issue. Del aldrig nøgler, private gemte data eller personlige oplysninger.

Slet aldrig /data/prosperoeden/; mappen kan indeholde gemte spil, indstillinger og nøgler. Lav også en kopi af eventuel ekstern lagerplads.

---

Den seneste offentligt kompilerede PS5-pakke er fra 15. oktober 2026. Udgivelsen den 30. oktober var en kopi. Det nye udkast indeholder ingen binære filer eller verificerede spil fra anden generation på konsollen.

[English — complete README](../../README.md) · [English — full settings reference](../../SETTINGS.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
