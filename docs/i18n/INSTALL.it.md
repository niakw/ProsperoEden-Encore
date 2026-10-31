# Prospero.Eden Encore — Migrazione dal progetto originale (Italiano)

[← Italiano](../../README.it.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

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

**Important:** Never delete `/data/prosperoeden/` or format external storage during an update. Back up first and preserve all saves, keys and existing media.

## Compatibilità e limiti

Solo il firmware PS5 13.60 è stato testato con Encore su una console reale. Versioni precedenti potrebbero funzionare, ma non esiste un minimo verificato. Alcuni titoli possono mostrare scatti, HUD in ritardo, pulsanti errati durante il gioco e blocchi alla pausa. Una build riuscita non prova la compatibilità.

## Domande frequenti

Se il menu resta in inglese, scegli Settings → Language e verifica che la cartella ui/lang/ sia stata copiata per intero.

If one title stops booting after settings changes, try **Safe Launch** without deleting its saves. Consult [ZIP/FFPFSC/ShadowMountPlus instructions](../../INSTALL.md), [Troubleshooting](../../TROUBLESHOOTING.md) or [Support](../../SUPPORT.md).

Il progetto non include giochi, chiavi o firmware. Non pubblicare dati personali nelle segnalazioni.
