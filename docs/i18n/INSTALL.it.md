# Prospero.Eden Encore — Migrazione dal progetto originale (Italiano)

[← Italiano](README.it.md) · [Guida completa in inglese](../../INSTALL.md) · [Tutte le lingue](../../LANGUAGES.md)

## Primi passi

1. Scarica il pacchetto completo da Encore Releases e verifica il checksum.
2. Esegui una copia di sicurezza dell'app PPSA99008, dei dati /data/prosperoeden e della memoria esterna.
3. Copia l'intera cartella PPSA99008 in /data/homebrew/PPSA99008/; il solo eboot.bin non basta.
4. Avvia Encore, controlla Settings → Storage e Language e usa soltanto contenuti ottenuti legalmente.

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

## Migrazione dal progetto originale

Encore e ProsperoEden originale condividono l'identificativo PPSA99008 e non sono due installazioni separate. Sostituisci l'intera applicazione ma conserva salvataggi, impostazioni, giochi e chiavi in /data/prosperoeden. Se la vecchia cartella assets/ conteneva dati personali, salvala prima della migrazione.

**Importante:** Non cancellare mai `/data/prosperoeden/` né formattare l'unità esterna durante un aggiornamento. Esegui il backup e conserva salvataggi e chiavi.

## Compatibilità e limiti

Solo il firmware PS5 13.60 è stato testato con Encore su una console reale. Versioni precedenti potrebbero funzionare, ma non esiste un minimo verificato. Alcuni titoli possono mostrare scatti, HUD in ritardo, pulsanti errati durante il gioco e blocchi alla pausa. Una build riuscita non prova la compatibilità.

## Domande frequenti

Se il menu resta in inglese, scegli Settings → Language e verifica che la cartella ui/lang/ sia stata copiata per intero.

Se un titolo smette di avviarsi dopo aver modificato le impostazioni, prova **Safe Launch** per una sessione senza cancellare i salvataggi. Consulta [installazione ZIP/FFPFSC](../../INSTALL.md), [risoluzione dei problemi](../../TROUBLESHOOTING.md) e [supporto](../../SUPPORT.md).

Il progetto non include giochi, chiavi o firmware. Non pubblicare dati personali nelle segnalazioni.
