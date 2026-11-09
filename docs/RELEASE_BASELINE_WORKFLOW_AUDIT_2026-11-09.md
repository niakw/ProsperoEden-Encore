# Eden Encore — Historical PS5 R1 baseline and CI workflow audit (9 November 2026)

> Documentation-only inventory. This file is **not** the P0–P4 acceptance tracker and does not close any roadmap gate. The authoritative live states remain [issue #15](https://github.com/niakw/ProsperoEden-Encore/issues/15), [the exit matrix](P0_P4_EXIT_MATRIX_2026-11-06.md), and the current exact engine/vendor pair. No PS5 build or gameplay test was performed for this documentation update.

## Binary lineage: do not substitute the mirror's date

| Event | Evidence | What it proves |
| --- | --- | --- |
| Historical native compilation | [Original native CI #38752177232](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38752177232) | Source compiled into the original R1 FTP artifact according to the release record |
| Native source SHA in release notes | `5629395324ff65c98b50c44f35f2142a4a92654a` | Release-declared source of the downloadable package |
| Historical Git tag commit | [`f037a78f88c0097d2031996390d7816b11e45479`](https://github.com/niakw/Prospero.Eden-Encore/commit/f037a78f88c0097d2031996390d7816b11e45479) | The commit targeted by `encore-R1-56293953`, **not** the source SHA shown for the compiled archive |
| Original [R1 FTP release](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) | **15 October 2026**, with `Eden-Encore-56293953-FTP-PPSA99008.zip` and `SHA256SUMS` | Last identified published native PS5 FTP binary baseline |
| [Standalone repository's mirrored R1](https://github.com/niakw/ProsperoEden-Encore/releases/tag/encore-R1-56293953) | **30 October 2026** | Mirror of prior assets, **not** a new compiler invocation or PS5 test |

The historical R1 release notes state that the ZIP was repackaged from the already successful CI artifact without recompiling `PPSA99008/`. Do not infer that all later changes to the current repository exist in the October executable. The exact release metadata takes precedence over a repository's `latest` badge or a later import timestamp.

## Post-R1 source areas that must not be advertised as shipped in R1

| Area | Subsequent work visible in `main` / project audits | Validation boundary |
| --- | --- | --- |
| NS1/NS2 shared content | NS1 and NS2 keys/firmware locations; NSP/XCI/NSZ/XCZ, extracted ExeFS; NUP VFS and content handling | Source or host tests do not demonstrate that the October package supports these newer paths |
| CPU / HLE / memory | Unified loader/process services, IPC, scheduling, sparse JIT, GPU memory accounting | P1 H01–H07 source-owner and positive/negative witness gates; no later R1 console proof |
| GPU | Ampere translation, Maxwell IR/SPIR-V, QMD3 compute, texture/cache/ASTC, synchronization, task/mesh and Vulkan guards | P2 G01–G10 and P4 host qualification; no confirmed NS2 guest-rendered PS5 image |
| Graphics / image | FSR 1 spatial option retained; additional AA, interpolation/frame-generation and R09 neural paths investigated | Distinguish selectable settings, host execution, measured real frame, and released hardware behavior |
| Launcher and controller | NS2 jackets, one-screen launch flow, touchpad quick overlay, input mapping and localization | Host previews and input fixtures are not device testing or proof of correct game behavior |
| Reliability and diagnostics | FC27 HUD/freeze work, memory/IPC/video fence fixes, log and resource safeguards | Only later matched PS5 capture can establish gameplay performance and stability |

These rows are a **high-level inventory**, not an assertion that every prototype is enabled. For file-by-file and current gate detail, use [source history](../MEMORY.md), [unified roadmap](ROADMAP_NS1_NS2_UNIFIED.md) and the [source/host exit matrix](P0_P4_EXIT_MATRIX_2026-11-06.md); avoid copying their live checkbox states into a second tracker.

## Workflow names, steps and interpretation

| Workflow file | Executed scope and correct interpretation |
| --- | --- |
| `.github/workflows/encore-core-fast-gate.yml` | Quick maintained source/host regressions; not a PS5 binary |
| `.github/workflows/encore-core-preflight.yml` | Sharded source and host tests, not console playability |
| `.github/workflows/ns2-research-host.yml` | Source owner, ABI, memory, compiler and guest GPU witnesses; not a native game render |
| `.github/workflows/ns2-p1-p2-exit.yml` | **Manual** enforce decision for 17 H01–H07 and G01–G10 contracts, including positive and negative evidence; do not treat the mere presence or green structure audit as closure |
| `.github/workflows/p0-p4-host-matrix.yml` | Sharded checks with same-SHA engine/vendor receipts; green shards are not a console release |
| `.github/workflows/r09-vit-boundary-qualification.yml` | Public-source model inventory, compiler, shader ABI and software-Vulkan I/O checks; no private model, full authentic inference or PS5 image is proven |
| `.github/workflows/r09-host-link.yml` | Deliberate/manual Linux executable link, public-only artifact and input rejection; binary startup is not full network completion |
| `.github/workflows/build-040-zbic.yml` | Actual native PS5 application build/package when **explicitly** triggered; ordinary pushes to `main` result in a **skipped** build job |
| `.github/workflows/publish-validated-build.yml` | Publication path must verify exact compiled artifact/source provenance before any release claims |

### Three independent evidence levels

1. **Source/host**: compiler syntax, extracted owner behavior, software Vulkan, fixture or hardware-independent tests.
2. **Compiled PS5 package**: actual native build, exact engine/vendor sources, ELF, archive and checksums all tied to the same SHA. A restored stage is identified as restored, not freshly compiled.
3. **Physical console**: executable launched on the declared firmware with real guest progress, first guest-rendered image, gameplay and diagnostics. This remains separate from P0–P4 host closure and belongs to P5.

### CI display-label policy

User-facing workflow titles, job names, step names, and generated public-kit descriptions use **Encore-owned or neutral descriptions**. They must not imply ownership by a commercial accelerator vendor or claim complete inference from a shader ABI/preview. Preserve indispensable technical names (DLL filenames, ABI symbols, shader formats, GPU architecture references, package IDs), automated artifact IDs, hashes and required licensing/third-party attribution. Brand names can remain in legal notices and objective compatibility documentation; they must not be used as decorative workflow branding.

**As inspected on 9 November 2026:** recent `main` push runs of `build-040-zbic.yml` showed `skipped`; a successful P0–P4 host matrix on one SHA must not be merged with pending or failed results on other SHAs. No claim is made that the current `main` or R09 has passed all gates, produced a newly compiled installable PS5 artifact, or demonstrated a complete authentic neural output.
