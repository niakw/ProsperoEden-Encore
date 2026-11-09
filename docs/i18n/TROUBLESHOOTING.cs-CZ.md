# Eden Encore — Řešení problémů · Čeština

[Přehled](README.cs-CZ.md) · [Instalace a aktualizace](INSTALL.cs-CZ.md) · [Nastavení](SETTINGS.cs-CZ.md) · [Řešení problémů](TROUBLESHOOTING.cs-CZ.md) · [Podpora](SUPPORT.cs-CZ.md) · [Přístupnost](ACCESSIBILITY.cs-CZ.md) · [🌐](../../LANGUAGES.md)

Pokud aplikace nenaběhne, ověřte eboot.bin, sce_sys a ui/lang ve správné složce. Chybějící hry hledejte v roms pod vybraným úložištěm. Pokud nabídky zůstávají anglické, zkontrolujte soubory překladů. Safe Launch obnoví nastavení problematické hry bez smazání uložených pozic.

## Instalace a aktualizace

Stáhněte skutečně vydaný balíček ze stránky Releases a nejdříve zazálohujte aplikaci i data. Při instalaci ZIP/FTP zkopírujte celý adresář PPSA99008 do /data/homebrew/PPSA99008/. Nemíchejte ZIP/FTP s FFPFSC/ShadowMountPlus a případně ověřte kontrolní součet SHA-256.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## Nastavení

Doporučené výchozí nastavení používá Vulkan, výstup 1440p, interní měřítko 1.25x, prostorové FSR 1 s ostrostí 50 %, FXAA a 60 Hz. Rozlišení televizního výstupu a vykreslovací rozlišení hry jsou rozdílné. Generování snímků nemění rychlost emulované hry.

## Podpora

Při hlášení chyby uveďte verzi Encore, firmware PS5, přesný postup, příslušná nastavení a anonymizované logy. Využijte oficiální GitHub Issues; nikdy nezveřejňujte klíče, soukromé soubory ani uložené hry.

Nikdy nemažte /data/prosperoeden/: může obsahovat nastavení, uložené hry a vaše klíče. Zálohujte i případné externí úložiště.

---

Poslední veřejně sestavený balíček PS5 pochází z 15. října 2026. Vydání z 30. října je jeho kopie. Nový koncept vydání neobsahuje binární soubory ani ověřenou podporu her druhé generace na konzoli.

[English](../../TROUBLESHOOTING.md) · [Instalace a aktualizace](INSTALL.cs-CZ.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
