# Prospero.Eden Encore — Русский

> Эмуляция на PS5 для игры с дивана · [English (default)](README.md) · [All 18 launcher language choices](LANGUAGES.md)

Эмуляция на PS5 для игры с дивана. Encore is an independent community fork with a controller-friendly launcher, game library, graphics settings and diagnostics, not an official Sony or Nintendo product.

## Быстрый старт

1. Загрузите полный пакет из Encore Releases и проверьте его контрольную сумму.
2. Сделайте резервную копию PPSA99008, данных /data/prosperoeden и внешних накопителей.
3. Скопируйте всю папку PPSA99008 в /data/homebrew/PPSA99008/; одного файла eboot.bin недостаточно.
4. Запустите Encore, проверьте Settings → Storage и Language; используйте только законно полученные файлы.

[Переход с оригинальной версии](docs/i18n/INSTALL.ru.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Переход с оригинальной версии

Encore и исходный ProsperoEden используют один идентификатор PPSA99008: установить их как две независимые программы нельзя. Заменяйте файлы приложения целиком, сохраняя игры, ключи, настройки и сохранения в /data/prosperoeden. Старую папку assets/ перед переносом обязательно скопируйте.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[Переход с оригинальной версии — step-by-step](docs/i18n/INSTALL.ru.md) · [Full installation instructions in English](INSTALL.md)

## Совместимость и известные проблемы

На настоящей PS5 с Encore проверена только прошивка 13.60. Старые версии могут работать, но минимальная версия не установлена. Возможны рывки, устаревшее изображение HUD, ошибки кнопок и зависания на паузе. Успешная сборка не доказывает совместимость игры.

Content formats in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee that a complete game will start.

## Частые вопросы

Switch 2 исследуется в отдельной ветке и не поддерживается текущей версией для PS5. Генерация кадров и автообновление запланированы, но не выпущены.

Если меню осталось английским, выберите Settings → Language и проверьте полноту папки ui/lang/.

## Community and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Проект не распространяет игры, ключи и прошивки. Не публикуйте личные данные в отчётах.

> This translation is a concise guide for the selected launcher language. For complete technical information, use the English README and linked guides. No console performance claim is implied.
