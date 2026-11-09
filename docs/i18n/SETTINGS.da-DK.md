# Eden Encore — Indstillinger · Dansk

[Overblik](README.da-DK.md) · [Installation og opdatering](INSTALL.da-DK.md) · [Indstillinger](SETTINGS.da-DK.md) · [Fejlfinding](TROUBLESHOOTING.da-DK.md) · [Support](SUPPORT.da-DK.md) · [Tilgængelighed](ACCESSIBILITY.da-DK.md) · [Languages](../../LANGUAGES.md)

Den anbefalede startprofil bruger Vulkan, tv-output på 1440p, intern spilskala 1.25x, FSR 1 med 50 % skarphed, FXAA og 60 Hz. Tv-output og spillets interne opløsning er ikke det samme. Billedgenerering øger ikke selve spillets simuleringshastighed.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Den anbefalede startprofil bruger Vulkan, tv-output på 1440p, intern spilskala 1.25x, FSR 1 med 50 % skarphed, FXAA og 60 Hz. Tv-output og spillets interne opløsning er ikke det samme. Billedgenerering øger ikke selve spillets simuleringshastighed.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Tilgængelighed

Større tekst, høj kontrast og reduceret bevægelse kan slås til enkeltvis under Tilgængelighed; alle er slået fra som standard. Launcherens fokuserede kontrol betyder ikke automatisk tilgængelighed inde i hvert spil.

## Fejlfinding

Starter appen ikke, så kontrollér eboot.bin, sce_sys og ui/lang i den korrekte mappe. Manglende spil findes ofte under en anden valgt lagerrod end roms. Hvis sproget bliver engelsk, skal oversættelsesfilerne kontrolleres. Safe Launch kan nulstille ét spils indstillinger uden at slette gemte data.

Slet aldrig /data/prosperoeden/; mappen kan indeholde gemte spil, indstillinger og nøgler. Lav også en kopi af eventuel ekstern lagerplads.

---

Den seneste offentligt kompilerede PS5-pakke er fra 15. oktober 2026. Udgivelsen den 30. oktober var en kopi. Det nye udkast indeholder ingen binære filer eller verificerede spil fra anden generation på konsollen.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)