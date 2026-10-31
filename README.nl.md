# Prospero.Eden Encore — Nederlands

> PS5-emulatie voor op de bank · [English (default)](README.md) · [Alle talen](LANGUAGES.md)

Encore is een onafhankelijk communityproject met een controllergerichte launcher, gamebibliotheek, beeldinstellingen en diagnostiek. Het is geen officieel product van Sony of Nintendo.

## Snel beginnen

1. Download het volledige pakket via Encore Releases en controleer de checksum.
2. Maak een back-up van de map PPSA99008, de gegevens in /data/prosperoeden en externe opslag.
3. Kopieer de volledige map PPSA99008 naar /data/homebrew/PPSA99008/; alleen eboot.bin volstaat niet.
4. Start Encore, controleer Settings → Storage en Language en gebruik alleen rechtmatig verkregen bestanden.

[Overstappen vanaf het oorspronkelijke project](docs/i18n/INSTALL.nl.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Overstappen vanaf het oorspronkelijke project

Encore en de originele ProsperoEden gebruiken dezelfde app-ID PPSA99008 en zijn geen onafhankelijke installaties. Vervang de volledige programmabestanden maar behoud opgeslagen spellen, instellingen, games en sleutels onder /data/prosperoeden. Maak ook een back-up van een oude assets/-map als die gebruikersgegevens bevat.

**App-ID :** `PPSA99008`. **Applicatie :** `/data/homebrew/PPSA99008/`. **Blijvende gegevens :** `/data/prosperoeden/`.

[Overstappen vanaf het oorspronkelijke project — stap voor stap](docs/i18n/INSTALL.nl.md) · [Volledige Engelse installatiehandleiding](INSTALL.md)

## Compatibiliteit en beperkingen

Alleen PS5-firmware 13.60 is met Encore op een echte console getest. Oudere versies werken misschien, maar zijn niet bevestigd en er is geen gecontroleerde minimumversie. Sommige games kunnen haperen, een vertraagde HUD tonen, verkeerde knoppen gebruiken of bij pauzeren vastlopen. Een geslaagde build bewijst geen spelcompatibiliteit.

De ontwikkelcode ondersteunt NSP/XCI en experimenteel NSZ/XCZ. Rechtstreekse NRO/NSO/NCA/NAX/KIP-laders vereisen de juiste inhoud; een herkende extensie garandeert niet dat een game start.

## Veelgestelde vragen

Switch 2 wordt apart onderzocht en maakt geen deel uit van de huidige PS5-versie. Framegeneratie en automatisch bijwerken staan op de planning maar zijn nog niet uitgebracht.

Blijft het menu Engels? Kies Settings → Language en controleer of de volledige map ui/lang/ is geïnstalleerd.

## Community en dankwoord

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Het project verspreidt geen games, sleutels of firmware. Deel geen privégegevens in openbare bugmeldingen.

> Deze vertaling bevat de belangrijkste gebruikersinformatie. De volledige technische documentatie is in het Engels; hosttests bewijzen geen PS5-prestaties.
