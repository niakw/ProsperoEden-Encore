<table width="100%">
  <tr><td align="center">
    <strong>🌐 LANGUAGES</strong> &nbsp; · &nbsp; <a href="README.md">English</a> &nbsp; · &nbsp; <a href="README.md">English UK</a> &nbsp; · &nbsp; <a href="README.zh-Hans.md">简体中文</a> &nbsp; · &nbsp; <a href="README.zh-Hant.md">繁體中文</a> &nbsp; · &nbsp; <a href="README.es-419.md">Español LatAm</a> &nbsp; · &nbsp; <a href="README.es.md">Español ES</a> &nbsp; · &nbsp; <a href="README.fr.md">Français</a> &nbsp; · &nbsp; <a href="README.fr-CA.md">Français CA</a> &nbsp; · &nbsp; <a href="README.pt-BR.md">Português BR</a><br>
    <a href="README.pt-PT.md">Português PT</a> &nbsp; · &nbsp; <a href="README.ru.md">Русский</a> &nbsp; · &nbsp; <a href="README.de.md">Deutsch</a> &nbsp; · &nbsp; <a href="README.ja.md">日本語</a> &nbsp; · &nbsp; <a href="README.ko.md">한국어</a> &nbsp; · &nbsp; <a href="README.it.md">Italiano</a> &nbsp; · &nbsp; <a href="README.th.md">ไทย</a> &nbsp; · &nbsp; <strong>Polski</strong> &nbsp; · &nbsp; <a href="README.nl.md">Nederlands</a> &nbsp; · &nbsp; <a href="LANGUAGES.md"><strong>All languages</strong></a>
  </td></tr>
</table>

<table width="100%">
  <tr>
    <td width="21%" align="center" valign="middle"><a href="README.md"><img src="assets/icon0.png" alt="Prospero.Eden Encore logo" width="148"></a></td>
    <td width="79%" align="left" valign="middle">
      <h1>Prospero.Eden Encore</h1>
      <p><strong>Emulacja PS5 do grania na kanapie</strong></p>
      <p>Encore to niezależny projekt społecznościowy z interfejsem sterowanym padem, biblioteką gier, ustawieniami obrazu i diagnostyką. Nie jest oficjalnym produktem Sony ani Nintendo.</p>
      <p><kbd>Firmware 13.60 · test PS5</kbd> &nbsp; <kbd>Vulkan + OpenGL</kbd> &nbsp; <kbd>Interfejs TV</kbd> &nbsp; <kbd>Dynarmic</kbd></p>
    </td>
  </tr>
</table>

<table width="100%">
  <tr>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/releases"><strong>Pobierz</strong></a></td>
    <td align="center"><a href="docs/i18n/INSTALL.pl.md"><strong>Instalacja</strong></a></td>
    <td align="center"><a href="#getting-started"><strong>Start</strong></a></td>
    <td align="center"><a href="#compatibility"><strong>Zgodność</strong></a></td>
    <td align="center"><a href="#faq"><strong>Pytania</strong></a></td>
    <td align="center"><a href="TROUBLESHOOTING.md"><strong>Pomoc</strong></a></td>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md"><strong>Plany</strong></a></td>
  </tr>
</table>

<a id="getting-started"></a>
## Szybki start

1. Pobierz kompletną paczkę z Encore Releases i sprawdź sumę kontrolną.
2. Zrób kopię katalogu PPSA99008, danych /data/prosperoeden i dysków zewnętrznych.
3. Skopiuj cały folder PPSA99008 do /data/homebrew/PPSA99008/; sam eboot.bin nie wystarczy.
4. Uruchom Encore, sprawdź Settings → Storage i Language, używaj tylko legalnie uzyskanych plików.

[Migracja z oryginalnego projektu](docs/i18n/INSTALL.pl.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migracja z oryginalnego projektu

Encore i oryginalny ProsperoEden mają ten sam identyfikator aplikacji PPSA99008 i nie są niezależnymi instalacjami. Wymień komplet plików programu, ale zachowaj zapisy, ustawienia, gry i klucze w /data/prosperoeden. Przed migracją zabezpiecz również stary folder assets/, jeśli zawiera dane użytkownika.

**ID aplikacji :** `PPSA99008`. **Aplikacja :** `/data/homebrew/PPSA99008/`. **Dane trwałe :** `/data/prosperoeden/`.

[Migracja z oryginalnego projektu — krok po kroku](docs/i18n/INSTALL.pl.md) · [Pełna instrukcja instalacji po angielsku](INSTALL.md)

<a id="compatibility"></a>
## Zgodność i ograniczenia

Encore przetestowano na prawdziwej konsoli PS5 wyłącznie z firmware 13.60. Starsze wersje mogą działać, lecz nie zostały sprawdzone i nie ustalono minimum. Nadal możliwe są przycięcia, opóźniony HUD, błędne przyciski podczas gry i zawieszenia po pauzie. Pomyślna kompilacja nie gwarantuje zgodności gry.

Kod w fazie rozwoju obsługuje NSP/XCI oraz eksperymentalnie NSZ/XCZ. Bezpośrednie formaty NRO/NSO/NCA/NAX/KIP wymagają odpowiedniej zawartości; rozpoznanie rozszerzenia nie gwarantuje uruchomienia gry.

<a id="faq"></a>
## Częste pytania

Switch 2 jest badany w odrębnej gałęzi i nie wchodzi w skład obecnego wydania PS5. Generowanie klatek i aktualizator są dopiero planowane.

Gdy menu pozostaje angielskie, wybierz Settings → Language i sprawdź kompletną instalację folderu ui/lang/.

## Społeczność i autorzy

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Projekt nie zawiera gier, kluczy ani firmware. Nie publikuj danych prywatnych w zgłoszeniach.

> To tłumaczenie obejmuje najważniejsze informacje użytkowe. Pełna dokumentacja techniczna jest po angielsku; testy na hoście nie potwierdzają wydajności PS5.
