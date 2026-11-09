# Eden Encore — Instalare și actualizare · Română

[Prezentare generală](README.ro-RO.md) · [Instalare și actualizare](INSTALL.ro-RO.md) · [Setări](SETTINGS.ro-RO.md) · [Depanare](TROUBLESHOOTING.ro-RO.md) · [Asistență](SUPPORT.ro-RO.md) · [Accesibilitate](ACCESSIBILITY.ro-RO.md) · [Languages](../../LANGUAGES.md)

Descarcă un pachet publicat efectiv din Releases și fă mai întâi copii de siguranță ale aplicației și datelor. Pentru ZIP/FTP, copiază întregul director PPSA99008 în /data/homebrew/PPSA99008/. Nu combina ZIP/FTP cu FFPFSC/ShadowMountPlus și verifică SHA-256 dacă este disponibil.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Nu șterge niciodată /data/prosperoeden/: poate conține salvări, setări și chei. Copiază și datele din stocarea externă.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Depanare

Dacă aplicația nu pornește, verifică eboot.bin, sce_sys și ui/lang. Dacă lipsesc jocuri, verifică roms în rădăcina de stocare selectată. Dacă meniul rămâne în engleză, verifică fișierele de traducere. Safe Launch restabilește setările unui joc fără ștergerea salvărilor.

Ultimul pachet public PS5 compilat efectiv datează din 15 octombrie 2026. Publicarea din 30 octombrie a fost o copie. Noul proiect de prerelease nu conține binare sau compatibilitate confirmată pentru jocurile de generația a doua pe consolă.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)