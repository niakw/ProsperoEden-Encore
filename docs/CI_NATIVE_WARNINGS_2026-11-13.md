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

## Latest completed native warning audit — 13 November 2026 (UTC)

Newer native build [#43330598915](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43330598915) completed **SUCCESS** on `5bdbf59a0b735e446062350768e62c05458d3109` (12 November 23:38–23:51 UTC). Its exact native build-job log contains **506 printed warning lines** matched by compiler `: warning:`, Ninja warning, and Node deprecation-warning signatures; **zero compiler error lines** matched in that build. This is **not** a build of the pending Nov13 PR #94 or its vendor pin.

| Distinct warning owner/type | Printed occurrences | Notes |
| --- | ---: | --- |
| OpenGNM/libpsbc `psbc_compile.c:2255` — `_` assigned but unused | 242 | One repeated code site, not 242 independent regressions |
| Mesa/NIR `nir.h:5266` — `_` assigned but unused | 237 | One repeated header/macro site |
| All remaining warning classes together | 27 | RADV/Mesa compiler warnings, four Eden/Dynarmic diagnostics, Ninja jobserver and Node `Buffer()` deprecation |
| **Total** | **506** | 479/506 (94.7%) came from two distinct repeated sites |

The newer job no longer prints launcher locale warnings; this is consistent with the merged translation corrections. The earlier 632-line reference and the new 506-line count concern **different engine SHAs** and are not a proof of zero warnings, runtime improvement, game boot, FPS or PS5 picture correctness.

## Next validation

1. Qualify the current Nov13 crash/launcher branch by its **own** native build and preserve its exact log, symbols and FTP archive before PS5 testing.
2. Prioritize compiler warning owners rather than hide the diagnostics: `psbc_compile.c` unused loop variable; Mesa/NIR unused macro variable; explicit RADV forward declaration; remaining native unused symbols and Task/Mesh enum switch; Ninja jobserver. Preserve fixed upstream source/code generation and licenses, add source-derived positive and negative tests.
3. Validate FC27 HUD, shader/texture fidelity, stutter interval distribution and MKW NS2 startup **on console**. A successful build or no-warning log alone cannot close either runtime incident.
