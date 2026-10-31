# Prospero.Eden Encore — Русский

> Эмуляция на PS5 для игры с дивана · [English (default)](README.md) · [Все языки](LANGUAGES.md)

Encore — независимый проект сообщества с интерфейсом для геймпада, библиотекой игр, настройками видео и диагностикой. Это не официальный продукт Sony или Nintendo.

## Быстрый старт

1. Загрузите полный пакет из Encore Releases и проверьте его контрольную сумму.
2. Сделайте резервную копию PPSA99008, данных /data/prosperoeden и внешних накопителей.
3. Скопируйте всю папку PPSA99008 в /data/homebrew/PPSA99008/; одного файла eboot.bin недостаточно.
4. Запустите Encore, проверьте Settings → Storage и Language; используйте только законно полученные файлы.

[Переход с оригинальной версии](docs/i18n/INSTALL.ru.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Переход с оригинальной версии

Encore и исходный ProsperoEden используют один идентификатор PPSA99008: установить их как две независимые программы нельзя. Заменяйте файлы приложения целиком, сохраняя игры, ключи, настройки и сохранения в /data/prosperoeden. Старую папку assets/ перед переносом обязательно скопируйте.

**ID приложения :** `PPSA99008`. **Приложение :** `/data/homebrew/PPSA99008/`. **Постоянные данные :** `/data/prosperoeden/`.

[Переход с оригинальной версии — пошагово](docs/i18n/INSTALL.ru.md) · [Полное руководство по установке на английском](INSTALL.md)

## Совместимость и известные проблемы

На настоящей PS5 с Encore проверена только прошивка 13.60. Старые версии могут работать, но минимальная версия не установлена. Возможны рывки, устаревшее изображение HUD, ошибки кнопок и зависания на паузе. Успешная сборка не доказывает совместимость игры.

В разработке поддерживаются контейнеры NSP/XCI и экспериментально NSZ/XCZ. Прямые файлы NRO/NSO/NCA/NAX/KIP должны содержать подходящие данные: распознанное расширение не гарантирует запуск.

## Частые вопросы

Switch 2 исследуется в отдельной ветке и не поддерживается текущей версией для PS5. Генерация кадров и автообновление запланированы, но не выпущены.

Если меню осталось английским, выберите Settings → Language и проверьте полноту папки ui/lang/.

## Сообщество и авторы

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Проект не распространяет игры, ключи и прошивки. Не публикуйте личные данные в отчётах.

> Этот перевод содержит основные сведения для пользователя. Полная техническая документация доступна на английском; тесты на ПК не доказывают производительность PS5.
