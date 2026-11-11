# R09 universal render graph — deduplication + coverage register
Date: 2026-11-11. Research PR #43 only; PS5 runtime remains **OFF**.

## Existing implementation audit: DO NOT DUPLICATE
| Concern | Real existing owner | Treatment in R09 |
|---|---|---|
| FXAA / FXAA+ / SMAA Ultra and spatial FSR1 / SGSR / SGSR Edge | Merged graphics PR #24; `headless/vulkan_present_layer_r24.cpp`; existing GLSL shaders | REUSE actual shader ids and `Kind::{AntiAlias,Spatial}`, don't introduce replacement Vulkan passes |
| Default global/game values, two UI themes and catalog | Merged PR #30; `headless/prosperoeden/pe/ui/video_presets.hpp`, `headless/neural_video_policy.h`, `headless/encore_overrides_runtime.h` | KEEP launcher policy; no second menu, new IDs or persisted user profile |
| Explicit R24 guest/forced MSAA guards | `extras/graphics/msaa_force_policy.h`, R24 shadow pass | Source `RasterAa` only. Forced MSAA still unqualified, not an image AA filter |
| A4K/Original model ownership and 720p plan | Existing R09 engine + maintained vendor | Planner methods 1–4 only; 5=Compact excluded until actual independent GPU proof |
| Spatial Vulkan ownership, FSR1+SGSR pairs | `native_spatial_chain_policy.h`, native owners and 3-pass Vulkan witness | REUSE. Do not rewrite or substitute the true GPU shader operations |
| FSR1 RCAS 0–100% and SGSR sharpness | `fsr1_sharpness_policy.h`, `sgsr_sharpness_policy.h` | Existing per-filter shader PARAMETER, not an extra always-on sharpening pass |
| FrameGen providers and cadence/histories | `framegen_capabilities.h`, `framegen_present_gate.h`, Mihawk/FSR3/LSFG owners | Existing capability gate. FG needs 2 real composed frames and display headroom |
| Source/game resolution, anisotropy, docked/handheld, output TV resolution and Hz | Settings/renderer/preset catalog | Independent source/presentation controls; **not** automatically inserted full-screen compute stages |
| Neural, post AA, spatial, FG ORDERING and native handle ownership | `neural_pipeline_composer.h`, `neural_pipeline_recipe.h` (research) | Single ordered topology engine; no separate competing pipeline |

**No competing universal path optimizer existed.** The old
`test_graphics_pipeline_policy.cpp` references a currently missing
`graphics_pipeline_policy.h` and is not proof of a live native graph.
No second graphical feature implementation was added.

## All optional stages — explicit finite catalog
A path is an **ordered** sequence of:
- Neural (0 or 1, real 1=A4K detail,2=soft,3=denoise,4=Original),
- Spatial (0 or more, native methods 0..6, repetitions and order matter),
- Post AA (0 or more, 1=FXAA,2=SMAA Ultra,3=FXAA+),
- Compose real frame (0 or more, mandatory before each FG),
- FG (0 or 1, 1=MihawkGen,2=FSR3 optical flow,3=LSFG),
- final Present (always required, including an otherwise EMPTY pipeline).
The absence of NR/AA/Spatial/FG is a real supported research topology.
**Never insert an 'Off' stage**: omit the pass completely to avoid
allocation/work. Repeated AA or redundant spatial passes may be allowed
by the topology, but are NOT recommended as a quality/performance gain.
NR AFTER FG, duplicate NR, duplicate FG, FG without a composited
pair, missing history/HUD and non-identity AA resize fail closed.
Stage ordering cannot be freely optimized without color/quality A/B.

Original NR **requires 1280×720**, A4K 2× requires true size scaling,
and Compact is NOT silently relabeled as Original. Future 540p modes
and temporal FSR3.1 require distinct model/graph/history proof.

## New exhaustive host-only tests
`test_neural_pipeline_universal_paths.cpp`:
- Every ordered word from the five types up to **6 processing steps**,
  including zero steps and duplicate stage types:
  1+5+25+125+625+3125+15625 = **19,531 sequences**. An independent
  oracle verifies admission/rejection; all **16** masks of optional
  NR/Spatial/AA/FG have at least one valid representative.
- **20,480** method/placement combinations:
  Neural {Off,A4K 1/2/3,Original}, AA {Off,FXAA,SMAA,FXAA+},
  first and second Spatial {Off,seven real IDs},
  FG {Off,three methods}, AA position {4 legal slots}.
  Includes unadorned present, AA-only, two spatial passes, no NR and
  post-FG AA handling, plus 720p/1440p/4K NR-free input modes.
- Versioned recipe `StageEvidence` now requires the **native owner**
  (not a user-saved flag) to attest that a post-FG spatial/AA pass
  processes BOTH real and generated streams.

This is **finite and exhaustive within that declared search domain**.
It does not claim every arbitrary n-pass graph, true GPU rendering or
all hardware-specific quality/format combinations are already proven.

## Path selection without fake FPS
`neural_pipeline_path_selection.h` chooses only between qualified
alternative RECIPES with measured physical-PS5 GPU frame time and peak
GPU memory, verified per-stage GPU trace, output-quality A/B, valid
native image+fence bindings and proven presentation/fallback. No
quality-preserving reordering is inferred automatically; recipes with
the exact same version/source/MSAA/ordered methods/extent are
**deduplicated**. Wrong output size or missing GPU budget is rejected.
The return status is **ResearchWinnerOnly** even with all measurements:
it never sets the PS5 runtime enable flag.

Do not confuse 60/120 Hz display output with real guest frame rate
or synthetic frame interpolation. Refresh, dynamic resolution, crop,
source-vs-output format, HDR/SDR/linear and alpha, HUD composition,
motion vectors/depth/jitter, real GPU queue barriers, shader memory,
and model/FG history must be audited as separate NATIVE prerequisites.

## Explicitly not covered / remaining engineering
- **No current PS5 general graph executor** for arbitrary AA↔NR↔FG
  order, true image views, descriptor ownership, shared scheduling or
  life-cycle. Existing shipping renderer still suppresses FXAA/SMAA
  when DLSS-NR is active.
- HDR/SDR transforms, pixel format, alpha, tone mapping, full crop /
  non-16:9 guest framebuffer; `ValidExtent` intentionally constrains
  research tests to 16:9. Require real owner+color-space validation.
- TAA and FSR3.1 temporal scaling: no generic verified guest
  depth/motion/jitter history for every title. Not interchangeable with
  FSR1 spatial or FSR3 optical-flow FG.
- 540p or arbitrary-resolution neural, DLSS-NR Compact 76-op and
  repeated / stacked *neural* engines need their own authentic GPU proof.
- Forced MSAA 2×–16×: guest rendering/resolve/format memory ownership
  is not yet broadly qualified, even if source policy tests accept
  hypothetical evidence.
- User-specified RCAS/SGSR sharpness and NR strength must be validated
  as PASS PARAMETERS; they must not become duplicate full-screen
  sharpening stages or unauthorized weights.
- Dynamic game-scale, 30/60 game FPS, 60/120 output Hz, refresh/VRR,
  frame pacing, menu pauses, HUD/subtitles changes, drops/scene resets,
  and interpolated-frame latency need real measurement and reset rules.
- Multiple GPUs/queues, three-slot VRAM lifetime, resize and shutdown,
  CPU fallbacks, automatic memory pooling, operator FP16/FP32 accuracy,
  shader/barrier validation, learned 152-op 720p output and measured
  PS5 stability/quality remain independent qualification gates.

No `main` merge, production gitlink change, PS5 native build or
launcher change is authorized by these research-only checks.
