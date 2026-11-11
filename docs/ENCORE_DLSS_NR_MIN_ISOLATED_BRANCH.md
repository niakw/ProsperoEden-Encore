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


## Vulkan test of the ViT reuse mechanism (synthetic only)

The standalone host test r09_min_vk_vit_reuse_smoke.cpp executes eight
real Vulkan compute dispatches via Lavapipe, using nine separate physical
VkBuffers: two ping-pong IO buffers and seven reusable scratch-class buffers.
Seven explicit SHADER_WRITE to SHADER_READ|SHADER_WRITE barriers separate
consecutive blocks. The test waits on a Vulkan fence and checks the final
64-token result and all seven scratch-buffer results against CPU oracles.

This is NOT execution of learned ViT weights or any of the authentic five
operations per ViT block. The real buffers have additional in-flight descriptor
and resource-lifetime requirements which this synthetic test cannot prove.
The fail-closed production admission gate remains disabled; zero PS5 runtime
code is modified. Nominal allocation savings are still projections, not VRAM
measurements.


The executable smoke now reads the actual candidate alias maps from the
Original and Compact 1080p native schedules and the two 720p structural
candidates. All four must agree on the nine VkBuffer binding slots before
any dispatch begins; any divergence is a hard failure. Even a successful
GPU smoke is still blocked by the separate PS5 runtime admission gate.


## Pinned vendor source-drift gate for actual ViT subgraphs

The isolated host CI now reads six **.cpp files from the exact pinned vendor
submodule Git object** using git show HEAD:path, not floating vendor main:
nr_rdna2_frame_session.cpp, nr_rdna2_vit_run.cpp, nr_rdna2_vit_block.cpp,
nr_rdna2_vit_projection_stage.cpp, nr_rdna2_vit_epilogue.cpp and
nr_rdna2_vit_qkv_attention_link.cpp.

The source-level guard checks the real 9-role buffer allocations, strict
previous-output-to-next-input equivalence, four ordered learned subgraphs,
GEMM/QKV stage ordering and the terminal residual dispatch followed by
compute-to-compute SHADER_WRITE -> SHADER_READ|SHADER_WRITE visibility.
Seven independent negative mutations (lost barrier, changed mask, broken
buffer identity, incorrect stage ordering, etc.) **must** fail the guard.
The checked source hashes and exact vendor gitlink are emitted in CI.

**Key revised finding:** the pinned native terminal projection already records
a matching compute-to-compute memory barrier, so it is inaccurate to state
that the existing engine has no inter-block barrier at all. This source
property is necessary for aliasing and supports further investigation, but
a static text check does NOT prove all descriptors' lifetimes, asynchronous
queues or frame retirement; no production allocation/pooling change occurs.
The hard-disabled gate remains hard-disabled pending actual PS5 qualification.


## Khronos synchronization validation (host only)

The standalone ViT reuse witness can also run with
R09_MIN_VALIDATE_SYNC=1. This opts into VK_LAYER_KHRONOS_validation,
VK_EXT_validation_features synchronization validation and the debug-utils
error callback, failing if a validation ERROR is emitted. The dedicated host
workflow runs both the original readback oracle and the validation variant
using Lavapipe. This is NOT a PS5 driver-validation run and cannot rule out
proprietary-model hazards or real ViT live-range conflicts.


### Deliberate missing-barrier negative control

The host sync validation fixture also removes exactly one of the seven
synthetic inter-block compute barriers (between blocks 3 and 4, zero-based)
only when invoked with --negative-missing-barrier and the software Vulkan ICD.
It expects Khronos synchronization validation to **report an ERROR**, and
never checks the undefined output of this intentionally invalid schedule.
If the validation layer does not detect this hazard, the CI itself fails.
This proves validator sensitivity on the tiny synthetic hazard, NOT
completeness for real learned ViT GPU usage.


## Native vendor translation-unit syntax gate

The isolated workflow r09-min-vit-native-syntax.yml temporarily checks out
vendor research SHA b1bc6b74d22bab1fef36cb2675848a59cb567221 inside
a CI runner without updating the engine submodule gitlink (22b69d6053db).
The existing source-inventory-complete Clang tool then checks six actual
ViT C++ translation units in BOTH experimental-macro configurations. It
generates the real Vulkan SPIR-V headers and uses the maintained production
header overlays. All-owner checks are unchanged unless the explicit
R09_MIN_VIT_NATIVE_TU_DUAL=1 selector is set.

This is a genuine header-integrated syntax test, not a compiled/linkable
PS5 binary or neural GPU execution. The pin remains unchanged.


## QKV exact FP8 capacity — 37.5 MiB nine-buffer candidate

The first 60 MiB ViT pooling proposal retained four-plane Q/K/V buffers
from the original 65-buffer allocator. The real E4M3FN norm producer
CanVitQkvNorm and attention consumer CanVitAttention require exactly
tokens*1024 bytes per Q/K/V tensor, **one plane**, not four.
The separate C++ policy witness test_dlss_nr_min_qkv_capacity.cpp must
prove native BuildVitQkvBatches/ValidVitQkvBatches accept all three
one-plane outputs at 960, 2560 and 4096 tokens, that underallocation by
four bytes is rejected, and that the learned QKV GEMM/normalize number
of batches is unchanged versus the old four-plane outputs. All three
FFN learned projection stage policies retain the original four-plane
scratch space, so their batching is not changed by this capacity trim.

**ViT requested sizes only:** 185 planes -> 15 planes at 1080p:
462.5 MiB -> **37.5 MiB** (~91.9% reduction / 425 MiB).
No runtime gain can be inferred until actual model weights and GPU
residency/frame time are tested on PS5. This DOES NOT make a valid
dynamic 720p neural graph or globally-optimal full-model schedule.
The vendor PR #34 holds the guarded layout change, unmerged, and the
engine native syntax CI pairs with exact vendor revision 6ee5be5a.


## Exact 1080p scratch Pareto frontier (real C++ dispatch policies)

A separate test enumerates **every integer scratch allocation size from
4 through 16 token-planes** for the actual 2560-token 1080p ViT block.
It uses the real native host FFN Expand, Contract, ResidualProjection and
QKV scheduling policies; a configuration is dominated if a smaller memory
budget can schedule no more batches in **any** of those operations.
The resulting non-dominated candidate scratch sizes are 4, 5, 6 and 12
planes (15, 16, 17 and 23 total ViT planes respectively):

| Scratch planes | ViT requested MiB | FFN Expand batches | QKV batches |
| ---: | ---: | ---: | ---: |
| 4 | 37.5 | 4 | 4 |
| 5 | 40 | 4 | 3 |
| 6 | 42.5 | 3 | 2 |
| 12 | 57.5 | 3 | 1 |

The previous **8-plane / 47.5 MiB** proposal is dominated by **6 planes /
42.5 MiB** at **1080p**: both schedule the same FFN and QKV batch counts.
These are per-block source-level counts, not measured runtime. The
three other ViT stages, per-block barriers, attention and overall engine
still require actual model/console qualification. At 720p and 4096 tokens
the Pareto thresholds can differ; this table must not be applied blindly.


## Native compilation qualification for four research scratch modes

The isolated CI runner temporarily checks out exact vendor research commit
64e08c8638358d46b8a9c4edf6096e81db416236, without changing either
repository's main or the pinned vendor gitlink. The maintained native C++
header-integrated syntax harness now checks six real ViT sources under
compile flags 0/1 (12 checks) plus the real nr_rdna2_frame_session.cpp
with scratch profile selection 4,5,6,12 (four additional checks). The
normal all-graph compilation path remains unchanged. This checks actual
native owner source syntax, not linked execution or real GPU model output.


## 720p native route reconstruction (CPU-only, no GPU enable)

The 720p trial rebuilds the 152-row Original and 76-row Compact schedule
in memory at 1280x720, using genuine native geometry and source ABI
classifiers. It recalculates FSwin windows, four learned U-Net upsample
dispatch domains, pre/post grids and Split-Swin dispatch window factors.
The exact NativeNrSchedule, NativeUNetSkipMap, NativeSplitRoutes,
NativeVitRoute and FSwin segmentation policies must all accept it.
The bottleneck is 22x40=880 real raster tiles padded to 960 ViT tokens
(vs 2560 padded tokens at 1080p). GCC/Clang UBSan positive and negative
tests cover both Original/Compact source plans.

Crucial: specialized ViT/decoder launch grids, true model tensor
addressing, the native preflight and all GPU descriptors still require
independent proof. The trial explicitly leaves all specialized
dispatches unqualified, returns GPU_DISABLED and NEVER feeds the plan
into the renderer. This is a CPU structural milestone, not a 720p
DLSS-NR model running on PS5.


## 720p ViT host policies: learned dispatch work and boundary geometry

After the two complete 720p structural route candidates pass, the host
witness test_dlss_nr_min_720_vit_runtime_capacity.cpp checks the REAL
four FFN/QKV projection and attention capacity policies for the 960
padded ViT tokens with all four existing scratch profiles (4/5/6/12).
It verifies GEMM/normalization and projection batch coverage has no
dropped tail and tests negative underallocation of each Q/K/V output.
The genuine ViT tiled repack policy also validates 22x40 logical
raster tiles => 960 padded 4x4 tokens, in BOTH directions, and refuses
undersized input/output allocations. Both Original/Compact variants
must pass GCC and Clang UBSan without any model or GPU submission.

Remaining mandatory: specialized ViT/decoder Vulkan launch dimensions,
the upstream FSwin/Split/token layout transitions, full graph image
comparison, actual 720p model preflight and PS5 GPU measurements.
All candidate GPU admission flags stay false.


## The 720p scratch frontier differs from 1080p

An exhaustive host-only 960-token sweep of genuine ViT scheduling
policies at scratch capacities 4..16 identifies the five
non-dominated 720p scratch choices: **4, 6, 8, 12, 16 token-planes**.
The 1080p choices (4,5,6,12) cannot simply be reused:

| 720p scratch | ViT requested bytes | FFN Expand batches | QKV batches |
| ---: | ---: | ---: | ---: |
| 4 | 14.0625 MiB | 4 | 3 |
| 6 | 15.9375 MiB | 3 | 2 |
| 8 | 17.8125 MiB | 2 | 2 |
| 12 | 21.5625 MiB | 2 | 1 |
| 16 | 25.3125 MiB | 1 | 1 |

Scratch 5 is dominated at 720p; scratch 8 is NOT. The vendor's
current selectable 9-buffer profiles were developed for 1080p and
do NOT yet include the 720p-specific profile 8. Do not treat the
vendor profile selector as 720p-optimal until it is extended and
qualified on a 720p-capable native graph. All numbers are
*requested ViT storage and CPU schedule batch counts*, not PS5 VRAM
residency or actual FPS. A green sweep never sets ready_to_enable_720p.

At 960 tokens, scratch 16 can cover the entire FFN Expand projection
in **one** native batch (the per-batch cap is 1,024), explaining why
this fifth profile is non-dominated at 720p but not at 1080p.
The 16-plane option has not been exposed in the vendor allocator;
this is still a host-only theoretical workload frontier.


## 720p native decoder and skip path: policy checks

A separate full-route host test now drives the genuine
DecoderProjectionBatches, SplitDecoderSkipRepack and DecoderUpsample
contracts at the actual 22×40 bottleneck. It proves the decoder
projects 880 live ViT tokens into a 960-token padded 4×4-tile envelope
in one native GEMM batch, consumes the 3×5 Split-Swin window-major skip,
and fits the learned FP16 projection + skip/upsample buffer bounds.
The test visits all 880 live 4×4-tile offsets and proves they are
unique, leaving exactly 80 tail slots, and rejects undersized
source, scratch, destination and gain buffers. Both Original and
Compact must pass GCC/Clang UBSan.

This is source-policy and host memory geometry validation only:
the actual Vulkan shaders, model weights, complete image composition
and console GPU fences still need qualified 720p A/B checks.


## Cross-repository 720p ViT allocator qualification

The latest vendor research candidate is d5da2b83a8b93e998920bb0b6d448956cc450f00.
The isolated host Clang gate temporarily checks it out in the CI runner
without updating the pinned gitlink and compiles six authentic native ViT
owner C++ units twice (pool off/on) plus frame-session scratch profiles
4/5/6/8/12/16 for a total of 18 translation-unit syntax checks.

Profiles 8 and 16 must fail closed if the model's native ViT route is
NOT 960 tokens. Scratch 16 is the fastest *host-policy batch-count*
candidate at 720p (one FFN Expand batch + one QKV batch), but does NOT
prove actual GPU performance. Only a full model, the guest frame path
and PS5 hardware A/B can establish end-to-end 720p neural fluency.


## 720p native plan serialization and parse round-trip (host only)

The CPU host utility dlss_nr_min_720_plan_emit.h now serializes every
row of the full 1280x720 Original (152 rows) and Compact (76 rows)
candidate back into the SAME 19/21-field native text syntax consumed
by the actual R09 plan parser. It then reparses the entire table,
verifies every single row member is unchanged after round-trip,
and revalidates NativeNrSchedule, all four U-Net skips, both Split-Swin
runs and all eight ViT blocks (960 padded tokens). Both variants and
negative malformed/empty source cases are tested under GCC/Clang UBSan.

The serialized text is a CPU-only DEVELOPMENT CANDIDATE, NOT a runnable
replacement model plan: some specialized launch fields remain from the
1080p reference and have NOT yet been qualified for 720p. Its
gpu_executable flag is hard false, and no native renderer, weights
or source/target Vulkan dimensions have been modified.


## Exact 720p GPU launch blockers — enumerated rather than assumed

The host route qualification now checks the original reference against the
full 720p candidate and records **41 specialized native-plan rows** whose
launch-grid fields were deliberately not rewritten: 8 blocks × 5 ViT
operations = 40 rows (FFN Expand, Contract, QKV, Attention, Projection),
plus 1 DecoderUpsample row. Every one retains the inherited 1080p launch
grid even though its token count and geometry have changed. Both 152-row
Original and 76-row Compact schedules must have this same breakdown.

The ViT implementations separately derive many native Vulkan dispatches
from the validated 960-token route and their own stage policies; the stale
serialized row grids are **not alone proof of an out-of-bounds GPU access**.
But no complete PS5 GPU integration proof exists for the 720p plan, so the
candidate stays disabled. Future tests should focus on the exact ViT stage
owner/descriptor dispatches, DecoderUpsample, input/output resolution and
full model image rather than repeating structural-route validation.


## 720p neural-then-FSR output contract (host-only)

The native presenter `headless/vulkan_present_layer_r24.cpp` has NOT been modified by this PR. It currently runs spatial FSR **before** the R09 neural stage, explicitly rejects concurrent upscale filters with `nr_exclusive`, and creates the R09 output image at **1920x1080**. This is not an executable post-neural 720p path. Merely changing the image extent or allowing both filters to be selected would be unsafe.

- New isolated C++ host contract `extras/graphics/dlss_nr_min_720_present_handoff.h` / `test_dlss_nr_min_720_present_handoff.cpp`: validates the intended order **NR compute -> compute-to-fragment visibility -> FSR EASU -> FSR RCAS -> final present**, independently for **1920x1080**, **2560x1440** and **3840x2160** targets, plus **22 negative ownership/shape/ordering/fence cases**. It requires FSR to consume the SAME real neural `VkImage` **and** `VkImageView`, not the previous guest image coupled to a neural view. This is only abstract host-state verification, not an attached VkCommandBuffer.
- `test_dlss_nr_min_720_present_owners.py` audits actual Encore presenter plus the *pinned vendor* FSR and `NrRdna2NoHistoryPresent` source, including a native compute-to-fragment barrier, per-slot scheduler retirement, real EASU/RCAS order and both output formats. Deliberate source mutations must fail the guard. Native `FSR::Draw` takes a source image **and** image view; its two pass-owned output surfaces are **RGBA16F**. Neural R09's output surface is **RGBA32F**. Existing FSR here is **spatial EASU/RCAS**, not FSR 3 frame generation; image-quality/HDR precision must be compared on hardware before any activation.
- `dlss_nr_min_720_post_fsr_bytes.h` / matching host test account **nominal image bytes only** for a 720p RGBA32F neural output plus EASU and RCAS RGBA16F output surfaces. For an illustrative **three-slot** presentation, the totals are **143,769,600 bytes (1080p)**, **221,184,000 bytes (1440p)**, **442,368,000 bytes (4K)**. At 4K this is **147,456,000 bytes (140.625 MiB) per slot**, **421.875 MiB across three slots**. The model excludes guest/swapchain, learned activations, model weights, memory tiling and allocator padding, so it is not measured VRAM. Actual slot counts and free reserve must be measured on PS5. The code rejects impossible sizes and slot counts and has no runtime-enable path.
- The next production-level tasks are precise and still open: **(1)** validate all genuine learned Original GPU operations and allocations at 720p with private user-supplied model weights, **(2)** add a post-neural FSR surface owner with the correct image and view, no pre-neural FSR, per-slot lifetime/fence and fallback, **(3)** verify compatibility of sampled RGBA32F input and two RGBA16F FSR renderpass outputs with HDR/quality tests, **(4)** measure per-title GPU frame time/VRAM on the physical PS5 and compare 720p->1440p/4K against the existing 1080p path.

All new code is still **research-only and runtime hard-disabled**. No changes to `main`, vendor pin, guest NS1/NS2 renderer, user model import, or PS5 build.


### Source-level 720p residual-dimension sweep — 264 source files

The **pinned vendor** SHA is `22b69d6053db41b74edac2633c012f925b84f69e`. This pass read exactly **73** `nr_rdna2_*.cpp` native implementation files, **107** `nr_rdna2_*.h` native Vulkan header files, and **35** active `r09_rdna2_nr/*.comp` compute shaders. It also read **49** host engine `extras/graphics/rdna2_nr_*.h` native policy headers on this experimental PR: **264 files total**.

A targeted literal scan for `1920`, `1080`, `2560`, `2160`, `1980`, `33u`, `60u`, `33x60`, `880u` and `960u` found **no matching executable-code line** among the 264 inspected files. Remaining matches are old-shape comments in `nr_rdna2_native_decoder_link.cpp`, `nr_rdna2_preblock_run.cpp`, `nr_rdna2_unet_upsample_link.cpp`, `rdna2_nr_decoder_upsample_policy.h`, `rdna2_nr_vit_attention_policy.h`, `rdna2_nr_vit_native_route_policy.h`, and `decoder_upsample_rdna2.comp`. This is **a reproducible targeted literal review, not a proof of model correctness**: constants can be encoded indirectly and tensor layouts/learned layer assumptions may still require source-specific 720p tests. The production presenter is outside those groups and **does** hard-code 1920x1080. The neural attention shader is token-count-parametric but states explicitly that its FP16 reduction order is not bit-equivalent to the original proprietary implementation. Neither observation replaces authentic image comparisons.

### 720p attention throughput arithmetic (not a performance test)

For the currently verified **eight full global-attention ViT blocks**, the original scalar QK and context matrices each require approximately `heads × tokens² × head_width` FMAs. Using 32 heads and width 32 for the eight blocks yields **107,374,182,400 FMAs/frame at 2560 padded tokens (1080p)** versus **15,099,494,400 FMAs/frame at 960 padded tokens (720p)**, or **14.0625% of the original scalar attention FMAs**. Counting two floating-point operations per FMA gives **30.199 GFLOPs per 720p neural frame** for those attention products, or **1.812 TFLOPs/s at 60 neural frames/s for attention alone**. These figures exclude every other learned operator, dispatch overhead, buffer traffic, cache pressure, FSR EASU/RCAS, the Switch GPU workload and console scheduling. They are not measured RDNA2 throughput, an FPS estimate, or proof of 60Hz viability. The tiled shader reduces shared-memory load duplication, not the quadratic FMA count.

## 720p native owner graph and session allocation audit

Host-only **full row-owner audit** now assigns each emitted 720p native row to exactly one policy owner: **Original 152 = pre(1) + FSwin(44) + Split-Swin(65) + ViT(40) + Decoder(1) + post(1)**; **Compact 76 = pre(1) + FSwin(16) + Split-Swin(17) + ViT(40) + Decoder(1) + post(1)**. All rows are counted once, with zero omissions or duplicates. The test uses the real `ExtractNativeFSwinSegments`, `BuildNativeSplitRoutes`, and `BuildNativeVitRoute` on reconstructed 720p shapes. This proves structural owner assignment, not that every learned operator is ready or GPU-recorded.

**Real unpooled allocation contracts** are checked with source-linked tests against the engine's *pinned* vendor SHA `22b69d6053db41b74edac2633c012f925b84f69e`. The FrameSession external estimator mirrors `State::Make`, split/bottleneck and pre/down/up/post creation; it refuses drifts through **11 deliberate unsafe source mutations**. A second estimator mirrors all FSwin-layer `NrRdna2FSwinGpuTensors::Initialize` requests, including the actual C32 middle-buffer skip and the Q/K/V views **aliasing** the expanded buffer; a separate source guard requires those real native contracts and tests **9 unsafe mutations**.

| Nominal 720p allocations per frame-session slot | Original | Compact |
| --- | ---: | ---: |
| FrameSession external buffers | 263 / 622.227 MiB | 137 / 546.289 MiB |
| Independently owned FSwin layer buffers | 256 / 1,046.25 MiB | 92 / 455.625 MiB |
| Additional 4K NR RGBA32F output + two FSR RGBA16F surfaces | 140.625 MiB | 140.625 MiB |
| **Subtotal per slot** | **1,809.102 MiB** | **1,142.539 MiB** |
| **Subtotal for 3 illustrative simultaneous frame slots** | **5,690,941,440 bytes** | **3,594,117,120 bytes** |

These are the **nominal requested sizes of these specified independent buffers**, not PS5 peak measured VRAM, not measured GPU residency, and **not the total complete-model memory requirement**. We intentionally EXCLUDE GPU model weights, FSwin per-layer weight staging/upload, downsample/upsample adapters, intermediate staging images, other adapter allocations, guest and swapchain images, VMA tiling/padding, emulator/game/OS allocations and texture memory. The native 3 GiB `State::Make` cap applies only to its own external buffers and cannot bound all separately allocated FSwin resources. Native shader execution, model weights and full frame quality are not proved. The output upscale remains completely unwired.

Most importantly, optimizing only the ViT pool in experimental **vendor PR #34** will **not** solve the full session memory cost. On its separately tested 960-token opt-in profile, nine buffers at scratch=4 require **14.0625 MiB** instead of legacy **173.4375 MiB** for the ViT part, saving **159.375 MiB per slot** in a hypothetical compiled research configuration. This savings must NOT be represented as present in the engine's pinned vendor: neither the pin nor the production mode was changed. The **FSwin allocations** are a larger independent optimization target. Pooling FSwin buffers requires a distinct live-handle/descriptor/transfer-barrier proof because layers intentionally own separate `MemoryUsage::Upload` and `MemoryUsage::DeviceLocal` buffers and the scheduler copies output to the next layer input. Blind aliasing would be unsafe.

Current evidence: no trained Original model GPU session executing at 720p, no authentic image A/B, no measured PS5 VRAM or frame time, no finished post-neural EASU/RCAS renderer handoff. Both PRs stay draft and the PS5 runtime remains hard-disabled.


## FSwin scratch pool — isolated native vendor PR #39

The previously dominant per-FSwin-layer tensor cost has a **separate isolated solution candidate**, [vendor draft PR #39](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/39), branch `research/r09-fswin-chain-scratch-pool`. **Engine pin stays at `22b69d6053db41b74edac2633c012f925b84f69e`; this branch is NOT integrated or enabled.** It maintains each layer's private host-writable Input buffer and GPU-local Output buffer, while allowing the expanded/middle/contracted/context buffers to be reused strictly among sequential layers of the **same FSwin segment**, with private GPU weights, Q/K/V descriptors and eight distinct chain owners. The experimental compile macro `EDEN_R09_MIN_FSWIN_SCRATCH_POOL_EXPERIMENTAL=1` is OFF in normal builds.

| 720p FSwin logical buffer requests | Original, 44 layers | Compact, 16 layers |
| --- | ---: | ---: |
| Maintained independent owners | 256 buffers / 1,046.25 MiB | 92 buffers / 455.625 MiB |
| Research chain-local pooled owner | 118 buffers / 419.0625 MiB | 62 buffers / 281.5625 MiB |
| **Unverified physical-VRAM savings candidate** | **627.1875 MiB per frame slot** | **174.0625 MiB per frame slot** |

The source-locked vendor CI [#42938153680](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42938153680) compiled **all three actual FSwin native C++ translation units under macro OFF and ON**, with the real Encore engine headers and a temporary vendor checkout in CI only. Native tensor and descriptor functions extracted into stubbed Vulkan tests also passed. **Genuine Vulkan 1.1 Lavapipe host** ran two synthetic sequential layers with one borrowed VkBuffer, verified exact readback, saw zero Khronos positive-path errors, and correctly reported the intentionally unsynchronized scratch-transfer hazards. Additional [CI #42939379907](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42939379907) verified **8 independent scratch segment owners and all 44 Original-shaped / 16 Compact-shaped synthetic GPU outputs** with zero positive Khronos hazards and a detected negative. These are *numeric synthetic host* witnesses, NOT the learned layer's real shader execution and NOT a PS5 model frame.

Assuming this vendor optimization someday passes authentic graph/console tests, the previously listed Original nominal 4K-presentation subtotal for **one slot** would fall from **1,809.102 MiB to 1,181.914 MiB**, Compact from **1,142.539 MiB to 968.477 MiB**. It would still EXCLUDE actual trained-model weights and numerous other allocations, so no total VRAM budget or 60 FPS viability can be inferred. The separate ViT pool [vendor PR #34](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/34) may provide additional savings; neither experimental branch is pinned, and they must not be combined until separately qualified.

**Still blocking completion:** authentic trained FSwin shaders with borrowed descriptors and segment adapters, true 152-stage Original neural GPU image at 720p, neural output after which a real Vulkan EASU+RCAS upscaler produces the 4K presentation, PS5 physical frame-time/VRAM and numerical image quality A/B and a safe fallback. Do not claim completion until these are independently demonstrated.
