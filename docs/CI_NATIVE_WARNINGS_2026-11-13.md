# Native PS5 build warnings — 13 November 2026

This is an evidence-based warning inventory, **not** a claim that the native compiler is warning-free. Keep the original warnings visible; do not use global `-Wno-*` switches, blanket `#pragma` suppression or synthetic CI success.

## Reference build

- Successful native build: https://github.com/niakw/ProsperoEden-Encore/actions/runs/43326603881 (source `9613c3a98da1838f11c1909ab414d922c020bb35`).
- FTP artifact: `Eden-Encore-PS5-FTP-PPSA99008` (39,735,108 bytes GitHub compressed artifact).
- Release artifact: `Prospero.Eden-Encore-release` (155,761,571 bytes GitHub compressed artifact).
- The successful native job does not demonstrate console game compatibility or fix the unrelated runtime crashes; test FC27 and MKW on device.

## Counts and ownership in the reference log

The successful job printed **632 warning-matched log lines**. The classifications below are counts of *printed lines*, not independent defects:

| Area | Printed lines | Actual scope |
| --- | ---: | --- |
| Third-party Mesa/RADV/NIR compiler diagnostics | 471 | Primarily `src/compiler/nir/nir.h` and `src/amd/vulkan/*` generated/expanded unused-variable diagnostics |
| Launcher translations | 123 | Only the first 12 per catalog are printed; catalog summary reported **130** total warnings |
| Dynarmic / native Eden compiler diagnostics | 4 | Three unused symbols/arguments; one unhandled Shader::Stage enum warning |
| Ninja / Make jobserver | 1 | Incompatible inherited pipe-style jobserver flag |
| Other diagnostics | 33 | Mainly third-party `libpsbc/psbc_compile.c` unused variables; includes informational `note:` lines |

### Launcher translations: fixed

PR https://github.com/niakw/ProsperoEden-Encore/pull/93 fixes all **130 reported catalog warnings** across the 31 supported languages (129 shortened/revised messages and the valid Finnish `GB -> Gt` localization rule). The dedicated CI https://github.com/niakw/ProsperoEden-Encore/actions/runs/43329795974 passed `strings.py check` and `check-launcher-translation-coverage.py`. CI now fails if any new locale warning reappears, rather than merely printing it.

The PR's changes have been merged. A fresh full native build is required to establish the **new** compiler-log warning count; the 632-line baseline predates the i18n changes.

### Pending non-i18n warnings (do not suppress)

1. **Mesa/NIR:** Many `[-Wunused-but-set-variable]` instances arise from repeated macros and code compiled from the pinned `blackbearreloaded/ps5-opengl` source snapshot (including its `third_party/mesa-26.2.0`). Fix the source owner/expansion once, then validate the shader compiler, RADV isolation and image output. Do not change all call sites or disable the diagnostic across Encore.
2. **RADV header:** `src/amd/vulkan/radv_instance.h:38` warns that `struct radv_physical_device` is first declared inside a function parameter list. Review a proper file-scope forward declaration in the actual upstream header and verify ABI/headers before adopting into an Encore-maintained fork.
3. **Eden/Dynarmic:** `ir/basic_block.cpp:75` (`terminal_variant`), generated `headless/emit_x64.cpp:59` (`inst`), and generated `constant_pool.h:48` (`insertion_point`) should be reviewed against selected code paths. Do not alter the pinned original snapshot or the JIT lifetime guarantees solely to remove cosmetic diagnostics.
4. **Vulkan stage warning:** `video_core/renderer_vulkan/maxwell_to_vk.cpp:322` does not handle `Task` and `Mesh` in its shader-stage switch. Determine whether these stages are supported by the selected guest/driver paths; add safe, explicitly tested handling or rejection, not an invented VK stage mapping.
5. **Ninja jobserver:** Ninja's FIFO-only GNU Make jobserver client detects a pipe-style `--jobserver-auth=3,4` and ignores it with one warning. Address the *upstream Make/Ninja invocation protocol* (FIFO-style GNU Make 4.4+ or a bounded independent Ninja job count) and verify job parallelism. It does not explain game launch crashes.
6. **OpenGNM/libpsbc:** Inspect the compiler-generated unused `_` variables in the pinned PS5 shader compiler at the toolchain owner. Preserve the PSBC compiler/archive identity and its host tests.

## Next validation

Run a new native build on the merged translation commit, preserve the full warning log, compare per-source warning classes with the baseline above, and require a green native source preflight. Do not claim a zero-warning native build until the third-party compiler diagnostics are addressed and the exact native SHA/build artifacts are verified.
