# Prospero.Eden Encore — Переход с оригинальной версии (Русский)

[← Русский](../../README.ru.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## Быстрый старт

1. Загрузите полный пакет из Encore Releases и проверьте его контрольную сумму.
2. Сделайте резервную копию PPSA99008, данных /data/prosperoeden и внешних накопителей.
3. Скопируйте всю папку PPSA99008 в /data/homebrew/PPSA99008/; одного файла eboot.bin недостаточно.
4. Запустите Encore, проверьте Settings → Storage и Language; используйте только законно полученные файлы.

## Paths / PPSA99008

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent user files
/data/prosperoeden/keys/          # legally obtained keys
/data/prosperoeden/firmware/      # compatible firmware files
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # game updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # diagnostics
```

## Переход с оригинальной версии

Encore и исходный ProsperoEden используют один идентификатор PPSA99008: установить их как две независимые программы нельзя. Заменяйте файлы приложения целиком, сохраняя игры, ключи, настройки и сохранения в /data/prosperoeden. Старую папку assets/ перед переносом обязательно скопируйте.

**Important:** Never delete `/data/prosperoeden/` or format external storage as a normal update step. Back up before migration; do not overwrite existing saves or keys.

## Совместимость и известные проблемы

На настоящей PS5 с Encore проверена только прошивка 13.60. Старые версии могут работать, но минимальная версия не установлена. Возможны рывки, устаревшее изображение HUD, ошибки кнопок и зависания на паузе. Успешная сборка не доказывает совместимость игры.

## Частые вопросы

Если меню осталось английским, выберите Settings → Language и проверьте полноту папки ui/lang/.

If a title stops booting after changing settings, use **Safe Launch** for a temporary reset. For ZIP and FFPFSC/ShadowMountPlus methods see [INSTALL.md](../../INSTALL.md); for error details see [Troubleshooting](../../TROUBLESHOOTING.md) and [Support](../../SUPPORT.md).

Проект не распространяет игры, ключи и прошивки. Не публикуйте личные данные в отчётах.
