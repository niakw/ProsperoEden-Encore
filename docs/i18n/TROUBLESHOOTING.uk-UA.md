# Eden Encore — Усунення несправностей · Українська

[Огляд](README.uk-UA.md) · [Встановлення й оновлення](INSTALL.uk-UA.md) · [Налаштування](SETTINGS.uk-UA.md) · [Усунення несправностей](TROUBLESHOOTING.uk-UA.md) · [Підтримка](SUPPORT.uk-UA.md) · [Доступність](ACCESSIBILITY.uk-UA.md) · [Languages](../../LANGUAGES.md)

Якщо програма не запускається, перевірте eboot.bin, sce_sys і ui/lang. Якщо ігри відсутні, перевірте roms у вибраному корені сховища. Якщо меню залишається англійським, перевірте переклади. Safe Launch відновлює налаштування окремої гри без видалення збережень.

## Встановлення й оновлення

Завантажуйте справді опублікований пакет із Releases і спершу створіть резервні копії програми та даних. Для ZIP/FTP повністю скопіюйте теку PPSA99008 у /data/homebrew/PPSA99008/. Не змішуйте ZIP/FTP з FFPFSC/ShadowMountPlus; перевіряйте SHA-256, якщо вона надана.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Налаштування

Рекомендований профіль: Vulkan, виведення на телевізор 1440p, внутрішній масштаб гри 1.25x, просторовий FSR 1 із різкістю 50%, FXAA та 60 Hz. Роздільна здатність ТВ відрізняється від внутрішнього рендерингу гри. Генерація кадрів не прискорює симуляцію гри.

## Підтримка

У GitHub Issues зазначте версію Encore, прошивку PS5, послідовність дій, потрібні налаштування та очищені від приватних даних журнали. Не публікуйте ключі, збереження чи особисті відомості.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Ніколи не видаляйте /data/prosperoeden/: там можуть зберігатися ігри, налаштування та ключі. Резервуйте також зовнішнє сховище.

---

Останній справді скомпільований публічний пакет PS5 датований 15 жовтня 2026 року. Публікація 30 жовтня була копією. Новий чернетковий попередній випуск не містить бінарних файлів чи підтвердженої підтримки ігор другого покоління на консолі.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)