# PS5 system languages — strict launcher allowlist

**Decision (9 November 2026): Eden Encore's native launcher must expose EXACTLY the 31 official PS5 system language/region selections, no more and no fewer.** This is a fixed compatibility constraint, not a worldwide popularity contest.

**Source of truth:** [Sony PlayStation — language support, console languages](https://www.playstation.com/fr-fr/legal/language-support/). This is the console UI list, not any game's available spoken/subtitle languages.

## The exact 31 choices

| # | Console interface language/region | PS5 locale catalog tag |
|---:|---|---|
| 1 | Arabic | `ar` |
| 2 | Chinese (Simplified) | `zh-Hans` |
| 3 | Chinese (Traditional) | `zh-Hant` |
| 4 | Czech | `cs-CZ` |
| 5 | Danish | `da-DK` |
| 6 | Dutch | `nl-NL` |
| 7 | English (UK) | `en-GB` |
| 8 | English (US) | `en-US` |
| 9 | Finnish | `fi-FI` |
| 10 | French (Canada) | `fr-CA` |
| 11 | French (France) | `fr-FR` |
| 12 | German | `de-DE` |
| 13 | Greek | `el-GR` |
| 14 | Hungarian | `hu-HU` |
| 15 | Indonesian | `id-ID` |
| 16 | Italian | `it-IT` |
| 17 | Japanese | `ja-JP` |
| 18 | Korean | `ko-KR` |
| 19 | Norwegian | `nb-NO` |
| 20 | Polish | `pl-PL` |
| 21 | Portuguese (Brazil) | `pt-BR` |
| 22 | Portuguese (Portugal) | `pt-PT` |
| 23 | Romanian | `ro-RO` |
| 24 | Russian | `ru-RU` |
| 25 | Spanish (Latin America) | `es-419` |
| 26 | Spanish (Spain) | `es-ES` |
| 27 | Swedish | `sv-SE` |
| 28 | Thai | `th-TH` |
| 29 | Turkish | `tr-TR` |
| 30 | Ukrainian | `uk-UA` |
| 31 | Vietnamese | `vi-VN` |

There are **31 launcher choices and 31 application `.po` catalogs**. English (US) and English (UK) have separate `en-US.po` and `en-GB.po` catalogs: US keeps the source spelling, while UK uses regional forms such as Colour and Customise. All 31 catalog tags are documented in [LANGUAGES.md](../LANGUAGES.md); the 29 non-English locales retain 174 translated user-facing guide pages.

## Contract for code, documentation and releases

- `third_party/ps5_system_language.hpp` represents the 31 PS5 system language tags and is the reference mapping.
- `headless/settings_store.h` must expose that **exact tag set**, with **no additional entries**. Its first 18 saved preference indices stay stable; the 13 previously hidden Sony entries are appended.
- `headless/prosperoeden/ui/lang/*.po` must contain exactly the 31 catalog tags, one per official PS5 selector, including both English regional variants. Do not include Filipino, Indian languages, or any other additional launcher selectors unless Sony adds them to the console UI list.
- UI language preference and game-language preference are not synonymous: the guest emulator supports fewer game-language enums. The original 18 mappings are preserved; the 13 additional console interface choices use supported English guest-language fallback.
- Source/test gates: `tools/check-language-runtime.py` compares the complete set, `tools/check-launcher-translation-coverage.py` checks catalog coverage, `tools/check-user-doc-locales.py` and `docs/i18n/check_user_docs.py` check documentation, `tools/ci/check-staged-app.py` and `tools/install-ftp.py` verify packaged/deployed catalogs.
- Update this list **only when Sony changes its documented PS5 system-language options**, and then update code, catalogs, localizations, packaging and tests in one coherent change.

This policy does **not** certify the completeness or professionalism of every translation, correct rendering of every script, native PS5 build success or game-localization compatibility. None of those claims may be inferred solely from catalog presence.
