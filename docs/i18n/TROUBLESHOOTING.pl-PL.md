# Eden Encore — Rozwiązywanie problemów · Polski

[Przegląd](README.pl.md) · [Instalacja i aktualizacja](INSTALL.pl-PL.md) · [Ustawienia](SETTINGS.pl-PL.md) · [Rozwiązywanie problemów](TROUBLESHOOTING.pl-PL.md) · [Pomoc](SUPPORT.pl-PL.md) · [Ułatwienia dostępu](ACCESSIBILITY.pl-PL.md) · [Languages](../../LANGUAGES.md)

Jeśli program nie uruchamia się, sprawdź eboot.bin, sce_sys i ui/lang. Jeśli nie widać gier, sprawdź roms w wybranym katalogu danych. Gdy menu pozostaje po angielsku, sprawdź pliki tłumaczeń. Safe Launch przywraca ustawienia konkretnej gry bez kasowania zapisów.

## Instalacja i aktualizacja

Pobierz faktycznie opublikowany pakiet ze strony Releases i wcześniej wykonaj kopię programu oraz danych. Przy ZIP/FTP skopiuj cały folder PPSA99008 do /data/homebrew/PPSA99008/. Nie łącz ZIP/FTP z FFPFSC/ShadowMountPlus; sprawdź SHA-256, jeśli podano sumę.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Ustawienia

Zalecany profil początkowy to Vulkan, wyjście TV 1440p, wewnętrzna skala gry 1.25x, przestrzenne FSR 1 z ostrością 50%, FXAA i 60 Hz. Rozdzielczość TV i wewnętrzna rozdzielczość gry to różne ustawienia. Generowanie klatek nie przyspiesza symulacji gry.

## Pomoc

Zgłoszenie w GitHub Issues powinno zawierać wersję Encore, firmware PS5, kroki odtworzenia błędu, istotne ustawienia i oczyszczone logi. Nie publikuj kluczy, zapisów gry ani danych osobowych.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Nigdy nie usuwaj /data/prosperoeden/: może zawierać zapisy, ustawienia i klucze. Zabezpiecz też zewnętrzne nośniki.

---

Ostatnia rzeczywiście skompilowana publiczna paczka PS5 pochodzi z 15 października 2026 r. Publikacja 30 października była kopią. Nowy szkic prerelease nie zawiera plików wykonywalnych ani potwierdzonej obsługi gier drugiej generacji na konsoli.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)