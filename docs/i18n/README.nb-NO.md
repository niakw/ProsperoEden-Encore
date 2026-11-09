# Eden Encore — Oversikt · Norsk bokmål

[Oversikt](README.nb-NO.md) · [Installasjon og oppdatering](INSTALL.nb-NO.md) · [Innstillinger](SETTINGS.nb-NO.md) · [Feilsøking](TROUBLESHOOTING.nb-NO.md) · [Brukerstøtte](SUPPORT.nb-NO.md) · [Tilgjengelighet](ACCESSIBILITY.nb-NO.md) · [🌐](../../LANGUAGES.md)

Eden Encore er et uoffisielt fellesskapsprosjekt for PS5 med felles kildekode for spill fra første og andre generasjon. Grensesnittet er laget for TV og håndkontroll. Beståtte kildekode- eller vertstester bekrefter ikke at et spill fungerer på konsollen.

## Installasjon og oppdatering

Last ned en faktisk utgitt pakke fra Releases og ta sikkerhetskopi av app og data først. Ved ZIP/FTP kopierer du hele PPSA99008-mappen til /data/homebrew/PPSA99008/. Ikke bland ZIP/FTP med FFPFSC/ShadowMountPlus, og kontroller SHA-256 der det finnes.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/updates/
/data/prosperoeden/firmware/
/data/prosperoeden/keys/
```

[Installasjon og oppdatering](./INSTALL.nb-NO.md) · [R1 — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Innstillinger

Anbefalt startprofil bruker Vulkan, TV-utgang 1440p, intern spillskalering 1.25x, romlig FSR 1 med skarphet 50 %, FXAA og 60 Hz. TV-oppløsning er ikke det samme som intern spilloppløsning. Bildegenerering øker ikke hastigheten på selve spilsimuleringen.

**Vulkan** · **FSR 1 (EASU/RCAS)** · **FXAA** · **60 Hz** · `Minimum` / `Recommended` / `High`

## Innstillinger · Touchpad

Et kort trykk på Touchpad åpner hurtiginnstillingene i Encore under spill. Den sentrale systemknappen er reservert for konsollen. Menyen samler grafikk, knappetilordning, FPS og diagnostikk. Enkelte endringer krever omstart av spillet. Språket velges under Settings → Language; ikke alle katalogspråk finnes i menyen.

## Tilgjengelighet

Større tekst, høy kontrast og redusert bevegelse kan slås på hver for seg under Tilgjengelighet; alle er av som standard. Tilgjengelighet i startmenyen garanterer ikke tilgjengelighet i hvert spill.

## Feilsøking

Hvis appen ikke starter, kontroller eboot.bin, sce_sys og ui/lang. Mangler spillene, sjekk roms i den valgte lagringsroten. Hvis menyen fortsatt er engelsk, kontroller oversettelsesfilene. Safe Launch tilbakestiller bare ett spills innstillinger uten å slette lagringer.

## Brukerstøtte

Oppgi Encore-versjon, PS5-firmware, fremgangsmåte for å gjenskape feilen, relevante innstillinger og anonymiserte logger i GitHub Issues. Del aldri nøkler, lagringsfiler eller personopplysninger.

Slett aldri /data/prosperoeden/; mappen kan inneholde lagringer, innstillinger og nøkler. Ta også kopi av ekstern lagring.

---

Siste offentlig kompilerte PS5-pakke er fra 15. oktober 2026. Publiseringen 30. oktober var en kopi. Det nye utkastet har ingen binærfiler eller verifiserte spill fra andre generasjon på konsollen.

[English — complete README](../../README.md) · [English — full settings reference](../../SETTINGS.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
