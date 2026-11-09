# Eden Encore — Instalace a aktualizace · Čeština

[Přehled](README.cs-CZ.md) · [Instalace a aktualizace](INSTALL.cs-CZ.md) · [Nastavení](SETTINGS.cs-CZ.md) · [Řešení problémů](TROUBLESHOOTING.cs-CZ.md) · [Podpora](SUPPORT.cs-CZ.md) · [Přístupnost](ACCESSIBILITY.cs-CZ.md) · [Languages](../../LANGUAGES.md)

Stáhněte skutečně vydaný balíček ze stránky Releases a nejdříve zazálohujte aplikaci i data. Při instalaci ZIP/FTP zkopírujte celý adresář PPSA99008 do /data/homebrew/PPSA99008/. Nemíchejte ZIP/FTP s FFPFSC/ShadowMountPlus a případně ověřte kontrolní součet SHA-256.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Nikdy nemažte /data/prosperoeden/: může obsahovat nastavení, uložené hry a vaše klíče. Zálohujte i případné externí úložiště.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Řešení problémů

Pokud aplikace nenaběhne, ověřte eboot.bin, sce_sys a ui/lang ve správné složce. Chybějící hry hledejte v roms pod vybraným úložištěm. Pokud nabídky zůstávají anglické, zkontrolujte soubory překladů. Safe Launch obnoví nastavení problematické hry bez smazání uložených pozic.

Poslední veřejně sestavený balíček PS5 pochází z 15. října 2026. Vydání z 30. října je jeho kopie. Nový koncept vydání neobsahuje binární soubory ani ověřenou podporu her druhé generace na konzoli.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)