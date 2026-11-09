# Eden Encore — Налаштування · Українська

[Огляд](README.uk-UA.md) · [Встановлення й оновлення](INSTALL.uk-UA.md) · [Налаштування](SETTINGS.uk-UA.md) · [Усунення несправностей](TROUBLESHOOTING.uk-UA.md) · [Підтримка](SUPPORT.uk-UA.md) · [Доступність](ACCESSIBILITY.uk-UA.md) · [Languages](../../LANGUAGES.md)

Рекомендований профіль: Vulkan, виведення на телевізор 1440p, внутрішній масштаб гри 1.25x, просторовий FSR 1 із різкістю 50%, FXAA та 60 Hz. Роздільна здатність ТВ відрізняється від внутрішнього рендерингу гри. Генерація кадрів не прискорює симуляцію гри.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Рекомендований профіль: Vulkan, виведення на телевізор 1440p, внутрішній масштаб гри 1.25x, просторовий FSR 1 із різкістю 50%, FXAA та 60 Hz. Роздільна здатність ТВ відрізняється від внутрішнього рендерингу гри. Генерація кадрів не прискорює симуляцію гри.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Доступність

Збільшений текст, високу контрастність і зменшення руху можна вмикати окремо в налаштуваннях доступності; за замовчуванням вони вимкнені. Доступність оболонки не гарантує доступності кожної гри.

## Усунення несправностей

Якщо програма не запускається, перевірте eboot.bin, sce_sys і ui/lang. Якщо ігри відсутні, перевірте roms у вибраному корені сховища. Якщо меню залишається англійським, перевірте переклади. Safe Launch відновлює налаштування окремої гри без видалення збережень.

Ніколи не видаляйте /data/prosperoeden/: там можуть зберігатися ігри, налаштування та ключі. Резервуйте також зовнішнє сховище.

---

Останній справді скомпільований публічний пакет PS5 датований 15 жовтня 2026 року. Публікація 30 жовтня була копією. Новий чернетковий попередній випуск не містить бінарних файлів чи підтвердженої підтримки ігор другого покоління на консолі.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)