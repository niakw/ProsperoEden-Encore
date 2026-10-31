# Prospero.Eden Encore — Overstappen vanaf het oorspronkelijke project (Nederlands)

[← Nederlands](../../README.nl.md) · [Volledige Engelse installatiehandleiding](../../INSTALL.md) · [Alle talen](../../LANGUAGES.md)

## Snel beginnen

1. Download het volledige pakket via Encore Releases en controleer de checksum.
2. Maak een back-up van de map PPSA99008, de gegevens in /data/prosperoeden en externe opslag.
3. Kopieer de volledige map PPSA99008 naar /data/homebrew/PPSA99008/; alleen eboot.bin volstaat niet.
4. Start Encore, controleer Settings → Storage en Language en gebruik alleen rechtmatig verkregen bestanden.

## PPSA99008 / storage

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent data
/data/prosperoeden/keys/          # legal keys
/data/prosperoeden/firmware/      # compatible firmware
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # logs
```

## Overstappen vanaf het oorspronkelijke project

Encore en de originele ProsperoEden gebruiken dezelfde app-ID PPSA99008 en zijn geen onafhankelijke installaties. Vervang de volledige programmabestanden maar behoud opgeslagen spellen, instellingen, games en sleutels onder /data/prosperoeden. Maak ook een back-up van een oude assets/-map als die gebruikersgegevens bevat.

**Belangrijk:** Verwijder `/data/prosperoeden/` nooit en formatteer geen externe opslag tijdens een update. Maak eerst een back-up en overschrijf geen opgeslagen spellen of sleutels.

## Compatibiliteit en beperkingen

Alleen PS5-firmware 13.60 is met Encore op een echte console getest. Oudere versies werken misschien, maar zijn niet bevestigd en er is geen gecontroleerde minimumversie. Sommige games kunnen haperen, een vertraagde HUD tonen, verkeerde knoppen gebruiken of bij pauzeren vastlopen. Een geslaagde build bewijst geen spelcompatibiliteit.

## Veelgestelde vragen

Blijft het menu Engels? Kies Settings → Language en controleer of de volledige map ui/lang/ is geïnstalleerd.

Start een game na het wijzigen van instellingen niet meer, probeer dan tijdelijk **Safe Launch** zonder opgeslagen data te wissen. Zie [ZIP/FFPFSC-installatie](../../INSTALL.md), [probleemoplossing](../../TROUBLESHOOTING.md) en [ondersteuning](../../SUPPORT.md).

Het project verspreidt geen games, sleutels of firmware. Deel geen privégegevens in openbare bugmeldingen.
