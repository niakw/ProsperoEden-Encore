# Eden Encore — isolated A4K Neural Rendering → Spatial Scaling → Frame Generation bridge

**Status:** 11 November 2026, host source and native C++ interface **qualified**, **not** activated on PS5, **not** a rendered combined GPU frame. Engine [draft PR #43](https://github.com/niakw/ProsperoEden-Encore/pull/43), additive vendor [draft PR #40](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/40). Both remain isolated and unmerged. The production `vendor` gitlink on Encore stays `22b69d6053db41b74edac2633c012f925b84f69e`, and no PS5 build was requested.

## Common frame topology

```text
Real game source (example 1280×720; actual VkImage + VkImageView)
  ├─ Neural Rendering = A4K Details / Soft / Denoise:
  │      maintained MIT Anime4K3D Vulkan CNN (4 / 8 / 5 native stages)
  │      source 1280×720 → genuine native A4K x2 image at 2560×1440
  │      GPU compute→fragment read barrier; maintain image + view owner
  │
  └─ Neural Rendering = DLSS-NR Original:
         authenticated model + 152 GPU plan rows (full GPU not yet proven)
         source 1280×720 → neural output 1280×720
         GPU compute→fragment read barrier; maintain image + view owner

  → Spatial filter chosen independently:
       0 Bilinear — native presentation sampler
       1 FSR 1 — EASU then RCAS
       2 Bicubic — native presentation filter
       3 Nearest — native presentation sampler
       4 Lanczos — native presentation filter
       5 SGSR — native Vulkan graphics pass
       6 SGSR Edge — native Vulkan graphics pass
     Target: 1920×1080 / 2560×1440 / 3840×2160
     NOTE: A4K 720p→1440p then 1080p is a DOWNSCALE, not extra upscaling.

  → Actual composed real frame + HUD/crop ownership
  → Frame Generation [Off | MihawkGen | FSR 3 optical flow | LSFG]
       (only after validated real-frame pair, GPU fences, provider readiness)
  → Final PS5 presentation
```

**Neither A4K nor the selected spatial filter is a frame generator.** MihawkGen, FSR 3 Optical Flow and Lossless Scaling only interpolate between **actual completed real frames**, and do not make the neural pass cheaper or the emulated game run faster. A4K already scales 2×, so an additional spatial pass is potentially redundant at 1440p and increases GPU workload and temporary image residency.

## Code actually modified

- `headless/neural_runtime_state.h` and `headless/main.cpp`: retain **all five** selected Neural Rendering IDs (A4K modes 1/2/3; DLSS-NR Original/Compact 4/5) in `NeuralRuntime::Current()`. The normal A4K selection still uses its existing internal native shader filter; no second A4K instance is created in normal PS5 runtime.
- `headless/vulkan_renderer_r08.cpp` and `extras/graphics/dlss_nr_min_720_framegen_bridge.h`: effective frame-generation selection now rejects stale Mihawk/FSR3/LSFG settings for **A4K and DLSS-NR** until actual combined-frame evidence exists.
- `extras/graphics/dlss_nr_min_720_spatial_bridge.h`: all seven stable user filter IDs supported as independent candidate passes for A4K **2560×1440** and DLSS Original **1280×720**. The output image identity, sample extent, operation order, compute→fragment visibility, original guest source, queue/fence lifetime and downscale cases are explicit.
- `headless/vulkan_present_layer_r24.h/.cpp`: optional **separate** A4K neural owner, so the selected FSR, SGSR or native display sampler can remain independent. Under experimental macro `EDEN_R09_A4K_DUAL_IMAGE_RESEARCH=1`, a guarded path calls the vendor research `Anime4K3D::DrawFrame`, confirms the **real A4K output image AND view**, records a per-image compute→fragment barrier, and then feeds that exact image to the existing FSR/SGSR or native presentation pass. If this path rejects a frame, restore the original guest image and crop. This macro is **not defined by production PS5 CMake**, and the two independent runtime constants `kA4kNeuralToSpatialRuntimeQualified` and `kPostNeuralSpatialRuntimeWired` remain **false**.
- Additive vendor PR #40 extends the maintained `Anime4K3D` owner with `DrawFrame()`, returning a **non-owning** `{VkImage,VkImageView,VkExtent2D}` for the real 2× output only after the existing `Draw()` succeeds. The original `Draw()` API and its production implementation are unchanged. The owner must stay alive through the last dependent spatial GPU tick.
- `NeuralVideo::CheckSelectable` and user menus currently **reject simultaneous NR + secondary scaling/FG**. This is intentional and must remain until the feature passes actual GPU benchmarks and physical PS5 safety testing. A host candidate does **not** imply that a user can enable it today.

## Evidence and coverage

- [Engine R09 host CI #42953749056](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42953749056): **GREEN**, GCC and Clang host tests. Spatial candidates: 21 DLSS Original + **63 A4K** (three A4K modes × seven spatial filters × three output resolutions), including 21 explicit A4K→1080p downscale cases; 30 negative safety cases. Framegen candidates: **189** (3 A4K × 7 spatial × 3 Mihawk/FSR3/LSFG × 3 output resolutions) — host eligibility and pacing only. All checked candidates keep `runtime_executable=false`. A4K and DLSS mode tracking checks green.
- [Engine isolated A4K C++ CI #42953749178](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42953749178): **GREEN**, compiling the actual research vendor `anime4k_3d.cpp` and the real renderer translation unit with the A4K output-hand-off research macro **OFF and ON**. The vendor draft PR #40 was checked out in the ephemeral CI workspace; engine gitlink remained unchanged. The 13 shader headers for this compilation are **syntax-only placeholders**, not executable Vulkan shader validation.
- The established A4K shader pipeline is real and pinned to upstream MIT weights, but **neither host CI runs an actual A4K→FSR/SGSR composited GPU frame**, nor real Mihawk/FSR3/LSFG generation after such an A4K frame. The PS5 runtime switch is intentionally OFF. Host tests are not device VRAM/FPS/quality benchmarks.

## Conditions before exposing combinations in the UI

1. Record **real A4K→FSR1/SGSR/SGSR-Edge and native-sampler output** on Vulkan, with true shader modules (not syntax placeholders), correct A4K output image ownership, and pixel readbacks at 1080p, 1440p and 4K.
2. Verify all **three A4K CNN profiles** independently, including compute→graphics barriers, negative synchronization fixtures and resource retirement when a frame drops, the guest resolution changes, or the filter fails.
3. Quantify A4K's per-slot transient memory, extra scaler images, input/output formats, actual display frame time and distortion/oversharpening; confirm 1440p→1080p is handled as downscaling.
4. Qualify each MihawkGen, FSR3 optical and LSFG provider **after the real composed frame**, with real completed history frames, native LSFG shader extraction, HUD segregation, GPU fences, VRAM budget and no misleading synthetic FPS claims.
5. Only then modify UI selection restrictions and introduce user-visible compatibility presets. Verify on a physical PS5 at 60/120 Hz; keep safe fallback and normal A4K-only behavior if any check fails.

**Nothing here establishes 60 FPS or 4K neural-frame performance on PS5, and nothing has been merged into either `main`.**
