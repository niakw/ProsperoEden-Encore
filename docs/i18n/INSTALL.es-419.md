# Prospero.Eden Encore — Migrar desde el proyecto original (Español (Latinoamérica))

[← Español (Latinoamérica)](../../README.es-419.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## Primeros pasos

1. Descarga el paquete completo en Encore Releases y verifica su checksum.
2. Respalda la carpeta PPSA99008, los datos /data/prosperoeden y el almacenamiento externo.
3. Copia toda la carpeta PPSA99008 en /data/homebrew/PPSA99008/; no basta con copiar eboot.bin.
4. Abre Encore, revisa Settings → Storage y Language, y utiliza solo tus archivos obtenidos legalmente.

## Paths / PPSA99008

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent user files
/data/prosperoeden/keys/          # legally obtained keys
/data/prosperoeden/firmware/      # compatible firmware files
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # game updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # diagnostics
```

## Migrar desde el proyecto original

Encore y ProsperoEden nativo comparten el ID PPSA99008: no son dos apps que se puedan instalar por separado. Reemplaza los archivos completos de la aplicación, conservando guardados, configuración, juegos y claves en /data/prosperoeden. Respalda también cualquier carpeta antigua assets/ antes de migrar.

**Important:** Never delete `/data/prosperoeden/` or format external storage as a normal update step. Back up before migration; do not overwrite existing saves or keys.

## Compatibilidad y problemas conocidos

Encore solo ha sido probado en una consola PS5 con firmware 13.60. Los anteriores podrían funcionar, pero no están confirmados ni existe una versión mínima verificada. Algunos juegos aún presentan tirones, HUD atrasado, controles incorrectos y bloqueos durante pausas. Una compilación correcta no prueba la jugabilidad.

## Preguntas frecuentes

Si el menú sigue en inglés, entra a Settings → Language y comprueba que instalaste toda la carpeta ui/lang/.

If a title stops booting after changing settings, use **Safe Launch** for a temporary reset. For ZIP and FFPFSC/ShadowMountPlus methods see [INSTALL.md](../../INSTALL.md); for error details see [Troubleshooting](../../TROUBLESHOOTING.md) and [Support](../../SUPPORT.md).

El proyecto no incluye juegos comerciales, claves ni firmware. No compartas información privada en reportes públicos.
