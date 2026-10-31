# Prospero.Eden Encore — Deutsch

> PS5-Emulation für das Wohnzimmer · [English (default)](README.md) · [All 18 launcher language choices](LANGUAGES.md)

PS5-Emulation für das Wohnzimmer. Encore is an independent community fork with a controller-friendly launcher, game library, graphics settings and diagnostics, not an official Sony or Nintendo product.

## Schnellstart

1. Lade das vollständige Paket aus den Encore Releases und prüfe die Prüfsumme.
2. Sichere PPSA99008, die Daten unter /data/prosperoeden und externe Laufwerke.
3. Kopiere den gesamten Ordner PPSA99008 nach /data/homebrew/PPSA99008/; nur eboot.bin reicht nicht.
4. Starte Encore, prüfe Settings → Storage und Language und verwende nur rechtmäßig erworbene Dateien.

[Wechsel vom Originalprojekt](docs/i18n/INSTALL.de.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Wechsel vom Originalprojekt

Encore und das ursprüngliche ProsperoEden nutzen dieselbe App-ID PPSA99008 und sind keine unabhängigen Installationen. Ersetze die vollständigen Anwendungsdateien, aber behalte Spielstände, Schlüssel, Einstellungen und Spiele unter /data/prosperoeden. Sichere einen alten assets/-Ordner vor der Migration.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[Wechsel vom Originalprojekt — step-by-step](docs/i18n/INSTALL.de.md) · [Full installation instructions in English](INSTALL.md)

## Kompatibilität und Grenzen

Nur PS5-Firmware 13.60 wurde mit Encore auf einer echten Konsole getestet. Ältere Versionen könnten funktionieren, sind aber nicht bestätigt; eine Mindestversion ist nicht bekannt. Einige Spiele ruckeln weiterhin, zeigen verzögerte HUD-Grafik, fehlerhafte Tasten oder Hänger beim Pausieren. Eine grüne CI ist kein Spieltest.

Content formats in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee that a complete game will start.

## Häufige Fragen

Switch 2 wird separat erforscht und ist in der PS5-Version nicht verfügbar. Frame Generation und automatische Updates stehen auf der Roadmap, wurden aber noch nicht veröffentlicht.

Bleibt das Menü englisch, wähle Settings → Language und überprüfe den gesamten Ordner ui/lang/.

## Community and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Encore verteilt keine Spiele, Schlüssel oder Firmware. Keine privaten Daten in öffentlichen Fehlerberichten teilen.

> This translation is a concise guide for the selected launcher language. For complete technical information, use the English README and linked guides. No console performance claim is implied.
