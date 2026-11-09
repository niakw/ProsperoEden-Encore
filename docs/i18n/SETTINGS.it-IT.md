# Eden Encore — Impostazioni · Italiano

[Panoramica](README.it.md) · [Installazione e aggiornamento](INSTALL.it-IT.md) · [Impostazioni](SETTINGS.it-IT.md) · [Risoluzione dei problemi](TROUBLESHOOTING.it-IT.md) · [Supporto](SUPPORT.it-IT.md) · [Accessibilità](ACCESSIBILITY.it-IT.md) · [Languages](../../LANGUAGES.md)

Il profilo consigliato parte da Vulkan, uscita TV 1440p, scala interna 1.25x, FSR 1 spaziale con nitidezza 50%, FXAA e 60 Hz. L'uscita TV è distinta dalla risoluzione di rendering del gioco. La generazione di fotogrammi non accelera la simulazione del gioco.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Il profilo consigliato parte da Vulkan, uscita TV 1440p, scala interna 1.25x, FSR 1 spaziale con nitidezza 50%, FXAA e 60 Hz. L'uscita TV è distinta dalla risoluzione di rendering del gioco. La generazione di fotogrammi non accelera la simulazione del gioco.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Accessibilità

Testo ingrandito, contrasto elevato e movimento ridotto si attivano separatamente nelle opzioni Accessibilità e sono disattivati all'inizio. La navigazione accessibile del launcher non certifica l'accessibilità di tutti i giochi.

## Risoluzione dei problemi

Se l'app non parte, controlla eboot.bin, sce_sys e ui/lang. Se mancano giochi, verifica roms sotto la radice di archiviazione selezionata. Se il menu resta in inglese, verifica i cataloghi tradotti. Safe Launch ripristina le impostazioni del singolo gioco senza eliminare i salvataggi.

Non cancellare mai /data/prosperoeden/: potrebbe contenere salvataggi, impostazioni e chiavi. Fai un backup anche dello spazio di archiviazione esterno.

---

L'ultimo pacchetto PS5 pubblicamente compilato risale al 15 ottobre 2026. La pubblicazione del 30 ottobre era una copia. La nuova bozza non contiene file binari né una compatibilità di seconda generazione verificata sulla console.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)