# Eden Encore — Felsökning · Svenska

[Översikt](README.sv-SE.md) · [Installation och uppdatering](INSTALL.sv-SE.md) · [Inställningar](SETTINGS.sv-SE.md) · [Felsökning](TROUBLESHOOTING.sv-SE.md) · [Support](SUPPORT.sv-SE.md) · [Tillgänglighet](ACCESSIBILITY.sv-SE.md) · [Languages](../../LANGUAGES.md)

Om appen inte startar kontrollerar du eboot.bin, sce_sys och ui/lang. Om spel saknas, kontrollera roms i vald lagringsrot. Om menyerna fortsätter vara på engelska, kontrollera språkfilerna. Safe Launch återställer inställningar för ett spel utan att ta bort sparfiler.

## Installation och uppdatering

Hämta ett faktiskt publicerat paket från Releases och säkerhetskopiera först appen och dina data. Vid ZIP/FTP kopierar du hela mappen PPSA99008 till /data/homebrew/PPSA99008/. Blanda inte ZIP/FTP med FFPFSC/ShadowMountPlus och kontrollera SHA-256 om en summa finns.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Inställningar

Rekommenderad startprofil är Vulkan, tv-utmatning 1440p, intern spelskala 1.25x, rumslig FSR 1 med 50 % skärpa, FXAA och 60 Hz. Tv-utmatningen är inte samma sak som spelets interna upplösning. Bildgenerering ökar inte spelets simuleringshastighet.

## Support

Ange Encore-version, PS5-firmware, exakta steg, relevanta inställningar och avidentifierade loggar i GitHub Issues. Publicera aldrig nycklar, sparfiler eller personuppgifter.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Radera aldrig /data/prosperoeden/: där kan finnas sparfiler, inställningar och nycklar. Säkerhetskopiera även extern lagring.

---

Det senaste offentligt kompilerade PS5-paketet är från 15 oktober 2026. Publiceringen den 30 oktober var en kopia. Det nya utkastet innehåller inga binärer eller verifierade spel från andra generationen på konsolen.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)