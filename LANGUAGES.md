# Languages — Prospero.Eden Encore

[← English README](README.md) · [English full installation guide](INSTALL.md)

The launcher supports **18 language/region selections in 13 distinct languages**. This table covers every entry in `headless/settings_store.h::kLanguageKeys`. **English (US) is the default.**

English appears first. Other languages are broadly ordered by worldwide speaking audience, with regional variants grouped together. This is not an exact speaker-count ranking or a ranking of Encore players.

| Language option in the launcher | README and FAQ | Installation and upgrading |
| --- | --- | --- |
| English (US) (`en-US`) | [Read](README.md) | [Install](INSTALL.md) |
| English (UK) (`en-GB`) | [Read](README.md) | [Install](INSTALL.md) |
| 简体中文 (`zh-Hans`) | [Read](README.zh-Hans.md) | [Install](docs/i18n/INSTALL.zh-Hans.md) |
| 繁體中文 (`zh-Hant`) | [Read](README.zh-Hant.md) | [Install](docs/i18n/INSTALL.zh-Hant.md) |
| Español (Latinoamérica) (`es-419`) | [Read](README.es-419.md) | [Install](docs/i18n/INSTALL.es-419.md) |
| Español (España) (`es-ES`) | [Read](README.es.md) | [Install](docs/i18n/INSTALL.es-ES.md) |
| Français (France) (`fr-FR`) | [Read](README.fr.md) | [Install](docs/i18n/INSTALL.fr-FR.md) |
| Français (Canada) (`fr-CA`) | [Read](README.fr-CA.md) | [Install](docs/i18n/INSTALL.fr-CA.md) |
| Português (Brasil) (`pt-BR`) | [Read](README.pt-BR.md) | [Install](docs/i18n/INSTALL.pt-BR.md) |
| Português (Portugal) (`pt-PT`) | [Read](README.pt-PT.md) | [Install](docs/i18n/INSTALL.pt-PT.md) |
| Русский (`ru-RU`) | [Read](README.ru.md) | [Install](docs/i18n/INSTALL.ru.md) |
| Deutsch (`de-DE`) | [Read](README.de.md) | [Install](docs/i18n/INSTALL.de.md) |
| 日本語 (`ja-JP`) | [Read](README.ja.md) | [Install](docs/i18n/INSTALL.ja.md) |
| 한국어 (`ko-KR`) | [Read](README.ko.md) | [Install](docs/i18n/INSTALL.ko.md) |
| Italiano (`it-IT`) | [Read](README.it.md) | [Install](docs/i18n/INSTALL.it.md) |
| ไทย (`th-TH`) | [Read](README.th.md) | [Install](docs/i18n/INSTALL.th.md) |
| Polski (`pl-PL`) | [Read](README.pl.md) | [Install](docs/i18n/INSTALL.pl.md) |
| Nederlands (`nl-NL`) | [Read](README.nl.md) | [Install](docs/i18n/INSTALL.nl.md) |

## How languages work

- **18 selectable entries are not 29 selectable languages.** A complete application package contains **29** `PPSA99008/ui/lang/*.po` catalogs, including translations for languages which the current menu does not expose.
- Both English regions share the English README. French, Spanish, Portuguese and Chinese regions/scripts have their own language paths where useful.
- The existing full English, French and Spanish READMEs are preserved. Other translations are shorter user-friendly introductions; the English pages remain the complete technical reference.
- Change the UI language under **Settings → Language**. A game may not provide the chosen language. Missing or incomplete translations may show English text.
- If the launcher stays English unexpectedly, verify the **complete** `ui/lang/` folder was installed; see [Troubleshooting](TROUBLESHOOTING.md).
- **13.60 is the only PS5 firmware actually tested with Encore.** Older versions may work but have not been qualified, and there is no established minimum firmware. Do not update a console just because 13.60 is mentioned.

## Improve a translation

For an incorrect string, missing text or clipped menu, [open an issue](https://github.com/niakw/ProsperoEden-Encore/issues) with the language code, affected screen, release/commit and a suggested correction. Do not share console keys, private saves or identifying details.

[Support](SUPPORT.md) · [Credits](README.md#credits) · [Licenses](THIRD_PARTY_NOTICES.md).
