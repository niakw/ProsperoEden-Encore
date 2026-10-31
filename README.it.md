# Prospero.Eden Encore — Italiano

> Emulazione PS5 pensata per il salotto · [English (default)](README.md) · [All launcher languages](LANGUAGES.md)

Emulazione PS5 pensata per il salotto. Encore is an independent community emulator fork with a controller-first launcher, library, video settings and diagnostics. It is not an official Sony or Nintendo product.

## Primi passi

1. Scarica il pacchetto completo da Encore Releases e verifica il checksum.
2. Esegui una copia di sicurezza dell'app PPSA99008, dei dati /data/prosperoeden e della memoria esterna.
3. Copia l'intera cartella PPSA99008 in /data/homebrew/PPSA99008/; il solo eboot.bin non basta.
4. Avvia Encore, controlla Settings → Storage e Language e usa soltanto contenuti ottenuti legalmente.

[Migrazione dal progetto originale](docs/i18n/INSTALL.it.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migrazione dal progetto originale

Encore e ProsperoEden originale condividono l'identificativo PPSA99008 e non sono due installazioni separate. Sostituisci l'intera applicazione ma conserva salvataggi, impostazioni, giochi e chiavi in /data/prosperoeden. Se la vecchia cartella assets/ conteneva dati personali, salvala prima della migrazione.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[Migrazione dal progetto originale — step-by-step](docs/i18n/INSTALL.it.md) · [Full installation instructions in English](INSTALL.md)

## Compatibilità e limiti

Solo il firmware PS5 13.60 è stato testato con Encore su una console reale. Versioni precedenti potrebbero funzionare, ma non esiste un minimo verificato. Alcuni titoli possono mostrare scatti, HUD in ritardo, pulsanti errati durante il gioco e blocchi alla pausa. Una build riuscita non prova la compatibilità.

Game container support in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee a title will run.

## Domande frequenti

Switch 2 è oggetto di una ricerca separata e non è incluso nell'attuale versione PS5. La generazione dei fotogrammi e gli aggiornamenti automatici sono solo previsti.

Se il menu resta in inglese, scegli Settings → Language e verifica che la cartella ui/lang/ sia stata copiata per intero.

## Links and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Il progetto non include giochi, chiavi o firmware. Non pubblicare dati personali nelle segnalazioni.

> This localized README covers essential user information. The English README remains the full technical reference; host tests do not certify PS5 performance.
