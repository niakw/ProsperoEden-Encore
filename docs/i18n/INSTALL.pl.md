# Prospero.Eden Encore — Migracja z oryginalnego projektu (Polski)

[← Polski](../../README.pl.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## Szybki start

1. Pobierz kompletną paczkę z Encore Releases i sprawdź sumę kontrolną.
2. Zrób kopię katalogu PPSA99008, danych /data/prosperoeden i dysków zewnętrznych.
3. Skopiuj cały folder PPSA99008 do /data/homebrew/PPSA99008/; sam eboot.bin nie wystarczy.
4. Uruchom Encore, sprawdź Settings → Storage i Language, używaj tylko legalnie uzyskanych plików.

## PPSA99008 / storage

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent data
/data/prosperoeden/keys/          # legal keys
/data/prosperoeden/firmware/      # compatible firmware
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # logs
```

## Migracja z oryginalnego projektu

Encore i oryginalny ProsperoEden mają ten sam identyfikator aplikacji PPSA99008 i nie są niezależnymi instalacjami. Wymień komplet plików programu, ale zachowaj zapisy, ustawienia, gry i klucze w /data/prosperoeden. Przed migracją zabezpiecz również stary folder assets/, jeśli zawiera dane użytkownika.

**Important:** Never delete `/data/prosperoeden/` or format external storage during an update. Back up first and preserve all saves, keys and existing media.

## Zgodność i ograniczenia

Encore przetestowano na prawdziwej konsoli PS5 wyłącznie z firmware 13.60. Starsze wersje mogą działać, lecz nie zostały sprawdzone i nie ustalono minimum. Nadal możliwe są przycięcia, opóźniony HUD, błędne przyciski podczas gry i zawieszenia po pauzie. Pomyślna kompilacja nie gwarantuje zgodności gry.

## Częste pytania

Gdy menu pozostaje angielskie, wybierz Settings → Language i sprawdź kompletną instalację folderu ui/lang/.

If one title stops booting after settings changes, try **Safe Launch** without deleting its saves. Consult [ZIP/FFPFSC/ShadowMountPlus instructions](../../INSTALL.md), [Troubleshooting](../../TROUBLESHOOTING.md) or [Support](../../SUPPORT.md).

Projekt nie zawiera gier, kluczy ani firmware. Nie publikuj danych prywatnych w zgłoszeniach.
