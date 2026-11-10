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
- `extras/graphics/r09_min_shaders/peripheral_pack.comp` and `peripheral_detail_transfer.comp`: standalone Vulkan 1.1 compute shaders, validated with glslang and spirv-val. Pack samples the native image into an RGBA16F warped work image; detail transfer samples before/after work images and adds the RGB residual to the original RGBA32F output, retaining original alpha. **Not connected to R09, not executed on real GPU yet.**
- `extras/graphics/dlss_nr_min_spatial_abi.h` / `test_dlss_nr_min_spatial_abi.cpp`: 32-byte Vulkan push constant layout and conservative extra-image budget: **60,051,456 bytes** for three staged images at 1080p/80:90, versus **26,689,536 bytes** at 720p/80:90. These are *proposed staging image bytes*, not total model VRAM or performance measurements. A measured free-memory budget with **nonzero safety reserve** is required; zero-reserve admission is rejected.
- `.github/workflows/r09-dlss-nr-min-host.yml`: isolated lightweight PR gate, sparse pinned vendor header fetch, GCC/Clang C++20 UBSan tests and standalone SPIR-V ABI validation. No native PS5 build.
- `tools/graphics/CMakeLists.txt`: host-only test registration. No change to the global PS5 build.

Importantly, `kPs5MinRuntimeQualified = false`. A fully green synthetic host test cannot unlock the feature. The existing `DLSS-NR Original` and `DLSS-NR Compact` user interface, user-owned `nvngx_dlssnr.dll`, SHA-256 tensor verification and no-substitution rules remain untouched.

## Follow-up implementation plan (NOT present in this PR)

1. Prove exact **Original** graph execution, image readback and genuine guest frame on console at 1080p. No FPS claim before this.
2. Measure R09 GPU time by pass, tensor buffer live ranges, actual peak GPU memory, per-title free budget and scheduling stalls on PS5. The 3 GiB allocation *ceiling* in the current source is **not** a measured memory footprint.
3. Add dimension-parametric native graph/tensor geometry and ABI tests before admitting 720p. Compare 1080p vs 720p on fixed images with a final 4K display scale; preserve UI render/upscale exclusivity until composition is proven.
4. **Next:** execute the now SPIR-V-validated *standalone* Vulkan pack/detail-transfer shaders on a host GPU/CPU Vulkan ICD with actual image A/B and an identity residual oracle. Only then design resource/fence integration into the R09 renderer and controlled PS5 A/B. First compare 100/100 vs 80/90 without temporal reuse; sample artifacts, edges, HUD and HDR.
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

**Verified GitHub host witnesses:** [R09 Min isolated C++20 GCC/Clang + UBSan + SPIR-V validation, run 42870136670](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870136670), green on commit `71f4fb0`. The pre-existing P0–P4 host and security suites follow their independent workflows. No standalone GPU shader execution, no real neural inference and **no native PS5 build or hardware qualification** has been performed for this PR.

The current draft is **a development foundation, not a finished DLSS-NR Min implementation**.
