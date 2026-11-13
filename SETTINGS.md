# Prospero.Eden Encore — Settings guide

> **Exactly the 31 official PS5 system language/region choices; 31 launcher translation catalogs (including en-US and en-GB):** [Language directory](LANGUAGES.md). No extra launcher languages are exposed. This strict policy follows [Sony's official console-language list](https://www.playstation.com/fr-fr/legal/language-support/); translation/font quality still requires validation.


This guide explains the settings exposed by Encore on PS5, their defaults, and practical starting profiles.

> **Important:** TV output and Game resolution are different. TV output is the final image sent to the display. Game resolution is the internal Switch render scale before scaling.

## Factory defaults

A clean Encore configuration starts with:

| Setting | Default |
| --- | --- |
| Renderer | **Vulkan** |
| Video preset | **Recommended** |
| TV output | **1440p** |
| Game resolution | **1.25x** |
| Upscaling filter | **FSR 1 (spatial)** |
| FSR sharpness | **50%** |
| Texture filtering (anisotropy) | **4x** |
| Frame Generation | **Off (extra)** |
| Neural Rendering | **Off (extra)** |
| DLSS-NR intensity | **100% stored, inactive when NR is Off** |
| Anti-aliasing | **FXAA** (Recommended) |
| Refresh rate | **60 Hz** |
| FPS overlay | **Off** |
| Console mode | **Docked** |
| Stick deadzone | **8%** |
| Vibration | **100%** |
| Detailed logging | **Off** |
| Language | Seeded from the PS5 system language on first setup |

A clean configuration starts on the authored **Recommended** tier. Selecting another Video preset rewrites the video settings owned by that tier; manual edits become Custom when they no longer match an authored profile.

## Video presets

| Preset | Renderer | TV output | Game resolution | Filter | FSR sharpness | AA | Refresh |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| **Minimum** | Vulkan | 1080p | 1x | Bilinear | 50% | None | 60 Hz |
| **Recommended** | Vulkan | 1440p | 1.25x | **FSR 1** | 50% | **FXAA** | 60 Hz |
| **High** | Vulkan | 2160p | 1.5x | Bicubic | 50% | **FXAA** | 60 Hz |
| **Ultra** | Vulkan | 2160p | 2x | Bilinear | 50% | None | 60 Hz |

Presets are real starting points, not labels. They are generated from `encore-overrides`, and a title-specific profile can refine a tier without changing the global choice. After applying one, every advanced row can still be changed manually. If the resulting combination no longer matches an authored tier, Encore shows **Custom** (`Personnalisé` in French); matching a tier again restores its label automatically. The same behavior applies to per-game overrides.

## Video settings

### Renderer

- **Vulkan — default/recommended.** Main PS5 renderer.
- **OpenGL.** Compatibility fallback for a title with a Vulkan-specific problem.

Do not use OpenGL only because a title is slow unless Vulkan is known to be the cause.

### TV output

Available: **1080p, 1440p, 2160p**.

This is the final output surface. It is not the internal game resolution. A 2160p output can look cleaner on a 4K TV, but it also increases presentation and bandwidth work.

For demanding titles, 1080p or 1440p is the safer starting point even on a 4K television.

### Game resolution

Available:

**0.25x · 0.5x · 0.75x · 1x · 1.25x · 1.5x · 2x · 3x · 4x**

- **1x.** Native Switch render scale and a useful lighter manual choice.
- **0.75x.** Useful performance compromise, especially with FSR.
- **0.5x / 0.25x.** Emergency performance or diagnostic values; visibly softer.
- **1.25x — Recommended tier.** Moderate supersampling while keeping sensible PS5 headroom.
- **1.5x.** Higher-quality supersampling for titles with spare GPU headroom.
- **2x and above.** Expensive in GPU time and graphics memory; not normal PS5 defaults.

Docked and Handheld modes can also change what the game itself chooses to render.

### Upscaling filter

- **Bilinear.** Lightest general-purpose scaler, useful as a manual fallback or when using a Neural Rendering mode.
- **AMD FSR 1 — Recommended default (spatial only).** Particularly useful when Game resolution is below TV output; this is not temporal FSR 3.1.
- **Bicubic.** Sharper conventional scaling.
- **Nearest.** Mainly useful for pixel-art or diagnostics.

### FSR sharpness

Range: **0–100%**, changed in 5% steps. Factory value: **50%**.

Higher is not automatically better. Too much sharpening can make grass, hair, crowds and thin lines look noisy or grainy.

Useful starting points:

- **40–55%** for 0.75x with FSR;
- **25–45%** if the image looks grainy;
- increase only when the image is clearly too soft.

### Anti-aliasing

The same **Anti-aliasing** row in Quick settings, Settings > Video and Library > Game settings now exposes the eight already-persisted values: **None, FXAA, SMAA Ultra, FXAA+, MSAA 2x, 4x, 8x and 16x**. The last five are Vulkan-only. There is **no separate MSAA multiplier** option. This restores menu/schema parity; it does **not** qualify native forced-sample Vulkan passes. A stored MSAA index is not proof of an actual multi-sampled game frame or a graphics fix. The renderer's forced-MSAA pipeline remains subject to the explicit R24 native hardware gate.

- **None — fastest manual choice.**
- **FXAA — Recommended preset.** Light smoothing with a small clarity trade-off.
- **SMAA.** Better edge quality, but use it only when performance headroom remains.

### Refresh rate

- **60 Hz — default/recommended.**
- **120 Hz.** Requests a 120 Hz output mode when the display supports it.

120 Hz does not turn a 30 FPS game into a 120 FPS game. Encore exposes optional frame-generation choices (MihawkGen, FSR 3 optical flow and LSFG with a user-supplied DLL), all **Off by default**. Selection does not mean a generated frame has been validated on PS5. For the separate research paths to improve *real* game FPS and investigate 30→60 **display** FPS via interpolation, see [Performance roadmap](docs/PERFORMANCE_ROADMAP.md). Synthetic FPS must never be presented as native game FPS.

### FPS overlay

**Off by default.** Useful while tuning or diagnosing a title.

### In-game Encore quick overlay (Vulkan)

**Short-click the DualSense touchpad**, not the PS button, to open the purple
translucent in-game quick menu. Use L1/R1 to switch between Game, Graphics,
Controller Mapping and Diagnostics. FPS visibility and bounded detailed logs
can be toggled there instead of using the retired touchpad + R1 FPS shortcut.
Per-game graphics and controller mapping changes are saved for the next launch.
The existing touchpad long hold remains guest Minus when the overlay is closed;
OpenGL games keep their previous guest tap behavior.

Full controls, limits and validation status:
[PS5 touchpad quick overlay](docs/PS5_TOUCHPAD_QUICK_OVERLAY.md).

## Console mode

- **Docked — default.** Usually asks the game for its higher graphics targets.
- **Handheld.** Can reduce the game's own workload and is worth testing on demanding titles.

This is a game-side mode change, not merely a TV-output setting.

## Neural Rendering and Frame Generation — optional extras

Both features default to **Off**. Standard Minimum, Recommended, High and Ultra presets change the spatial/AA/resolution settings without silently enabling neural effects or synthetic frames.

- **Neural Rendering choices:** Off, A4K Détails améliorés, A4K Image adoucie, A4K Image nettoyée, DLSS-NR Original, and DLSS-NR Compact. The A4K family belongs to Neural Rendering, not Upscaling.
- **DLSS-NR intensity:** 0–100% (stored default 100%). Editable only with Original or Compact. It remains saved when selecting A4K or Off; the source catalog does not yet contain measured per-title intensity recommendations.
- **Composition guardrails:** Vulkan only; the currently supported policy requires Bilinear spatial scaling, no concurrent Frame Generation, and no forced MSAA. These conservative limitations must not be mistaken for permanent renderer capabilities.
- **DLSS-NR runtime:** The two models can be selected and persisted, but the full native image graph is not yet proven to render a complete frame on PS5.

The classic Encore and Switch-style visual themes must expose the same extras, including their per-game inherited values. No change to a video preset should turn either extra on without an explicit user action.

## Per-game video settings

Library → Game settings can override the global configuration for one title:

- Renderer
- Video preset
- TV output
- Game resolution
- Upscaling filter
- FSR sharpness
- Anti-aliasing
- Texture filtering (anisotropy)
- Frame Generation (Off/explicit method)
- Neural Rendering (Off/A4K/DLSS-NR)
- DLSS-NR intensity (stored independently)
- Refresh rate
- Console mode

A per-game value of **Default** means “follow the global setting”. Resetting the game overrides returns those rows to the global configuration.

## Controls

Encore exposes four controller profiles globally and per game:

| Profile | Behavior |
| --- | --- |
| **PlayStation** — default | PS-style Cross/Circle menu semantics. In the stock profile, Encore can switch to physical Switch face-button positions during sustained gameplay input and return to menu context with hysteresis. |
| **Switch** | Fixed Nintendo-position face-button layout. No automatic context switching. |
| **Custom PS5** | User-defined mapping derived from the PlayStation layout. Fixed exactly as configured. |
| **Custom Switch** | User-defined mapping derived from the Switch layout. Fixed exactly as configured. |

Settings → Controls → Button mapping can assign the emulated A/B/X/Y, L/R/ZL/ZR, Plus/Minus and stick-click actions to DualSense buttons. A title can use its own mapping without changing the global one.

The adaptive behavior applies **only** to the untouched PlayStation profile. Switch and both Custom profiles are never rewritten automatically. The profile's thresholds are generated from `encore-overrides/general/controls.json` with the video-profile snapshot.

Defaults:

| Setting | Default |
| --- | --- |
| Button profile | **PlayStation** |
| Stick deadzone | **8%** |
| Vibration | **On** |
| Vibration strength | **100%** |

Encore controls the emulated input mapping and its own PlayStation-style UI glyphs. A game's own rendered button textures/prompts are game assets and cannot be universally replaced by the emulator; per-title patches may still be needed for titles that hard-code Nintendo glyph artwork.

## Language

The launcher exposes **exactly 31 official PS5 system language/region choices** and **31 translation catalogs** (including distinct English US/UK spelling variants). This is a deliberate compatibility policy: **no extra launcher languages** beyond the [Sony PS5 system language list](https://www.playstation.com/fr-fr/legal/language-support/). All 31 are selectable; the historical first 18 keep their saved indices. See [LANGUAGES.md](LANGUAGES.md) for the full matrix and the [strict PS5 language policy](docs/PS5_SYSTEM_LANGUAGE_POLICY.md) for the authoritative 31-entry allowlist.

Settings → Language primarily selects the launcher interface. Only the original 18 selections map directly to a supported guest language.

On first setup, Encore seeds the preference from the PS5 system language. Changing it rebuilds the launcher immediately with the selected catalog/fonts. The original 18 selections preserve their guest language/region mappings; the 13 newly selectable PS5 system-language entries use an English guest-language fallback because these locales are not supported by the emulator's existing game-language enum. A game can still ignore the requested language when unsupported.

## Audio

- Game volume: **100%**
- Mute: **Off**
- Launcher/menu volume: **70%**

## Accessibility

Launcher-only options:

- Larger text
- High contrast
- Reduce motion

All are **Off by default**.

For verified launcher behavior, limitations (including unverified screen-reader integration), controller guidance and a reporting checklist, see [ACCESSIBILITY.md](ACCESSIBILITY.md). These options do not modify game graphics or animation.

## Diagnostics

Detailed logging is **Off by default**. In the **unreleased local release-profile candidate**,
turning the setting on will **not** force the whole game to `*:Debug`: that previously generated
excessive output during FC27. Detailed guest tracing requires an explicitly diagnostic build.
The preference may remain visible for compatibility, but normal shipping builds use a bounded
log policy instead of unlimited debug output.

Logs are stored under the Encore storage root, normally `/data/prosperoeden/logs/`.
The local candidate keeps up to **8 MiB of earliest plus 8 MiB of recent content per active
log stream**, with previous-session rotation/cleanup. This is a storage policy, not a guarantee
that a crash or frozen guest can always be diagnosed from the available records.

## Practical profiles

These are starting points, not compatibility guarantees.

### 4K TV — balanced

| Setting | Value |
| --- | --- |
| Renderer | Vulkan |
| TV output | **1440p** |
| Game resolution | **1x** |
| Filter | Bilinear |
| Anti-aliasing | **FXAA** |
| Refresh | 60 Hz |
| Console mode | Docked |

A modern 4K TV can upscale 1440p well while Encore keeps more GPU and presentation headroom.

### 4K TV — image quality

Use only after the title is already stable.

| Setting | Value |
| --- | --- |
| Renderer | Vulkan |
| TV output | **2160p** |
| Game resolution | **1x to 1.25x** |
| Filter | Bilinear or Bicubic |
| Anti-aliasing | None first, then SMAA if headroom remains |
| Refresh | 60 Hz |

Increase one setting at a time. If frame pacing worsens, return TV output to 1440p first.

### 4K TV — demanding game / unstable frame pacing

For a heavy title, start by separating **stability** from **image reconstruction**.

**Preferred first test when the picture already looked grainy/pixelated:**

| Setting | Value |
| --- | --- |
| Renderer | Vulkan |
| TV output | **1080p** |
| Game resolution | **1x** |
| Filter | **Bilinear** |
| FSR sharpness | Not used |
| Anti-aliasing | None first; test FXAA only if edge shimmer remains |
| Refresh | 60 Hz |
| Console mode | Docked |

This avoids adding FSR sharpening while diagnosing grain, shimmer or pixel crawl. If 1x is still too
heavy after runtime/stability fixes, then try **0.75x + AMD FSR**, but begin around **25–35% FSR
sharpness**, not an aggressive value. Raise sharpness only if the image is too soft.

Anti-aliasing can reduce jagged edges or shimmer, but it does not fix every kind of grain. FXAA may
hide some high-frequency shimmer at the cost of softness; SMAA preserves more detail but is a little
heavier. Encore R1 does not add a separate debanding pass: Eden has no reusable deband stage today,
and an extra fullscreen shader is not enabled without PS5 performance evidence. A game's own temporal
AA/reconstruction may also interact with Encore's post-process AA, so
there is no universally best AA choice.

Once stable and visually clean at 1080p/1x, try 1440p output. Treat 2160p and internal scales above
1x as later image-quality experiments, not starting values.

### 1080p TV

| Setting | Value |
| --- | --- |
| TV output | **1080p** |
| Game resolution | **1x** |
| Filter | Bilinear |
| Anti-aliasing | None |
| Refresh | 60 Hz |

There is normally little benefit in forcing a 2160p Encore output on a 1080p display.

### Troubleshooting / compatibility

When a game crashes, freezes or renders incorrectly:

1. Use **Safe Launch** once.
2. Keep **60 Hz, 1080p, 1x, Bilinear, AA None**.
3. If the issue is graphical, test OpenGL.
4. If it is performance-related, return to Vulkan and try 0.75x + FSR.
5. Change one major setting at a time and compare logs/FPS.

Safe Launch is temporary and does not overwrite saved global or per-game settings.

## Compared with Eden desktop/Windows

Encore now exposes most of the settings that are useful for normal PS5 tuning, but it intentionally does **not** mirror every Eden desktop debug/advanced switch.

Still internal or not exposed include examples such as:

- anisotropic-filter overrides;
- aspect-ratio overrides;
- advanced GPU-accuracy toggles;
- ASTC decode/recompression modes;
- low-level VSync/frame-pacing controls;
- VRAM/memory-layout modes;
- shader-backend and shader-cache internals;
- advanced CPU timing/accuracy controls;
- platform-specific options that do not make sense on fixed PS5 hardware.

The goal is **complete practical PS5 tuning**, not a one-for-one copy of every Windows engineering switch. Additional Eden controls should be exposed only when they have a real PS5 use case and a safe default.


## Neural Rendering and image composition

Neural Rendering is a **separate image-processing engine**, not another spatial upscaling filter. The six directly selectable modes are:
`off`, `a4k_detail`, `a4k_soft`, `a4k_denoise`,
`dlss_nr_original`, and `dlss_nr_compact`.

The three A4K modes use their existing Vulkan shaders (formerly identified internally as 7/8/9), but no longer appear in the upscaling-filter list. Original and Compact neural modes have separate RDNA2 model-processing paths. Their 0–100% intensity setting is visible, but cannot be edited unless one of those two modes is selected.

- **Neural Rendering:** `off` by default, including on a new installation.
- **Frame Generation:** independently `off` by default.
- **Upscaling:** a separate spatial filter; it does not include the A4K modes.
- **Anti-aliasing:** None/FXAA/SMAA are distinct; forced MSAA composition is not enabled for Neural Rendering without physical-console proof.
- **Neural Rendering + Frame Generation:** the combined mode is not validated and is therefore rejected.
- **Renderer:** selecting an A4K or learned-model mode requires Vulkan.
- **Evidence boundary:** selecting a model or intensity is not a performance preset and does not demonstrate that an authentic neural image has already been rendered on PS5.

The real preference keys are `video.neural_rendering` (one of the six modes) and `video.neural_strength` (0–100). Per-game overrides use the same keys under `games.<TITLE_ID>`; missing per-game keys inherit the global settings.

Legacy filters `anime4k_3d`, `anime4k_soft`, and `anime4k_denoise` migrate to the corresponding Neural Rendering modes. The older `neural_rendering:rdna2` value is migrated according to the previous `neural_model` field.

See [Neural Rendering UI and override behavior](docs/ENCORE_R09_NEURAL_RENDERING_UI_OVERRIDES.md).
