# Prospero.Eden Encore — Deutsch

> PS5-Emulation für das Wohnzimmer · [English (default)](README.md) · [Alle Sprachen](LANGUAGES.md)

Encore ist ein unabhängiger Community-Fork mit Controller-Oberfläche, Spielebibliothek, Videoeinstellungen und Diagnosefunktionen. Es ist kein offizielles Produkt von Sony oder Nintendo.

## Schnellstart

1. Lade das vollständige Paket aus den Encore Releases und prüfe die Prüfsumme.
2. Sichere PPSA99008, die Daten unter /data/prosperoeden und externe Laufwerke.
3. Kopiere den gesamten Ordner PPSA99008 nach /data/homebrew/PPSA99008/; nur eboot.bin reicht nicht.
4. Starte Encore, prüfe Settings → Storage und Language und verwende nur rechtmäßig erworbene Dateien.

[Wechsel vom Originalprojekt](docs/i18n/INSTALL.de.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Wechsel vom Originalprojekt

Encore und das ursprüngliche ProsperoEden nutzen dieselbe App-ID PPSA99008 und sind keine unabhängigen Installationen. Ersetze die vollständigen Anwendungsdateien, aber behalte Spielstände, Schlüssel, Einstellungen und Spiele unter /data/prosperoeden. Sichere einen alten assets/-Ordner vor der Migration.

**Anwendungs-ID :** `PPSA99008`. **Anwendung :** `/data/homebrew/PPSA99008/`. **Benutzerdaten :** `/data/prosperoeden/`.

[Wechsel vom Originalprojekt — Schritt für Schritt](docs/i18n/INSTALL.de.md) · [Vollständige Installationsanleitung (Englisch)](INSTALL.md)

## Kompatibilität und Grenzen

Nur PS5-Firmware 13.60 wurde mit Encore auf einer echten Konsole getestet. Ältere Versionen könnten funktionieren, sind aber nicht bestätigt; eine Mindestversion ist nicht bekannt. Einige Spiele ruckeln weiterhin, zeigen verzögerte HUD-Grafik, fehlerhafte Tasten oder Hänger beim Pausieren. Eine grüne CI ist kein Spieltest.

Die Entwicklungsversion unterstützt NSP/XCI und experimentell NSZ/XCZ. Direkte NRO/NSO/NCA/NAX/KIP-Dateien benötigen passende Inhalte: Eine bekannte Dateiendung garantiert keinen erfolgreichen Start.

## Häufige Fragen

Switch 2 wird separat erforscht und ist in der PS5-Version nicht verfügbar. Frame Generation und automatische Updates stehen auf der Roadmap, wurden aber noch nicht veröffentlicht.

Bleibt das Menü englisch, wähle Settings → Language und überprüfe den gesamten Ordner ui/lang/.

## Community und Mitwirkende

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Encore verteilt keine Spiele, Schlüssel oder Firmware. Keine privaten Daten in öffentlichen Fehlerberichten teilen.

> Diese Übersetzung bietet die wichtigsten Nutzerinformationen. Die vollständige technische Referenz ist auf Englisch verfügbar; Host-Tests beweisen keine PS5-Leistung.
