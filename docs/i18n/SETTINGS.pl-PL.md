# Eden Encore — Ustawienia · Polski

[Przegląd](README.pl.md) · [Instalacja i aktualizacja](INSTALL.pl-PL.md) · [Ustawienia](SETTINGS.pl-PL.md) · [Rozwiązywanie problemów](TROUBLESHOOTING.pl-PL.md) · [Pomoc](SUPPORT.pl-PL.md) · [Ułatwienia dostępu](ACCESSIBILITY.pl-PL.md) · [Languages](../../LANGUAGES.md)

Zalecany profil początkowy to Vulkan, wyjście TV 1440p, wewnętrzna skala gry 1.25x, przestrzenne FSR 1 z ostrością 50%, FXAA i 60 Hz. Rozdzielczość TV i wewnętrzna rozdzielczość gry to różne ustawienia. Generowanie klatek nie przyspiesza symulacji gry.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Zalecany profil początkowy to Vulkan, wyjście TV 1440p, wewnętrzna skala gry 1.25x, przestrzenne FSR 1 z ostrością 50%, FXAA i 60 Hz. Rozdzielczość TV i wewnętrzna rozdzielczość gry to różne ustawienia. Generowanie klatek nie przyspiesza symulacji gry.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Ułatwienia dostępu

Powiększony tekst, wysoki kontrast i ograniczenie animacji można włączyć osobno w ustawieniach dostępności; domyślnie są wyłączone. Dostępny interfejs nie gwarantuje dostępności wszystkich gier.

## Rozwiązywanie problemów

Jeśli program nie uruchamia się, sprawdź eboot.bin, sce_sys i ui/lang. Jeśli nie widać gier, sprawdź roms w wybranym katalogu danych. Gdy menu pozostaje po angielsku, sprawdź pliki tłumaczeń. Safe Launch przywraca ustawienia konkretnej gry bez kasowania zapisów.

Nigdy nie usuwaj /data/prosperoeden/: może zawierać zapisy, ustawienia i klucze. Zabezpiecz też zewnętrzne nośniki.

---

Ostatnia rzeczywiście skompilowana publiczna paczka PS5 pochodzi z 15 października 2026 r. Publikacja 30 października była kopią. Nowy szkic prerelease nie zawiera plików wykonywalnych ani potwierdzonej obsługi gier drugiej generacji na konsoli.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)