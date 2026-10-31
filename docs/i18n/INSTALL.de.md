# Prospero.Eden Encore — Wechsel vom Originalprojekt (Deutsch)

[← Deutsch](README.de.md) · [Vollständige Installationsanleitung (Englisch)](../../INSTALL.md) · [Alle Sprachen](../../LANGUAGES.md)

## Schnellstart

1. Lade das vollständige Paket aus den Encore Releases und prüfe die Prüfsumme.
2. Sichere PPSA99008, die Daten unter /data/prosperoeden und externe Laufwerke.
3. Kopiere den gesamten Ordner PPSA99008 nach /data/homebrew/PPSA99008/; nur eboot.bin reicht nicht.
4. Starte Encore, prüfe Settings → Storage und Language und verwende nur rechtmäßig erworbene Dateien.

## Anwendung / PPSA99008

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent user files
/data/prosperoeden/keys/          # legally obtained keys
/data/prosperoeden/firmware/      # compatible firmware files
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # game updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # diagnostics
```

## Wechsel vom Originalprojekt

Encore und das ursprüngliche ProsperoEden nutzen dieselbe App-ID PPSA99008 und sind keine unabhängigen Installationen. Ersetze die vollständigen Anwendungsdateien, aber behalte Spielstände, Schlüssel, Einstellungen und Spiele unter /data/prosperoeden. Sichere einen alten assets/-Ordner vor der Migration.

**Wichtig:** Lösche beim Aktualisieren niemals `/data/prosperoeden/` und formatiere keine externen Laufwerke. Erstelle zuerst ein Backup und überschreibe keine Spielstände oder Schlüssel.

## Kompatibilität und Grenzen

Nur PS5-Firmware 13.60 wurde mit Encore auf einer echten Konsole getestet. Ältere Versionen könnten funktionieren, sind aber nicht bestätigt; eine Mindestversion ist nicht bekannt. Einige Spiele ruckeln weiterhin, zeigen verzögerte HUD-Grafik, fehlerhafte Tasten oder Hänger beim Pausieren. Eine grüne CI ist kein Spieltest.

## Häufige Fragen

Bleibt das Menü englisch, wähle Settings → Language und überprüfe den gesamten Ordner ui/lang/.

Startet ein Titel nach einer Einstellungsänderung nicht mehr, nutze **Safe Launch** für diese Sitzung, ohne Spielstände zu löschen. Weitere Informationen: [ZIP/FFPFSC-Installation](../../INSTALL.md), [Fehlerbehebung](../../TROUBLESHOOTING.md), [Support](../../SUPPORT.md).

Encore verteilt keine Spiele, Schlüssel oder Firmware. Keine privaten Daten in öffentlichen Fehlerberichten teilen.
