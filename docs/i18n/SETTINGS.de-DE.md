# Eden Encore — Einstellungen · Deutsch

[Überblick](README.de.md) · [Installation und Update](INSTALL.de-DE.md) · [Einstellungen](SETTINGS.de-DE.md) · [Fehlerbehebung](TROUBLESHOOTING.de-DE.md) · [Support](SUPPORT.de-DE.md) · [Barrierefreiheit](ACCESSIBILITY.de-DE.md) · [Languages](../../LANGUAGES.md)

Das empfohlene Ausgangsprofil nutzt Vulkan, 1440p-TV-Ausgabe, 1.25x interne Spielauflösung, räumliches FSR 1 bei 50 % Schärfe, FXAA und 60 Hz. TV-Ausgabe und Spielauflösung sind unterschiedliche Einstellungen. Frame Generation erhöht nicht die tatsächlich berechneten Spielbilder.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Das empfohlene Ausgangsprofil nutzt Vulkan, 1440p-TV-Ausgabe, 1.25x interne Spielauflösung, räumliches FSR 1 bei 50 % Schärfe, FXAA und 60 Hz. TV-Ausgabe und Spielauflösung sind unterschiedliche Einstellungen. Frame Generation erhöht nicht die tatsächlich berechneten Spielbilder.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Barrierefreiheit

Größere Schrift, hoher Kontrast und reduzierte Bewegung lassen sich unter Barrierefreiheit unabhängig aktivieren; standardmäßig sind sie aus. Sichtbare Fokusnavigation im Launcher garantiert keine Barrierefreiheit innerhalb der Spiele.

## Fehlerbehebung

Bei Startproblemen eboot.bin, sce_sys und ui/lang im richtigen Verzeichnis prüfen. Fehlende Spiele liegen häufig unter einem anderen gewählten Speicherstamm als roms. Bleibt die Oberfläche englisch, Übersetzungskataloge prüfen. Safe Launch setzt nur die Einstellungen eines Spiels zurück, nicht dessen Spielstände.

Lösche /data/prosperoeden/ niemals: Dort können Spielstände, Einstellungen und eigene Schlüssel liegen. Sichere auch externe Speicherpfade.

---

Die letzte tatsächlich kompilierte öffentliche PS5-Version stammt vom 15. Oktober 2026. Die Veröffentlichung vom 30. Oktober ist eine Kopie. Der neue Entwurf enthält weder Binärdateien noch bestätigte Spiele der zweiten Generation auf PS5.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)