# Eden Encore — Fehlerbehebung · Deutsch

[Überblick](README.de.md) · [Installation und Update](INSTALL.de-DE.md) · [Einstellungen](SETTINGS.de-DE.md) · [Fehlerbehebung](TROUBLESHOOTING.de-DE.md) · [Support](SUPPORT.de-DE.md) · [Barrierefreiheit](ACCESSIBILITY.de-DE.md) · [Languages](../../LANGUAGES.md)

Bei Startproblemen eboot.bin, sce_sys und ui/lang im richtigen Verzeichnis prüfen. Fehlende Spiele liegen häufig unter einem anderen gewählten Speicherstamm als roms. Bleibt die Oberfläche englisch, Übersetzungskataloge prüfen. Safe Launch setzt nur die Einstellungen eines Spiels zurück, nicht dessen Spielstände.

## Installation und Update

Lade ein tatsächlich veröffentlichtes Paket von Releases herunter und sichere zunächst Anwendung und Daten. Bei ZIP/FTP den vollständigen Ordner PPSA99008 nach /data/homebrew/PPSA99008/ kopieren. ZIP/FTP und FFPFSC/ShadowMountPlus nicht vermischen; verfügbare SHA-256-Prüfsummen kontrollieren.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Einstellungen

Das empfohlene Ausgangsprofil nutzt Vulkan, 1440p-TV-Ausgabe, 1.25x interne Spielauflösung, räumliches FSR 1 bei 50 % Schärfe, FXAA und 60 Hz. TV-Ausgabe und Spielauflösung sind unterschiedliche Einstellungen. Frame Generation erhöht nicht die tatsächlich berechneten Spielbilder.

## Support

Fehlerberichte sollten Encore-Version, PS5-Firmware, reproduzierbare Schritte, betroffene Einstellungen und bereinigte Protokolle enthalten. Nutze GitHub Issues und veröffentliche niemals Schlüssel, persönliche Daten oder Spielstände.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Lösche /data/prosperoeden/ niemals: Dort können Spielstände, Einstellungen und eigene Schlüssel liegen. Sichere auch externe Speicherpfade.

---

Die letzte tatsächlich kompilierte öffentliche PS5-Version stammt vom 15. Oktober 2026. Die Veröffentlichung vom 30. Oktober ist eine Kopie. Der neue Entwurf enthält weder Binärdateien noch bestätigte Spiele der zweiten Generation auf PS5.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)