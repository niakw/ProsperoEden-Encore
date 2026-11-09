# Eden Encore — Vianmääritys · Suomi

[Yleiskatsaus](README.fi-FI.md) · [Asennus ja päivitys](INSTALL.fi-FI.md) · [Asetukset](SETTINGS.fi-FI.md) · [Vianmääritys](TROUBLESHOOTING.fi-FI.md) · [Tuki](SUPPORT.fi-FI.md) · [Saavutettavuus](ACCESSIBILITY.fi-FI.md) · [Languages](../../LANGUAGES.md)

Jos sovellus ei käynnisty, tarkista eboot.bin, sce_sys ja ui/lang. Jos pelit puuttuvat, tarkista valitun tallennusjuuren roms-kansio. Jos kieli pysyy englantina, varmista käännöstiedostojen asennus. Safe Launch palauttaa yksittäisen pelin asetukset poistamatta tallennuksia.

## Asennus ja päivitys

Lataa oikeasti julkaistu paketti Releases-sivulta ja varmuuskopioi ensin sovellus sekä käyttäjätiedot. ZIP/FTP-asennuksessa kopioi koko PPSA99008-kansio polkuun /data/homebrew/PPSA99008/. Älä sekoita ZIP/FTP- ja FFPFSC/ShadowMountPlus-asennuksia; tarkista SHA-256, jos se on saatavilla.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Asetukset

Suositeltu aloitusprofiili on Vulkan, TV-ulostulo 1440p, pelin sisäinen tarkkuuskerroin 1.25x, spatiaalinen FSR 1 50 %:n terävöityksellä, FXAA ja 60 Hz. Näytön ulostulo ja pelin renderöintitarkkuus ovat eri asetuksia. Ruutujen generointi ei nopeuta itse pelin simulointia.

## Tuki

Ilmoita GitHub Issues -palvelussa Encore-versio, PS5-laiteohjelmisto, toistovaiheet, olennaiset asetukset ja henkilötiedoista siivotut lokit. Älä koskaan jaa avaimia, tallennuksia tai yksityisiä tietoja.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Älä poista /data/prosperoeden/-kansiota: se voi sisältää tallennuksia, asetuksia ja avaimia. Varmuuskopioi myös ulkoinen tallennustila.

---

Viimeisin oikeasti käännetty julkinen PS5-paketti on 15. lokakuuta 2026. Lokakuun 30. päivän julkaisu oli kopio. Uusi luonnos ei sisällä binääritiedostoja eikä varmennettua toisen sukupolven pelikokemusta konsolilla.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)