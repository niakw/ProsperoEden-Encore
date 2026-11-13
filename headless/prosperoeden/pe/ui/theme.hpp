// ProsperoEden - Launcher colours, type sizes and motion constants.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include "pe/gfx/draw_list.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <string>

namespace pe::ui
{

using gfx::Align;
using gfx::Color;
using gfx::Rect;

namespace theme
{

// Eden brand palette: dark neutral surfaces with the official violet/pink/blue accents.
inline Color kBase = Color::rgb(0x07070d);
inline Color kScrim = Color::rgb(0x04040a);
inline Color kGlass = Color::rgb(0x120f1c);  // translucent Eden surfaces
inline Color kPanel = Color::rgb(0x0b0a12);  // screens and dialogs
inline Color kPanelEdge = Color::rgb(0x8c78ad);
inline Color kPanelEdgeSoft = Color::rgb(0x5b506f);
inline Color kRow = Color::rgb(0x12101a);
inline Color kRowEdge = Color::rgb(0x625875);
inline Color kRowFocus = Color::rgb(0x2b1b42);
inline Color kFocusCore = Color::rgb(0xff70e4); // Eden neon pink focus edge
inline Color kFocusBlue = Color::rgb(0xbb59ff); // Eden luminous violet; historic identifier retained

// Keep the historic names to avoid touching every widget; values are Eden's official accents.
inline Color kLime = Color::rgb(0xbf42f6);      // Eden violet
inline Color kLimeDeep = Color::rgb(0x6547c7);  // deep violet/blue
inline Color kLimePale = Color::rgb(0xe1b7ff);  // pale violet
inline Color kSun = Color::rgb(0xff44c4);       // Eden pink
inline Color kBlue = Color::rgb(0x62b4ff);      // Eden blue
inline Color kAccentTeal = Color::rgb(0xe0b1ff); // Eden lilac values; historic identifier retained

// Text
inline Color kText = Color::rgb(0xf4f2f8);
inline Color kTitle = Color::rgb(0xffffff);
inline Color kValue = Color::rgb(0xf0edf7);
inline Color kBody = Color::rgb(0xdedbe8);
inline Color kCopy = Color::rgb(0xc5c1d2);
inline Color kMeta = Color::rgb(0xa9a5b8);
inline Color kLabel = Color::rgb(0xb7b2c5);
inline Color kMuted = Color::rgb(0xa19cad);
inline Color kFaint = Color::rgb(0x7e798b);
inline Color kWarning = Color::rgb(0xff9f9f);
inline Color kRule = Color::rgb(0x3f3b51);

// Type sizes (Montserrat Medium)
constexpr float kDisplay = 48.0f;
constexpr float kLead = 40.0f;
constexpr float kBrand = 36.0f;
constexpr float kHeading = 32.0f;
constexpr float kClock = 28.0f;
constexpr float kText24 = 24.0f;
constexpr float kSmall = 20.0f;

// Motion (spring responsiveness in rad/s, durations in seconds)
constexpr float kFocusSpring = 20.0f;
constexpr float kCursorSpring = 26.0f;
constexpr float kScrollSpring = 16.0f;
constexpr float kScreenSeconds = 0.30f;
// Allow one visible face change while keeping game admission bounded.
// Front preview 1.2 s, first turn 1.3 s, BACK remains readable 4.5 s,
// return turn 1.3 s, final settle/fade 0.5 s. A truthful staged cinematic
// transition, NOT a proxy for guest/emulation loading percentage.
constexpr float kCaseFrontHold = 1.20f;
constexpr float kCaseTurnSeconds = 0.72f; // rapid pass through spine; never a pause
constexpr float kCaseBackHold = 4.50f;
constexpr float kCaseSettleSeconds = 0.50f;
constexpr float kLaunchSeconds = kCaseFrontHold + 2.0f * kCaseTurnSeconds +
                                 kCaseBackHold + kCaseSettleSeconds;


// Color tokens share the existing draw path. Theme changes never affect game shaders.
// Like Nuvio, the palette is separate from the selected home-screen layout.
inline void apply_palette(int palette, int accent)
{
    const std::array<Color*, 27> slots = {
        &kBase, &kScrim, &kGlass, &kPanel, &kPanelEdge, &kPanelEdgeSoft, &kRow,
        &kRowEdge, &kRowFocus, &kFocusCore, &kFocusBlue, &kLime, &kLimeDeep,
        &kLimePale, &kSun, &kBlue, &kAccentTeal, &kText, &kTitle, &kValue,
        &kBody, &kCopy, &kMeta, &kLabel, &kMuted, &kFaint, &kWarning};
    static const auto neon = [&] {
        std::array<Color, 27> result{};
        for (std::size_t i = 0; i < result.size(); ++i) result[i] = *slots[i];
        return result;
    }();
    for (std::size_t i = 0; i < slots.size(); ++i) *slots[i] = neon[i];
    kRule = Color::rgb(0x3f3b51);
    if (palette == 1 || palette == 2) { // subdued Non-Neon and Dark
        kBase = Color::rgb(0x0d1014); kScrim = Color::rgb(0x080c10);
        kGlass = Color::rgb(0x171b22); kPanel = Color::rgb(0x171b22);
        kPanelEdge = Color::rgb(0x66717d); kPanelEdgeSoft = Color::rgb(0x3d4753);
        kRow = Color::rgb(0x20262d); kRowEdge = Color::rgb(0x48515c);
        kRowFocus = Color::rgb(0x23374c); kRule = Color::rgb(0x343d48);
        kLime = Color::rgb(0x7196bc); kLimeDeep = Color::rgb(0x3b5873);
        kLimePale = Color::rgb(0xa9cee9); kFocusCore = Color::rgb(0x8ab8ec);
        kFocusBlue = Color::rgb(0x749fc6); kSun = Color::rgb(0x8997aa);
        kAccentTeal = Color::rgb(0xb7d2e6);
    }
    if (palette == 2) { // monochrome Dark
        kBase = Color::rgb(0x0b0c0f); kGlass = Color::rgb(0x141519);
        kPanel = Color::rgb(0x16171b); kRow = Color::rgb(0x1f2025);
        kRowFocus = Color::rgb(0x34363c); kPanelEdge = Color::rgb(0x74777e);
        kLime = Color::rgb(0x9297a1); kLimePale = Color::rgb(0xf2f4f6);
        kLimeDeep = Color::rgb(0x50535a); kSun = Color::rgb(0x91949c);
        kFocusCore = Color::rgb(0xffffff); kFocusBlue = Color::rgb(0x9297a1);
        kBlue = Color::rgb(0x8e97a5);
    } else if (palette == 3) { // Neutral Light
        kBase = Color::rgb(0xf1f3f5); kScrim = Color::rgb(0x1a2938);
        kGlass = Color::rgb(0xf8fafc); kPanel = Color::rgb(0xffffff);
        kPanelEdge = Color::rgb(0x8b98a7); kPanelEdgeSoft = Color::rgb(0xc2cbd4);
        kRow = Color::rgb(0xe6eaf0); kRowEdge = Color::rgb(0xa7b4c3);
        kRowFocus = Color::rgb(0xc9e0f3);
        kLime = Color::rgb(0x175071); kLimeDeep = Color::rgb(0x194e7a);
        kLimePale = Color::rgb(0x15527e); kFocusCore = Color::rgb(0x135eaa);
        kFocusBlue = Color::rgb(0x216ba6); kSun = Color::rgb(0x20526b);
        kBlue = Color::rgb(0x1c5982); kAccentTeal = Color::rgb(0x12516f);
        kText = Color::rgb(0x16202c); kTitle = Color::rgb(0x101820);
        // Small metadata is drawn against translucent white panels and the
        // pale focused row. The earlier blue-gray inks faded badly on TV.
        // Prefer dark slate copy rather than low-contrast muted accents.
        kValue = Color::rgb(0x172532); kBody = Color::rgb(0x253645);
        kCopy = Color::rgb(0x293b4b); kMeta = Color::rgb(0x2e4050);
        kLabel = Color::rgb(0x28394a); kMuted = Color::rgb(0x324354);
        kFaint = Color::rgb(0x334554); kWarning = Color::rgb(0xa52a2a);
        kRule = Color::rgb(0xc4ced8);
    }
    if (accent > 0 && accent <= 4) {
        static constexpr std::uint32_t swatches[] = {
            0x000000u, 0x347fc4u, 0x278b70u, 0xb17724u, 0xc04f72u};
        static constexpr std::uint32_t bright[] = {
            0x000000u, 0x9ccbf7u, 0x8bd9b5u, 0xf7cc87u, 0xf5a6c4u};
        // Light-theme focus and metadata labels must retain >=4.5:1
        // contrast even on the brightest selected row. Preserve the hue
        // of each accent while darkening the text/focus ink, not the theme.
        static constexpr std::uint32_t light_accessible[] = {
            0x000000u, 0x165584u, 0x165c48u, 0x6f4816u, 0x7d3650u};
        kLime = Color::rgb(palette == 3 ? light_accessible[accent] : swatches[accent]);
        kLimePale = Color::rgb(palette == 3 ? light_accessible[accent] : bright[accent]);
        kFocusCore = kLimePale;
        kFocusBlue = kFocusCore;
        kAccentTeal = kLimePale;
    }
}

} // namespace theme

// How the launcher is shown: Settings > Accessibility.
struct Look
{
    bool large_text = false;    // small text is drawn larger
    bool high_contrast = false; // solid panels, brighter text, an outlined highlight
    bool reduce_motion = false; // nothing drifts, slides or zooms: screens fade
    int palette = 0; // Neon, Non-Neon, Dark, Light
    int background = 0; // Auto, Artwork, Solid, Gradient, Image, Daily
    bool glow = true;
    float glow_strength = 1.0f;
    std::uint32_t background_color = 0x121824u, background_color2 = 0x263d59u;
    int background_overlay = 20;
    float panel_opacity = 1.0f; // not applied to guest graphics
    bool background_animate = true;
    int background_fit = 0;
    std::string wallpaper_path;
};
inline Look &look()
{
    static Look value;
    return value;
}
// 1 normally, 0 with reduced motion: every slide, zoom and drift is multiplied by it.
inline float motion()
{
    return look().reduce_motion ? 0.0f : 1.0f;
}
// The size text of `size` is drawn at. "Larger text" raises everything under 30 to between 26
// and 30 (26 is the least the console accessibility guidelines ask of text on a 1080p TV).
inline float text_size(float size)
{
    return look().large_text && size < 30.0f ? std::clamp(size * 1.3f, 26.0f, 30.0f) : size;
}

// The baseline that centres text of `size` in a line box of height `line` starting at `top`.
inline float baseline(float top, float line, float size)
{
    return top + line * 0.5f + size * 0.35f;
}

inline bool inside(const Rect &r, float x, float y)
{
    return x >= r.x && y >= r.y && x < r.x + r.w && y < r.y + r.h;
}

} // namespace pe::ui
