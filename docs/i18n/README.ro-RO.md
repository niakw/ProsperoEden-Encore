# Eden Encore — Prezentare generală · Română

[Prezentare generală](README.ro-RO.md) · [Instalare și actualizare](INSTALL.ro-RO.md) · [Setări](SETTINGS.ro-RO.md) · [Depanare](TROUBLESHOOTING.ro-RO.md) · [Asistență](SUPPORT.ro-RO.md) · [Accesibilitate](ACCESSIBILITY.ro-RO.md) · [🌐](../../LANGUAGES.md)

Eden Encore este un proiect comunitar neoficial pentru PS5, cu un motor comun pentru jocurile din prima și a doua generație. Interfața este concepută pentru televizor și controler. Testele reușite ale codului sau pe gazdă nu dovedesc că un joc funcționează pe consolă.

## Instalare și actualizare

Descarcă un pachet publicat efectiv din Releases și fă mai întâi copii de siguranță ale aplicației și datelor. Pentru ZIP/FTP, copiază întregul director PPSA99008 în /data/homebrew/PPSA99008/. Nu combina ZIP/FTP cu FFPFSC/ShadowMountPlus și verifică SHA-256 dacă este disponibil.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/updates/
/data/prosperoeden/firmware/
/data/prosperoeden/keys/
```

[Instalare și actualizare](./INSTALL.ro-RO.md) · [R1 — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Setări

Profilul recomandat folosește Vulkan, ieșire TV 1440p, scară internă 1.25x, FSR 1 spațial cu claritate 50%, FXAA și 60 Hz. Rezoluția ieșirii TV nu este aceeași cu rezoluția internă a jocului. Generarea cadrelor nu mărește viteza simulării jocului.

**Vulkan** · **FSR 1 (EASU/RCAS)** · **FXAA** · **60 Hz** · `Minimum` / `Recommended` / `High`

## Setări · Touchpad

O apăsare scurtă pe Touchpad deschide setările rapide Encore în timpul jocului. Butonul central de sistem rămâne rezervat consolei. Meniul include grafică, configurarea butoanelor, FPS și diagnosticare. Unele modificări necesită repornirea jocului. Limba se alege din Settings → Language; nu toate limbile din cataloage apar în meniu.

## Accesibilitate

Textul mărit, contrastul ridicat și mișcarea redusă pot fi activate separat din Accesibilitate și sunt dezactivate implicit. Accesibilitatea lansatorului nu garantează accesibilitatea fiecărui joc.

## Depanare

Dacă aplicația nu pornește, verifică eboot.bin, sce_sys și ui/lang. Dacă lipsesc jocuri, verifică roms în rădăcina de stocare selectată. Dacă meniul rămâne în engleză, verifică fișierele de traducere. Safe Launch restabilește setările unui joc fără ștergerea salvărilor.

## Asistență

În GitHub Issues include versiunea Encore, firmware-ul PS5, pașii de reproducere, setările relevante și jurnale fără informații personale. Nu publica niciodată chei, salvări sau date private.

Nu șterge niciodată /data/prosperoeden/: poate conține salvări, setări și chei. Copiază și datele din stocarea externă.

---

Ultimul pachet public PS5 compilat efectiv datează din 15 octombrie 2026. Publicarea din 30 octombrie a fost o copie. Noul proiect de prerelease nu conține binare sau compatibilitate confirmată pentru jocurile de generația a doua pe consolă.

[English — complete README](../../README.md) · [English — full settings reference](../../SETTINGS.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
