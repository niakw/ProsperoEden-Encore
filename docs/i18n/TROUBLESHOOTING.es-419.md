# Eden Encore — Solución de problemas · Español (Latinoamérica)

[Resumen](README.es-419.md) · [Instalación y actualización](INSTALL.es-419.md) · [Configuración](SETTINGS.es-419.md) · [Solución de problemas](TROUBLESHOOTING.es-419.md) · [Soporte](SUPPORT.es-419.md) · [Accesibilidad](ACCESSIBILITY.es-419.md) · [Languages](../../LANGUAGES.md)

Si no inicia la aplicación, revisa eboot.bin, sce_sys y ui/lang. Si faltan juegos, comprueba roms en la raíz de almacenamiento seleccionada. Si el menú sigue en inglés, verifica los catálogos de traducción. Safe Launch puede restaurar ajustes de un juego sin borrar partidas.

## Instalación y actualización

Descarga un paquete realmente publicado desde Releases y respalda antes la aplicación y tus datos. Para ZIP/FTP, copia la carpeta PPSA99008 completa a /data/homebrew/PPSA99008/. No mezcles este método con FFPFSC/ShadowMountPlus y verifica SHA-256 cuando esté disponible.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Configuración

El perfil recomendado utiliza Vulkan, salida de TV 1440p, escala interna de juego 1.25x, FSR 1 espacial con nitidez 50 %, FXAA y 60 Hz. La salida del televisor no es la resolución interna del juego. La generación de cuadros no aumenta por sí sola la simulación del juego.

## Soporte

Indica versión de Encore, firmware PS5, pasos para reproducir el problema, configuración relevante y registros anonimizados en GitHub Issues. Nunca publiques claves, partidas guardadas ni datos personales.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Nunca borres /data/prosperoeden/: puede contener partidas guardadas, ajustes y claves. Respalda también el almacenamiento externo.

---

La última compilación pública auténtica de PS5 es del 15 de octubre de 2026; la publicación del 30 de octubre fue una copia. El nuevo borrador no tiene binarios ni juegos de segunda generación verificados en consola.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)