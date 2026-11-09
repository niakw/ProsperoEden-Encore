# Eden Encore — Installation och uppdatering · Svenska

[Översikt](README.sv-SE.md) · [Installation och uppdatering](INSTALL.sv-SE.md) · [Inställningar](SETTINGS.sv-SE.md) · [Felsökning](TROUBLESHOOTING.sv-SE.md) · [Support](SUPPORT.sv-SE.md) · [Tillgänglighet](ACCESSIBILITY.sv-SE.md) · [Languages](../../LANGUAGES.md)

Hämta ett faktiskt publicerat paket från Releases och säkerhetskopiera först appen och dina data. Vid ZIP/FTP kopierar du hela mappen PPSA99008 till /data/homebrew/PPSA99008/. Blanda inte ZIP/FTP med FFPFSC/ShadowMountPlus och kontrollera SHA-256 om en summa finns.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Radera aldrig /data/prosperoeden/: där kan finnas sparfiler, inställningar och nycklar. Säkerhetskopiera även extern lagring.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Felsökning

Om appen inte startar kontrollerar du eboot.bin, sce_sys och ui/lang. Om spel saknas, kontrollera roms i vald lagringsrot. Om menyerna fortsätter vara på engelska, kontrollera språkfilerna. Safe Launch återställer inställningar för ett spel utan att ta bort sparfiler.

Det senaste offentligt kompilerade PS5-paketet är från 15 oktober 2026. Publiceringen den 30 oktober var en kopia. Det nya utkastet innehåller inga binärer eller verifierade spel från andra generationen på konsolen.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)