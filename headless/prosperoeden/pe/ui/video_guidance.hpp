// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Short, option-specific guidance shared by global and per-game settings.
// The highlighted help panel is separate from small secondary footer text.
#include "pe/ui/widgets.hpp"
#include "pe/core/strings.hpp"
#include <string_view>

namespace pe::ui {
inline const char* UpscalingGuide(int filter) {
    switch (filter) {
    case 0: return tr(TR("Bilinear: fast and soft. Best when the game already renders near the TV resolution."));
    case 1: return tr(TR("AMD FSR 1: EASU enlarges the picture; RCAS adds sharpness. Most useful below the TV output resolution."));
    case 2: return tr(TR("Bicubic: sharper than bilinear, but may create bright edges. The FSR sharpness slider does not apply."));
    default: return tr(TR("Nearest: keeps hard pixel edges, with visible stair-steps. Best for pixel art, not most 3D games."));
    }
}
inline const char* AntiAliasingGuide(int aa) {
    switch (aa) {
    case 0: return tr(TR("Off: no edge smoothing. Fastest, but diagonal lines may look jagged."));
    case 1: return tr(TR("FXAA: lightweight edge smoothing in one pass. It can slightly soften text and fine details."));
    case 3: return tr(TR("FXAA+: extended edge search. Can smooth more jagged edges but may soften textures. Compare with SMAA Ultra."));
    default: return tr(TR("SMAA Ultra: high-quality multi-pass edge smoothing. Clearer contours but more GPU work than FXAA."));
    }
}
inline const char* FsrSharpnessGuide(bool active) {
    return active
        ? tr(TR("Only AMD FSR 1 uses this percentage. Start at 50%. Increase gently for detail; reduce if edges shimmer or show halos."))
        : tr(TR("Inactive for this filter. Select AMD FSR 1 under Upscaling to adjust sharpness. It does not alter the game's textures."));
}
inline const char* FxaaUnsupportedGuide() {
    return tr(TR("FXAA+ requires Vulkan. Choose Vulkan or another anti-aliasing method."));
}
inline const char* FramegenUnsupportedGuide() {
    return tr(TR("This option needs Vulkan. OpenGL cannot generate extra frames; changing it would have no effect."));
}
inline const char* TextureGuide() {
    return tr(TR("Texture filtering sharpens roads, floors and walls viewed at an angle. Start at 4x; 8x/16x use more GPU bandwidth. Unlike FSR sharpness, it does not sharpen the whole picture."));
}
inline void DrawVideoGuide(Canvas& c, std::string_view label,
                           std::string_view explanation,
                           bool inactive = false, bool light_theme = false) {
    constexpr Rect panel{592.0f, 724.0f, 736.0f, 112.0f};
    const Color background = light_theme
        ? Color::rgb(inactive ? 0xfff4e6 : 0xeaf5ff, 0.99f)
        : Color::rgb(inactive ? 0x332617 : 0x101e30, 0.99f);
    const Color ink = light_theme ? Color::rgb(0x172c40) : Color::rgb(0xf2f7ff);
    const Color accent = light_theme
        ? Color::rgb(inactive ? 0x925100 : 0x087a80)
        : Color::rgb(inactive ? 0xffc26e : 0x8cf5d4);
    c.list.rounded_rect(panel, 14.0f, background);
    c.list.rounded_rect({panel.x, panel.y + 8.0f, 5.0f, panel.h - 16.0f},
                        2.5f, accent);
    text_shrink(c, label, panel.x + 18.0f, panel.y + 25.0f,
                17.0f, accent, panel.w - 36.0f);
    // Real measured word wrapping: up to 3 lines, not a single squeezed
    // sentence or an ellipsis that hides the actual instructions.
    text_block(c, explanation, panel.x + 18.0f, panel.y + 51.0f,
               18.0f, 22.0f, ink, panel.w - 38.0f, 3, 0.86f);
}
} // namespace pe::ui
