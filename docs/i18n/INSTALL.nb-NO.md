# Eden Encore — Installasjon og oppdatering · Norsk bokmål

[Oversikt](README.nb-NO.md) · [Installasjon og oppdatering](INSTALL.nb-NO.md) · [Innstillinger](SETTINGS.nb-NO.md) · [Feilsøking](TROUBLESHOOTING.nb-NO.md) · [Brukerstøtte](SUPPORT.nb-NO.md) · [Tilgjengelighet](ACCESSIBILITY.nb-NO.md) · [🌐](../../LANGUAGES.md)

Last ned en faktisk utgitt pakke fra Releases og ta sikkerhetskopi av app og data først. Ved ZIP/FTP kopierer du hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Ikke bland ZIP/FTP med FFPFSC/ShadowMountPlus, og kontroller SHA-256 der det finnes.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/eboot.bin
/data/homebrew/PPSA99008/sce_sys/
/data/homebrew/PPSA99008/ui/lang/
```

Slett aldri /data/prosperoeden/; mappen kan inneholde lagringer, innstillinger og nøkler. Ta også kopi av ekstern lagring.

## FFPFSC / ShadowMountPlus

Last ned en faktisk utgitt pakke fra Releases og ta sikkerhetskopi av app og data først. Ved ZIP/FTP kopierer du hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Ikke bland ZIP/FTP med FFPFSC/ShadowMountPlus, og kontroller SHA-256 der det finnes.

[FFPFSC / ShadowMountPlus — English reference](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus)

## Innstillinger

Anbefalt startprofil bruker Vulkan, TV-utgang 1440p, intern spillskalering 1.25x, romlig FSR 1 med skarphet 50 %, FXAA og 60 Hz. TV-oppløsning er ikke det samme som intern spilloppløsning. Bildegenerering øker ikke hastigheten på selve spilsimuleringen.

## Feilsøking

Hvis appen ikke starter, kontroller eboot.bin, sce_sys og ui/lang. Mangler spillene, sjekk roms i den valgte lagringsroten. Hvis menyen fortsatt er engelsk, kontroller oversettelsesfilene. Safe Launch tilbakestiller bare ett spills innstillinger uten å slette lagringer.

## Brukerstøtte

Oppgi Encore-versjon, PS5-firmware, fremgangsmåte for å gjenskape feilen, relevante innstillinger og anonymiserte logger i GitHub Issues. Del aldri nøkler, lagringsfiler eller personopplysninger.

---

Siste offentlig kompilerte PS5-pakke er fra 15. oktober 2026. Publiseringen 30. oktober var en kopi. Det nye utkastet har ingen binærfiler eller verifiserte spill fra andre generasjon på konsollen.

[English — complete installation and migration](../../INSTALL.md) · [R1 — October 15, 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)
