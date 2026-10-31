<table width="100%">
  <tr><td align="center">
    <strong>🌐 LANGUAGES</strong> &nbsp; · &nbsp; <a href="README.md">English</a> &nbsp; · &nbsp; <a href="README.md">English UK</a> &nbsp; · &nbsp; <a href="README.zh-Hans.md">简体中文</a> &nbsp; · &nbsp; <a href="README.zh-Hant.md">繁體中文</a> &nbsp; · &nbsp; <a href="README.es-419.md">Español LatAm</a> &nbsp; · &nbsp; <a href="README.es.md">Español ES</a> &nbsp; · &nbsp; <a href="README.fr.md">Français</a> &nbsp; · &nbsp; <a href="README.fr-CA.md">Français CA</a> &nbsp; · &nbsp; <a href="README.pt-BR.md">Português BR</a><br>
    <a href="README.pt-PT.md">Português PT</a> &nbsp; · &nbsp; <strong>Русский</strong> &nbsp; · &nbsp; <a href="README.de.md">Deutsch</a> &nbsp; · &nbsp; <a href="README.ja.md">日本語</a> &nbsp; · &nbsp; <a href="README.ko.md">한국어</a> &nbsp; · &nbsp; <a href="README.it.md">Italiano</a> &nbsp; · &nbsp; <a href="README.th.md">ไทย</a> &nbsp; · &nbsp; <a href="README.pl.md">Polski</a> &nbsp; · &nbsp; <a href="README.nl.md">Nederlands</a> &nbsp; · &nbsp; <a href="LANGUAGES.md"><strong>All languages</strong></a>
  </td></tr>
</table>

<table width="100%">
  <tr>
    <td width="21%" align="center" valign="middle"><a href="README.md"><img src="assets/icon0.png" alt="Prospero.Eden Encore logo" width="148"></a></td>
    <td width="79%" align="left" valign="middle">
      <h1>Prospero.Eden Encore</h1>
      <p><strong>Эмуляция на PS5 для игры с дивана</strong></p>
      <p>Encore — независимый проект сообщества с интерфейсом для геймпада, библиотекой игр, настройками видео и диагностикой. Это не официальный продукт Sony или Nintendo.</p>
      <p><kbd>Прошивка 13.60 · тест PS5</kbd> &nbsp; <kbd>Vulkan + OpenGL</kbd> &nbsp; <kbd>Интерфейс ТВ</kbd> &nbsp; <kbd>Dynarmic</kbd></p>
    </td>
  </tr>
</table>

<table width="100%">
  <tr>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/releases"><strong>Скачать</strong></a></td>
    <td align="center"><a href="docs/i18n/INSTALL.ru.md"><strong>Установка</strong></a></td>
    <td align="center"><a href="#getting-started"><strong>Начало</strong></a></td>
    <td align="center"><a href="#compatibility"><strong>Совместимость</strong></a></td>
    <td align="center"><a href="#faq"><strong>Вопросы</strong></a></td>
    <td align="center"><a href="TROUBLESHOOTING.md"><strong>Помощь</strong></a></td>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md"><strong>Планы</strong></a></td>
  </tr>
</table>

<a id="getting-started"></a>
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

<a id="compatibility"></a>
## Совместимость и известные проблемы

На настоящей PS5 с Encore проверена только прошивка 13.60. Старые версии могут работать, но минимальная версия не установлена. Возможны рывки, устаревшее изображение HUD, ошибки кнопок и зависания на паузе. Успешная сборка не доказывает совместимость игры.

В разработке поддерживаются контейнеры NSP/XCI и экспериментально NSZ/XCZ. Прямые файлы NRO/NSO/NCA/NAX/KIP должны содержать подходящие данные: распознанное расширение не гарантирует запуск.

<a id="faq"></a>
## Частые вопросы

Switch 2 исследуется в отдельной ветке и не поддерживается текущей версией для PS5. Генерация кадров и автообновление запланированы, но не выпущены.

Если меню осталось английским, выберите Settings → Language и проверьте полноту папки ui/lang/.

## Сообщество и авторы

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Проект не распространяет игры, ключи и прошивки. Не публикуйте личные данные в отчётах.

> Этот перевод содержит основные сведения для пользователя. Полная техническая документация доступна на английском; тесты на ПК не доказывают производительность PS5.
