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

## 13 November later successful native builds — source owner and proposed fix

Later native build [#43405065280](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43405065280) and pre-fix console build [#43351221410](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43351221410) each report **510 actual warning lines**, using `warning:`, Meson `WARNING:` and Node `DeprecationWarning:` signatures. The compiled `psbc_compile.c:2255` expansion repeats the same `src/compiler/nir/nir.h:5266 UNUSED bool _;` warning 242 times; another 237 are the same NIR macro expanded from compiler paths. **479/510 = 93.9% are one compiler feature-detection omission, not 479 independent code issues.**

The PSBC Make toolchain flags include `-DHAVE_FUNC_ATTRIBUTE_PACKED=1` and `-DHAVE_FUNC_ATTRIBUTE_NORETURN=1` but omit `HAVE_FUNC_ATTRIBUTE_UNUSED`. Mesa's `src/util/macros.h` defines `UNUSED __attribute__((unused))` only if `HAVE_FUNC_ATTRIBUTE_UNUSED` is declared. In the PSBC host build, the macro is therefore **empty**. This is verified with both GCC and Clang compiling `UNUSED bool _; if(...) _=true;` under `-Werror=unused-but-set-variable`: without flag compilation fails; with `-DHAVE_FUNC_ATTRIBUTE_UNUSED=1` it passes.

**Reviewable narrow fix on branch `fix/nov13-psbc-479-unused-warnings`:** extend the existing temporary, fail-closed compiler-config adjustment `tools/ci/patch-psbc-noreturn-flags.py` to add `-DHAVE_FUNC_ATTRIBUTE_UNUSED=1` only for the pinned PSBC host and PS5 tool configs. The existing `tools/build-opengl-sdk.sh` backs up and restores them byte-for-byte on success/failure. No broad `-Wno-*` diagnostic suppression, original Mesa/PSBC source changes, new dependency versions, runtime/GPU code changes, SDK build/cache identity changes or hidden log filtering. `tools/check-psbc-noreturn-host.py` tests both attributes, flag drift rejection, GCC/Clang warning provenance and failure rollback.

**Qualification not complete:** source/host CI is evidence of the compiler capability fix; a **fresh native OpenGL/PSBC compile**, with cache invalidated in a controlled build, must verify whether all 479 printed instances disappear. Builds whose OpenGL SDK already passed its source-manifest cache gate will reuse the prior SDK and cannot prove a warning-count reduction. The current native PS5 build on SHA `88538c45...` started before this PR, so it cannot include the fix. Keep both old and new full logs to compare.

Other observed warnings remain separately tracked: Mesa/RADV type and conversion diagnostics (~24), Dynarmic/STB/Vulkan (5), maintained NS2 VI2 unsigned-count (1), Node buffer deprecation (1), cross-Meson TLS and Ninja jobserver messages. Source correctness should take precedence over count; the missing Task/Mesh switch case must be semantically qualified before mapping any new Vulkan stage.

## Additional real NIR print truncation warning (separate source-fix PR)

The successful native build `88538c45` [#43426275772](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43426275772) retains one `src/compiler/nir/nir_print.c:877:25 [-Wformat-truncation=]`: `snprintf(buf, 4, "%u", location)` can truncate shader location values. The function accepts unsigned `location`, and **two callers** define `char buf[4]`. A 32-bit unsigned decimal number needs ten digits plus a zero terminator. This is a genuine diagnostic-accuracy/correctness issue; do not silence the warning.

An isolated PSBC-only fix is reviewed on `fix/nov13-psbc-nir-location-truncation`: after the frozen OpenGL source fetcher verifies its original git tree, modify only its temporary staged PSBC `src/compiler/nir/nir_print.c` using `tools/ci/patch-psbc-nir-location-print.py` and exact source anchors. Change the single formatter to `snprintf(buf, 11, "%u", location)` and BOTH local buffers to `char buf[11]`. The existing build wrapper backs up original bytes per PID and restores them on completion or any failure via the exit trap. No `-Wno-*`, no app renderer/guest changes, no modification to `vendor/sources/` or immutable vendor SHAs.

`tools/check-psbc-nir-location-host.py` asserts exact source-drift rejection, both bound-compatible callers, restoration order, Bash syntax and GCC/Clang sanitizer behavior for `UINT_MAX = 4294967295` including adjacent byte canaries. A fresh PSBC SDK compilation (not an already-verified cached SDK) is required to show the original warning disappeared; test results alone cannot claim an entire native build is warning-free.

## 14 November — PSBC RADV compatibility stub scope

Four old native compiler log lines (two GCC host, two native Clang) identify the same C declaration-scope defect in PSBC's **compatibility stub**, not the real RADV driver. [Upstream PSBC](https://github.com/PS4-OpenGNM/opengnm-psbc/blob/main/src/amd/vulkan/radv_instance.h) and vendor c339fd0 both contain Git blob `34437d0216c5438d209b544accddb0030e7fae98`. [Mesa's real implementation](https://chromium.googlesource.com/external/gitlab.freedesktop.org/mesa/mesa/+/bdd7d3b7ab4251651182128f89bf17071787973f/src/amd/vulkan/radv_physical_device.h) has a complete device type before the helper; the PSBC stub only needs an opaque file-scope declaration. Add exactly that declaration to the verified scratch compiler window; preserve both original source files before subsequent upstream verification and on exit. The changed patcher hash invalidates old SDK markers. Host C test uses the real header, reproduces the original mismatch under -Werror and checks the repaired function pointer and returned default instance. Native warning reduction not yet measured.

### PSBC ACO signed comparison and NIR mask follow-up

Original run 43426275772 job 131888348458 reports two GCC `-Wsign-compare` at aco_select_nir_intrinsics.cpp:564/576 and one native clang `-Wconstant-conversion` at ac_nir_meta_cs_clear_copy_buffer.c:264. Confirmed exact isolated PSBC owners `9479ba5f980f1e254801afd6a068282b7b571df8` and `9702ce7e1d3fa5dc35118c6eff7a10fdf55f1cde` match PS4-OpenGNM/opengnm-psbc main; newer Mesa ACO still includes a comparable ffs comparison. No applicable upstream fix found. Cast the POSIX ffs result to unsigned (0..32 only), use typed nir_component_mask for partial-store count (nonzero 1..3, derived from remainder modulo 4*dwords_per_thread). Real source anchors and original bytes pinned; host tests cover all 32 bit positions and legal remainder domain; outer and inner restoration for both new owners. Do not suppress warnings or edit full RADV. Native clean rebuild remains mandatory to quantify warning reduction.


### 2026-11-14 — assert-only Mesa/PSBC warnings
Native syntax run 43571792002 still emitted four release-only unused warnings after the ACO signedness/NIR mask fixes: `nir_unlower_io_to_vars.c: component`, `aco_lower_to_hw_instr.cpp: non_linear_vgpr`, `aco_spill_preserved.cpp: found_reg`, and `radv_nir_lower_descriptors.c: indirect`. Exact pinned source review shows each value is consumed only by `assert()`. Mesa's own `util/macros.h` documents `ASSERTED` specifically for this case and maps it to `UNUSED` only under `NDEBUG`. Current Mesa 26.2/26.3 still carries the ACO pattern, so no semantic upstream replacement was imported. The compile-window patch annotates only those four declarations, restores all source bytes afterwards, and the real native syntax workflow now triggers when these patchers change. Full shader/runtime behavior remains to be qualified.


Correction de propriété: `non_linear_vgpr` appartient à `amd/compiler/aco_lower_to_hw_instr.cpp` blob `337e296ad310279b6aa8e8d96e355d9e049a2acd`, pas à `aco_select_nir_intrinsics.cpp`. Le patch de signedness reste limité au second; l'annotation `ASSERTED` devient un quatrième owner séparé et byte-restored.

### Assert-only warning owners: actual platform-patched input

Native sparse syntax run 43573583387 failed before CMake generation because the verified PS5 platform patch transforms `aco_lower_to_hw_instr.cpp` and `radv_nir_lower_descriptors.c`. Replayed every hunk of exact vendor platform patch a05bb92 (declared SHA-256 35967c8f...) against the two original blobs; resulting full Git hashes `3a6346cba427c411ae4cd839989a0b885770de06` and `71ac6f6f01fc5e14102487812fb714e0abb93f99` match patch index prefixes (first also matches actual CI log). Allow only these exact preimages alongside pristine versions; two other owners are unchanged. Host fixture now applies the actual audited patch to three selected source copies, checks full hashes and tests restored bytes for normal/failing compiler exits. No warning suppression or source drift acceptance. Native syntax retry required.
