# Eden Encore R457 — Development Preview

### Complete post-R1 development changelog · 15 October – 11 November 2026

> **UNPUBLISHED DRAFT PRERELEASE — ZERO RELEASE ASSETS.** This is the proposed R457 development changelog, now updated through the **R457 native PS5 CI build** of 11 November 2026. A signed, packaged candidate exists as temporary GitHub Actions artifacts, **not as assets attached to this draft**. P0–P4 source and host evidence must not be confused with physical PS5 execution; **P5 native compilation, linking, signing and ZIP checks passed CI, but installation, gameplay, performance and stability on a real PS5 remain unverified**.

**Draft R457 reference:** engine `ec8b519182532d3864c5a67dd27aa41aa9d43ff3` · pinned vendor `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2` · source changes since the R1 compiled-source SHA `5629395324ff65c98b50c44f35f2142a4a92654a`.

**R1 provenance:** [Original 15 October release](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [native build run #38752177232](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38752177232) · original source `56293953...` · release tag points to a different historical metadata commit `f037a78...`. The [30 October release in this repository](https://github.com/niakw/ProsperoEden-Encore/releases/tag/encore-R1-56293953) contains the **same imported R1 package**, not a new native compilation.

---

## Highlights

- **One maintained native PS5 application and shared NS1/NS2 core.** First- and second-generation guest support now share the maintained loader, CPU/JIT, memory, GPU and display infrastructure on `main`; no separate experimental second-generation application is required.
- **Major guest GPU and Vulkan work.** New second-generation command handling, Ampere-to-common-IR translation, compute descriptors, graphics stages, synchronization, texture and memory protections, shader compilation and rejection paths.
- **Safer content handling.** Better handling of NSP/XCI/NSZ/XCZ, extracted game files, updates/DLC, NUP, per-generation keys and firmware, and corrupted or incomplete input.
- **Launcher and controller improvements.** Updated library, covers and 3D packaging, per-game settings, language support, controller mapping, faster startup presentation and a **touchpad-triggered Encore quick overlay**.
- **Graphics and image processing.** Preserved spatial FSR 1 (EASU/RCAS and sharpening), revised presentation/AA/scaling policies, optional frame-interpolation source work and a separate neural-rendering R09 development path.
- **Reliability and tooling.** Memory ownership, HLE/IPC, video queues, shader/graphics synchronization, more useful diagnostics, hardened release provenance and bounded code/host verification.
- **International user documentation.** Six user-facing document types available across **all 29 application catalog locales**. The launcher source now exposes **exactly all 31 official PS5 system language/region choices**, backed by 31 catalogs (including distinct English US/UK variants), with no non-PS5 additions.
- **First R457 native PS5 candidate (CI only).** R457 linked, signed and packaged at exact engine SHA `ec8b5191`, with a verified release ZIP, FTP ZIP and SHA-256 manifest; no PS5 game test or public release is implied.
- **Clean GitHub presentation.** Neutral workflow/job/step titles and non-essential brand mentions in owned source comments; required technical API names, provenance and third-party license notices stay intact.

## 1. Unified engine and project architecture (P0)

- Integrated shared first- and second-generation runtime owners into a **single active engine on `main`**.
- Reused common OS services, scheduling, filesystem, translation, input, video output and rendering foundations instead of duplicating console executables.
- Removed historical dependence on separate experimental/release CMake profiles for selecting different products; retain automatic capability detection and strict admissibility decisions.
- Separated optional graphics experiments from the core engine's supported guest instruction and ABI requirements.
- Retained only source-level compatibility where generation-specific behavior genuinely differs: executable format details, GPU instruction set, descriptor layout, firmware services and timing.
- Consolidated maintained overrides into complete source units and explicit build selections; pinned the corresponding vendor tree rather than relying on invisible build-time rewriting.
- Reconciled historical source inventories and post-audit owner additions without reinterpreting an old baseline as proof of performance.
- Preserved the normal first-generation renderer and application behavior as the regression baseline.
- Added source/provenance checks for common CMake, Vulkan, host service contracts, dependencies and graphics owners.
- Kept native PS5 builds an **explicit choice** and publication a **separate approval**, instead of treating every successful host workflow as a release.

## 2. Game discovery, executable loading, updates and DLC (P1)

### Content types and file organization

- Continued discovery and admission work for **NSP, XCI, NSZ and XCZ** game packages, extracted **ExeFS/RomFS** content and executable inputs such as **NRO, NSO, NCA, NAX and KIP**, where the corresponding loader supports the form.
- Unified library scanning and explicit game/update/add-on matching, including generation-aware metadata and launch identity.
- Improved handling of **base games, updates and DLC**, avoiding assumptions based solely on a file extension or hard-coded title list.
- Kept a **flexible storage contract**: `roms/`, `updates/`, `dlc/`, `mods/`, user data and external roots can be resolved without user-side source edits.
- Introduced independent `keys/ns1` and `keys/ns2`, and `firmware/ns1` and `firmware/ns2`, while retaining supported legacy flat storage layouts.
- Added or refined named firmware-dump metadata and source-side guards for missing, incomplete or inconsistent system files.
- Improved case-by-case handling of compressed NSO segments (**LZ4, ZBIC and zstd**) with bounded decompression, coherent error responses and no silent fallback to unrelated data.
- Maintained NCZ/NSZ handling for supported compressed inputs, including validation of sizes, block indexes, extracted output and resource budgets.
- Hardened content paths, directory traversal checks, invalid titles, metadata lengths and partial-input cleanup.

### NUP and virtual filesystem

- Introduced a maintained **NUP virtual filesystem** reader and mount path rather than forcing a bespoke extraction workflow.
- Added validation of NUP v1 headers, table of contents, identifier/UUID records, SHA-256 integrity and normalized paths.
- Added raw and zstd-backed entry handling and bounded file reads.
- Integrated RomFS/add-on search and mounting contracts while rejecting invalid or ambiguous content.
- Conserved NUP as part of the common source configuration, not a second-generation-only optional build product.

### Process creation and execution

- Worked on **NPDM/ACID/ACI, NSO/ExeFS, process identity and KProcess handoff** with actual maintained source owners.
- Improved fail-closed admission for malformed process metadata, missing file segments, invalid access ranges and partial session construction.
- Avoided publishing partially initialized processes or changing an established first-generation process path just to pass a second-generation test.

## 3. CPU, JIT, memory and process synchronization (P1)

- Consolidated first-/second-generation CPU translation policy, process setup, code memory and host callback boundaries.
- Continued work on executable-memory aliases, JIT allocation/reuse, sparse commit, I-cache visibility and safe process shutdown.
- Maintained source-level safeguards against dense JIT over-allocation, stale aliases and inconsistent guest/host permissions.
- Improved 64-bit guest address checks and range arithmetic, including overflow, alignment and uncommitted memory validation.
- Added bounded **49-bit GPU virtual-address** and page-mapping policies, with 4 KiB mappings and generation-specific sparse handling.
- Strengthened guest/GPU ownership bookkeeping, **NVMap**, temporary pin references, VA remapping, allocation fallback and rollback after an error or out-of-memory event.
- Avoided stale file descriptors, leaked pins, half-committed page tables and invalid access after teardown.
- Revisited CPU scheduling, event signallers, atomic waits, process-wide synchronization and host/guest clock boundaries.
- Kept fences, semaphore ordering and ownership transfers explicit rather than fixing freezes by disabling synchronization.
- Added negative tests for invalid handle/session states, race-sensitive release order, oversized mappings and re-entrant teardown.

## 4. Operating-system services, HLE, audio and video output (P1)

- Expanded common **IPC/TIPC** parsing and dispatch guards, response buffers, handles, service sessions and command-specific failure paths.
- Audited key services in **AM, SM, filesystem, NVDRV, VI/VI2 and audio** against expected guest message layouts.
- Corrected session lifetime and close/teardown order, including NVDRV process registration and map release ownership.
- Improved version-specific service admission rather than assuming a first-generation command has the same behavior for the successor.
- Strengthened native **VI2** display queries, resolution and encoding responses, display/session identity checks, malformed packet rejection and output ownership.
- Reviewed display cadence, virtual present state and guest-to-host presentation handoff.
- Improved audio buffer and sink lifecycle, invalid-format responses and cleanup after guest state changes.
- Corrected video decoder surface scheduling so a surface waiting on a fence does not unnecessarily stall other available output surfaces.
- Conserved GPU/video fences and explicit errors when a frame, service or buffer is not ready.
- Isolated host validation of individual service owners from PS5 runtime behavior; no claim of complete sound/video output for a successor game is made here.

## 5. Guest GPU command processing and memory safety (P2)

### Command submission, DMA and channel state

- Maintained an explicit command path from guest **GPFIFO / GPU channels** through validated command decoding to the shared renderer.
- Worked on generation-specific **Ampere DMA**, 3D/Compute command classes, macro processing, subchannel binding and command fetch.
- Improved pre-initialization command behavior, GPU process identity, invalid binding and stale-process rejection.
- Tightened semaphore/acquire ordering, synchronization points and queue publication.
- Added bounded failure responses for malformed GPU commands and unmapped memory rather than pretending that unsupported instructions succeeded.

### Virtual memory, buffers and descriptors

- Improved GPU virtual-memory translation and **NVMap** integration, including 49-bit access bounds, sparse mappings, page pin ownership and rollback.
- Revisited guest memory coherence, dirty ranges, DMA copies, texture invalidation and cache consistency.
- Added detailed control over **CBUF banks, SSBOs, UBOs, global memory and texel buffers**.
- Refined QMD3 descriptor discovery, indirect constant-buffer addresses, descriptor-array span validation and buffer/image classification.
- Corrected write-only global-memory shader cases where a store needed an SSBO descriptor even without a corresponding read.
- Checked complete byte spans, alignment, overflow, alias, write permissions and failed mapping at descriptor admission time.
- Protected dynamically indexed/indirect resources against divergent offsets and unsupported addressing modes.
- Improved atomic operations and per-buffer access tracking where source semantics could be established.
- Reduced invalid reuse of stale resource views, pipeline descriptors and destroyed buffers.
- Added real-source host witnesses and conservative negative cases for data-dependent GPU access.

### Textures, caches and surfaces

- Improved **TIC/TSC** sampling and descriptor interpretation, texture arrays, image views, image/buffer alias rules and unsupported format rejection.
- Continued **ASTC** and sparse-texture transfer integration with safe staging and resource budgets.
- Strengthened texture cache invalidation, rasterizer writes, GPU cache ownership and deferred cleanup.
- Added protections for asynchronous allocation, queued presentation, framebuffer lifetime and render-pass transitions.
- Improved GPU-only allocations, buffer identities and reserve/commit checks to reduce incorrect visibility between CPU and GPU.
- Preserved first-generation texturing behavior when a successor-specific descriptor cannot be represented safely.

## 6. GPU instruction translation, SPIR-V and Vulkan (P2)

- Expanded Ampere instruction decoding and lowering into the shared Maxwell/IR-oriented back end without indiscriminately treating two generations as identical.
- Reviewed high-register operands and multi-register vectors for arithmetic, memory and predicate operations.
- Corrected branch relocation/target handling for conditional, signed and indirect branch forms where verified; unqualified variants remain explicit failures.
- Improved macro engine sequencing, method and QMD interpretation, including rejection of invalid or reserved fields.
- Continued **Vertex, Fragment, Geometry, Tessellation, Task and Mesh** stage integration with stage-specific capability checks.
- Added checks for undefined patch variables, invalid tessellation stage usage, unrepresentable input/output layouts and out-of-range attributes.
- Worked on native **Compute** pipelines from guest shader state through **SPIR-V** module generation, descriptor binding and Vulkan dispatch.
- Revisited cross-dispatch memory dependencies, indirect dispatch arguments, barriers, image layouts and buffer visibility.
- Hardened descriptor state during pipeline compilation, rasterizer binding and queued replay.
- Improved Vulkan pipeline creation, shader cache, presentation image ownership and deferred destruction.
- Qualified host-side shader syntax/ABI with Clang/GCC, shader witnesses and `spirv-val` where applicable.
- Preserved the **fail-closed** policy for unknown guest opcodes, invalid descriptors, incompatible stage combinations and unsupported GPU capabilities.
- **Important limitation:** a valid SPIR-V module or Vulkan host test is not a verified guest-rendered second-generation PS5 frame.

## 7. Native graphics, scaling, anti-aliasing and frame presentation

### Spatial rendering and display

- Preserved **FSR 1** as the spatial upscaling mode, including **EASU**, **RCAS** and the user-adjustable sharpness control.
- Restored or archived legacy translated FSR labels where needed instead of silently losing the original feature's locale coverage.
- Distinguished TV output resolution from internal game scale, interpolation filter, sharpening, anti-aliasing and frame generation.
- Continued tuning and safeguards for bilinear/bicubic/Lanczos-style scaling choices and output-size arithmetic.
- Worked on **FXAA**, optional AA integrations, multisampling and resolution targets with strict compatibility checks.
- Improved Vulkan presentation scheduling, display image history, render-pass transitions and overlay/HUD composition contracts.
- Refined frame-timing measurements and source/host replay without asserting a specific FPS increase on PS5.

### Optional frame generation

- Added or refined optional frame-generation selection and host-side capability gates.
- Separated actual emulated game cadence from displayed/interpolated frames.
- Explored Vulkan optical-flow and native frame-interpolation approaches without treating an experimental source path as a universally supported release feature.
- Preserved explicit off/unsupported states when required hardware, frame history, depth or motion input is absent.

### Neural Rendering / R09

- Introduced an optional neural-rendering workstream with distinct Original and Compact model manifests and user-side selection policies.
- Added public model-layout and per-tensor verification tools, structural plan checks, optional image-path composition and Vulkan compute/shader ABIs.
- Kept all **model DLLs and learned weights user-private**; they are never committed or attached to a release.
- Added strict checks for tensor count, file bounds, offsets, byte ranges, hashes, model flavor and inconsistent resources.
- Refined image pre/post-processing, Swin/ViT attention, QKV, feed-forward, U-Net/decoder stages and expected intermediate shapes.
- Added source and host tooling to attempt complete graph execution and inspect GPU readback without distributing private inputs.
- Updated public host examples and GitHub display names so a successful link, parser run, shader fixture or partial frame cannot be mistaken for a full authentic model inference.
- **Not claimed:** a verified output image from the complete 152-operation Original network on the PS5 GPU, general game support, or equivalent quality to a desktop proprietary implementation.

## 8. Launcher, home screen, game library and media (P3)

- Reworked the PS5-oriented **controller-first home screen**, main navigation, settings menus, library browsing and per-game information.
- Improved recent-game ordering, selected item focus, browsing state and background presentation.
- Refined **NS1/NS2 game recognition** and book-keeping so changing sections does not repeatedly lose the ROM inventory.
- Improved game metadata lookup and artwork association using available title information and media sources.
- Extended jacket/cover reconstruction, front/back/spine handling, 3D box presentation and safe fallback when artwork is missing.
- Addressed malformed or incomplete covers, transparency, incorrect box tinting, reversed artwork and long-title layouts in the source/host UI paths.
- Updated TV-scale text, focus readability, navigation hints, spacing, clipping and accessibility option wiring.
- Reduced unnecessary preview/covers work, improved asset format handling and used efficient image assets where supported.
- Worked on preserving the selected jacket during game launch instead of showing an extra, unhelpful loading screen.
- Maintained a single-file native application concept and the existing application identity.
- Added or expanded launcher preview and source checks; they are not substitutes for observation on a physical console.

## 9. Controller input, per-game controls and Encore quick overlay

- Preserved the normal controller input chain and first-generation guest button semantics.
- Extended per-game controller-layout selection and mapping rather than globally overwriting the user's preferred profile.
- Supported virtual guest HOME/capture behaviors only through approved mappings; the console's own central system button remains reserved.
- Added the **in-game Encore quick overlay on a touchpad press**, **not** on the central console system button.
- Grouped current game settings, graphics, control mapping, FPS/diagnostics and log options in the overlay.
- Removed the legacy standalone FPS-show shortcut in favor of the overlay-controlled setting.
- Added contextual feedback when an option requires a game restart before it can take effect.
- Revisited controller button glyphs, contextual prompts, mixed physical/guest mapping and title-specific artwork substitution policies.
- Kept the local mapping state and in-game texture assets separate so an unsupported glyph conversion cannot silently alter game inputs.

## 10. Languages, documentation and accessibility

- Maintained **31 application gettext locale catalogs**, including both English variants,, including new graphics, neural and frame-generation settings.
- Improved coverage of new option labels and preserved useful historical FSR translations as inactive references where needed.
- Added practical **README, installation, settings, troubleshooting, support and accessibility guides for all 29 catalog locales** (174 localized pages in total).
- Preserved the existing detailed French and Spanish README/installation pages rather than replacing them with shorter copies.
- Added a single language directory linking every one of the six user-facing pages for each locale.
- Made the distinction explicit: the **launcher offers exactly 31 official PS5 system language/region choices**; all 31 catalog locales are selectable, and no extra languages are provided.
- Documented the selected storage root, keys/firmware ownership, safe migration, release packaging and recovery steps.
- Documented larger launcher text, high contrast and reduced motion as separate optional settings, not guaranteed accessibility inside games.
- Improved the README's version history, R1 source SHA, native-build restrictions and provenance explanation.
- Added source checks for the full user-guide matrix to prevent missing language links.
- **Translation quality note:** complete file/key coverage is not a professional linguistic review. Arabic right-to-left layout, CJK glyph fallbacks, regional variants and UI truncation require native-speaker/device checks.

## 11. Reliability, performance safeguards and diagnostics

- Revisited stalls and timing regressions observed historically in FC27 and other first-generation titles, including gameplay HUD/pause behavior and service synchronization.
- Improved explicit handling of GPU queue backpressure, video surface fences, stale present resources and kernel wait paths.
- Hardened memory lifetime around JIT, direct-memory allocations, decoder surfaces, GPU caches and teardown.
- Reduced repeated source-side allocations or conversion work where clearly justified without promising universal performance gains.
- Added bounded diagnostics, host counters, error categories and trace review for unsupported guest operations.
- Improved fail-closed behavior during malformed package loading, game restart and partial construction.
- Expanded host-negative tests so guards are not considered correct merely because a synthetic positive fixture passes.
- Preserved diagnostic modes without enabling costly logs or unqualified experimental behavior by default.

## 12. Security, dependency provenance and GitHub workflows (P4)

- Kept the maintained source and the **vendor** repository pinned by exact Git commit, preserving third-party licenses and source provenance.
- Clarified which vendor directories are immutable upstream snapshots and which contain maintained source overrides.
- Reviewed user-private model parsing, filename/size bounds, memory ownership and content path validation.
- Maintained static security scans and conservative CodeQL reporting rather than suppressing real findings for cosmetic green CI.
- Updated neutral names/descriptions for relevant workflow headings, jobs, steps and host artifacts.
- Removed non-essential commercial-brand references from authored comments and local test messages without rewriting ABI symbols or upstream authorship.
- Expanded source/host validation with **Clang, GCC, UBSan, SPIR-V and Vulkan host** witnesses.
- Kept a finite P1/P2 acceptance structure with **H01–H07 and G01–G10** (17 contracts), expected positive and negative behavior, stable owner references and rejection of artificial blanket exclusions.
- Separated a **structural audit** of test coverage from the `--enforce` evidence-based exit decision.
- Maintained source preflight, Core fast gate, NS2 host guards, dedicated SPIR-V qualification, P0–P4 host matrix and vendor parity checks.
- Avoided treating green jobs from different SHA revisions as one clean acceptance record.
- Clarified the actual release workflow: ordinary `main` pushes do not cause a full native PS5 build; an explicit manual action or approved build marker is required; release publication is a further deliberate step.
- Updated install guides so they reference actual R1 downloadable file names instead of imaginary historical assets.
- Added this expanded, English-only R457 draft to an isolated release-preparation branch, with **no release assets and no automatic publication**.

## R457 native build and packaging evidence — 11 November 2026

**Verifiable candidate:** [successful P5 recovered native package #42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990), engine `ec8b519182532d3864c5a67dd27aa41aa9d43ff3`, pinned vendor `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`, app ID `PPSA99008`, content version `01.400.457`.

- Link from cached native objects (after the 12th full-build attempt), signing, stage validation, distribution assembly, SHA-256 verification and artifact uploads all **PASS**. This is not evidence of a fresh 1,399-object compilation at this particular SHA; the workflow deliberately reuses native objects and relinks selected owners. Use the exact workflow provenance when assessing compiled-source equivalence.
- Outer Actions bundle: `dist/Prospero.Eden-Encore-R457.zip` (258 entries), FTP distribution ZIP `dist/Eden-Encore-R457-ec8b5191-FTP-PPSA99008.zip` (78 entries), `dist/SHA256SUMS`, release notes, ELF and crash provenance. The independent raw staged FTP artifact has 185 files. The smaller FTP distribution intentionally omits bundled legal materials and `.txt` language companions while retaining the 31 `.po` launcher catalogs; all common file contents compared equal.
- **Verified SHA-256** — full ZIP: `3b39c603fb97e558e5fe815fb0f77def475ab874adaf43ae9b8bdae488f3df3a`; distribution FTP ZIP: `7b87abb567247cf06cdfc7adc7cd498e7826367d1a5548b8d000a3a19e63f474`.
- **Diagnostic-package caveat:** the uploaded symbol archive contains the unstripped ELF and `crash-provenance.json`, but not the `link.map` referenced in that receipt. The ELF hash matches the receipt. A packaging correction is being qualified separately; do not claim the R457 crash bundle already contains every referenced symbol file. The receipt deliberately says `confirmed_same_console_binary=false` pending a physical PS5 sample.
- **CI warnings under review:** the expensive native stage logs contain Mesa/NIR/RADV third-party `-Wunused-but-set-variable`, `-Wreturn-type`, and truncation/uninitialized diagnostics, plus Ampere implicit conversions in pinned vendor sources; these require triage by owner rather than global warning suppression. The optional daily wallpaper snapshot reported ImageMagick invocation incompatibility on the runner, and an ImageMagick PNG profile warning. None of these alone proves PS5 runtime correctness.
- **No generated frame or real hardware acceptance claim.** First-generation and second-generation games, UI and input still need console testing. The draft remains hidden and asset-free; the Actions artifacts expire on 25 November 2026.

**Additional source/host milestones since the initial draft:** 17/17 P1/P2 positive and negative host contracts passed in their formal host exit receipt; dependency/CMake, NS1/NS2 service and graphics owner source preflights improved; the active launcher now catalogs **31 exact PS5 language/region choices** rather than the outdated 18-choice description in early drafts. Language catalog coverage does not certify visual rendering or linguistic quality.

## 13. Development milestone summary for this draft

| Milestone | R457 prerelease narrative | What is not included |
| --- | --- | --- |
| **P0** — common architecture, provenance, source CI | **Completed development scope** | PS5 hardware verification |
| **P1** — loaders, CPU/JIT, memory, HLE and services | **Completed development scope** | Game-by-game console compatibility |
| **P2** — GPU command paths, shaders, descriptors, SPIR-V/Vulkan | **Completed development scope** | Verified first NS2 game framebuffer on PS5 |
| **P3** — launcher, controls, languages, media | **Completed development scope** | Physical console UI/cover verification |
| **P4** — host code/ABI qualification and evidence framework | **Completed development scope for this changelog** | Formal same-SHA sign-off is tracked independently |
| **P5** — native PS5 build, installation, games, stability and performance | **R457 native link, signature and packaging CI successful** | Physical installation, NS1/NS2 frame, audio, saves, performance and stability remain unverified |

This editorial summary **does not rewrite the tracked host evidence or the actual issue checklist**. Where those records still list open or `proof_defined` entries, they remain authoritative for formal verification. A planned-release description must not be used as a fabricated `--enforce` pass.

## 14. Compatibility, limitations and expected testing

**Last hardware-tested firmware:** **PS5 13.60 only**. There is no documented minimum firmware and no recommendation to update a console merely to match the test target.

**First-generation titles:** existing first-generation behavior is the baseline. Previously observed issues included FC27 frame-pacing/HUD freezes and occasional crashes; BOTW was reported as playable in selected profiles on an older binary. None of these results qualify the new R457 candidate.

**Second-generation titles:** Mario Kart World and Donkey Kong Bananza have previously reached guest initialization stages, but no confirmed guest-rendered first frame on the physical PS5 is available. Do not interpret loader progress, Vulkan initialization or host shader compilation as game compatibility.

**Graphics extras:** FSR 1 is a retained spatial filter. Frame interpolation and neural rendering are separate, optional paths with additional restrictions. Selecting or compiling an option is not proof that the game produced more simulated frames or that R09 completed authentic inference.

**User data:** never delete `/data/prosperoeden/` just to repair a failed installation. The original native app and Encore use the same `PPSA99008` title identity, so updating is a replacement, **not** an independent side-by-side install.

**No private files:** the package contains no games, keys, firmware, DLLs, learned model weights, user saves or proprietary distribution assets.

**P5 qualification still needed:** the native R457 CI link, signed staging and SHA-256 verification are complete. Physical installation from a verified ZIP/FTP package; startup and language/artwork on PS5; FC27/BOTW NS1 regressions; Mario Kart World/Donkey Kong Bananza first-frame observations; audio, graphics/VRAM/synchronization, saves, per-game settings and reliable performance traces **remain open**.

## 15. Install and upgrade information

**No file is attached to this R457 draft release (zero assets); do not publish it.** The independently audited [R457 CI bundle](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990/artifacts/13821128432) and [R457 staged FTP folder](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990/artifacts/13822080376) exist as temporary Actions artifacts (expiry: **25 November 2026**), not published release assets. For the last public release, download the [15 October R1 FTP package](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953), which includes:

- `Eden-Encore-56293953-FTP-PPSA99008.zip`
- `SHA256SUMS`

For ZIP/FTP, extract the complete `PPSA99008/` folder and install it under `/data/homebrew/PPSA99008/`. Do not create a nested `PPSA99008/PPSA99008/` folder. Preserve `/data/prosperoeden/` and any configured external storage. Use the [installation guide](https://github.com/niakw/ProsperoEden-Encore/blob/main/INSTALL.md) for firmware/keys, backup, migration, checksums and the **separate** FFPFSC/ShadowMountPlus method.

## Documentation, sources and credits

- [Main README and complete feature overview](https://github.com/niakw/ProsperoEden-Encore/blob/main/README.md)
- [User documentation — 29 catalog languages](https://github.com/niakw/ProsperoEden-Encore/blob/main/LANGUAGES.md)
- [Installation](https://github.com/niakw/ProsperoEden-Encore/blob/main/INSTALL.md) · [Settings](https://github.com/niakw/ProsperoEden-Encore/blob/main/SETTINGS.md) · [Troubleshooting](https://github.com/niakw/ProsperoEden-Encore/blob/main/TROUBLESHOOTING.md)
- [Accessibility](https://github.com/niakw/ProsperoEden-Encore/blob/main/ACCESSIBILITY.md) · [Support](https://github.com/niakw/ProsperoEden-Encore/blob/main/SUPPORT.md)
- [Historical R1 and workflow audit](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/RELEASE_BASELINE_WORKFLOW_AUDIT_2026-11-09.md)
- [Unified roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/ROADMAP_NS1_NS2_UNIFIED.md) · [current milestone issue](https://github.com/niakw/ProsperoEden-Encore/issues/15)
- [Engine source](https://github.com/niakw/ProsperoEden-Encore) · [Pinned dependency/vendor source](https://github.com/niakw/Prospero.Eden-Encore-vendor)
- [Licenses and third-party notices](https://github.com/niakw/ProsperoEden-Encore/blob/main/THIRD_PARTY_NOTICES.md)

**Eden Encore is an independent community project.** All upstream copyright, source attribution and license terms are retained. Trademark names used strictly to describe APIs, target platforms or compatibility do not imply endorsement or affiliation.


## Verified documentation and vendor presentation qualification — 9 November 2026

The documentation localization follow-up has been implemented on `main` **after the original draft notes were written**:

- All **29 application catalog locales** now have six consumer-focused Markdown guides each: README/overview, installation and upgrading, settings, troubleshooting, support and accessibility (**174 localized pages**). These are practical native-language guides, **not** a claim that the longer English documentation has been translated line for line or independently proofread by 29 native speakers.
- The language index distinguishes the **31 translation catalogs** (including US/UK English) from the **29 non-English localized guide sets** under the **31 exact PS5 system language/region choices**. English remains the most detailed normative user reference. The [strict Sony 31-choice policy](../PS5_SYSTEM_LANGUAGE_POLICY.md) excludes all languages not on Sony's official console menu.
- The [user documentation and local-link validation workflow](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42618975742) **passed** for the documentation changes, checking catalog coverage, internal links, preservation of save-data warnings and key localized help. It does not test PS5 rendering or certify linguistic quality.
- Invalid French/Spanish guide links and obsolete feature/research branch links in the main and translated READMEs have been corrected.
- The [vendor maintained-source presentation audit](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42618761816) **passed**, scanning **775 active source-text files**. Commercial names were absent from the vendor's visible workflow titles and step labels. The audit recorded 100 branded references in comment-like lines of the maintained source; these are predominantly driver/ABI/format facts, namespace markers or required upstream attribution and were **not** blindly removed. Third-party snapshots remain unmodified.
- The R457 engine's `vendor` gitlink is pinned to `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2` (verified from the R457 source tree); the prior 9 November documentation/vendor review refers to an older historical pin. Neither documentation qualification nor vendor presentation review is a substitute for P1/P2 functional exit receipts, a new native PS5 compilation or P5 hardware tests.

---

*This release record remains an **unpublished draft prerelease with zero assets**. R457 is a verified **CI-native build and artifact**, not a console-validated game release. No new full native build or release publication is requested by these editorial changes.*
