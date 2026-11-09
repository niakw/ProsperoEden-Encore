# Eden Encore — Installation og opdatering · Dansk

[Overblik](README.da-DK.md) · [Installation og opdatering](INSTALL.da-DK.md) · [Indstillinger](SETTINGS.da-DK.md) · [Fejlfinding](TROUBLESHOOTING.da-DK.md) · [Support](SUPPORT.da-DK.md) · [Tilgængelighed](ACCESSIBILITY.da-DK.md) · [Languages](../../LANGUAGES.md)

Hent en faktisk offentliggjort pakke fra Releases, og sikkerhedskopiér app og data først. Ved ZIP/FTP kopieres hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Bland ikke ZIP/FTP med FFPFSC/ShadowMountPlus, og kontrollér SHA-256, hvis en kontrolsum er tilgængelig.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Slet aldrig /data/prosperoeden/; mappen kan indeholde gemte spil, indstillinger og nøgler. Lav også en kopi af eventuel ekstern lagerplads.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Fejlfinding

Starter appen ikke, så kontrollér eboot.bin, sce_sys og ui/lang i den korrekte mappe. Manglende spil findes ofte under en anden valgt lagerrod end roms. Hvis sproget bliver engelsk, skal oversættelsesfilerne kontrolleres. Safe Launch kan nulstille ét spils indstillinger uden at slette gemte data.

Den seneste offentligt kompilerede PS5-pakke er fra 15. oktober 2026. Udgivelsen den 30. oktober var en kopi. Det nye udkast indeholder ingen binære filer eller verificerede spil fra anden generation på konsollen.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)