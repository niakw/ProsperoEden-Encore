# Eden Encore — Instellingen · Nederlands

[Overzicht](README.nl.md) · [Installatie en updates](INSTALL.nl-NL.md) · [Instellingen](SETTINGS.nl-NL.md) · [Problemen oplossen](TROUBLESHOOTING.nl-NL.md) · [Ondersteuning](SUPPORT.nl-NL.md) · [Toegankelijkheid](ACCESSIBILITY.nl-NL.md) · [Languages](../../LANGUAGES.md)

Het aanbevolen beginprofiel gebruikt Vulkan, tv-uitvoer 1440p, interne gameschaal 1.25x, ruimtelijke FSR 1 met 50% scherpte, FXAA en 60 Hz. Tv-uitvoer is niet hetzelfde als de interne spelresolutie. Framegeneratie verhoogt de simulatiesnelheid van de game niet.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Het aanbevolen beginprofiel gebruikt Vulkan, tv-uitvoer 1440p, interne gameschaal 1.25x, ruimtelijke FSR 1 met 50% scherpte, FXAA en 60 Hz. Tv-uitvoer is niet hetzelfde als de interne spelresolutie. Framegeneratie verhoogt de simulatiesnelheid van de game niet.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Toegankelijkheid

Grotere tekst, hoog contrast en minder beweging zijn afzonderlijk beschikbaar onder Toegankelijkheid en standaard uitgeschakeld. Een toegankelijke launcher garandeert niet dat alle games toegankelijk zijn.

## Problemen oplossen

Start de app niet, controleer dan eboot.bin, sce_sys en ui/lang. Ontbrekende games? Controleer roms onder de gekozen opslaglocatie. Blijft de interface Engels, controleer de vertaalbestanden. Met Safe Launch herstel je instellingen voor één game zonder savegames te verwijderen.

Verwijder /data/prosperoeden/ nooit: deze map kan saves, instellingen en sleutels bevatten. Maak ook een back-up van externe opslag.

---

Het laatste werkelijk gecompileerde openbare PS5-pakket dateert van 15 oktober 2026. De publicatie van 30 oktober was een kopie. Het nieuwe prereleaseconcept bevat geen uitvoerbare bestanden en geen bevestigde ondersteuning voor games van de tweede generatie op de console.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)