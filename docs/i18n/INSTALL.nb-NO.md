# Eden Encore — Installasjon og oppdatering · Norsk bokmål

[Oversikt](README.nb-NO.md) · [Installasjon og oppdatering](INSTALL.nb-NO.md) · [Innstillinger](SETTINGS.nb-NO.md) · [Feilsøking](TROUBLESHOOTING.nb-NO.md) · [Brukerstøtte](SUPPORT.nb-NO.md) · [Tilgjengelighet](ACCESSIBILITY.nb-NO.md) · [Languages](../../LANGUAGES.md)

Last ned en faktisk utgitt pakke fra Releases og ta sikkerhetskopi av app og data først. Ved ZIP/FTP kopierer du hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Ikke bland ZIP/FTP med FFPFSC/ShadowMountPlus, og kontroller SHA-256 der det finnes.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Slett aldri /data/prosperoeden/; mappen kan inneholde lagringer, innstillinger og nøkler. Ta også kopi av ekstern lagring.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Feilsøking

Hvis appen ikke starter, kontroller eboot.bin, sce_sys og ui/lang. Mangler spillene, sjekk roms i den valgte lagringsroten. Hvis menyen fortsatt er engelsk, kontroller oversettelsesfilene. Safe Launch tilbakestiller bare ett spills innstillinger uten å slette lagringer.

Siste offentlig kompilerte PS5-pakke er fra 15. oktober 2026. Publiseringen 30. oktober var en kopi. Det nye utkastet har ingen binærfiler eller verifiserte spill fra andre generasjon på konsollen.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)