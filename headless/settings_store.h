// SPDX-License-Identifier: GPL-3.0-or-later
// Everything the launcher remembers, in one JSON file (config/prosperoeden.json):
//
//   {
//     "version": 1,
//     "video": { "renderer": "vulkan", "fps_overlay": false, "resolution": "1x",
//                "upscaling_filter": "bilinear", "refresh_rate": "60",
//                "output_resolution": "1080p" },
//     "audio": { "volume": 100, "mute": false, "menu_volume": 70 },
//     "controls": { "vibration": true, "vibration_strength": 100, "stick_deadzone": 8, "mapping": { "a": "cross" } },
//     "system": { "language": "en-US" },
//     "accessibility": { "large_text": false, "high_contrast": false, "reduce_motion": false },
//     "diagnostics": { "detailed_logging": false },
//     "game_files": "/mnt/ext1/eden", // legacy JSON key: one Encore storage root
//     "library": { "last_game": "Game [id].nsp", "recent": ["Game [id].nsp"] },
//     "games": { "0100000000010000": { "console_mode": "handheld", "renderer": "opengl",
//                                      "resolution": "0.75x", "upscaling_filter": "fsr",
//                                      "refresh_rate": "120", "mods": false,
//                                      "mods_off": ["A mod's folder name"] } }
//   }
//
// Missing or mistyped values read as their defaults. Writes replace the file atomically. The
// text files of earlier versions (settings.txt, last-game.txt, recent-games.txt, assets-dir.txt,
// game-<title>-mode.txt) are read once into the JSON file and left in place.
#pragma once
#include <algorithm>
#include <cctype>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#include <nlohmann/json.hpp>

#include "button_mapping.h"
#include "encore_overrides_generated.h"
#include "encore_texture_profiles.h"
#include "neural_video_policy.h"
#include "encore_overrides_runtime.h"
#include "storage_paths.h"
#include "game_files.h"

namespace Eden {
enum class GraphicsBackend { OpenGL, Vulkan };
inline const char* BackendName(GraphicsBackend backend) {
    return backend == GraphicsBackend::OpenGL ? "OpenGL" : "Vulkan";
}
// Settings > Video: the internal rendering resolution (a scale of the game's own 720p handheld
// or 1080p docked output) and the filter that scales the result to the TV output. 3x and 4x draw
// nine and sixteen times the game's own pixels: they need the graphics memory for it.
inline constexpr const char* kResolutionKeys[] = {"0.25x", "0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x", "3x", "4x"};
inline constexpr const char* kResolutionLabels[] = {
    "0.25x (minimum)", "0.5x (fastest, softer)", "0.75x (faster)", "1x (native)",
    "1.25x (recommended)", "1.5x (sharper)", "2x (high memory)", "3x (very high memory)",
    "4x (extreme memory)"};
static_assert(std::size(kResolutionLabels) == std::size(kResolutionKeys));
inline constexpr int kNativeResolution = 3;
// Existing indices stable. SGSR options are native Vulkan only; Lanczos
// uses the upstream window-adapt shader on Vulkan and OpenGL.
inline constexpr const char* kUpscalingFilterKeys[] = {
    "bilinear", "fsr", "bicubic", "nearest", "lanczos", "sgsr", "sgsr_edge",
    "anime4k_3d", "anime4k_soft", "anime4k_denoise"};
// These are spatial display filters, NOT FSR 3 temporal reconstruction.
inline constexpr const char* kUpscalingFilterLabels[] = {
    "Bilinear", "FSR 1", "Bicubic", "Nearest", "Lanczos", "SGSR", "SGSR Edge",
    "A4K — Détails améliorés", "A4K — Image adoucie", "A4K — Image nettoyée"};
// Keep existing indices stable; index 3 is a new Vulkan-only shader.
// Preserve all previously persisted AA indices 0-3. Real forced samples
// extend the same global/per-game AA field; no parallel experimental control.
inline constexpr const char* kAntiAliasingKeys[] = {
    "none", "fxaa", "smaa", "fxaa_quality",
    "msaa_2x", "msaa_4x", "msaa_8x", "msaa_16x"};
inline constexpr const char* kAntiAliasingLabels[] = {
    "None", "FXAA", "SMAA Ultra", "FXAA+",
    "MSAA 2x", "MSAA 4x", "MSAA 8x", "MSAA 16x"};
// Real Eden Vulkan texture sampler anisotropy, separate from spatial upscaling,
// frame generation and resolution. 0 uses Eden's automatic choice.
inline constexpr const char* kTextureAnisotropyKeys[] = {
    "automatic", "default", "2x", "4x", "8x", "16x"};
// Settings > Video: the refresh rate of the output while a game runs. 120 Hz is asked of the
// display (display_refresh.h); one that cannot show it stays at 60 Hz.
inline constexpr const char* kRefreshKeys[] = {"60", "120"};
// UI preference order: Off -> MihawkGen -> AMD FSR3 optical flow ->
// Lossless Scaling LAST because it requires the user's Lossless.dll.
// Keep persisted indices stable across releases; do not reorder separately.
inline constexpr const char* kFrameGenerationKeys[] = {"off", "mihawkgen", "fsr3", "lsfg"};
// Persisted model/intensity only: cannot activate NR until the graph works.
// Stable persisted IDs; A4K is a NR engine, never a spatial upscaler.
inline constexpr const char* kNeuralModeKeys[] = {
    "off", "a4k_detail", "a4k_soft", "a4k_denoise",
    "dlss_nr_original", "dlss_nr_compact"};
inline constexpr const char* kNeuralModelKeys[] = {"original", "small"};
inline constexpr const char* kNeuralModelLabels[] = {"Original", "Compact"};
static_assert(std::size(kNeuralModelKeys) == std::size(kNeuralModelLabels));
inline constexpr int kRefreshHz[] = {60, 120};
// Settings > Video: the size of the picture the app puts out, for the menu and for a game (its
// frame after the upscaling filter). The console scales it to what the TV shows.
inline constexpr const char* kOutputKeys[] = {"1080p", "1440p", "2160p"};
inline constexpr int kOutputWidth[] = {1920, 2560, 3840};
inline constexpr int kOutputHeight[] = {1080, 1440, 2160};
// Settings > Controls: face-button semantics on the DualSense while a Switch game runs.
// PlayStation is the native PS5 feel (Cross=A, Circle=B, Square=X, Triangle=Y).
// Nintendo preserves the physical-position mapping used by the original port.
inline constexpr const char* kControllerLayoutKeys[] = {"playstation", "switch"};
inline constexpr const char* kControllerLayoutLabels[] = {"PlayStation", "Switch"};
inline constexpr const char* kPerformanceProfileKeys[] = {"minimum", "recommended", "high", "ultra", "custom"};
inline constexpr const char* kPerformanceProfileLabels[] = {"Minimum", "Recommended", "High", "Ultra", "Custom"};
// Official PS5 system interface languages only (31 choices): see
// https://www.playstation.com/fr-fr/legal/language-support/
// Preserve the original 18 saved indices and their guest language mappings.
// The 13 additional PS5 interface locales use a safe English guest fallback because
// the emulator's game-language enum is narrower than the PS5 system language menu.
// Do not add non-PS5 interface language selectors without revising this explicit policy.
inline constexpr const char* kLanguageKeys[] = {"en-US", "en-GB", "fr", "fr-CA", "de", "it", "es", "es-419", "pt", "pt-BR", "nl", "ru", "pl", "ja", "ko", "zh-Hans", "zh-Hant", "th",
    "ar", "cs-CZ", "da-DK", "el-GR", "fi-FI", "hu-HU", "id-ID", "nb-NO", "ro-RO", "sv-SE", "tr-TR", "uk-UA", "vi-VN"};
inline constexpr const char* kLanguageLabels[] = {"English (US)", "English (UK)", "French", "French (Canada)", "German", "Italian", "Spanish", "Spanish (Latin America)", "Portuguese", "Portuguese (Brazil)", "Dutch", "Russian", "Polish", "Japanese", "Korean", "Chinese (Simplified)", "Chinese (Traditional)", "Thai",
    "Arabic", "Czech", "Danish", "Greek", "Finnish", "Hungarian", "Indonesian", "Norwegian (Bokmål)", "Romanian", "Swedish", "Turkish", "Ukrainian", "Vietnamese"};
inline constexpr const char* kLanguageCatalogTags[] = {"en-US", "en-GB", "fr-FR", "fr-CA", "de-DE", "it-IT", "es-ES", "es-419", "pt-PT", "pt-BR", "nl-NL", "ru-RU", "pl-PL", "ja-JP", "ko-KR", "zh-Hans", "zh-Hant", "th-TH",
    "ar", "cs-CZ", "da-DK", "el-GR", "fi-FI", "hu-HU", "id-ID", "nb-NO", "ro-RO", "sv-SE", "tr-TR", "uk-UA", "vi-VN"};
inline constexpr int kLanguageSettings[] = {1, 12, 2, 13, 3, 4, 5, 14, 9, 17, 8, 10, 18, 0, 7, 15, 16, 19,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
inline constexpr int kLanguageRegions[] = {1, 2, 2, 1, 2, 2, 2, 1, 2, 1, 2, 2, 2, 0, 5, 4, 6, 1,
    1, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 1};
static_assert(std::size(kLanguageLabels) == std::size(kLanguageKeys) &&
              std::size(kLanguageCatalogTags) == std::size(kLanguageKeys) &&
              std::size(kLanguageSettings) == std::size(kLanguageKeys) &&
              std::size(kLanguageRegions) == std::size(kLanguageKeys));
struct Preferences {
    bool hud = false;
    int volume = 100;
    bool mute = false;
    bool detailed_logging = false;
    GraphicsBackend backend = GraphicsBackend::Vulkan;
    int resolution = EncoreOverrides::kGeneralProfiles[1].resolution;  // Recommended from encore-overrides
    int upscaling_filter = EncoreOverrides::kGeneralProfiles[1].filter;
    int fsr_sharpness = EncoreOverrides::kGeneralProfiles[1].fsr_sharpness;
    int anti_aliasing = EncoreOverrides::kGeneralProfiles[1].anti_aliasing;
    int texture_anisotropy = EncoreTextureProfiles::ForTitle(0, 1); // Recommended: 4x
    int refresh = EncoreOverrides::kGeneralProfiles[1].refresh;
    int frame_generation = 0; // Off, MihawkGen, FSR3, LSFG; method, not fake FPS
    int neural_mode = NeuralVideo::kOff; // Six direct choices, Off default
    int neural_model = 0; // Original or Small; staged until graph verification
    int neural_strength = 100; // 0-100% independent of FSR/A4K
    int output = EncoreOverrides::kGeneralProfiles[1].output;
    int performance_profile = 1;         // 0 Minimum, 1 Recommended, 2 High, 3 Ultra, 4 Custom
    int controller_layout = 0;            // 0 PlayStation, 1 Switch; custom status is derived from mapping
    ButtonMapping mapping = kPlayStationMapping;
    bool vibration = true;
    int vibration_strength = 100;         // 0-100
    int stick_deadzone = 8;               // percent, 0-20
    int language = 0;                    // index into kLanguageKeys (English (US), Eden's default)
    int menu_volume = 70;                // the launcher's own sounds, 0 (off) to 100
    bool large_text = false;             // Settings > Accessibility: the launcher's look
    bool high_contrast = false;
    bool reduce_motion = false;
    int ui_theme = 0; // 0 Encore (default), 1 Switch-style
    int color_palette = 0; // 0 Neon, 1 Non-Neon, 2 Dark, 3 Light
    int accent_color = 0; // 0 Default, 1 Ocean, 2 Emerald, 3 Amber, 4 Rose
    int background_style = 0; // 0 Auto, 1 Artwork, 2 Solid, 3 Gradient, 4 Image, 5 Daily
    int logo_choice = 0;
    bool glow_enabled = true;
    int glow_strength = 100;
    unsigned background_color = 0x121824u;
    unsigned background_color2 = 0x263d59u;
    int background_overlay = 20;
    int panel_opacity = 50; // Percent; high-contrast UI is always opaque
    bool background_animate = true;
    int background_fit = 0;
    bool show_game_background = true;
    std::string wallpaper_file;
    // Auto-check metadata on first launcher start (never auto-install).
    // Existing saved opt-out values remain unchanged.
    bool check_updates_on_start = true;
};

inline int KeyIndex(const std::string& value, const char* const* keys, int count, int fallback) {
    for (int i = 0; i < count; ++i)
        if (value == keys[i]) return i;
    return fallback;
}

inline int DetectPerformanceProfile(const Preferences& value) {
    const int renderer = value.backend == GraphicsBackend::Vulkan ? 1 : 0;
    for (int tier = 0; tier < EncoreOverrides::kAuthoredProfileCount; ++tier) {
        const auto p = EncoreOverridesRuntime::ProfileForTitle(0, tier);
        if (renderer == p.renderer && value.output == p.output && value.resolution == p.resolution &&
            value.upscaling_filter == p.filter && value.fsr_sharpness == p.fsr_sharpness &&
            value.anti_aliasing == p.anti_aliasing && value.refresh == p.refresh)
            return tier;
    }
    return EncoreOverrides::kCustomProfile;
}

inline int PerformanceProfileIndex(std::string_view value, int fallback = -1) {
    for (int i = 0; i < int(std::size(kPerformanceProfileKeys)); ++i)
        if (value == kPerformanceProfileKeys[i]) return i;
    // Migration from Encore builds that exposed Recommended / Smooth / Performance.
    if (value == "smooth" || value == "performance") return EncoreOverrides::kCustomProfile;
    return fallback;
}

// Accept exact persisted legacy codes and official PS5 locale tags.
// Keep writes in the existing canonical format for older builds.
inline int SavedLanguageIndex(std::string_view locale) {
    for (int i = 0; i < int(std::size(kLanguageKeys)); ++i)
        if (locale == kLanguageKeys[i] || locale == kLanguageCatalogTags[i]) return i;
    return -1;
}

inline int LanguageIndexForLocale(std::string_view locale) {
    if (const int exact = SavedLanguageIndex(locale); exact >= 0) return exact;
    const std::size_t dash = locale.find('-');
    if (dash != std::string_view::npos) {
        const std::string_view base = locale.substr(0, dash);
        for (int i = 0; i < int(std::size(kLanguageKeys)); ++i)
            if (base == kLanguageKeys[i]) return i;
    }
    return -1;
}

inline bool ValidRomFilename(std::string_view name) {
    if (name.size() < 5 || name.size() > 255) return false;
    const bool exefs = Eden::IsDeconstructedGameSelection(name);
    const bool nested_package = Eden::IsNestedGameFileSelection(name);
    // A top-level update_/DLC- package must not be returned as the base
    // when the library scanner has no CNMT/TitleID proof of its role.
    // Apply the same reserved-name policy as nested package discovery.
    const std::size_t slash = name.find('/');
    const std::size_t extension = name.find_last_of('.');
    if (slash == std::string_view::npos && extension != std::string_view::npos &&
        (Eden::IsPackageFile(name) || Eden::IsCardImageFile(name) ||
         Eden::IsNupFile(name)) &&
        Eden::IsReservedAddOnPackageStem(name.substr(0, extension)))
        return false;
    for (unsigned char c : name)
        if (c < 32 || c == 127 || (c == '/' && !exefs && !nested_package) || c == '\\') return false;
    return Eden::IsGameFile(name) || exefs || nested_package;
}

// History stores the same relative selection as the library catalog, not
// the last path component (all extracted titles otherwise become "main").
// This is a storage identity helper, not authorization to launch a file.
inline std::string LibraryHistorySelection(const std::filesystem::path& selected,
                                           const std::filesystem::path& roms_root) {
    if (!selected.is_absolute() || !roms_root.is_absolute()) return {};
    const auto relative = selected.lexically_relative(roms_root);
    if (relative.empty() || relative.is_absolute()) return {};
    for (const auto& component : relative)
        if (component == "." || component == ".." || component.empty()) return {};
    const auto selection = relative.generic_string();
    return ValidRomFilename(selection) ? selection : std::string{};
}

inline std::string SettingsFile() { return ConfigFile("prosperoeden.json"); }

namespace Settings {
using Json = nlohmann::json;

inline std::string Folder(const std::string& file) {
    const auto slash = file.find_last_of('/');
    return slash == std::string::npos ? std::string{"."} : file.substr(0, slash);
}

// The whole file, or empty when it cannot be read completely.
inline bool ReadFile(const std::string& path, std::string& text) {
    FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) return false;
    text.clear();
    char buffer[4096];
    for (std::size_t count; (count = std::fread(buffer, 1, sizeof(buffer), file)) > 0;) text.append(buffer, count);
    const bool ok = !std::ferror(file);
    std::fclose(file);
    return ok;
}

inline bool WriteFile(const std::string& path, std::string_view contents) {
    const std::string temporary = path + ".tmp";
    FILE* file = std::fopen(temporary.c_str(), "wb");
    if (!file) return false;
    bool ok = std::fwrite(contents.data(), 1, contents.size(), file) == contents.size();
    if (std::fflush(file) != 0) ok = false;
    if (std::fclose(file) != 0) ok = false;
    if (ok && std::rename(temporary.c_str(), path.c_str()) == 0) return true;
    std::remove(temporary.c_str());
    return false;
}

inline bool Write(const Json& document, const std::string& file) {
    return WriteFile(file, document.dump(2, ' ', false, Json::error_handler_t::replace) + "\n");
}

inline std::string TitleKey(uint64_t title_id) {
    char key[17];
    std::snprintf(key, sizeof(key), "%016" PRIX64, title_id);
    return key;
}

// The earlier text files, when they are still in the settings folder.
inline Json Legacy(const std::string& folder) {
    Json document = Json::object();
    std::string text;
    if (ReadFile(folder + "/settings.txt", text)) {
        int version, hud, volume, mute, logging, backend = 1;
        char extra;
        std::istringstream input(text);
        if ((input >> version >> hud >> volume >> mute >> logging) &&
            (version == 1 || (version == 2 && (input >> backend))) && !(input >> extra) &&
            (backend == 0 || backend == 1) && (hud == 0 || hud == 1) && volume >= 0 && volume <= 100 &&
            (mute == 0 || mute == 1) && (logging == 0 || logging == 1)) {
            document["video"] = {{"renderer", backend ? "vulkan" : "opengl"}, {"fps_overlay", hud != 0}};
            document["audio"] = {{"volume", volume}, {"mute", mute != 0}};
            document["diagnostics"] = {{"detailed_logging", logging != 0}};
        }
    }
    if (ReadFile(folder + "/last-game.txt", text) && ValidRomFilename(text))
        document["library"]["last_game"] = text;
    if (ReadFile(folder + "/recent-games.txt", text)) {
        Json recent = Json::array();
        std::istringstream lines(text);
        for (std::string line; std::getline(lines, line) && recent.size() < 4;)
            if (ValidRomFilename(line)) recent.push_back(line);
        if (!recent.empty()) document["library"]["recent"] = recent;
    }
    if (ReadFile(folder + "/assets-dir.txt", text)) {
        while (!text.empty() && (text.back() == '\n' || text.back() == '\r')) text.pop_back();
        if (ValidAssetsDir(text) || LegacyAppAssetsPath(text)) document["game_files"] = text;
    }
    return document;
}

// The settings document; the first read after an update builds it from the earlier text files.
inline Json Load(const std::string& file) {
    std::string text;
    if (ReadFile(file, text)) {
        Json document = Json::parse(text, nullptr, false);
        return document.is_object() ? document : Json::object();
    }
    Json document = Legacy(Folder(file));
    if (!document.empty()) {
        document["version"] = 1;
        (void)Write(document, file);
    }
    return document;
}

// A button mapping as the file names it. Invalid or duplicate assignments fail back safely.
inline ButtonMapping Mapping(const Json& document, const Json::json_pointer& at,
                             const ButtonMapping& fallback) {
    if (!document.contains(at) || !document.at(at).is_object()) return fallback;
    ButtonMapping result = fallback;
    for (const auto& [name, value] : document.at(at).items()) {
        const int game = KeyIndex(name, kGameButtonKeys, kGameButtons, -1);
        const int pad = value.is_string() ?
            KeyIndex(value.get<std::string>(), kPadButtonKeys, kPadButtons, -1) : -1;
        if (game < 0 || pad < 0) return fallback;
        result[game] = pad;
    }
    return ValidMapping(result) ? result : fallback;
}
inline Json MappingJson(const ButtonMapping& mapping, const ButtonMapping& base = kDefaultMapping) {
    Json result = Json::object();
    for (int game = 0; game < kGameButtons; ++game)
        if (mapping[game] != base[game])
            result[kGameButtonKeys[game]] = kPadButtonKeys[mapping[game]];
    return result;
}

inline bool Bool(const Json& document, const Json::json_pointer& at, bool fallback) {
    return document.contains(at) && document.at(at).is_boolean() ? document.at(at).get<bool>() : fallback;
}
inline int Int(const Json& document, const Json::json_pointer& at, int fallback) {
    return document.contains(at) && document.at(at).is_number_integer() ? document.at(at).get<int>() : fallback;
}
inline std::string String(const Json& document, const Json::json_pointer& at) {
    return document.contains(at) && document.at(at).is_string() ? document.at(at).get<std::string>() : std::string{};
}
} // namespace Settings

inline Preferences LoadPreferences(const std::string& file = SettingsFile()) {
    using Settings::Json;
    const Json document = Settings::Load(file);
    Preferences result;
    result.hud = Settings::Bool(document, Json::json_pointer("/video/fps_overlay"), result.hud);
    result.backend = Settings::String(document, Json::json_pointer("/video/renderer")) == "opengl" ?
        GraphicsBackend::OpenGL : GraphicsBackend::Vulkan;
    const int volume = Settings::Int(document, Json::json_pointer("/audio/volume"), result.volume);
    if (volume >= 0 && volume <= 100) result.volume = volume;
    result.mute = Settings::Bool(document, Json::json_pointer("/audio/mute"), result.mute);
    const int menu_volume = Settings::Int(document, Json::json_pointer("/audio/menu_volume"), result.menu_volume);
    if (menu_volume >= 0 && menu_volume <= 100) result.menu_volume = menu_volume;
    result.detailed_logging = Settings::Bool(document, Json::json_pointer("/diagnostics/detailed_logging"),
                                             result.detailed_logging);
    result.resolution = KeyIndex(Settings::String(document, Json::json_pointer("/video/resolution")),
                                 kResolutionKeys, int(std::size(kResolutionKeys)), result.resolution);
    result.upscaling_filter = KeyIndex(Settings::String(document, Json::json_pointer("/video/upscaling_filter")),
                                       kUpscalingFilterKeys, int(std::size(kUpscalingFilterKeys)),
                                       result.upscaling_filter);
    const int fsr_sharpness = Settings::Int(document, Json::json_pointer("/video/fsr_sharpness"), result.fsr_sharpness);
    if (fsr_sharpness >= 0 && fsr_sharpness <= 100) result.fsr_sharpness = fsr_sharpness;
    result.anti_aliasing = KeyIndex(Settings::String(document, Json::json_pointer("/video/anti_aliasing")),
                                    kAntiAliasingKeys, int(std::size(kAntiAliasingKeys)), result.anti_aliasing);
    result.texture_anisotropy = KeyIndex(
        Settings::String(document, Json::json_pointer("/video/texture_anisotropy")),
        kTextureAnisotropyKeys, int(std::size(kTextureAnisotropyKeys)),
        result.texture_anisotropy);
    result.refresh = KeyIndex(Settings::String(document, Json::json_pointer("/video/refresh_rate")),
                              kRefreshKeys, int(std::size(kRefreshKeys)), result.refresh);
    result.frame_generation = KeyIndex(Settings::String(document, Json::json_pointer("/video/frame_generation")),
                                       kFrameGenerationKeys, int(std::size(kFrameGenerationKeys)), 0);
    const auto mode_key = Settings::String(
        document,Json::json_pointer("/video/neural_rendering"));
    const auto legacy_model = KeyIndex(
        Settings::String(document,Json::json_pointer("/video/neural_model")),
        kNeuralModelKeys,int(std::size(kNeuralModelKeys)),0);
    result.neural_mode = mode_key=="rdna2" ?
        (legacy_model==0?NeuralVideo::kDlssOriginal:NeuralVideo::kDlssCompact) :
        KeyIndex(mode_key,kNeuralModeKeys,int(std::size(kNeuralModeKeys)),0);
    // Backward compatibility: the old three A4K filters now belong to NR.
    if(NeuralVideo::IsA4kFilter(result.upscaling_filter)){
        if(mode_key.empty())result.neural_mode=
            NeuralVideo::ModeFromLegacyA4kFilter(result.upscaling_filter);
        result.upscaling_filter=0;
    }
    if(result.neural_mode!=NeuralVideo::kOff &&
       NeuralVideo::CheckSelectable(
           result.neural_mode,
           result.backend==GraphicsBackend::Vulkan?1:0,
           result.upscaling_filter,result.anti_aliasing,
           result.frame_generation)!=NeuralVideo::Reason::Available)
        result.neural_mode=NeuralVideo::kOff;
    result.neural_model = KeyIndex(Settings::String(document, Json::json_pointer("/video/neural_model")),
                                    kNeuralModelKeys, int(std::size(kNeuralModelKeys)), 0);
    const int neural_strength = Settings::Int(document, Json::json_pointer("/video/neural_strength"), 100);
    if (neural_strength >= 0 && neural_strength <= 100) result.neural_strength = neural_strength;
    result.output = KeyIndex(Settings::String(document, Json::json_pointer("/video/output_resolution")),
                             kOutputKeys, int(std::size(kOutputKeys)), result.output);
    // The profile label is derived from the actual settings. This migrates older three-profile
    // Encore configs honestly: a combination that no longer matches a current authored tier is Custom.
    result.performance_profile = DetectPerformanceProfile(result);
    // Migration: older saved profiles lacked a sampler level. Preserve their
    // authored preset rather than reclassifying every old High/Ultra as Custom.
    if (!document.contains(Json::json_pointer("/video/texture_anisotropy")) &&
        result.performance_profile >= 0 &&
        result.performance_profile < EncoreOverrides::kAuthoredProfileCount)
        result.texture_anisotropy =
            EncoreTextureProfiles::ForTitle(0, result.performance_profile);
    const Json::json_pointer global_layout("/controls/layout");
    const Json::json_pointer global_mapping("/controls/mapping");
    const std::string saved_layout = Settings::String(document, global_layout);
    if (saved_layout == "switch" || saved_layout == "nintendo")
        result.controller_layout = 1;
    else if (saved_layout == "playstation")
        result.controller_layout = 0;
    else if (document.contains(global_mapping))
        result.controller_layout = 1; // pre-profile Encore custom mappings were Switch-position based
    const ButtonMapping& global_base = BaseMappingForLayout(result.controller_layout);
    result.mapping = Settings::Mapping(document, global_mapping, global_base);
    result.vibration = Settings::Bool(document, Json::json_pointer("/controls/vibration"), result.vibration);
    const int vibration_strength = Settings::Int(document, Json::json_pointer("/controls/vibration_strength"),
                                                  result.vibration_strength);
    if (vibration_strength >= 0 && vibration_strength <= 100) result.vibration_strength = vibration_strength;
    const int stick_deadzone = Settings::Int(document, Json::json_pointer("/controls/stick_deadzone"),
                                              result.stick_deadzone);
    if (stick_deadzone >= 0 && stick_deadzone <= 20) result.stick_deadzone = stick_deadzone;
    if (const int language = SavedLanguageIndex(
            Settings::String(document, Json::json_pointer("/system/language"))); language >= 0)
        result.language = language;
    result.large_text = Settings::Bool(document, Json::json_pointer("/accessibility/large_text"), false);
    result.high_contrast = Settings::Bool(document, Json::json_pointer("/accessibility/high_contrast"), false);
    result.reduce_motion = Settings::Bool(document, Json::json_pointer("/accessibility/reduce_motion"), false);
    result.ui_theme = Settings::String(document, Json::json_pointer("/appearance/theme")) == "switch" ? 1 : 0;
    const int palette = Settings::Int(document, Json::json_pointer("/appearance/palette"), 0);
    const int accent = Settings::Int(document, Json::json_pointer("/appearance/accent"), 0);
    const int background = Settings::Int(document, Json::json_pointer("/appearance/background"), 0);
    if (palette >= 0 && palette <= 3) result.color_palette = palette;
    if (accent >= 0 && accent <= 4) result.accent_color = accent;
    if (background >= 0 && background <= 5) result.background_style = background;
    result.check_updates_on_start = Settings::Bool(
        document, Json::json_pointer("/app_updates/check_on_start"),
        result.check_updates_on_start);
    const int logo = Settings::Int(document, Json::json_pointer("/appearance/logo"), 0);
    const int strength = Settings::Int(document, Json::json_pointer("/appearance/glow_strength"), 100);
    const int overlay = Settings::Int(document, Json::json_pointer("/appearance/overlay"), 20);
    const int panel_opacity = Settings::Int(document, Json::json_pointer("/appearance/panel_opacity"), 50);
    const int fit = Settings::Int(document, Json::json_pointer("/appearance/fit"), 0);
    const int color_a = Settings::Int(document, Json::json_pointer("/appearance/color_a"), 0x121824);
    const int color_b = Settings::Int(document, Json::json_pointer("/appearance/color_b"), 0x263d59);
    if (logo >= 0 && logo <= 4) result.logo_choice = logo;
    if (strength >= 0 && strength <= 100) result.glow_strength = strength;
    if (overlay >= 0 && overlay <= 80) result.background_overlay = overlay;
    if (panel_opacity >= 0 && panel_opacity <= 100) result.panel_opacity = panel_opacity;
    if (fit >= 0 && fit <= 1) result.background_fit = fit;
    if (color_a >= 0 && color_a <= 0xffffff) result.background_color = static_cast<unsigned>(color_a);
    if (color_b >= 0 && color_b <= 0xffffff) result.background_color2 = static_cast<unsigned>(color_b);
    result.glow_enabled = Settings::Bool(document, Json::json_pointer("/appearance/glow"), true);
    result.background_animate = Settings::Bool(document, Json::json_pointer("/appearance/animate"), true);
    result.show_game_background = Settings::Bool(document, Json::json_pointer("/appearance/game_background"), true);
    const std::string wallpaper = Settings::String(document, Json::json_pointer("/appearance/wallpaper"));
    if (wallpaper.size() <= 120 && !wallpaper.empty() && wallpaper != "." && wallpaper != ".." &&
        wallpaper.find("..") == std::string::npos &&
        wallpaper.find_first_of("/\\") == std::string::npos)
        result.wallpaper_file = wallpaper;
    return result;
}

inline bool HasSavedLanguage(const std::string& file = SettingsFile()) {
    using Settings::Json;
    const std::string saved =
        Settings::String(Settings::Load(file), Json::json_pointer("/system/language"));
    return SavedLanguageIndex(saved) >= 0;
}

inline bool SavePreferences(const Preferences& value, const std::string& file = SettingsFile()) {
    if (value.volume < 0 || value.volume > 100 || value.menu_volume < 0 || value.menu_volume > 100 ||
        (value.backend != GraphicsBackend::OpenGL && value.backend != GraphicsBackend::Vulkan) ||
        value.resolution < 0 || value.resolution >= int(std::size(kResolutionKeys)) ||
        value.upscaling_filter < 0 || value.upscaling_filter >= int(std::size(kUpscalingFilterKeys)) ||
        value.fsr_sharpness < 0 || value.fsr_sharpness > 100 ||
        value.anti_aliasing < 0 || value.anti_aliasing >= int(std::size(kAntiAliasingKeys)) ||
        value.texture_anisotropy < 0 ||
        value.texture_anisotropy >= int(std::size(kTextureAnisotropyKeys)) ||
        value.refresh < 0 || value.refresh >= int(std::size(kRefreshKeys)) ||
        value.frame_generation < 0 || value.frame_generation >= int(std::size(kFrameGenerationKeys)) ||
        value.neural_mode < 0 || value.neural_mode >= int(std::size(kNeuralModeKeys)) ||
        value.upscaling_filter > 6 ||
        (value.neural_mode != NeuralVideo::kOff &&
          NeuralVideo::CheckSelectable(value.neural_mode,
            value.backend==GraphicsBackend::Vulkan?1:0,
            value.upscaling_filter,value.anti_aliasing,
            value.frame_generation)!=NeuralVideo::Reason::Available) ||
        value.neural_model < 0 || value.neural_model >= int(std::size(kNeuralModelKeys)) ||
        value.neural_strength < 0 || value.neural_strength > 100 ||
        value.output < 0 || value.output >= int(std::size(kOutputKeys)) ||
        value.performance_profile < 0 || value.performance_profile >= int(std::size(kPerformanceProfileKeys)) ||
        value.controller_layout < 0 || value.controller_layout >= int(std::size(kControllerLayoutKeys)) ||
        !ValidMapping(value.mapping) ||
        value.vibration_strength < 0 || value.vibration_strength > 100 ||
        value.stick_deadzone < 0 || value.stick_deadzone > 20 ||
        value.language < 0 || value.language >= int(std::size(kLanguageKeys)) ||
        value.ui_theme < 0 || value.ui_theme > 1) return false;
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    document["video"]["renderer"] = value.backend == GraphicsBackend::Vulkan ? "vulkan" : "opengl";
    document["video"]["fps_overlay"] = value.hud;
    document["video"]["resolution"] = kResolutionKeys[value.resolution];
    document["video"]["upscaling_filter"] = kUpscalingFilterKeys[value.upscaling_filter];
    document["video"]["fsr_sharpness"] = value.fsr_sharpness;
    document["video"]["anti_aliasing"] = kAntiAliasingKeys[value.anti_aliasing];
    document["video"]["texture_anisotropy"] =
        kTextureAnisotropyKeys[value.texture_anisotropy];
    document["video"]["refresh_rate"] = kRefreshKeys[value.refresh];
    document["video"]["frame_generation"] = kFrameGenerationKeys[value.frame_generation];
    document["video"]["neural_rendering"] = kNeuralModeKeys[value.neural_mode];
    document["video"].erase("neural_model"); // now encoded by neural_rendering
    document["video"]["neural_strength"] = value.neural_strength;
    document["video"]["output_resolution"] = kOutputKeys[value.output];
    document["video"]["performance_profile"] = kPerformanceProfileKeys[value.performance_profile];
    document["audio"]["volume"] = value.volume;
    document["audio"]["mute"] = value.mute;
    document["audio"]["menu_volume"] = value.menu_volume;
    document["controls"]["layout"] = kControllerLayoutKeys[value.controller_layout];
    const ButtonMapping& base_mapping = BaseMappingForLayout(value.controller_layout);
    if (value.mapping == base_mapping) document["controls"].erase("mapping");
    else document["controls"]["mapping"] = Settings::MappingJson(value.mapping, base_mapping);
    document["controls"]["vibration"] = value.vibration;
    document["controls"]["vibration_strength"] = value.vibration_strength;
    document["controls"]["stick_deadzone"] = value.stick_deadzone;
    document["system"]["language"] = kLanguageKeys[value.language];
    document["diagnostics"]["detailed_logging"] = value.detailed_logging;
    document["accessibility"]["large_text"] = value.large_text;
    document["accessibility"]["high_contrast"] = value.high_contrast;
    document["accessibility"]["reduce_motion"] = value.reduce_motion;
    document["appearance"]["theme"] = value.ui_theme == 1 ? "switch" : "encore";
    document["appearance"]["palette_schema"] = 1;
    document["appearance"]["palette"] = std::clamp(value.color_palette, 0, 3);
    document["appearance"]["accent"] = std::clamp(value.accent_color, 0, 4);
    document["appearance"]["background"] = std::clamp(value.background_style, 0, 5);
    document["appearance"]["logo"] = std::clamp(value.logo_choice, 0, 4);
    document["appearance"]["glow"] = value.glow_enabled;
    document["appearance"]["glow_strength"] = std::clamp(value.glow_strength, 0, 100);
    document["appearance"]["color_a"] = std::min(value.background_color, 0xffffffu);
    document["appearance"]["color_b"] = std::min(value.background_color2, 0xffffffu);
    document["appearance"]["overlay"] = std::clamp(value.background_overlay, 0, 80);
    document["appearance"]["panel_opacity"] = std::clamp(value.panel_opacity, 0, 100);
    document["appearance"]["fit"] = std::clamp(value.background_fit, 0, 1);
    document["appearance"]["animate"] = value.background_animate;
    document["appearance"]["game_background"] = value.show_game_background;
    if (value.wallpaper_file.size() <= 120 && value.wallpaper_file.find("..") == std::string::npos &&
        value.wallpaper_file.find_first_of("/\\") == std::string::npos)
        document["appearance"]["wallpaper"] = value.wallpaper_file;
    else document["appearance"]["wallpaper"] = "";
    document["app_updates"]["check_on_start"] = value.check_updates_on_start;
    return Settings::Write(document, file);
}

// Visual button art in games, independent of the already configured
// DualSense -> emulated Switch action mapping. PlayStation is the preferred
// presentation, falling back to the game's native art if no verified rule.
inline bool LoadInGamePlayStationGlyphs(std::uint64_t title_id,
                                       const std::string& file = SettingsFile()) {
    using Settings::Json;
    const Json document = Settings::Load(file);
    std::string choice = Settings::String(document,
        Json::json_pointer("/appearance/ingame_button_glyphs"));
    if (title_id != 0) {
        const auto game_choice = Settings::String(document, Json::json_pointer(
            "/games/" + Settings::TitleKey(title_id) + "/ingame_button_glyphs"));
        if (game_choice == "playstation" || game_choice == "switch")
            choice = game_choice;
    }
    return choice != "switch";
}
inline bool SaveInGameButtonGlyphs(std::uint64_t title_id, bool playstation,
                                   const std::string& file = SettingsFile()) {
    using Settings::Json;
    Json document = Settings::Load(file);
    if (title_id)
        document["games"][Settings::TitleKey(title_id)]["ingame_button_glyphs"] =
            playstation ? "playstation" : "switch";
    else
        document["appearance"]["ingame_button_glyphs"] =
            playstation ? "playstation" : "switch";
    return Settings::Write(document, file);
}

// -1 means no explicit per-title console mode; authored Encore profiles then supply the default.
inline int LoadGameDockedOverride(uint64_t title_id, const std::string& file = SettingsFile()) {
    if (!title_id) return -1;
    using Settings::Json;
    const Json document = Settings::Load(file);
    const Json::json_pointer at("/games/" + Settings::TitleKey(title_id) + "/console_mode");
    if (document.contains(at)) {
        const std::string mode = Settings::String(document, at);
        if (mode == "docked") return 1;
        if (mode == "handheld") return 0;
    }
    // A mode saved by an earlier version, in its own file.
    char name[48];
    std::snprintf(name, sizeof(name), "/game-%016llx-mode.txt", static_cast<unsigned long long>(title_id));
    std::string text;
    if (Settings::ReadFile(Settings::Folder(file) + name, text)) {
        if (text == "1 handheld\n") return 0;
        if (text == "0 docked\n") return 1;
    }
    return -1;
}

inline bool LoadGameDocked(uint64_t title_id, const std::string& file = SettingsFile()) {
    const int saved = LoadGameDockedOverride(title_id, file);
    return saved < 0 || saved == 1;
}

inline bool SaveGameDocked(uint64_t title_id, bool docked, const std::string& file = SettingsFile()) {
    if (!title_id) return false;
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    document["games"][Settings::TitleKey(title_id)]["console_mode"] = docked ? "docked" : "handheld";
    return Settings::Write(document, file);
}

// Library > Game settings: renderer, resolution, upscaling filter, refresh rate and controller layout for one game;
// -1 (absent from the file) uses the global setting.
struct GameSettings {
    int console_mode = -1;      // -1 follows profile/default, 0 Handheld, 1 Docked
    int renderer = -1;          // 0 OpenGL, 1 Vulkan
    int output = -1;            // index into kOutputKeys
    int resolution = -1;        // index into kResolutionKeys
    int upscaling_filter = -1;  // index into kUpscalingFilterKeys
    int fsr_sharpness = -1;     // 0-100; -1 follows global
    int anti_aliasing = -1;     // index into kAntiAliasingKeys
    int texture_anisotropy = -1; // -1 inherits global, 0 Automatic ... 5 16x
    int refresh = -1;           // index into kRefreshKeys
    int frame_generation = -1; // -1 inherits global, 0=off, 1=MihawkGen, 2=FSR3, 3=LSFG
    int neural_mode = -1; // Inherit, Off, three A4K, two DLSS-NR
    int neural_model = -1; // -1 inherits global; 0 Original, 1 Small
    int neural_strength = -1; // -1 inherits global, 0-100
    int performance_profile = -1; // index into kPerformanceProfileKeys
    int controller_layout = -1; // -1 follows global, 0 PlayStation, 1 Switch
    bool own_mapping = false;
    ButtonMapping mapping = kPlayStationMapping;
};
inline constexpr const char* kRendererKeys[] = {"opengl", "vulkan"};

inline GameSettings LoadGameSettings(uint64_t title_id, const std::string& file = SettingsFile()) {
    GameSettings result;
    if (!title_id) return result;
    using Settings::Json;
    const Json document = Settings::Load(file);
    const std::string base = "/games/" + Settings::TitleKey(title_id);
    const auto key = [&](const char* name) { return Settings::String(document, Json::json_pointer(base + "/" + name)); };
    const std::string mode = key("console_mode");
    if (mode == "docked") result.console_mode = 1;
    else if (mode == "handheld") result.console_mode = 0;
    else result.console_mode = LoadGameDockedOverride(title_id, file);
    result.renderer = KeyIndex(key("renderer"), kRendererKeys, int(std::size(kRendererKeys)), -1);
    result.output = KeyIndex(key("output_resolution"), kOutputKeys, int(std::size(kOutputKeys)), -1);
    result.resolution = KeyIndex(key("resolution"), kResolutionKeys, int(std::size(kResolutionKeys)), -1);
    result.upscaling_filter = KeyIndex(key("upscaling_filter"), kUpscalingFilterKeys,
                                       int(std::size(kUpscalingFilterKeys)), -1);
    const int fsr_sharpness = Settings::Int(document, Json::json_pointer(base + "/fsr_sharpness"), -1);
    result.fsr_sharpness = fsr_sharpness >= 0 && fsr_sharpness <= 100 ? fsr_sharpness : -1;
    result.anti_aliasing = KeyIndex(key("anti_aliasing"), kAntiAliasingKeys, int(std::size(kAntiAliasingKeys)), -1);
    result.texture_anisotropy = KeyIndex(
        key("texture_anisotropy"), kTextureAnisotropyKeys,
        int(std::size(kTextureAnisotropyKeys)), -1);
    result.refresh = KeyIndex(key("refresh_rate"), kRefreshKeys, int(std::size(kRefreshKeys)), -1);
    result.frame_generation = KeyIndex(key("frame_generation"), kFrameGenerationKeys,
                                       int(std::size(kFrameGenerationKeys)), -1);
    const auto nr_key=key("neural_rendering");
    const int legacy_model=KeyIndex(
        key("neural_model"),kNeuralModelKeys,
        int(std::size(kNeuralModelKeys)),0);
    result.neural_mode=nr_key=="rdna2"?
        (legacy_model==0?NeuralVideo::kDlssOriginal:NeuralVideo::kDlssCompact):
        KeyIndex(nr_key,kNeuralModeKeys,int(std::size(kNeuralModeKeys)),-1);
    if(NeuralVideo::IsA4kFilter(result.upscaling_filter)){
        if(nr_key.empty())result.neural_mode=
            NeuralVideo::ModeFromLegacyA4kFilter(result.upscaling_filter);
        result.upscaling_filter=0;
    }
    result.neural_model = KeyIndex(key("neural_model"), kNeuralModelKeys,
                                    int(std::size(kNeuralModelKeys)), -1);
    const int neural_strength = Settings::Int(
        document, Json::json_pointer(base + "/neural_strength"), -1);
    result.neural_strength = neural_strength >= 0 && neural_strength <= 100 ? neural_strength : -1;
    result.performance_profile = PerformanceProfileIndex(key("performance_profile"), -1);
    const std::string saved_game_layout = key("controller_layout");
    if (saved_game_layout == "switch" || saved_game_layout == "nintendo")
        result.controller_layout = 1;
    else if (saved_game_layout == "playstation")
        result.controller_layout = 0;
    const Json::json_pointer mapping(base + "/mapping");
    result.own_mapping = document.contains(mapping);
    if (result.own_mapping) {
        if (result.controller_layout < 0)
            result.controller_layout = 1; // legacy per-game custom mappings used Switch positions
        result.mapping = Settings::Mapping(document, mapping,
                                           BaseMappingForLayout(result.controller_layout));
    }
    if (result.performance_profile >= 0 &&
        result.performance_profile < EncoreOverrides::kAuthoredProfileCount) {
        const auto p = EncoreOverridesRuntime::ProfileForTitle(title_id, result.performance_profile);
        const bool complete = result.renderer >= 0 && result.output >= 0 && result.resolution >= 0 &&
                              result.upscaling_filter >= 0 && result.fsr_sharpness >= 0 &&
                              result.anti_aliasing >= 0 && result.refresh >= 0;
        if (complete && (result.renderer != p.renderer || result.output != p.output ||
            result.resolution != p.resolution || result.upscaling_filter != p.filter ||
            result.fsr_sharpness != p.fsr_sharpness || result.anti_aliasing != p.anti_aliasing ||
            result.refresh != p.refresh ||
            (result.console_mode >= 0 && (result.console_mode == 1) != p.docked)))
            result.performance_profile = EncoreOverrides::kCustomProfile;
    }
    return result;
}

inline bool SaveGameSettings(uint64_t title_id, const GameSettings& value, const std::string& file = SettingsFile()) {
    if (!title_id || value.console_mode < -1 || value.console_mode > 1 ||
        value.renderer < -1 || value.renderer >= int(std::size(kRendererKeys)) ||
        value.output < -1 || value.output >= int(std::size(kOutputKeys)) ||
        value.resolution < -1 || value.resolution >= int(std::size(kResolutionKeys)) ||
        value.upscaling_filter < -1 || value.upscaling_filter >= int(std::size(kUpscalingFilterKeys)) ||
        value.fsr_sharpness < -1 || value.fsr_sharpness > 100 ||
        value.anti_aliasing < -1 || value.anti_aliasing >= int(std::size(kAntiAliasingKeys)) ||
        value.texture_anisotropy < -1 ||
        value.texture_anisotropy >= int(std::size(kTextureAnisotropyKeys)) ||
        value.refresh < -1 || value.refresh >= int(std::size(kRefreshKeys)) ||
        value.frame_generation < -1 || value.frame_generation >= int(std::size(kFrameGenerationKeys)) ||
        value.neural_mode < -1 || value.neural_mode >= int(std::size(kNeuralModeKeys)) ||
        value.upscaling_filter > 6 ||
        (value.neural_mode > NeuralVideo::kOff &&
         (value.renderer==0 || value.upscaling_filter>0 ||
          value.anti_aliasing>=4 || value.frame_generation>0)) ||
        value.neural_model < -1 || value.neural_model >= int(std::size(kNeuralModelKeys)) ||
        value.neural_strength < -1 || value.neural_strength > 100 ||
        value.performance_profile < -1 ||
        value.performance_profile >= int(std::size(kPerformanceProfileKeys)) ||
        value.controller_layout < -1 ||
        value.controller_layout >= int(std::size(kControllerLayoutKeys)) ||
        (value.own_mapping && !ValidMapping(value.mapping))) return false;
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    auto& game = document["games"][Settings::TitleKey(title_id)];
    if (!game.is_object()) game = Settings::Json::object();
    const auto store = [&](const char* name, int index, const char* const* keys) {
        if (index < 0) game.erase(name);
        else game[name] = keys[index];
    };
    if (value.console_mode < 0) game.erase("console_mode");
    else game["console_mode"] = value.console_mode == 1 ? "docked" : "handheld";
    store("renderer", value.renderer, kRendererKeys);
    store("output_resolution", value.output, kOutputKeys);
    store("resolution", value.resolution, kResolutionKeys);
    store("upscaling_filter", value.upscaling_filter, kUpscalingFilterKeys);
    if (value.fsr_sharpness < 0) game.erase("fsr_sharpness");
    else game["fsr_sharpness"] = value.fsr_sharpness;
    store("anti_aliasing", value.anti_aliasing, kAntiAliasingKeys);
    store("texture_anisotropy", value.texture_anisotropy, kTextureAnisotropyKeys);
    store("refresh_rate", value.refresh, kRefreshKeys);
    store("frame_generation", value.frame_generation, kFrameGenerationKeys);
    store("neural_rendering", value.neural_mode, kNeuralModeKeys);
    game.erase("neural_model"); // legacy, encoded by direct mode
    if (value.neural_strength < 0) game.erase("neural_strength");
    else game["neural_strength"] = value.neural_strength;
    store("performance_profile", value.performance_profile, kPerformanceProfileKeys);
    store("controller_layout", value.controller_layout, kControllerLayoutKeys);
    if (value.own_mapping) {
        // The serialized button differences use the PlayStation base when
        // no title layout was selected. Persist that base explicitly: the
        // reader treats a mapping without a layout as legacy Switch data.
        // Without this, save -> reload silently changes A/B/X/Y bindings.
        const int layout = value.controller_layout >= 0 ? value.controller_layout : 0;
        if (value.controller_layout < 0)
            game["controller_layout"] = kControllerLayoutKeys[layout];
        game["mapping"] = Settings::MappingJson(value.mapping, BaseMappingForLayout(layout));
    } else {
        game.erase("mapping");
    }
    return Settings::Write(document, file);
}

// Library > Game settings > Mods: the names of the game's mods that are switched off (mods.h). A
// mod is on unless it is listed, so one added later is used without a visit to the launcher.
inline std::vector<std::string> LoadDisabledMods(uint64_t title_id, const std::string& file = SettingsFile()) {
    std::vector<std::string> names;
    if (!title_id) return names;
    using Settings::Json;
    const Json document = Settings::Load(file);
    const Json::json_pointer at("/games/" + Settings::TitleKey(title_id) + "/mods_off");
    if (!document.contains(at) || !document.at(at).is_array()) return names;
    for (const auto& entry : document.at(at))
        if (entry.is_string() && std::find(names.begin(), names.end(), entry.get<std::string>()) == names.end())
            names.push_back(entry.get<std::string>());
    return names;
}

inline bool SaveModEnabled(uint64_t title_id, std::string_view name, bool enabled,
                           const std::string& file = SettingsFile()) {
    if (!title_id || name.empty() || name.size() > 255) return false;
    auto names = LoadDisabledMods(title_id, file);
    names.erase(std::remove(names.begin(), names.end(), name), names.end());
    if (!enabled) names.emplace_back(name);
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    auto& game = document["games"][Settings::TitleKey(title_id)];
    if (!game.is_object()) game = Settings::Json::object();
    if (names.empty()) game.erase("mods_off");
    else game["mods_off"] = names;
    return Settings::Write(document, file);
}

// The Library's Mods switch: one switch for all of a game's mods, on unless the player turned it
// off ("mods": false). The mods' own switches (mods_off) keep their state behind it.
inline bool LoadModsEnabled(uint64_t title_id, const std::string& file = SettingsFile()) {
    if (!title_id) return true;
    using Settings::Json;
    return Settings::Bool(Settings::Load(file),
                          Json::json_pointer("/games/" + Settings::TitleKey(title_id) + "/mods"), true);
}

inline bool SaveModsEnabled(uint64_t title_id, bool enabled, const std::string& file = SettingsFile()) {
    if (!title_id) return false;
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    auto& game = document["games"][Settings::TitleKey(title_id)];
    if (!game.is_object()) game = Settings::Json::object();
    if (enabled) game.erase("mods");
    else game["mods"] = false;
    return Settings::Write(document, file);
}

inline std::string LoadLastGame(const std::string& file = SettingsFile()) {
    const std::string name = Settings::String(Settings::Load(file), Settings::Json::json_pointer("/library/last_game"));
    return ValidRomFilename(name) ? name : std::string{};
}

inline bool SaveLastGame(std::string_view name, const std::string& file = SettingsFile()) {
    if (!ValidRomFilename(name)) return false;
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    document["library"]["last_game"] = std::string(name);
    return Settings::Write(document, file);
}

inline std::vector<std::string> LoadRecentGames(const std::string& file = SettingsFile()) {
    using Settings::Json;
    const Json document = Settings::Load(file);
    const Json::json_pointer at("/library/recent");
    std::vector<std::string> recent;
    if (!document.contains(at) || !document.at(at).is_array()) return recent;
    for (const auto& entry : document.at(at)) {
        if (!entry.is_string()) continue;
        const std::string name = entry.get<std::string>();
        if (recent.size() < 4 && ValidRomFilename(name) && std::find(recent.begin(), recent.end(), name) == recent.end())
            recent.push_back(name);
    }
    return recent;
}

inline bool SaveRecentGame(std::string_view name, const std::string& file = SettingsFile()) {
    if (!ValidRomFilename(name)) return false;
    auto recent = LoadRecentGames(file);
    recent.erase(std::remove(recent.begin(), recent.end(), name), recent.end());
    recent.insert(recent.begin(), std::string(name));
    if (recent.size() > 4) recent.resize(4);
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    document["library"]["recent"] = recent;
    return Settings::Write(document, file);
}

// The saved Encore storage root, or empty for the internal /data/prosperoeden default.
// The JSON key remains "game_files" for backward compatibility with ProsperoEden.
inline std::string LoadSavedAssetsDir(const std::string& file = SettingsFile()) {
    const std::string value = Settings::String(Settings::Load(file), Settings::Json::json_pointer("/game_files"));
    return ValidAssetsDir(value) ? value : std::string{};
}

// Migration-only reader: accepts historical app-local aliases so Encore can recognize and retire
// them, without making those paths valid as a normal storage root.
inline std::string LoadStoredAssetsDirForMigration(const std::string& file = SettingsFile()) {
    const std::string value = Settings::String(Settings::Load(file), Settings::Json::json_pointer("/game_files"));
    return (ValidAssetsDir(value) || LegacyAppAssetsPath(value)) ? value : std::string{};
}

inline bool SaveAssetsDir(std::string_view directory, const std::string& file = SettingsFile()) {
    if (!ValidAssetsDir(directory)) return false;
    Settings::Json document = Settings::Load(file);
    document["version"] = 1;
    document["game_files"] = std::string(directory);
    return Settings::Write(document, file);
}

inline int AudioVolume(const Preferences& value) {
    return value.mute ? 0 : 0x8000 * value.volume / 100;
}
} // namespace Eden
