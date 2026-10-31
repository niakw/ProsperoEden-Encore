# Instalar y actualizar Encore — Español (España)

[← README en español](../../README.es.md) · [Todos los idiomas](../../LANGUAGES.md) · [Instalación completa (inglés)](../../INSTALL.md)

**Firmware probado con Encore en PS5 real: únicamente 13.60.** Otras versiones podrían funcionar, pero no están verificadas y no existe un mínimo confirmado. No actualices la consola solo porque se mencione 13.60.

## Instalar en cuatro pasos

1. Descarga un paquete **completo** de [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) y comprueba la versión y su integridad. Una compilación CI satisfactoria no demuestra compatibilidad en PS5.
2. **Haz una copia de seguridad** de la aplicación `/data/homebrew/PPSA99008/`, los datos `/data/prosperoeden/` y cualquier almacenamiento externo.
3. Para **ZIP/FTP**, copia toda la carpeta `PPSA99008/` con `eboot.bin`, `sce_sys/` y `ui/lang/` en `/data/homebrew/PPSA99008/`. Evita `PPSA99008/PPSA99008/`. Para **FFPFSC/ShadowMountPlus**, sigue [el método específico](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), sin mezclarlo con ZIP.
4. Abre Encore y comprueba **Settings → Storage / Language**, la biblioteca y los guardados antes de eliminar copias anteriores.

## Pasar desde ProsperoEden nativo

**ProsperoEden original y Encore comparten el ID `PPSA99008`.** Es una actualización de la aplicación existente, no otra aplicación instalada en paralelo.

- **Nunca borres `/data/prosperoeden/`**: contiene configuraciones, partidas, juegos, claves y datos persistentes.
- Si tu versión anterior tenía archivos de usuario en `PPSA99008/assets/`, **respáldalos primero** y conserva esa carpeta hasta finalizar la migración.
- Conserva la raíz de almacenamiento externo seleccionada. No sobrescribas guardados para resolver un conflicto de archivos.
- Para **Encore → Encore**, utiliza una versión oficial de **Encore Releases**, sustituye todos los archivos de aplicación y verifica los datos.
- La actualización automática **R21 está planeada, pero aún no se ha publicado**.

## Carpetas importantes

```text
/data/homebrew/PPSA99008/     # aplicación
/data/prosperoeden/           # datos persistentes
/data/prosperoeden/keys/      # claves propias
/data/prosperoeden/firmware/  # firmware compatible
/data/prosperoeden/roms/      # juegos
/data/prosperoeden/updates/   # actualizaciones de juegos
/data/prosperoeden/logs/      # diagnósticos
```

En un disco externo se utiliza la misma estructura bajo la raíz seleccionada. El programa no incluye juegos.

## Solución de problemas

- **El menú sigue en inglés**: elige Settings → Language y verifica los **29 catálogos** de `PPSA99008/ui/lang/`. El selector ofrece **18 opciones regionales** de 13 idiomas.
- **Biblioteca vacía**: comprueba la raíz elegida y la carpeta `roms/`.
- **Configuración incompleta**: revisa `keys/` y `firmware/` con tus archivos adquiridos legalmente.
- **Un juego deja de funcionar después de cambiar ajustes**: prueba **Safe Launch** sin borrar los guardados.
- **Tirones, HUD atrasado o bloqueos**: siguen siendo posibles aunque los tests de código sean correctos.

[Solución de problemas (inglés)](../../TROUBLESHOOTING.md) · [Soporte](../../SUPPORT.md).

Encore no proporciona juegos, claves ni firmware propietario.
