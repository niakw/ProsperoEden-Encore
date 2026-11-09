# Eden Encore — Ajustes · Español (España)

[Información general](README.es.md) · [Instalación y actualización](INSTALL.es-ES.md) · [Ajustes](SETTINGS.es-ES.md) · [Solución de problemas](TROUBLESHOOTING.es-ES.md) · [Asistencia](SUPPORT.es-ES.md) · [Accesibilidad](ACCESSIBILITY.es-ES.md) · [Languages](../../LANGUAGES.md)

El perfil recomendado utiliza Vulkan, salida 1440p, resolución interna 1.25x, FSR 1 espacial con nitidez 50 %, FXAA y 60 Hz. La salida del televisor es distinta de la resolución interna del juego. La generación de fotogramas no acelera la simulación del juego.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** El perfil recomendado utiliza Vulkan, salida 1440p, resolución interna 1.25x, FSR 1 espacial con nitidez 50 %, FXAA y 60 Hz. La salida del televisor es distinta de la resolución interna del juego. La generación de fotogramas no acelera la simulación del juego.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Accesibilidad

Texto más grande, contraste alto y movimiento reducido se activan de forma independiente en Accesibilidad y están desactivados inicialmente. La navegación del lanzador no garantiza la accesibilidad del contenido de cada juego.

## Solución de problemas

Si la aplicación no arranca, comprueba eboot.bin, sce_sys y ui/lang. Si faltan juegos, verifica roms dentro de la raíz de almacenamiento seleccionada. Si la interfaz sigue en inglés, revisa los catálogos de traducción. Safe Launch restaura ajustes de un juego sin borrar las partidas.

No borres nunca /data/prosperoeden/: puede contener partidas guardadas, ajustes y claves. Haz también copia del almacenamiento externo.

---

La última compilación pública auténtica para PS5 data del 15 de octubre de 2026; la publicación del 30 de octubre fue una copia. El nuevo borrador no incluye binarios ni compatibilidad de segunda generación comprobada en consola.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)