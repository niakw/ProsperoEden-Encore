# Eden Encore — Feilsøking · Norsk bokmål

[Oversikt](README.nb-NO.md) · [Installasjon og oppdatering](INSTALL.nb-NO.md) · [Innstillinger](SETTINGS.nb-NO.md) · [Feilsøking](TROUBLESHOOTING.nb-NO.md) · [Brukerstøtte](SUPPORT.nb-NO.md) · [Tilgjengelighet](ACCESSIBILITY.nb-NO.md) · [Languages](../../LANGUAGES.md)

Hvis appen ikke starter, kontroller eboot.bin, sce_sys og ui/lang. Mangler spillene, sjekk roms i den valgte lagringsroten. Hvis menyen fortsatt er engelsk, kontroller oversettelsesfilene. Safe Launch tilbakestiller bare ett spills innstillinger uten å slette lagringer.

## Installasjon og oppdatering

Last ned en faktisk utgitt pakke fra Releases og ta sikkerhetskopi av app og data først. Ved ZIP/FTP kopierer du hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Ikke bland ZIP/FTP med FFPFSC/ShadowMountPlus, og kontroller SHA-256 der det finnes.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Innstillinger

Anbefalt startprofil bruker Vulkan, TV-utgang 1440p, intern spillskalering 1.25x, romlig FSR 1 med skarphet 50 %, FXAA og 60 Hz. TV-oppløsning er ikke det samme som intern spilloppløsning. Bildegenerering øker ikke hastigheten på selve spilsimuleringen.

## Brukerstøtte

Oppgi Encore-versjon, PS5-firmware, fremgangsmåte for å gjenskape feilen, relevante innstillinger og anonymiserte logger i GitHub Issues. Del aldri nøkler, lagringsfiler eller personopplysninger.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Slett aldri /data/prosperoeden/; mappen kan inneholde lagringer, innstillinger og nøkler. Ta også kopi av ekstern lagring.

---

Siste offentlig kompilerte PS5-pakke er fra 15. oktober 2026. Publiseringen 30. oktober var en kopi. Det nye utkastet har ingen binærfiler eller verifiserte spill fra andre generasjon på konsollen.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)