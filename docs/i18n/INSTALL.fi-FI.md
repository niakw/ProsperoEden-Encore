# Eden Encore — Asennus ja päivitys · Suomi

[Yleiskatsaus](README.fi-FI.md) · [Asennus ja päivitys](INSTALL.fi-FI.md) · [Asetukset](SETTINGS.fi-FI.md) · [Vianmääritys](TROUBLESHOOTING.fi-FI.md) · [Tuki](SUPPORT.fi-FI.md) · [Saavutettavuus](ACCESSIBILITY.fi-FI.md) · [🌐](../../LANGUAGES.md)

Lataa oikeasti julkaistu paketti Releases-sivulta ja varmuuskopioi ensin sovellus sekä käyttäjätiedot. ZIP/FTP-asennuksessa kopioi koko PPSA99008-kansio polkuun /data/homebrew/PPSA99008/. Älä sekoita ZIP/FTP- ja FFPFSC/ShadowMountPlus-asennuksia; tarkista SHA-256, jos se on saatavilla.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/eboot.bin
/data/homebrew/PPSA99008/sce_sys/
/data/homebrew/PPSA99008/ui/lang/
```

Älä poista /data/prosperoeden/-kansiota: se voi sisältää tallennuksia, asetuksia ja avaimia. Varmuuskopioi myös ulkoinen tallennustila.

## FFPFSC / ShadowMountPlus

Lataa oikeasti julkaistu paketti Releases-sivulta ja varmuuskopioi ensin sovellus sekä käyttäjätiedot. ZIP/FTP-asennuksessa kopioi koko PPSA99008-kansio polkuun /data/homebrew/PPSA99008/. Älä sekoita ZIP/FTP- ja FFPFSC/ShadowMountPlus-asennuksia; tarkista SHA-256, jos se on saatavilla.

[FFPFSC / ShadowMountPlus — English reference](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus)

## Asetukset

Suositeltu aloitusprofiili on Vulkan, TV-ulostulo 1440p, pelin sisäinen tarkkuuskerroin 1.25x, spatiaalinen FSR 1 50 %:n terävöityksellä, FXAA ja 60 Hz. Näytön ulostulo ja pelin renderöintitarkkuus ovat eri asetuksia. Ruutujen generointi ei nopeuta itse pelin simulointia.

## Vianmääritys

Jos sovellus ei käynnisty, tarkista eboot.bin, sce_sys ja ui/lang. Jos pelit puuttuvat, tarkista valitun tallennusjuuren roms-kansio. Jos kieli pysyy englantina, varmista käännöstiedostojen asennus. Safe Launch palauttaa yksittäisen pelin asetukset poistamatta tallennuksia.

## Tuki

Ilmoita GitHub Issues -palvelussa Encore-versio, PS5-laiteohjelmisto, toistovaiheet, olennaiset asetukset ja henkilötiedoista siivotut lokit. Älä koskaan jaa avaimia, tallennuksia tai yksityisiä tietoja.

---

Viimeisin oikeasti käännetty julkinen PS5-paketti on 15. lokakuuta 2026. Lokakuun 30. päivän julkaisu oli kopio. Uusi luonnos ei sisällä binääritiedostoja eikä varmennettua toisen sukupolven pelikokemusta konsolilla.

[English — complete installation and migration](../../INSTALL.md) · [R1 — October 15, 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)
