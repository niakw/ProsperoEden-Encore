# Eden Encore — Översikt · Svenska

[Översikt](README.sv-SE.md) · [Installation och uppdatering](INSTALL.sv-SE.md) · [Inställningar](SETTINGS.sv-SE.md) · [Felsökning](TROUBLESHOOTING.sv-SE.md) · [Support](SUPPORT.sv-SE.md) · [Tillgänglighet](ACCESSIBILITY.sv-SE.md) · [🌐](../../LANGUAGES.md)

Eden Encore är ett inofficiellt PS5-projekt från communityn med gemensam kod för spel från första och andra generationen. Gränssnittet är gjort för tv och handkontroll. Godkända källkods- eller värddatortester bevisar inte att ett spel fungerar på konsolen.

## Installation och uppdatering

Hämta ett faktiskt publicerat paket från Releases och säkerhetskopiera först appen och dina data. Vid ZIP/FTP kopierar du hela mappen PPSA99008 till /data/homebrew/PPSA99008/. Blanda inte ZIP/FTP med FFPFSC/ShadowMountPlus och kontrollera SHA-256 om en summa finns.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/updates/
/data/prosperoeden/firmware/
/data/prosperoeden/keys/
```

[Installation och uppdatering](./INSTALL.sv-SE.md) · [R1 — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Inställningar

Rekommenderad startprofil är Vulkan, tv-utmatning 1440p, intern spelskala 1.25x, rumslig FSR 1 med 50 % skärpa, FXAA och 60 Hz. Tv-utmatningen är inte samma sak som spelets interna upplösning. Bildgenerering ökar inte spelets simuleringshastighet.

**Vulkan** · **FSR 1 (EASU/RCAS)** · **FXAA** · **60 Hz** · `Minimum` / `Recommended` / `High`

## Inställningar · Touchpad

Ett kort tryck på Touchpad öppnar Encores snabbinställningar under spelet. Den centrala systemknappen är reserverad för konsolen. Menyn samlar grafik, knappmappning, FPS och diagnostik. Vissa ändringar kräver att spelet startas om. Språk väljs under Settings → Language; inte alla katalogspråk kan väljas i menyn.

## Tillgänglighet

Större text, hög kontrast och minskad rörelse kan aktiveras var för sig under Tillgänglighet; de är avstängda som standard. En tillgänglig startmeny garanterar inte tillgänglighet inne i spelen.

## Felsökning

Om appen inte startar kontrollerar du eboot.bin, sce_sys och ui/lang. Om spel saknas, kontrollera roms i vald lagringsrot. Om menyerna fortsätter vara på engelska, kontrollera språkfilerna. Safe Launch återställer inställningar för ett spel utan att ta bort sparfiler.

## Support

Ange Encore-version, PS5-firmware, exakta steg, relevanta inställningar och avidentifierade loggar i GitHub Issues. Publicera aldrig nycklar, sparfiler eller personuppgifter.

Radera aldrig /data/prosperoeden/: där kan finnas sparfiler, inställningar och nycklar. Säkerhetskopiera även extern lagring.

---

Det senaste offentligt kompilerade PS5-paketet är från 15 oktober 2026. Publiceringen den 30 oktober var en kopia. Det nya utkastet innehåller inga binärer eller verifierade spel från andra generationen på konsolen.

[English — complete README](../../README.md) · [English — full settings reference](../../SETTINGS.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
