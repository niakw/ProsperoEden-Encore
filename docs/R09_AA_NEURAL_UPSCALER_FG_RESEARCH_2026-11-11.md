# R09 — Anti-aliasing × Neural × Upscaling × Frame Generation
Date: 2026-11-11. Research-only, PR #43. **PS5 runtime remains OFF.**

## Actual renderer today, not hypothetical pipeline
- `headless/vulkan_present_layer_r24.cpp` applies ONE of FXAA / SMAA Ultra
  (FXAA+ selects a separate FXAA quality shader) **before** native spatial
  FSR/SGSR; no free selectable post-FG pass exists.
- `headless/neural_video_policy.h::EffectiveAntiAliasing` intentionally
  suppresses screen-space AA while DLSS-NR Original/Compact is selected.
  Do not relax this launcher protection without a native Vulkan renderer
  owner, pass lifetime/fences, performance and image-quality proof.
- Guest-requested multisample raster targets are part of the renderpass;
  native forced MSAA X2/X4/X8/X16 is unfinished research. MSAA is NOT
  representable as an image-space FXAA/SMAA pass.
- No general guest-wide TAA or motion/depth history source is qualified.
  FSR 3.1 temporal image reconstruction is not interchangeable with FXAA.

## Proposed independently ordered image-space stages (planner v3)
The `Kind::AntiAlias` stage has unchanged input and output resolution,
requires a **distinct real** output image + image view, compatible queue,
producer/consumer barrier, and lifetime until GPU fence retirement.
Methods: 1=FXAA, 2=SMAA Ultra, 3=FXAA+; None means omit the stage.
Codes 4..7 (forced MSAA) and 8 (unqualified TAA) are rejected as post
stages. Source raster `RasterAa::{GuestNative,ForcedX2,...,ForcedX16}`
is a *separate*, pre-neural source property and requires actual
raster-owner/resolve, guest-attachment, format/sample, fence proof and,
for forced modes, measured frame memory/time headroom.

Candidate order examples (not operational PS5 renderers):

- Guest raster -> optional **resolved MSAA** -> **FXAA** ->
  Original 720p -> FSR1 4K -> compose -> present.
- Guest raster -> Original 720p -> **SMAA Ultra** -> SGSR 4K ->
  compose real frame -> MihawkGen -> present.
- Guest raster -> A4K 2× (1440p) -> FSR1 4K ->
  **FXAA+** -> compose -> FSR3 flow FG -> present.
- Guest raster -> FSR1 -> compose real frame -> LSFG ->
  **SMAA Ultra on BOTH real and synthetic frames** -> present.
- Guest raster -> Original -> **FXAA + SMAA + FXAA+** ->
  spatial -> compose -> present is permitted by the experimental topology
  but is **not recommended without image A/B**: repeated AA can blur
  UI, thin lines and fine detail, and the GPU costs add.

**Critical order rules:** image AA may not resize; FSR1/SGSR may not
downscale; model R09 Original 720p only receives 1280×720; neural pass
may not run on generated frames; frame generation requires two
composited real-frame histories and validated HUD policy; any pass
AFTER FG must transform both image streams at matching extents.
A compositor/Preset MUST NOT substitute a fake image, owner, sample-count,
queue barrier, GPU fence, model weight, or measured VRAM budget.

The serialized, research-only `neural_pipeline_recipe.h` schema is
**version 3**, so previous v1/v2 recipes require explicit migration. Each Original NR / FSR1 / SGSR stage may inherit the existing intensity/sharpness (-1) or use an independent 0–100% value; two identical shader methods with different values are **not** duplicate recipes. No new sharpening shader is introduced.
It stores logical method/order/resolution and source MSAA selection,
not driver evidence or Vulkan handles. Actual `Bindings` from a native
stage owner are mandatory. The complete `Plan` still forces
`kComposablePs5RuntimeQualified=false`, even for every positive test.

## Host qualification
`extras/graphics/test_neural_pipeline_aa_composer.cpp` enumerates
2 neural modes × 3 post-AA methods × 7 spatial methods × 3 frame
generation choices × 4 AA placements = **504** planner permutations.
Also checks stacked AA, unqualified TAA, invalid AA resize, MSAA-as-post,
missing post-FG real/synthetic coverage, stale VkImage identifiers,
missing barrier/fence and five distinct source MSAA types with
successive fail-closed missing-proof scenarios. Run together with
existing composer/recipe suites on GCC and Clang, UBSan enabled, in
`.github/workflows/r09-composable-pipeline-host.yml`.

**This test does not run FXAA/SMAA/FXAA+ on a physical GPU**, does not
connect a real framegen stage, and does not establish DLSS-NR 152-stage
output or PS5 performance. The existing Vulkan GPU spatial witness
is separate evidence for chained FSR1/SGSR, not for these AA passes.
No runtime stage activation, SDK import, vendor pin move, PS5 build,
main merge, or release.
