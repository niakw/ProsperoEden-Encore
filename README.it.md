# Prospero.Eden Encore — Italiano

> Emulazione PS5 pensata per il salotto · [English (default)](README.md) · [Tutte le lingue](LANGUAGES.md)

Encore è un progetto indipendente della comunità, con launcher per controller, libreria giochi, impostazioni video e diagnostica. Non è un prodotto ufficiale Sony o Nintendo.

## Primi passi

1. Scarica il pacchetto completo da Encore Releases e verifica il checksum.
2. Esegui una copia di sicurezza dell'app PPSA99008, dei dati /data/prosperoeden e della memoria esterna.
3. Copia l'intera cartella PPSA99008 in /data/homebrew/PPSA99008/; il solo eboot.bin non basta.
4. Avvia Encore, controlla Settings → Storage e Language e usa soltanto contenuti ottenuti legalmente.

[Migrazione dal progetto originale](docs/i18n/INSTALL.it.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migrazione dal progetto originale

Encore e ProsperoEden originale condividono l'identificativo PPSA99008 e non sono due installazioni separate. Sostituisci l'intera applicazione ma conserva salvataggi, impostazioni, giochi e chiavi in /data/prosperoeden. Se la vecchia cartella assets/ conteneva dati personali, salvala prima della migrazione.

**ID applicazione :** `PPSA99008`. **Applicazione :** `/data/homebrew/PPSA99008/`. **Dati persistenti :** `/data/prosperoeden/`.

[Migrazione dal progetto originale — passo per passo](docs/i18n/INSTALL.it.md) · [Guida completa in inglese](INSTALL.md)

## Compatibilità e limiti

Solo il firmware PS5 13.60 è stato testato con Encore su una console reale. Versioni precedenti potrebbero funzionare, ma non esiste un minimo verificato. Alcuni titoli possono mostrare scatti, HUD in ritardo, pulsanti errati durante il gioco e blocchi alla pausa. Una build riuscita non prova la compatibilità.

Nel codice in sviluppo sono previsti NSP/XCI e, in via sperimentale, NSZ/XCZ. I loader diretti NRO/NSO/NCA/NAX/KIP richiedono contenuti adeguati; un'estensione riconosciuta non garantisce l'avvio.

## Domande frequenti

Switch 2 è oggetto di una ricerca separata e non è incluso nell'attuale versione PS5. La generazione dei fotogrammi e gli aggiornamenti automatici sono solo previsti.

Se il menu resta in inglese, scegli Settings → Language e verifica che la cartella ui/lang/ sia stata copiata per intero.

## Comunità e crediti

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Il progetto non include giochi, chiavi o firmware. Non pubblicare dati personali nelle segnalazioni.

> Questa traduzione presenta le informazioni essenziali. Il README inglese resta il riferimento tecnico completo; i test host non dimostrano le prestazioni su PS5.
