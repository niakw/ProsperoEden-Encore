# Eden Encore — Встановлення й оновлення · Українська

[Огляд](README.uk-UA.md) · [Встановлення й оновлення](INSTALL.uk-UA.md) · [Налаштування](SETTINGS.uk-UA.md) · [Усунення несправностей](TROUBLESHOOTING.uk-UA.md) · [Підтримка](SUPPORT.uk-UA.md) · [Доступність](ACCESSIBILITY.uk-UA.md) · [Languages](../../LANGUAGES.md)

Завантажуйте справді опублікований пакет із Releases і спершу створіть резервні копії програми та даних. Для ZIP/FTP повністю скопіюйте теку PPSA99008 у /data/homebrew/PPSA99008/. Не змішуйте ZIP/FTP з FFPFSC/ShadowMountPlus; перевіряйте SHA-256, якщо вона надана.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Ніколи не видаляйте /data/prosperoeden/: там можуть зберігатися ігри, налаштування та ключі. Резервуйте також зовнішнє сховище.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Усунення несправностей

Якщо програма не запускається, перевірте eboot.bin, sce_sys і ui/lang. Якщо ігри відсутні, перевірте roms у вибраному корені сховища. Якщо меню залишається англійським, перевірте переклади. Safe Launch відновлює налаштування окремої гри без видалення збережень.

Останній справді скомпільований публічний пакет PS5 датований 15 жовтня 2026 року. Публікація 30 жовтня була копією. Новий чернетковий попередній випуск не містить бінарних файлів чи підтвердженої підтримки ігор другого покоління на консолі.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)