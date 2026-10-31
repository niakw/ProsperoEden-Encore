# Prospero.Eden Encore — Español (Latinoamérica)

> Emulación comunitaria para jugar en PS5 desde el sillón · [English (default)](README.md) · [Todos los idiomas](LANGUAGES.md)

Encore es una bifurcación comunitaria independiente con una interfaz para control, biblioteca de juegos, ajustes gráficos y herramientas de diagnóstico. No es un producto oficial de Sony ni Nintendo.

## Primeros pasos

1. Descarga el paquete completo en Encore Releases y verifica su checksum.
2. Respalda la carpeta PPSA99008, los datos /data/prosperoeden y el almacenamiento externo.
3. Copia toda la carpeta PPSA99008 en /data/homebrew/PPSA99008/; no basta con copiar eboot.bin.
4. Abre Encore, revisa Settings → Storage y Language, y utiliza solo tus archivos obtenidos legalmente.

[Migrar desde el proyecto original](docs/i18n/INSTALL.es-419.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migrar desde el proyecto original

Encore y ProsperoEden nativo comparten el ID PPSA99008: no son dos apps que se puedan instalar por separado. Reemplaza los archivos completos de la aplicación, conservando guardados, configuración, juegos y claves en /data/prosperoeden. Respalda también cualquier carpeta antigua assets/ antes de migrar.

**ID de aplicación :** `PPSA99008`. **Aplicación :** `/data/homebrew/PPSA99008/`. **Datos persistentes :** `/data/prosperoeden/`.

[Migrar desde el proyecto original — paso a paso](docs/i18n/INSTALL.es-419.md) · [Instalación completa en inglés](INSTALL.md)

## Compatibilidad y problemas conocidos

Encore solo ha sido probado en una consola PS5 con firmware 13.60. Los anteriores podrían funcionar, pero no están confirmados ni existe una versión mínima verificada. Algunos juegos aún presentan tirones, HUD atrasado, controles incorrectos y bloqueos durante pausas. Una compilación correcta no prueba la jugabilidad.

El código en desarrollo admite contenedores NSP/XCI y experimentalmente NSZ/XCZ; los cargadores directos NRO/NSO/NCA/NAX/KIP requieren contenido adecuado. Reconocer la extensión no garantiza que el juego funcione.

## Preguntas frecuentes

Switch 2 se investiga en una rama independiente y no funciona en la versión PS5 actual. La generación de cuadros y el actualizador automático figuran en los planes, pero no se han lanzado.

Si el menú sigue en inglés, entra a Settings → Language y comprueba que instalaste toda la carpeta ui/lang/.

## Comunidad y créditos

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

El proyecto no incluye juegos comerciales, claves ni firmware. No compartas información privada en reportes públicos.

> Esta traducción resume lo esencial. El README en inglés contiene la referencia técnica completa; los tests de código no certifican el rendimiento real de PS5.
