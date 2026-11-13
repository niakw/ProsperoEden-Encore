// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include "encore_overrides_generated.h"
#include "encore_overrides_runtime.h"
#include "encore_texture_profiles.h"
#include "pe/ui/services.hpp"

#include <algorithm>
#include <array>
#include <cstdint>

namespace pe::ui {

using VideoPresetValues = Eden::EncoreOverrides::VideoProfile;

inline constexpr int kAuthoredVideoProfiles = Eden::EncoreOverrides::kAuthoredProfileCount;
inline constexpr int kCustomVideoProfile = Eden::EncoreOverrides::kCustomProfile;

inline VideoPresetValues VideoPresetForTitle(std::uint64_t title_id, int preset) {
    return Eden::EncoreOverridesRuntime::ProfileForTitle(title_id, preset);
}

// QUALITY ORDER — theoretical spatial reconstruction (BEST -> LOWEST)
// and post-AA (BEST -> LOWEST). No static chart can guarantee superiority
// across games/frames; see docs/ENCORE_GRAPHICS_QUALITY_RANKING.md.
// This is ONLY the interface/cycling order: persisted enum IDs do not change.
inline constexpr std::array<int, 7> kUpscalingQualityOrder{
    6, 5, 1, 4, 2, 0, 3}; // Spatial scaling only; the three A4K engines live in Neural Rendering.
// Navigation order only: no visual superiority is established before console A/B.
inline constexpr std::array<int, 8> kAntiAliasingQualityOrder{
    2, 3, 1, 0, 7, 6, 5, 4
}; // SMAA Ultra, FXAA+, FXAA, None, MSAA 16x/8x/4x/2x.
// Every settings entry (global/triangle/quick) must use the same exact
// persisted AA indices; console rendering support is verified separately.
inline constexpr bool AntiAliasingOptionSelectable(int aa, int renderer) noexcept {
    return aa < 3 || renderer == 1; // FXAA+ and MSAA need native Vulkan.
}

template <std::size_t N, typename Allowed>
inline int CycleQualityRanked(int current, int step,
                             const std::array<int, N>& order,
                             bool allow_inherit, Allowed allowed) {
    constexpr int kCountMax = 16;
    static_assert(N > 0 && N <= kCountMax);
    const int count = static_cast<int>(N) + (allow_inherit ? 1 : 0);
    int position = allow_inherit ? 0 : -1;
    for (int i = 0; i < static_cast<int>(N); ++i)
        if (order[static_cast<std::size_t>(i)] == current)
            position = i + (allow_inherit ? 1 : 0);
    if (!allow_inherit && position < 0) position = 0;
    const int direction = step < 0 ? -1 : 1;
    for (int i = 0; i < count; ++i) {
        position = (position + direction + count) % count;
        const int candidate = allow_inherit && position == 0
            ? -1 : order[static_cast<std::size_t>(position - (allow_inherit ? 1 : 0))];
        if (candidate == -1 || allowed(candidate)) return candidate;
    }
    return current;
}

inline constexpr bool UpscalingRequiresVulkan(int filter) {
    return filter >= 5 && filter <= 9; // SGSR and A4K CNN profiles; Vulkan only
}
inline constexpr bool UpscalingSupportsSharpness(int filter) {
    return filter == 1 || filter == 5 || filter == 6;
}
inline constexpr bool UpscalingFilterSelectable(int filter,int renderer) {
    return !UpscalingRequiresVulkan(filter) || renderer == 1;
}

// Frame synthesis is implemented exclusively on the native Vulkan path.
inline bool FrameGenerationSelectable(int renderer) {
    return renderer == 1;
}

inline int EffectiveGameRenderer(const GameSettings& game,
                                 const Preferences& global,
                                 std::uint64_t title_id) {
    if (game.renderer >= 0) return game.renderer;
    if (game.performance_profile >= 0 &&
        game.performance_profile < kAuthoredVideoProfiles)
        return VideoPresetForTitle(title_id, game.performance_profile).renderer;
    if (global.performance_profile >= 0 &&
        global.performance_profile < kAuthoredVideoProfiles)
        return VideoPresetForTitle(title_id, global.performance_profile).renderer;
    return global.renderer;
}

inline int EffectiveGameUpscalingFilter(const GameSettings& game,
                                        const Preferences& global,
                                        std::uint64_t title_id) {
    if (game.filter >= 0) return game.filter;
    if (game.performance_profile >= 0 &&
        game.performance_profile < kAuthoredVideoProfiles)
        return VideoPresetForTitle(title_id, game.performance_profile).filter;
    if (global.performance_profile >= 0 &&
        global.performance_profile < kAuthoredVideoProfiles)
        return VideoPresetForTitle(title_id, global.performance_profile).filter;
    return global.filter;
}

inline int ClampVideoPreset(int preset) {
    return std::clamp(preset, 0, kAuthoredVideoProfiles - 1);
}

inline int CycleVideoPreset(int current, int step) {
    // Custom is derived from manual edits, never an authored preset to apply. From Custom, moving
    // right starts at Minimum; moving left starts at Ultra.
    if (current == kCustomVideoProfile)
        return step >= 0 ? 0 : kAuthoredVideoProfiles - 1;
    current = std::clamp(current, 0, kAuthoredVideoProfiles - 1);
    return (current + step + kAuthoredVideoProfiles) % kAuthoredVideoProfiles;
}

inline bool MatchesPreset(const Preferences& preferences, const VideoPresetValues& value,
                          int tier) {
    return preferences.renderer == value.renderer && preferences.output == value.output &&
           preferences.resolution == value.resolution && preferences.filter == value.filter &&
           preferences.fsr_sharpness == value.fsr_sharpness &&
           preferences.anti_aliasing == value.anti_aliasing &&
           preferences.texture_anisotropy ==
               Eden::EncoreTextureProfiles::ForTitle(0, tier) &&
           preferences.refresh == value.refresh;
}

inline int DetectVideoProfile(const Preferences& preferences) {
    for (int preset = 0; preset < kAuthoredVideoProfiles; ++preset)
        if (MatchesPreset(preferences, VideoPresetForTitle(0, preset), preset))
            return preset;
    return kCustomVideoProfile;
}

inline void RefreshVideoProfile(Preferences& preferences) {
    preferences.performance_profile = DetectVideoProfile(preferences);
}

inline int DetectVideoProfile(const GameSettings& settings, const Preferences& global,
                              std::uint64_t title_id = 0) {
    const auto effective = [](int local, int fallback) { return local >= 0 ? local : fallback; };
    for (int preset = 0; preset < kAuthoredVideoProfiles; ++preset) {
        const auto value = VideoPresetForTitle(title_id, preset);
        if (effective(settings.renderer, global.renderer) == value.renderer &&
            effective(settings.output, global.output) == value.output &&
            effective(settings.resolution, global.resolution) == value.resolution &&
            effective(settings.filter, global.filter) == value.filter &&
            effective(settings.fsr_sharpness, global.fsr_sharpness) == value.fsr_sharpness &&
            effective(settings.anti_aliasing, global.anti_aliasing) == value.anti_aliasing &&
            (settings.texture_anisotropy >= 0
                ? settings.texture_anisotropy
                : global.performance_profile == kCustomVideoProfile
                    ? global.texture_anisotropy
                    : Eden::EncoreTextureProfiles::ForTitle(title_id, preset))
                    == Eden::EncoreTextureProfiles::ForTitle(title_id, preset) &&
            effective(settings.refresh, global.refresh) == value.refresh &&
            (settings.console_mode < 0 || (settings.console_mode == 1) == value.docked))
            return preset;
    }
    return kCustomVideoProfile;
}

inline void RefreshVideoProfile(GameSettings& settings, const Preferences& global,
                                std::uint64_t title_id = 0) {
    settings.performance_profile = DetectVideoProfile(settings, global, title_id);
}

inline void ApplyVideoPreset(Preferences& preferences, int preset) {
    const auto value = VideoPresetForTitle(0, ClampVideoPreset(preset));
    preferences.performance_profile = ClampVideoPreset(preset);
    preferences.renderer = value.renderer;
    preferences.output = value.output;
    preferences.resolution = value.resolution;
    preferences.filter = value.filter;
    preferences.fsr_sharpness = value.fsr_sharpness;
    preferences.anti_aliasing = value.anti_aliasing;
    preferences.texture_anisotropy = Eden::EncoreTextureProfiles::ForTitle(0, preset);
    preferences.refresh = value.refresh;
}

inline void ApplyVideoPreset(GameSettings& settings, int preset, std::uint64_t title_id = 0) {
    preset = ClampVideoPreset(preset);
    const auto value = VideoPresetForTitle(title_id, preset);
    settings.performance_profile = preset;
    settings.console_mode = value.docked ? 1 : 0;
    settings.renderer = value.renderer;
    settings.output = value.output;
    settings.resolution = value.resolution;
    settings.filter = value.filter;
    settings.fsr_sharpness = value.fsr_sharpness;
    settings.anti_aliasing = value.anti_aliasing;
    settings.texture_anisotropy =
        Eden::EncoreTextureProfiles::ForTitle(title_id, preset);
    settings.refresh = value.refresh;
}

} // namespace pe::ui
