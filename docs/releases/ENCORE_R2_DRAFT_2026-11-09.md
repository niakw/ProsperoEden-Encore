# Eden Encore R2 Preview — complete post-R1 development changelog

**Development period:** October 15 – November 9, 2026  
**Release status:** **UNPUBLISHED DRAFT · PRERELEASE · NO ASSETS**  
**Release scope:** P0–P4 unified-engine development candidate; P5 hardware build and validation excluded.

This draft documents the work introduced or advanced **after the last genuinely compiled public PS5 R1 package**, including shared NS1/NS2 architecture, native loader and services, graphics, launcher, settings, resilience, host qualification, and the maintained vendor source tree. It is not a new PS5 binary, a compatibility announcement or an instruction to replace the existing installation.

## Historical release baseline — October 15, not October 30

- **Last identified public native build:** [Eden Encore R1 — PS5 FTP](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953), published **October 15, 2026**.
- **Exact source SHA declared by that release:** `5629395324ff65c98b50c44f35f2142a4a92654a`.
- **Native build evidence:** [GitHub Actions run #38752177232](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38752177232).
- **Historical release tag commit:** `f037a78f88c0097d2031996390d7816b11e45479`; this tag pointer is **not** the compiled-source SHA.
- **Package:** `Eden-Encore-56293953-FTP-PPSA99008.zip` plus `SHA256SUMS`.
- **October 30 appearance in the standalone repository:** a mirror of the earlier release assets, **without recompilation**.
- **This R2 draft:** source reference `0b1d6587bec608a9f8cf98944c2ecc121e4d0e7f`, with pinned vendor `dba9a02931dc3de32e1059379904e2aefa34e912`. These SHAs identify the source tree for documentation, **not** a newly built native binary.

**Milestone framing:** P0, P1, P2, P3 and P4 are treated as **completed development work for this release candidate**. Formal acceptance receipts must still be read against the exact engine/vendor pair and the published [17-contract P1/P2 exit rules](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/P0_P4_EXIT_MATRIX_2026-11-06.md). P5—physical console compilation, installation, boot, frame delivery, game tests, stability and performance measurements—is a distinct, later gate. This changelog does not fabricate a successful P5 run.

## 1. A single shared first-/second-generation emulation engine

- Consolidated the engine's first- and second-generation work into the maintained `main` architecture instead of treating separate research branches or standalone prototypes as shipping implementations.
- Reused the existing first-generation CPU, service, memory, graphics, shader and Vulkan infrastructure as the integration base for second-generation behavior.
- Refactored generation-specific admission, service contracts and GPU formats behind shared source ownership rather than title-specific hacks.
- Established predictable single native-target selection, owner manifests, explicit vendor pinning and source provenance checks.
- Retained the original first-generation behavior as a regression boundary, including memory ownership, CPU/JIT, controller input, shaders and video presentation.
- Kept unsupported guest behavior conservative: unrecognized instructions, invalid descriptors and unsupported service variants must not be silently reported as working.

## 2. Game discovery, formats, firmware, keys and content

- Expanded the shared content-discovery paths for `NSP`, `XCI`, `NSZ`, `XCZ`, extracted `ExeFS/RomFS`, and relevant direct executable/content forms (`NRO`, `NSO`, `NCA`, `NAX`, `KIP`) when their real layout and metadata permit admission.
- Improved compressed-content handling, including NCZ/NSZ and compatible ZBIC/zstd and LZ4 paths, with explicit size, offset, compression-block and allocation bounds.
- Added or reinforced negative-path handling for malformed archive tables, missing sections, unsupported content, truncated data and partial extraction.
- Supported flexible library organization: base games, updates and DLC can be discovered from their documented folders or supported package layouts without silently misclassifying game generations.
- Standardized per-generation `keys/ns1`, `keys/ns2`, `firmware/ns1` and `firmware/ns2` paths while preserving validated legacy layouts.
- Worked on firmware imports, naming metadata, recognized firmware dumps and safe failure when required user-provided files are absent.
- Preserved user data and installed content isolation: no keys, firmware, commercial game files, private saves or other proprietary inputs are bundled with Encore.

## 3. NUP, VFS, RomFS and update/DLC integration

- Integrated native NUP reader/VFS structures rather than relying on archive-name recognition alone.
- Validated table-of-contents metadata, UUID, SHA-256 and bounded path normalization; rejected traversal and unsafe or inconsistent entry offsets.
- Implemented raw and zstd content handling with integrity checks and explicit mount/read contracts.
- Advanced the native filesystem owners for RomFS, service mounts, updates and add-on content, keeping per-title and per-process ownership explicit.
- Improved rollback and partial-failure behavior so rejected content does not leave stale mounts or falsely available filesystem objects.

## 4. Guest CPU, process admission, JIT and runtime scheduling

- Advanced executable and process admission across ExeFS, NSO/NPDM metadata and associated identity/permission checks.
- Consolidated host and guest process lifecycle rules, handle ownership, cleanup and shutdown ordering.
- Refined AArch64/guest CPU support, instruction-boundary checks and source-level fallback behavior without claiming complete unknown-instruction coverage.
- Reworked sparse native JIT allocation and alias probing to reduce unnecessary reservations and avoid unchecked dense-memory assumptions; added explicit fail-closed behavior and safer retry paths.
- Preserved instruction-cache, guest-write visibility and host-service wait safeguards, with deterministic host tests where possible.
- Tightened scheduling, worker ownership, condition and atomic waiting, thread transitions and synchronization to prevent lost notifications and invalid cleanup.
- Extended diagnostic evidence for memory pressure, CPU waits, JIT regions and title lifecycle, while keeping expensive tracing optional.

## 5. Memory, GMMU, NVMap and GPU resource ownership

- Added or reinforced second-generation GPU virtual-memory contracts, including 49-bit address-space checks, 4 KiB guest pages, bounded mappings and arithmetic overflow guards.
- Improved GPU-only allocations, NVMap lifetime rules, contiguous/sparse mappings, alias constraints and rollback on partial allocation or out-of-memory conditions.
- Separated guest address validity from host allocation success, including checked lengths, offsets, ranges, alignment and permissions.
- Added typed CPU/GPU memory-access validation, cache invalidation and deferred write publication in shared components.
- Reduced the risk of stale buffers, premature frees and illegal GPU access during process teardown or graphics submission failures.
- Preserved explicit rejection paths for inaccessible or unproven mappings instead of substituting dummy buffers.

## 6. HLE, IPC/TIPC, services, video and audio

- Expanded reviewed IPC/TIPC command handling, identity and session validation, request/response size checking and error responses.
- Reinforced service-manager and process-bound handle lifetimes, ownership and cleanup.
- Advanced display-system contracts: VI/VI2 negotiation, display identification, output resolution/format validation, timing and synchronization.
- Improved native video-decoder queue behavior and surface/fence selection so an unavailable surface cannot unnecessarily prevent other eligible work.
- Refined audio and multimedia service interfaces, bounded buffers, supported service commands and separation of host-only protocol tests from console playback.
- Applied consistency checks to AM, filesystem, NVDRV and display-related service paths; invalid requests receive explicit safe outcomes.
- Retained the first-generation service ABI as a mandatory shared-engine regression boundary.

## 7. Second-generation GPU commands and shader translation

- Advanced the native GPU path for GPFIFO/GMMU, DMA and channel ownership, with guarded initialization, submission, scheduling and fatal-error behavior.
- Added reviewed Ampere method and instruction translation into common engine representations and the Maxwell/IR/SPIR-V pipeline.
- Strengthened high-GPR operand handling, signed branch relocation, execution masks, vector spans and conservative handling of unreviewed instructions.
- Worked on graphics stages including vertex, fragment, geometry and tessellation, and task/mesh where native host capabilities and actual shader semantics allow them.
- Improved compute dispatch admission, shader resource reflection, instruction decoding, descriptor layout validation and SPIR-V compilation.
- Extended the QMD3 path for CBUF banks, indirect accesses, SSBO bindings, global loads/stores, alignment, memory spans, atomics and texture/sampler descriptors.
- Added strict failure rules when indirect descriptor indices, buffer offsets or branch targets cannot be safely established.
- Improved synchronization between compute writes, later graphics/indirect reads, Vulkan barriers and fence ownership.
- Enforced stage-appropriate patch/output access and structured shader emission rather than accepting invalid SPIR-V.

## 8. Vulkan renderer, textures, caches and graphics stability

- Hardened texture and buffer lifetime management, cache invalidation, staging buffers and resource recycling under GPU fences.
- Reviewed texture descriptors, TIC/TSC, arrays, ASTC, image formats, sparse resources and access widths in the maintained renderer.
- Improved native Vulkan buffer/image barriers, scheduler ordering and replay behavior for deferred GPU operations.
- Consolidated maintained host graphics sources, RADV/PS5 adaptations and source-parity checks; preserved required third-party API and license identifiers.
- Addressed selected HUD/update timing, rasterizer state, blit and presentation-path defects using host-source evidence and targeted regression checks.
- Refined memory-pressure policies, GPU resource budgets and native graphics diagnostics to reduce unsafe behavior on a constrained device.
- Kept first-generation rendering code paths available, with explicit host regression witnesses for shared changes.

## 9. Video scaling, spatial FSR 1, anti-aliasing and image quality

- **Preserved FSR 1 spatial upscaling** with its EASU/RCAS paths and sharpness preference. Translation cleanup must never remove the implemented filter.
- Reviewed TV output versus internal guest resolution, sharpening strength, bilinear alternatives and other video-scaling choices.
- Improved preset/profile bookkeeping across Minimum, Recommended, High, Ultra and Custom modes as supported by the source.
- Worked on FXAA, optional antialiasing choices and compatible image-quality adaptations without asserting they are all GPU-certified on PS5.
- Added source and host checks for graphics settings, UI labels and the distinction between render-scale settings and real game performance.
- Investigated FSR 3 optical-flow interpolation and other frame-generation paths separately from spatial FSR 1; no unsupported option is to be promoted to a demonstrated native mode.

## 10. R09 neural rendering and optional image generation

- Advanced R09 neural-rendering research and maintained runtime integration for optional Anime4K-style paths, learned-model import and image composition.
- Added checks for a **user-supplied private Windows model DLL** and model-package integrity. The DLL is read as data where supported; no proprietary DLL, tensor weights or private binaries are redistributed.
- Validated model inventories and expected tensor manifests, size/shape checks, SHA-256 digests and original-versus-compact model paths.
- Extended public host tools for model parsing, tensor layout, FSwin/ViT stages, convolution/decoder paths, GPU resource scheduling, Vulkan/SPIR-V ABI checks and bounded image readback.
- Distinguished an authentic model import, a linked host executable, software-Vulkan shader execution, a synthetic fixture and successful end-to-end neural inference.
- **No complete authentic Original 152-operation network output on PS5 is claimed.** Host tests or a generated sample image alone do not prove this.
- Integrated safety gates for invalid user models and unsupported frame-generation modes so a setting cannot misleadingly claim native functionality.

## 11. Launcher, media library and artwork

- Expanded controller-first TV launcher behavior: home, tabs, settings, library, recent games, per-title settings, visual focus and consistent navigation.
- Improved handling of first- and second-generation game artwork, fallback covers, case layouts, artwork indexing, front/back media and long titles.
- Refined native 3D case previews, game-library sorting, responsive text and supported preview image formats.
- Improved launcher loading/presentation continuity so the selected jacket remains visible rather than introducing an unnecessary second full-screen loading interruption.
- Advanced background artwork, theme styling, visual hierarchies, screenshots and host preview workflows.
- Preserved the distinction between real screenshot evidence and fictional/sample launcher artwork; sample covers are not a game-compatibility matrix.

## 12. Controller mapping and in-game quick overlay

- Established the **physical touchpad click** as the intended quick-overlay trigger; the central PS system button remains reserved for the console.
- Added or refined in-game graphics, per-game settings, controller mapping, FPS/diagnostic information and runtime options in the overlay UI.
- Moved FPS display control into settings rather than relying on a separate gameplay toggle shortcut.
- Added warnings where a setting cannot take effect until a game restart.
- Improved controller mapping, button/chord handling, capture/Home fallbacks, vibration and persistence of per-game preferences.
- Preserved separation between the physical controller's input semantics, the guest button mapping and the game's own on-screen glyph artwork.
- Kept unsupported ROM-specific glyph replacement or controller assumptions from being silently applied globally.

## 13. Localization, documentation and accessibility

- Maintained **29 application translation catalogs** and added user documentation for all 29 catalog locales, covering **six subjects per locale**: project overview, installation, settings, troubleshooting, support and accessibility.
- Preserved the distinction between **29 catalogs** and the launcher's **18 currently selectable language/region choices**, which represent 13 spoken languages.
- Fixed or extended Neural Rendering, A4K, frame-generation and FSR-related UI translation keys; retained useful previous translations as historical gettext entries instead of silently losing them.
- Improved the English README, installation paths, upgrade guidance, troubleshooting, system-version caveats and user expectations.
- Clarified accessible launcher controls: larger text, higher contrast and reduced motion, without claiming complete accessibility certification or universal in-game behavior.
- Added a [complete language directory](https://github.com/niakw/ProsperoEden-Encore/blob/main/LANGUAGES.md). Localized practical guides are **shorter than the full English references** and still need native-speaker proofreading.
- Updated the [vendor README, contributor rules and accessibility routing](https://github.com/niakw/Prospero.Eden-Encore-vendor) so consumers use the engine manuals, not dependency-source documentation.

## 14. Reliability, security, CI and packaging

- Expanded Clang/GCC checks, UBSan host witnesses, source-owner provenance, SPIR-V validation, Vulkan smoke tests and negative-path tests.
- Added bounded **H01–H07** and **G01–G10** P1/P2 exit contracts, separating the structural audit from an enforceable all-proof exit decision.
- Maintained source-preflight, core fast-gate, NS2 guards, P0–P4 sharded host qualification and release-source checks, with exact engine/vendor pairing.
- Kept the native PS5 build workflow **explicitly opted-in**. Successful host checks and skipped native build jobs are never relabeled as newly compiled console packages.
- Improved source integrity, dependency pinning, memory/path safety, dangerous archive-input rejection and private model handling.
- Reviewed visible GitHub Actions workflow, job and step labels, and neutralized unnecessary commercial product naming in project-owned code comments.
- Preserved third-party copyright and attribution, technical namespace names, vendor API identifiers, original SDK provenance and file names necessary for ABI correctness.
- Fixed README provenance where source-only improvements had incorrectly sounded like features in the October R1 binary.
- Provided conservative release-note distinctions among **implemented source**, **host-validated behavior**, **native build** and **physical device tests**.

## 15. P0–P4 completed development scope and P5 handoff

| Milestone | Release-candidate interpretation | Evidence boundary |
| --- | --- | --- |
| **P0** | Completed shared source architecture and pinned dependency ownership | Same-SHA source/CI gate evidence |
| **P1** | Completed planned host-side loader, process, memory, HLE and service development | H01–H07 positive/negative owner contracts |
| **P2** | Completed planned host-side GPU, compute, shader and Vulkan development | G01–G10 positive/negative owner contracts |
| **P3** | Completed planned launcher, controls, locale and documentation development | UI source and host checks; real device UI remains P5 |
| **P4** | Completed host qualification workstream for the candidate | Final explicit same-engine/vendor receipts, not a single unrelated green shard |
| **P5** | **NOT INCLUDED IN THIS DRAFT** | Native package build, PS5 installation, boot, guest frame, games, crash/VRAM/FPS traces |

These are **candidate changelog milestone states**, not a claim that the current technical issue tracker has been formally signed off or that `--enforce` has passed on this latest SHA. The [live roadmap issue](https://github.com/niakw/ProsperoEden-Encore/issues/15) and [exit matrix](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/P0_P4_EXIT_MATRIX_2026-11-06.md) provide the exact validation evidence and may record outstanding proof requirements.

### Compatibility and deployment limitations

- **Tested console firmware reference:** PS5 **13.60**; no new hardware run has been performed for this draft.
- **First-generation titles:** previous R1-era evidence does not prove that all later memory, GPU, HUD or pause/freeze changes are stable on physical hardware.
- **Second-generation titles:** no confirmed first guest-rendered PS5 frame or game-playability certificate for Mario Kart World or Donkey Kong Bananza.
- **Performance:** no new FPS, latency, VRAM reduction or compatibility percentage is claimed without matched device measurements.
- **Neural rendering and frame generation:** code, settings, host examples and vendor parsers are not a guarantee of completed native neural output or real interpolated frames.
- **Installation:** do not delete or overwrite your personal `/data/prosperoeden/` folder or any external storage root; back up saves, settings and user-owned files before any future upgrade.
- **Distribution:** no new `eboot.bin`, FTP ZIP, FFPFSC image, symbol package or other attachment exists in this draft. The October 15 R1 remains the last identified compiled public package.

## Further documentation

- [Engine README](https://github.com/niakw/ProsperoEden-Encore/blob/main/README.md) · [29-language user guide directory](https://github.com/niakw/ProsperoEden-Encore/blob/main/LANGUAGES.md)
- [Installation](https://github.com/niakw/ProsperoEden-Encore/blob/main/INSTALL.md) · [Settings](https://github.com/niakw/ProsperoEden-Encore/blob/main/SETTINGS.md) · [Troubleshooting](https://github.com/niakw/ProsperoEden-Encore/blob/main/TROUBLESHOOTING.md)
- [P0–P4 and P5 technical roadmap](https://github.com/niakw/ProsperoEden-Encore/issues/15) · [Source acceptance matrix](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/P0_P4_EXIT_MATRIX_2026-11-06.md)
- [Historical release and CI audit](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/RELEASE_BASELINE_WORKFLOW_AUDIT_2026-11-09.md)
- [Pinned source/vendor dependency repository](https://github.com/niakw/Prospero.Eden-Encore-vendor)
- [Last actual compiled public R1 (October 15)](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

---

**Release management:** This entry is intentionally kept as **draft + prerelease, with zero attached assets and no publication**. It is a documentation and release-planning candidate, not a replacement for the verified R1 download.
