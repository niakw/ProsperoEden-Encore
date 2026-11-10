# DLSS-NR Min — isolated RDNA2 / PS5 preparation

> **Experiment only. Not qualified on PS5. Do not merge into `main` while the current PS5 build is running.**

This branch exists at the maintainer's explicit request as an exception to the historical main-only development policy. It does not touch the pinned vendor submodule, production renderer, launcher, build packaging or Switch 1 paths. The testable workload policy is host-only and **runtime-hard-disabled**.

## Resolution: PS5 4K output is not the R09 neural graph resolution

PS5 may output **3840×2160** while an intermediate pass computes at **1920×1080**, followed by a separate presentation-scale operation. These are not interchangeable. The current R09 native Original/Compact plans and their tensor layouts encode **1920×1080 exactly**; `PreflightR09Session` rejects source/output shapes that do not match the graph. Just replacing the source extent with 720p or output extent with 4K is invalid.

Candidate workload comparison (theoretical):
| Processing size | Pixels | Relative to 1080p | R09 native graph valid today? |
| --- | ---: | ---: | --- |
| 1920×1080 | 2,073,600 | 100% | Exact fixed schedule, GPU proof outstanding |
| 1280×720 | 921,600 | 44.44% | **No** — dynamic plan and shape tests needed |
| 3840×2160 | 8,294,400 | 400% | **No** — not the existing native plan |

A 720p neural model would process 55.56% fewer pixels, but this is **not** an FPS, VRAM or GPU-time saving guarantee. Model weights and compute stages also matter. **4K TV output** does not mean 4K model execution, and the existing spatial upscalers may not be composed with R09 until their ownership, history, AA policy and validation are solved.

## Four upstream sources assessed

| Repository | Useful idea | Decision for PS5 |
| --- | --- | --- |
| [matiasLombo/neural-upstream](https://github.com/matiasLombo/neural-upstream) | Run same-resolution neural enhancement at render resolution, *before* a separate upscaler | **Target design**, not yet enabled. Current R09 graph lacks a validated variable-raster/720p native plan; D3D12 NGX/ReShade hook itself is not portable to PS5. |
| [BeliyG3/optimizer-fps-dlss5](https://github.com/BeliyG3/optimizer-fps-dlss5) | Spatially compress the periphery, retain full-quality center (default 80/90); temporal inference every N frames with motion-vector residual reprojection | **Standalone mathematical and Vulkan-shader prototypes**: deterministic 80/90 geometry, CPU inverse-map oracles, unconnected SPIR-V pack + residual detail transfer. No integration into R09 renderer, no allocated live PS5 resources and no temporal cadence; missing motion/depth/fences remain blockers. |
| [NVIDIA-RTX/RTXNTC](https://github.com/NVIDIA-RTX/RTXNTC) | Neural **material texture** compression; portable non-cooperative DP4a/integer fallback; decompress on load to BCn or on-sample | **Separate texture study, not DLSS-NR**. Inference-on-load can lower disk/I/O but not resident BCn VRAM, and Switch guest textures have no NTC-encoded material set. No NTC shader or proprietary SDK pulled in. |
| [danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD) | Other AMD feasibility observations | **Reference only**. Public tree does not contain its implementation source; licence prohibits redistribution and derivatives except mandatory exceptions, Windows D3D12/HIP runtime not usable on PS5. Keep Encore's own Vulkan/RDNA2 implementation. |

Upstream vendor **sources** must remain in `vendor/sources`; Encore-specific **overrides** in `vendor/encore-active`. This PR makes **no vendor changes**. It adapts algorithmic MIT geometric principles while retaining the copyright terms in `LICENSES/optimizer-fps-dlss5-MIT.txt`; no NGX/ReShade runtime is copied. Full engine integration will require an independently validated vendor override under `vendor/encore-active`.

## Included in this draft

- `extras/graphics/dlss_nr_min_policy.h`: source/work/center dimensions; default candidate geometry; candidate pixel budget; measured-VRAM guard; ordered evidence blockers for dynamic shape, guest frame handoff, complete R09 graph, motion/depth/reprojection, resource lifetimes and Vulkan GPU path.
- `extras/graphics/test_dlss_nr_min_policy.cpp`: static and runtime host guards (invalid dimensions, edge/corner geometry, overflow, budget reserve, missing evidence and disabled runtime).
- `extras/graphics/dlss_nr_min_spatial_math.h` / `test_dlss_nr_min_spatial_math.cpp`: working **host CPU** symmetric peripheral coordinate maps inspired by the MIT `optimizer-fps-dlss5` SDK, with invertibility/monotonicity/center/negative tests. This is numerical groundwork, **not image pack/unpack, not Vulkan, and not a neural performance improvement**.
- `extras/graphics/dlss_nr_min_graph_geometry.h` / `test_dlss_nr_min_graph_geometry.cpp`: re-audit the **actual 152-step Original and 76-step Compact** 1080p plans and derive 720p *structural candidates*, never executable GPU plans. Breakdown: Original 40 standard FSwin + 4 learned upsamples + 108 specialized rows; Compact 12 + 4 + 60. The four upsample grid sizes refer to the **previous level**, unlike their token-output count, so a simple divisor on every row is wrong.
- `extras/graphics/r09_min_shaders/peripheral_pack.comp` and `peripheral_detail_transfer.comp`: standalone Vulkan 1.1 compute shaders, validated with glslang and spirv-val. Pack samples the native image into an RGBA16F warped work image; detail transfer samples before/after work images and adds the RGB residual to the original RGBA32F output, retaining original alpha. **Not connected to R09; executed on the Mesa Lavapipe host Vulkan software driver with synthetic inputs and checked image readback. No real neural inference or PS5 GPU validation.**
- `extras/graphics/dlss_nr_min_vit_memory_audit.h` / `test_dlss_nr_min_vit_memory_audit.cpp`: inventory of the *actual* `MakeVitBuffers()` requested buffer sizes for eight five-operation ViT blocks, using the native Original and Compact plan geometry: **65 new VkBuffer requests**, **462.5 MiB nominal at 1080p**, **173.4375 MiB candidate at 720p** (difference **289.0625 MiB**). This is an accounting of one stage's requested logical buffer sizes, *not an implemented pooling/reuse optimisation*, not measured resident VRAM and not the model's full memory footprint.
- `extras/graphics/dlss_nr_min_vit_reuse_plan.h` / `test_dlss_nr_min_vit_reuse_plan.cpp`: **non-runnable** structural inter-block alias proposal, preserving the within-block 9-buffer-distinct contract and exact previous-output → next-input binding. Two alternating IO buffers plus seven *different* shared scratch-class buffers would request **24 planes = 60.0 MiB** at 1080p instead of 185 planes = 462.5 MiB, a **402.5 MiB** theoretical reduction for *this one buffer family*. At 720p: **22.5 MiB** vs **173.4375 MiB**. The plan also implements a **fail-closed evidence matrix** for queue serialisation, seven individual inter-block barriers, no concurrent frame/queue use, descriptor immutability, lifetime/fence retirement and positive/negative GPU tests. The test proves every missing condition blocks admission. Even when all synthetic flags are set, the final gate returns `RuntimeHardDisabled`. There are **no actual PS5 alias barriers, no runtime pool allocation, and no inference**. No real VRAM-saving, frame time or quality claim.
- `extras/graphics/dlss_nr_min_spatial_abi.h` / `test_dlss_nr_min_spatial_abi.cpp`: 32-byte Vulkan push constant layout and conservative extra-image budget: **60,051,456 bytes** for three staged images at 1080p/80:90, versus **26,689,536 bytes** at 720p/80:90. These are *proposed staging image bytes*, not total model VRAM or performance measurements. A measured free-memory budget with **nonzero safety reserve** is required; zero-reserve admission is rejected.
- `.github/workflows/r09-dlss-nr-min-host.yml`: isolated lightweight PR gate, sparse pinned vendor header fetch, GCC/Clang C++20 UBSan tests, standalone SPIR-V ABI validation and actual **software-driver Vulkan GPU computation** for the two synthetic cases. No native PS5 build.
- `extras/graphics/r09_min_shaders/peripheral_synthetic_delta.comp`: explicit **non-neural synthetic** RGB work-space gradient (signed X/Y variation), never linked into the production renderer.
- `extras/graphics/r09_min_vk_spatial_smoke.cpp`: independent Vulkan 1.1 **four-case** GPU readback under Lavapipe: 32×32 → 28×28 → 32×32 and **16:9 160×90 → 144×82 → 160×90** (including non-8-aligned work height), both with zero-effect identity (negative control) and spatially varying synthetic RGB delta against independent CPU coordinate oracles. HDR input, checkerboard edges and native alpha survive; **not trained-network inference**.
- **No `tools/graphics/CMakeLists.txt` changes** and no pinned vendor gitlink modification; all six GCC/Clang C++20+UBSan tests and SPIR-V+Lavapipe smoke are run by the dedicated PR workflow, avoiding expensive global P0–P4 shards.

Importantly, `kPs5MinRuntimeQualified = false`. A fully green synthetic host test cannot unlock the feature. The existing `DLSS-NR Original` and `DLSS-NR Compact` user interface, user-owned `nvngx_dlssnr.dll`, SHA-256 tensor verification and no-substitution rules remain untouched.

## Follow-up implementation plan (NOT present in this PR)

1. Prove exact **Original** graph execution, image readback and genuine guest frame on console at 1080p. No FPS claim before this.
2. Measure R09 GPU time by pass, tensor buffer live ranges, actual peak GPU memory, per-title free budget and scheduling stalls on PS5. The 3 GiB allocation *ceiling* in the current source is **not** a measured memory footprint. The new ViT 462.5/173.4375 MiB **nominal requests** have an independently tested **non-executable** pool proposal of 60.0/22.5 MiB nominal; never alias buffers without proving all Vulkan read/write hazards, inter-block barriers, and completed retirement fences.
3. Add dimension-parametric native graph/tensor geometry and ABI tests before admitting 720p. Compare 1080p vs 720p on fixed images with a final 4K display scale; preserve UI render/upscale exclusivity until composition is proven.
4. **Completed for public synthetic inputs:** both standalone Vulkan pack/detail-transfer and GPU readback identity/positive residual oracles on Lavapipe. **Next:** build genuine non-private image fixtures (HDR, UI/HUD edges, movement), quantitative quality regressions (PSNR/SSIM and image captures), and then design safe Vulkan resource/fence integration into R09. Do not enable rendering from a synthetic oracle.
5. Only if real depth, motion vectors, disocclusion rejection, frame history and valid GPU lifetime fences are available, assess N=2 inference cadence, including frame pacing, ghosting and fallback. No speculative frame-gen compatibility.
6. Consider RTXNTC only as a **separate** texture-cache research item, with NTC-encoded source data, licence checks, codec compatibility, cache residency and net VRAM measurements. It does not belong in the DLSS-NR first-pass Min profile.
7. Maintain deterministic fallback to unmodified guest frame on all errors; NS1 remains untouched; no default feature enablement without an explicit console qualification and merge decision.

### Safe acceptance criteria for eventual production merge

- No change to NS1, no forced new file for users, no redistribution of DLSS model binaries/weights.
- At least one authentic PS5 guest image and real R09 model execution, accurate 4K presentation path, and stable Vulkan fences.
- Measured **PS5** worst-case frame time and VRAM, picture quality A/B, no new crashes, and conservative automatic fallback.
- Both positive and negative tests for every new GPU resource lifetime, mode transition and graph shape.

## Public novelty claim (not a product promise)

As of 10 November 2026, public searches found no confirmed native **DLSS 5 Neural Rendering** implementation on a retail base PS5, but absence of a public demonstration cannot prove worldwide priority. Sony's **Quick Spectral Super Resolution (QSSR)** was announced for PS5 on **1 October 2026** and is an actual neural *upscaler*; it is not the same as DLSS Neural Rendering, which enhances an image at the same resolution. Never describe Encore as the first *AI upscaler* on PS5. Possible future positioning only after hardware validation: **one of the first public DLSS 5 Neural Rendering implementations ported to base PS5 RDNA2**.

- Sony's official post: https://blog.playstation.com/2026/10/01/ai-upscaling-is-coming-to-ps5
- NVIDIA developer context: https://forums.developer.nvidia.com/t/unreal-nis-plugin-for-ps5/355767
- Independent 3 Nov context: https://windowsforum.com/news/dlss-5-on-playstation-games-pc-mod-alters-bloodbornes-look-and-hits-performance.450797/

**Verified GitHub host witnesses:** [R09 Min spatial gradient/HDR Vulkan GPU readback, run 42873799497](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42873799497), green on exact code SHA `441f3ac621b4f1aa6aa8dfbee2cb39fb731dc3de`, following [the earlier positive/identity baseline #42872603322](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42872603322). [R09 Min ViT pool *planning only*, run 42875805254](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42875805254), green on SHA `210c0c2670fd4054117987a1df80d3c42f59c8f1`. Real Vulkan GPU commands executed through a **software ICD**, with synthetic RGB effects; not a trained neural network, not 152 Original shader stages, not a physical PS5 GPU. No native PS5 build or hardware qualification has been performed for this PR.

The current draft is **a development foundation, not a finished DLSS-NR Min implementation**.

## Run provenance and remaining blockers

- **Run provenance:** the dedicated host workflow is green for latest functional code SHA `210c0c2670fd4054117987a1df80d3c42f59c8f1`, including both image cases (identity and spatially varying artificial RGB), audited ViT allocation requests, and a strictly **non-executable** cross-block alias candidate. [The updated six-test + four GPU-case proof #42875805254](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42875805254) is green on code SHA `210c0c2670fd4054117987a1df80d3c42f59c8f1`. The new `VitReuseGate` independently rejects missing inter-block compute barriers, concurrent frame/queue use, missing lifetime/fence proof, or missing positive/negative GPU qualification; it remains hard-disabled even if all test evidence is synthesized. Documentation-only commits after a green run do not imply that a new code SHA has been tested.
- **Next blocker:** link our existing authentic R09 model to genuinely produced guest frames and full Original graph GPU fences. The 720p row plan is **structural** only: specialized Split-Swin, ViT, decoder and learned-layout resource ABI remain unqualified.
- **No speed claim:** 55.56% fewer 720p pixels is arithmetic, not observed GPU time, and adding the two work images has its own memory/compute costs. Validate net savings on PS5 against the existing 1080p baseline before enabling.
- **No release or main merge:** this PR is isolated and draft by design, even after a green host-run.
