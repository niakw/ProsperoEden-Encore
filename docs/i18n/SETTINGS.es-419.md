# Eden Encore — Configuración · Español (Latinoamérica)

[Resumen](README.es-419.md) · [Instalación y actualización](INSTALL.es-419.md) · [Configuración](SETTINGS.es-419.md) · [Solución de problemas](TROUBLESHOOTING.es-419.md) · [Soporte](SUPPORT.es-419.md) · [Accesibilidad](ACCESSIBILITY.es-419.md) · [Languages](../../LANGUAGES.md)

El perfil recomendado utiliza Vulkan, salida de TV 1440p, escala interna de juego 1.25x, FSR 1 espacial con nitidez 50 %, FXAA y 60 Hz. La salida del televisor no es la resolución interna del juego. La generación de cuadros no aumenta por sí sola la simulación del juego.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** El perfil recomendado utiliza Vulkan, salida de TV 1440p, escala interna de juego 1.25x, FSR 1 espacial con nitidez 50 %, FXAA y 60 Hz. La salida del televisor no es la resolución interna del juego. La generación de cuadros no aumenta por sí sola la simulación del juego.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Accesibilidad

Texto más grande, alto contraste y movimiento reducido se activan por separado en Accesibilidad y están apagados inicialmente. La navegación con foco visible no garantiza accesibilidad dentro de todos los juegos.

## Solución de problemas

Si no inicia la aplicación, revisa eboot.bin, sce_sys y ui/lang. Si faltan juegos, comprueba roms en la raíz de almacenamiento seleccionada. Si el menú sigue en inglés, verifica los catálogos de traducción. Safe Launch puede restaurar ajustes de un juego sin borrar partidas.

Nunca borres /data/prosperoeden/: puede contener partidas guardadas, ajustes y claves. Respalda también el almacenamiento externo.

---

La última compilación pública auténtica de PS5 es del 15 de octubre de 2026; la publicación del 30 de octubre fue una copia. El nuevo borrador no tiene binarios ni juegos de segunda generación verificados en consola.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)