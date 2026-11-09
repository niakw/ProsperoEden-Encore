# Eden Encore — Inställningar · Svenska

[Översikt](README.sv-SE.md) · [Installation och uppdatering](INSTALL.sv-SE.md) · [Inställningar](SETTINGS.sv-SE.md) · [Felsökning](TROUBLESHOOTING.sv-SE.md) · [Support](SUPPORT.sv-SE.md) · [Tillgänglighet](ACCESSIBILITY.sv-SE.md) · [Languages](../../LANGUAGES.md)

Rekommenderad startprofil är Vulkan, tv-utmatning 1440p, intern spelskala 1.25x, rumslig FSR 1 med 50 % skärpa, FXAA och 60 Hz. Tv-utmatningen är inte samma sak som spelets interna upplösning. Bildgenerering ökar inte spelets simuleringshastighet.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Rekommenderad startprofil är Vulkan, tv-utmatning 1440p, intern spelskala 1.25x, rumslig FSR 1 med 50 % skärpa, FXAA och 60 Hz. Tv-utmatningen är inte samma sak som spelets interna upplösning. Bildgenerering ökar inte spelets simuleringshastighet.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Tillgänglighet

Större text, hög kontrast och minskad rörelse kan aktiveras var för sig under Tillgänglighet; de är avstängda som standard. En tillgänglig startmeny garanterar inte tillgänglighet inne i spelen.

## Felsökning

Om appen inte startar kontrollerar du eboot.bin, sce_sys och ui/lang. Om spel saknas, kontrollera roms i vald lagringsrot. Om menyerna fortsätter vara på engelska, kontrollera språkfilerna. Safe Launch återställer inställningar för ett spel utan att ta bort sparfiler.

Radera aldrig /data/prosperoeden/: där kan finnas sparfiler, inställningar och nycklar. Säkerhetskopiera även extern lagring.

---

Det senaste offentligt kompilerade PS5-paketet är från 15 oktober 2026. Publiceringen den 30 oktober var en kopia. Det nya utkastet innehåller inga binärer eller verifierade spel från andra generationen på konsolen.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)