# Eden Encore — Depanare · Română

[Prezentare generală](README.ro-RO.md) · [Instalare și actualizare](INSTALL.ro-RO.md) · [Setări](SETTINGS.ro-RO.md) · [Depanare](TROUBLESHOOTING.ro-RO.md) · [Asistență](SUPPORT.ro-RO.md) · [Accesibilitate](ACCESSIBILITY.ro-RO.md) · [🌐](../../LANGUAGES.md)

Dacă aplicația nu pornește, verifică eboot.bin, sce_sys și ui/lang. Dacă lipsesc jocuri, verifică roms în rădăcina de stocare selectată. Dacă meniul rămâne în engleză, verifică fișierele de traducere. Safe Launch restabilește setările unui joc fără ștergerea salvărilor.

## Instalare și actualizare

Descarcă un pachet publicat efectiv din Releases și fă mai întâi copii de siguranță ale aplicației și datelor. Pentru ZIP/FTP, copiază întregul director PPSA99008 în /data/homebrew/PPSA99008/. Nu combina ZIP/FTP cu FFPFSC/ShadowMountPlus și verifică SHA-256 dacă este disponibil.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## Setări

Profilul recomandat folosește Vulkan, ieșire TV 1440p, scară internă 1.25x, FSR 1 spațial cu claritate 50%, FXAA și 60 Hz. Rezoluția ieșirii TV nu este aceeași cu rezoluția internă a jocului. Generarea cadrelor nu mărește viteza simulării jocului.

## Asistență

În GitHub Issues include versiunea Encore, firmware-ul PS5, pașii de reproducere, setările relevante și jurnale fără informații personale. Nu publica niciodată chei, salvări sau date private.

Nu șterge niciodată /data/prosperoeden/: poate conține salvări, setări și chei. Copiază și datele din stocarea externă.

---

Ultimul pachet public PS5 compilat efectiv datează din 15 octombrie 2026. Publicarea din 30 octombrie a fost o copie. Noul proiect de prerelease nu conține binare sau compatibilitate confirmată pentru jocurile de generația a doua pe consolă.

[English](../../TROUBLESHOOTING.md) · [Instalare și actualizare](INSTALL.ro-RO.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
