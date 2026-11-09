# Eden Encore — Översikt · Svenska

[Översikt](README.sv-SE.md) · [Installation och uppdatering](INSTALL.sv-SE.md) · [Inställningar](SETTINGS.sv-SE.md) · [Felsökning](TROUBLESHOOTING.sv-SE.md) · [Support](SUPPORT.sv-SE.md) · [Tillgänglighet](ACCESSIBILITY.sv-SE.md) · [Languages](../../LANGUAGES.md)

Eden Encore är ett inofficiellt PS5-projekt från communityn med gemensam kod för spel från första och andra generationen. Gränssnittet är gjort för tv och handkontroll. Godkända källkods- eller värddatortester bevisar inte att ett spel fungerar på konsolen.

## Installation och uppdatering

Hämta ett faktiskt publicerat paket från Releases och säkerhetskopiera först appen och dina data. Vid ZIP/FTP kopierar du hela mappen PPSA99008 till /data/homebrew/PPSA99008/. Blanda inte ZIP/FTP med FFPFSC/ShadowMountPlus och kontrollera SHA-256 om en summa finns.

[Actual R1 package — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Inställningar

Rekommenderad startprofil är Vulkan, tv-utmatning 1440p, intern spelskala 1.25x, rumslig FSR 1 med 50 % skärpa, FXAA och 60 Hz. Tv-utmatningen är inte samma sak som spelets interna upplösning. Bildgenerering ökar inte spelets simuleringshastighet.

## Felsökning

Om appen inte startar kontrollerar du eboot.bin, sce_sys och ui/lang. Om spel saknas, kontrollera roms i vald lagringsrot. Om menyerna fortsätter vara på engelska, kontrollera språkfilerna. Safe Launch återställer inställningar för ett spel utan att ta bort sparfiler.

## Support

Ange Encore-version, PS5-firmware, exakta steg, relevanta inställningar och avidentifierade loggar i GitHub Issues. Publicera aldrig nycklar, sparfiler eller personuppgifter.

## Tillgänglighet

Större text, hög kontrast och minskad rörelse kan aktiveras var för sig under Tillgänglighet; de är avstängda som standard. En tillgänglig startmeny garanterar inte tillgänglighet inne i spelen.

Radera aldrig /data/prosperoeden/: där kan finnas sparfiler, inställningar och nycklar. Säkerhetskopiera även extern lagring.

---

Det senaste offentligt kompilerade PS5-paketet är från 15 oktober 2026. Publiceringen den 30 oktober var en kopia. Det nya utkastet innehåller inga binärer eller verifierade spel från andra generationen på konsolen.

[Full English reference](../../README.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)