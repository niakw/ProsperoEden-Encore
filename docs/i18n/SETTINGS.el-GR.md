# Eden Encore — Ρυθμίσεις · Ελληνικά

[Επισκόπηση](README.el-GR.md) · [Εγκατάσταση και ενημέρωση](INSTALL.el-GR.md) · [Ρυθμίσεις](SETTINGS.el-GR.md) · [Αντιμετώπιση προβλημάτων](TROUBLESHOOTING.el-GR.md) · [Υποστήριξη](SUPPORT.el-GR.md) · [Προσβασιμότητα](ACCESSIBILITY.el-GR.md) · [Languages](../../LANGUAGES.md)

Οι προτεινόμενες αρχικές ρυθμίσεις είναι Vulkan, έξοδος 1440p, εσωτερική ανάλυση 1.25x, FSR 1 με ευκρίνεια 50%, FXAA και 60 Hz. Η έξοδος της τηλεόρασης διαφέρει από την εσωτερική ανάλυση του παιχνιδιού. Η δημιουργία καρέ δεν επιταχύνει την ίδια την προσομοίωση.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Οι προτεινόμενες αρχικές ρυθμίσεις είναι Vulkan, έξοδος 1440p, εσωτερική ανάλυση 1.25x, FSR 1 με ευκρίνεια 50%, FXAA και 60 Hz. Η έξοδος της τηλεόρασης διαφέρει από την εσωτερική ανάλυση του παιχνιδιού. Η δημιουργία καρέ δεν επιταχύνει την ίδια την προσομοίωση.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Προσβασιμότητα

Το μεγαλύτερο κείμενο, η υψηλή αντίθεση και η μειωμένη κίνηση ενεργοποιούνται ανεξάρτητα στις ρυθμίσεις προσβασιμότητας και είναι απενεργοποιημένα από προεπιλογή. Η πλοήγηση του μενού δεν εγγυάται προσβασιμότητα κάθε παιχνιδιού.

## Αντιμετώπιση προβλημάτων

Αν δεν ξεκινά η εφαρμογή, ελέγξτε τα eboot.bin, sce_sys και ui/lang. Αν λείπουν παιχνίδια, ελέγξτε το roms στη σωστή ρίζα αποθήκευσης. Για μενού που παραμένουν στα αγγλικά, ελέγξτε τις μεταφράσεις. Το Safe Launch επαναφέρει ρυθμίσεις συγκεκριμένου παιχνιδιού χωρίς διαγραφή αποθηκεύσεων.

Μη διαγράφετε το /data/prosperoeden/: μπορεί να περιέχει αποθηκεύσεις, ρυθμίσεις και κλειδιά. Κρατήστε αντίγραφο και της εξωτερικής αποθήκευσης.

---

Η τελευταία δημόσια μεταγλώττιση PS5 έγινε στις 15 Οκτωβρίου 2026. Η έκδοση της 30ής Οκτωβρίου ήταν αντίγραφο. Το νέο προσχέδιο δεν περιέχει εκτελέσιμα αρχεία ούτε επαληθευμένη συμβατότητα δεύτερης γενιάς.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)