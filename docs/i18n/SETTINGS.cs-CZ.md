# Eden Encore — Nastavení · Čeština

[Přehled](README.cs-CZ.md) · [Instalace a aktualizace](INSTALL.cs-CZ.md) · [Nastavení](SETTINGS.cs-CZ.md) · [Řešení problémů](TROUBLESHOOTING.cs-CZ.md) · [Podpora](SUPPORT.cs-CZ.md) · [Přístupnost](ACCESSIBILITY.cs-CZ.md) · [Languages](../../LANGUAGES.md)

Doporučené výchozí nastavení používá Vulkan, výstup 1440p, interní měřítko 1.25x, prostorové FSR 1 s ostrostí 50 %, FXAA a 60 Hz. Rozlišení televizního výstupu a vykreslovací rozlišení hry jsou rozdílné. Generování snímků nemění rychlost emulované hry.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Doporučené výchozí nastavení používá Vulkan, výstup 1440p, interní měřítko 1.25x, prostorové FSR 1 s ostrostí 50 %, FXAA a 60 Hz. Rozlišení televizního výstupu a vykreslovací rozlišení hry jsou rozdílné. Generování snímků nemění rychlost emulované hry.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Přístupnost

V nastavení přístupnosti lze samostatně zapnout větší text, vysoký kontrast a omezení animací; standardně jsou vypnuté. Ovládání nabídky používá viditelné zvýraznění. Nezaručuje to přístupnost obsahu jednotlivých her.

## Řešení problémů

Pokud aplikace nenaběhne, ověřte eboot.bin, sce_sys a ui/lang ve správné složce. Chybějící hry hledejte v roms pod vybraným úložištěm. Pokud nabídky zůstávají anglické, zkontrolujte soubory překladů. Safe Launch obnoví nastavení problematické hry bez smazání uložených pozic.

Nikdy nemažte /data/prosperoeden/: může obsahovat nastavení, uložené hry a vaše klíče. Zálohujte i případné externí úložiště.

---

Poslední veřejně sestavený balíček PS5 pochází z 15. října 2026. Vydání z 30. října je jeho kopie. Nový koncept vydání neobsahuje binární soubory ani ověřenou podporu her druhé generace na konzoli.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)