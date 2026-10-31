# Prospero.Eden Encore — Polski

> Emulacja PS5 do grania na kanapie · [English (default)](README.md) · [All launcher languages](LANGUAGES.md)

Emulacja PS5 do grania na kanapie. Encore is an independent community emulator fork with a controller-first launcher, library, video settings and diagnostics. It is not an official Sony or Nintendo product.

## Szybki start

1. Pobierz kompletną paczkę z Encore Releases i sprawdź sumę kontrolną.
2. Zrób kopię katalogu PPSA99008, danych /data/prosperoeden i dysków zewnętrznych.
3. Skopiuj cały folder PPSA99008 do /data/homebrew/PPSA99008/; sam eboot.bin nie wystarczy.
4. Uruchom Encore, sprawdź Settings → Storage i Language, używaj tylko legalnie uzyskanych plików.

[Migracja z oryginalnego projektu](docs/i18n/INSTALL.pl.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migracja z oryginalnego projektu

Encore i oryginalny ProsperoEden mają ten sam identyfikator aplikacji PPSA99008 i nie są niezależnymi instalacjami. Wymień komplet plików programu, ale zachowaj zapisy, ustawienia, gry i klucze w /data/prosperoeden. Przed migracją zabezpiecz również stary folder assets/, jeśli zawiera dane użytkownika.

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[Migracja z oryginalnego projektu — step-by-step](docs/i18n/INSTALL.pl.md) · [Full installation instructions in English](INSTALL.md)

## Zgodność i ograniczenia

Encore przetestowano na prawdziwej konsoli PS5 wyłącznie z firmware 13.60. Starsze wersje mogą działać, lecz nie zostały sprawdzone i nie ustalono minimum. Nadal możliwe są przycięcia, opóźniony HUD, błędne przyciski podczas gry i zawieszenia po pauzie. Pomyślna kompilacja nie gwarantuje zgodności gry.

Game container support in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee a title will run.

## Częste pytania

Switch 2 jest badany w odrębnej gałęzi i nie wchodzi w skład obecnego wydania PS5. Generowanie klatek i aktualizator są dopiero planowane.

Gdy menu pozostaje angielskie, wybierz Settings → Language i sprawdź kompletną instalację folderu ui/lang/.

## Links and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Projekt nie zawiera gier, kluczy ani firmware. Nie publikuj danych prywatnych w zgłoszeniach.

> This localized README covers essential user information. The English README remains the full technical reference; host tests do not certify PS5 performance.
