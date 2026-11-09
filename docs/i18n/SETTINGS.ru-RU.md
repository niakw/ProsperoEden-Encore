# Eden Encore — Настройки · Русский

[Обзор](README.ru.md) · [Установка и обновление](INSTALL.ru-RU.md) · [Настройки](SETTINGS.ru-RU.md) · [Решение проблем](TROUBLESHOOTING.ru-RU.md) · [Поддержка](SUPPORT.ru-RU.md) · [Доступность](ACCESSIBILITY.ru-RU.md) · [Languages](../../LANGUAGES.md)

Рекомендуемый профиль: Vulkan, вывод на ТВ 1440p, внутренний масштаб игры 1.25x, пространственный FSR 1 с резкостью 50%, FXAA и 60 Hz. Разрешение вывода на ТВ отличается от внутреннего рендеринга игры. Генерация кадров не ускоряет саму симуляцию игры.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Рекомендуемый профиль: Vulkan, вывод на ТВ 1440p, внутренний масштаб игры 1.25x, пространственный FSR 1 с резкостью 50%, FXAA и 60 Hz. Разрешение вывода на ТВ отличается от внутреннего рендеринга игры. Генерация кадров не ускоряет саму симуляцию игры.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Доступность

Увеличенный текст, повышенная контрастность и уменьшение движения включаются независимо в настройках доступности и изначально отключены. Доступность оболочки не гарантирует доступность каждой игры.

## Решение проблем

Если приложение не запускается, проверьте eboot.bin, sce_sys и ui/lang. Если игры не отображаются, проверьте roms в выбранном корне хранения. Если меню остаётся английским, проверьте файлы переводов. Safe Launch восстанавливает настройки отдельной игры без удаления сохранений.

Никогда не удаляйте /data/prosperoeden/: там могут находиться сохранения, настройки и ключи. Сделайте резервную копию внешнего хранилища.

---

Последняя действительно собранная публичная версия PS5 датирована 15 октября 2026 года; публикация 30 октября была её копией. Новый черновик предварительного выпуска не содержит бинарных файлов или подтверждённой совместимости игр второго поколения на консоли.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)