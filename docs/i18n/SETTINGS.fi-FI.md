# Eden Encore — Asetukset · Suomi

[Yleiskatsaus](README.fi-FI.md) · [Asennus ja päivitys](INSTALL.fi-FI.md) · [Asetukset](SETTINGS.fi-FI.md) · [Vianmääritys](TROUBLESHOOTING.fi-FI.md) · [Tuki](SUPPORT.fi-FI.md) · [Saavutettavuus](ACCESSIBILITY.fi-FI.md) · [All languages](../../LANGUAGES.md)

Suositeltu aloitusprofiili on Vulkan, TV-ulostulo 1440p, pelin sisäinen tarkkuuskerroin 1.25x, spatiaalinen FSR 1 50 %:n terävöityksellä, FXAA ja 60 Hz. Näytön ulostulo ja pelin renderöintitarkkuus ovat eri asetuksia. Ruutujen generointi ei nopeuta itse pelin simulointia.

## Vulkan / FSR 1 — Asetukset

The following are **exact option names and numeric values** shown for comparison; descriptions and guidance remain in Suomi. 

| `Minimum` | `Recommended` | `High` |
| --- | --- | --- |
| `Vulkan` · `TV 1080p` · `1×` · `Bilinear` · `60 Hz` | `Vulkan` · `TV 1440p` · `1.25×` · `FSR 1` · `FXAA` · `60 Hz` | `Vulkan` · `TV 2160p` · `1.5×` · `Bicubic` · `FXAA` · `60 Hz` |

Suositeltu aloitusprofiili on Vulkan, TV-ulostulo 1440p, pelin sisäinen tarkkuuskerroin 1.25x, spatiaalinen FSR 1 50 %:n terävöityksellä, FXAA ja 60 Hz. Näytön ulostulo ja pelin renderöintitarkkuus ovat eri asetuksia. Ruutujen generointi ei nopeuta itse pelin simulointia.

## Asetukset · Touchpad

Touchpadin lyhyt painallus avaa Encoren pika-asetukset pelin aikana. Konsolin keskimmäinen järjestelmäpainike on varattu järjestelmälle. Valikossa on grafiikka-, näppäinmääritys-, FPS- ja diagnostiikka-asetuksia. Osa muutoksista vaatii pelin uudelleenkäynnistyksen. Kieli valitaan kohdasta Settings → Language; kaikkia luettelokieliä ei voi valita valikosta.

## Saavutettavuus

Suurempi teksti, suuri kontrasti ja liikkeen vähentäminen voi ottaa käyttöön erikseen saavutettavuusasetuksista; oletuksena ne ovat pois päältä. Käynnistimen käytettävyys ei takaa yksittäisten pelien saavutettavuutta.

## Vianmääritys

Jos sovellus ei käynnisty, tarkista eboot.bin, sce_sys ja ui/lang. Jos pelit puuttuvat, tarkista valitun tallennusjuuren roms-kansio. Jos kieli pysyy englantina, varmista käännöstiedostojen asennus. Safe Launch palauttaa yksittäisen pelin asetukset poistamatta tallennuksia.

## Tuki

Ilmoita GitHub Issues -palvelussa Encore-versio, PS5-laiteohjelmisto, toistovaiheet, olennaiset asetukset ja henkilötiedoista siivotut lokit. Älä koskaan jaa avaimia, tallennuksia tai yksityisiä tietoja.

Älä poista /data/prosperoeden/-kansiota: se voi sisältää tallennuksia, asetuksia ja avaimia. Varmuuskopioi myös ulkoinen tallennustila.

---

Viimeisin oikeasti käännetty julkinen PS5-paketti on 15. lokakuuta 2026. Lokakuun 30. päivän julkaisu oli kopio. Uusi luonnos ei sisällä binääritiedostoja eikä varmennettua toisen sukupolven pelikokemusta konsolilla.

[Detailed English settings and all available options](../../SETTINGS.md) · [Installation](./INSTALL.fi-FI.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
