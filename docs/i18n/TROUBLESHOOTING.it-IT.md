# Eden Encore — Risoluzione dei problemi · Italiano

[Panoramica](README.it.md) · [Installazione e aggiornamento](INSTALL.it-IT.md) · [Impostazioni](SETTINGS.it-IT.md) · [Risoluzione dei problemi](TROUBLESHOOTING.it-IT.md) · [Supporto](SUPPORT.it-IT.md) · [Accessibilità](ACCESSIBILITY.it-IT.md) · [Languages](../../LANGUAGES.md)

Se l'app non parte, controlla eboot.bin, sce_sys e ui/lang. Se mancano giochi, verifica roms sotto la radice di archiviazione selezionata. Se il menu resta in inglese, verifica i cataloghi tradotti. Safe Launch ripristina le impostazioni del singolo gioco senza eliminare i salvataggi.

## Installazione e aggiornamento

Scarica da Releases un pacchetto effettivamente pubblicato e salva prima una copia dell'applicazione e dei dati. Per ZIP/FTP copia l'intera cartella PPSA99008 in /data/homebrew/PPSA99008/. Non mescolare ZIP/FTP con FFPFSC/ShadowMountPlus; controlla SHA-256 quando disponibile.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Impostazioni

Il profilo consigliato parte da Vulkan, uscita TV 1440p, scala interna 1.25x, FSR 1 spaziale con nitidezza 50%, FXAA e 60 Hz. L'uscita TV è distinta dalla risoluzione di rendering del gioco. La generazione di fotogrammi non accelera la simulazione del gioco.

## Supporto

Apri una GitHub Issue con versione Encore, firmware PS5, passi di riproduzione, impostazioni interessate e log privi di dati personali. Non pubblicare mai chiavi, salvataggi o informazioni riservate.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Non cancellare mai /data/prosperoeden/: potrebbe contenere salvataggi, impostazioni e chiavi. Fai un backup anche dello spazio di archiviazione esterno.

---

L'ultimo pacchetto PS5 pubblicamente compilato risale al 15 ottobre 2026. La pubblicazione del 30 ottobre era una copia. La nuova bozza non contiene file binari né una compatibilità di seconda generazione verificata sulla console.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)