# Eden Encore — Αντιμετώπιση προβλημάτων · Ελληνικά

[Επισκόπηση](README.el-GR.md) · [Εγκατάσταση και ενημέρωση](INSTALL.el-GR.md) · [Ρυθμίσεις](SETTINGS.el-GR.md) · [Αντιμετώπιση προβλημάτων](TROUBLESHOOTING.el-GR.md) · [Υποστήριξη](SUPPORT.el-GR.md) · [Προσβασιμότητα](ACCESSIBILITY.el-GR.md) · [Languages](../../LANGUAGES.md)

Αν δεν ξεκινά η εφαρμογή, ελέγξτε τα eboot.bin, sce_sys και ui/lang. Αν λείπουν παιχνίδια, ελέγξτε το roms στη σωστή ρίζα αποθήκευσης. Για μενού που παραμένουν στα αγγλικά, ελέγξτε τις μεταφράσεις. Το Safe Launch επαναφέρει ρυθμίσεις συγκεκριμένου παιχνιδιού χωρίς διαγραφή αποθηκεύσεων.

## Εγκατάσταση και ενημέρωση

Κατεβάστε πακέτο που έχει όντως δημοσιευτεί από τα Releases και κρατήστε πρώτα αντίγραφα ασφαλείας. Για ZIP/FTP αντιγράψτε ολόκληρο τον φάκελο PPSA99008 στο /data/homebrew/PPSA99008/. Μην αναμειγνύετε ZIP/FTP με FFPFSC/ShadowMountPlus και ελέγξτε το SHA-256 εφόσον παρέχεται.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Ρυθμίσεις

Οι προτεινόμενες αρχικές ρυθμίσεις είναι Vulkan, έξοδος 1440p, εσωτερική ανάλυση 1.25x, FSR 1 με ευκρίνεια 50%, FXAA και 60 Hz. Η έξοδος της τηλεόρασης διαφέρει από την εσωτερική ανάλυση του παιχνιδιού. Η δημιουργία καρέ δεν επιταχύνει την ίδια την προσομοίωση.

## Υποστήριξη

Στην αναφορά σφάλματος αναφέρετε έκδοση Encore, firmware PS5, ακριβή βήματα, σχετικές ρυθμίσεις και καθαρισμένα αρχεία καταγραφής. Χρησιμοποιήστε GitHub Issues· μη δημοσιεύετε κλειδιά ή προσωπικά δεδομένα.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Μη διαγράφετε το /data/prosperoeden/: μπορεί να περιέχει αποθηκεύσεις, ρυθμίσεις και κλειδιά. Κρατήστε αντίγραφο και της εξωτερικής αποθήκευσης.

---

Η τελευταία δημόσια μεταγλώττιση PS5 έγινε στις 15 Οκτωβρίου 2026. Η έκδοση της 30ής Οκτωβρίου ήταν αντίγραφο. Το νέο προσχέδιο δεν περιέχει εκτελέσιμα αρχεία ούτε επαληθευμένη συμβατότητα δεύτερης γενιάς.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)