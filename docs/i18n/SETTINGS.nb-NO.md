# Eden Encore — Innstillinger · Norsk bokmål

[Oversikt](README.nb-NO.md) · [Installasjon og oppdatering](INSTALL.nb-NO.md) · [Innstillinger](SETTINGS.nb-NO.md) · [Feilsøking](TROUBLESHOOTING.nb-NO.md) · [Brukerstøtte](SUPPORT.nb-NO.md) · [Tilgjengelighet](ACCESSIBILITY.nb-NO.md) · [Languages](../../LANGUAGES.md)

Anbefalt startprofil bruker Vulkan, TV-utgang 1440p, intern spillskalering 1.25x, romlig FSR 1 med skarphet 50 %, FXAA og 60 Hz. TV-oppløsning er ikke det samme som intern spilloppløsning. Bildegenerering øker ikke hastigheten på selve spilsimuleringen.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Anbefalt startprofil bruker Vulkan, TV-utgang 1440p, intern spillskalering 1.25x, romlig FSR 1 med skarphet 50 %, FXAA og 60 Hz. TV-oppløsning er ikke det samme som intern spilloppløsning. Bildegenerering øker ikke hastigheten på selve spilsimuleringen.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Tilgjengelighet

Større tekst, høy kontrast og redusert bevegelse kan slås på hver for seg under Tilgjengelighet; alle er av som standard. Tilgjengelighet i startmenyen garanterer ikke tilgjengelighet i hvert spill.

## Feilsøking

Hvis appen ikke starter, kontroller eboot.bin, sce_sys og ui/lang. Mangler spillene, sjekk roms i den valgte lagringsroten. Hvis menyen fortsatt er engelsk, kontroller oversettelsesfilene. Safe Launch tilbakestiller bare ett spills innstillinger uten å slette lagringer.

Slett aldri /data/prosperoeden/; mappen kan inneholde lagringer, innstillinger og nøkler. Ta også kopi av ekstern lagring.

---

Siste offentlig kompilerte PS5-pakke er fra 15. oktober 2026. Publiseringen 30. oktober var en kopi. Det nye utkastet har ingen binærfiler eller verifiserte spill fra andre generasjon på konsollen.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)