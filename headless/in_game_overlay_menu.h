// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <iterator>
#include <string>
#include <string_view>
#include "in_game_overlay.h"
#include "pe/core/strings.hpp"
#include "prosperoeden/pe/ui/texture_quality.hpp"
#include "prosperoeden/pe/ui/video_guidance.hpp"
#include "quick_overlay_font.h"
#include "log_pipe.h"
#include "settings_store.h"

namespace Eden {
void SetHudEnabled(bool enabled);
}

namespace Eden::QuickOverlay {
// Input/UI policy lives outside the render thread. Changes to video and
// controller assignments are saved per title, and take effect at next launch.
class Menu {
public:
    enum class Outcome { none, close, library, multiplayer };
    explicit Menu(std::uint64_t title) :
        title_id(title), game(LoadGameSettings(title)), prefs(LoadPreferences()) {}

    void Show(bool next) {
        visible = next;
        if (visible) {
            // Refresh appearance only when the user opens the menu.
            prefs = LoadPreferences();
            tab = 0;
            selected = 0;
            multiplayer_confirm = false;
            notice = Text("Game settings");
        }
        Rebuild();
    }

    Outcome Handle(std::uint32_t actions) {
        if (!visible || actions == 0) return Outcome::none;
        if (actions & back) {
            if (tab != 0) {
                const int previous = tab;
                tab = 0;
                selected = kHomeActionRows + previous - 1;
                multiplayer_confirm = false;
                Rebuild();
                return Outcome::none;
            }
            Show(false);
            return Outcome::close;
        }
        if (actions & previous_tab) {
            tab = (tab + kOverlayTabs - 1) % kOverlayTabs;
            multiplayer_confirm = false;
            selected = 0;
        }
        if (actions & next_tab) {
            tab = (tab + 1) % kOverlayTabs;
            multiplayer_confirm = false;
            selected = 0;
        }
        if (actions & up) { selected = (selected + Count() - 1) % Count(); multiplayer_confirm = false; }
        if (actions & down) { selected = (selected + 1) % Count(); multiplayer_confirm = false; }
        const int direction = (actions & right) ? 1 : (actions & left) ? -1 : 0;
        if (tab == 0) {
            if (selected == 1 && (direction || (actions & select))) ToggleFps();
            if (selected == 2 && (direction || (actions & select))) ToggleLogs();
            if (actions & select) {
                if (selected == 0) { Show(false); return Outcome::close; }
                if (selected == 3) { Show(false); return Outcome::library; }
                if (const int category = HomeCategoryTab(selected); category != 0) {
                    tab = category;
                    selected = 0;
                    multiplayer_confirm = false;
                }
            }
        } else if (tab == 1 && (direction || (actions & select))) {
            EditGraphics(direction ? direction : 1);
        } else if (tab == 2 && (direction || (actions & select))) {
            EditMapping(direction ? direction : 1);
        } else if (tab == 3) {
            if (selected == 0 && (direction || (actions & select))) ToggleFps();
            if (selected == 1 && (direction || (actions & select))) ToggleLogs();
        } else if (tab == 4 && (actions & select)) {
            if (selected == 1) { Show(false); return Outcome::close; }
            if (selected == 0) {
                if (multiplayer_confirm) { Show(false); return Outcome::multiplayer; }
                multiplayer_confirm = true;
                notice = Text("Confirm this action?");
            }
        }
        Rebuild();
        return Outcome::none;
    }

private:
    std::uint64_t title_id{};
    GameSettings game{};
    Preferences prefs{};
    bool visible{};
    // Kept across close/reopen: saved renderer/HID edits are not live.
    bool restart_required{};
    bool multiplayer_confirm{};
    int tab{};
    int selected{};
    std::string notice;
    static constexpr int kGraphicsRows = 12;
    static constexpr int kMappingRows = kGameButtons;
    static constexpr int kVisibleRows = 8;
    static_assert(kHomeRows <= kVisibleRows);

    int Count() const {
        return tab == 0 ? kHomeRows : tab == 1 ? kGraphicsRows : tab == 2 ? kMappingRows : tab == 3 ? 4 : 2;
    }
    static std::string Name(const char* const* keys, int count, int index) {
        return index >= 0 && index < count ? keys[index] : pe::tr("Automatic");
    }
    template<std::size_t N>
    static std::string Name(const char* const (&keys)[N], int index) {
        return Name(keys, int(N), index);
    }
    static std::string Text(const char* english) {
        return std::string{pe::tr(english)};
    }
    static std::string NextLaunchNotice() {
        auto text = Text("Next launch: {0}");
        const auto placeholder = text.find("{0}");
        if (placeholder != std::string::npos)
            text.replace(placeholder, 3, Text("Game settings"));
        return text;
    }
    static std::string Percent(int value) {
        return value < 0 ? std::string{pe::tr("Automatic")} : std::to_string(value) + "%";
    }
    static std::string Toggle(bool enabled) {
        return std::string{pe::tr(enabled ? "On" : "Off")};
    }
    std::string LanguageLine() const {
        const int language = std::clamp(prefs.language, 0,
            static_cast<int>(std::size(kLanguageCatalogTags)) - 1);
        return std::string{pe::tr(kLanguageLabels[language])} + " / " +
               kLanguageCatalogTags[language];
    }
    static std::string FrameGenerationName(int value) {
        if (value < 0) return std::string{pe::tr("Automatic")};
        switch (value) {
        case 0: return std::string{pe::tr("Off")};
        case 1: return "MihawkGen";
        case 2: return "FSR 3";
        case 3: return "LSFG";
        default: return std::string{pe::tr("Automatic")};
        }
    }
    std::string GraphicsRow(int row) const {
        const auto translated = [](const char* value) { return std::string{pe::tr(value)}; };
        switch (row) {
        case 0:
            return Text("Renderer") + " " +
                   std::string(game.renderer < 0 ? pe::tr("Automatic") :
                               game.renderer == 0 ? "OpenGL" : "Vulkan");
        case 1:
            return Text("Game resolution") + " " +
                   std::string(game.resolution < 0 ? pe::tr("Automatic") :
                               kResolutionKeys[game.resolution]);
        case 2:
            return Text("Upscaling") + " " + (game.upscaling_filter < 0
                ? std::string{pe::tr("Automatic")}
                : translated(kUpscalingFilterLabels[game.upscaling_filter]));
        case 3: return Text("Sharpness") + " " + Percent(game.fsr_sharpness);
        case 4:
            return Text("Anti-aliasing") + " " + (game.anti_aliasing < 0
                ? std::string{pe::tr("Automatic")}
                : translated(kAntiAliasingLabels[game.anti_aliasing]));
        case 5:
            return Text("Texture filtering") + " " +
                   (game.texture_anisotropy < 0 ? std::string{pe::tr("Automatic")}
                                                : pe::ui::TextureAnisotropyName(game.texture_anisotropy));
        case 6:
            return Text("Refresh rate") + " " +
                   (game.refresh < 0 ? std::string{pe::tr("Automatic")}
                                     : std::to_string(kRefreshHz[game.refresh]) + " Hz");
        case 7:
            return Text("Frame Generation") + " " + FrameGenerationName(game.frame_generation);
        case 8:
            return Text("Neural Rendering") + " " + std::string(game.neural_mode < 0 ? pe::tr("Automatic")
                                                             : pe::ui::NeuralModeName(game.neural_mode));
        case 9: return Text("Intensité DLSS-NR") + " " + Percent(game.neural_strength);
        case 10:
            return Text("TV output") + " " +
                   std::string(game.output < 0 ? pe::tr("Automatic") : kOutputKeys[game.output]);
        case 11:
            return Text("Console mode") + " " +
                   std::string(game.console_mode < 0 ? pe::tr("Automatic") :
                               game.console_mode ? pe::tr("Docked") : pe::tr("Handheld"));
        default: return {};
        }
    }
    std::string MappingRow(int row) const {
        static constexpr const char* guest[kGameButtons] = {
            "SW A", "SW B", "SW X", "SW Y", "SW L", "SW R", "SW ZL", "SW ZR",
            "SW PLUS", "SW MINUS", "SW L3", "SW R3"};
        static constexpr const char* pad[kPadButtons] = {
            "X", "O", "SQ", "TR", "L1", "R1", "L2", "R2",
            "L3", "R3", "OPT", "CR", "TP"};
        const auto& map = game.own_mapping ? game.mapping : prefs.mapping;
        return std::string(guest[row]) + " > " + pad[map[row]];
    }
    std::string Row(int row) const {
        if (tab == 0) {
            switch (row) {
            case 0: return Text("CONTINUE PLAYING");
            case 1: return Text("FPS OVERLAY") + " " + Toggle(prefs.hud);
            case 2: return Text("DETAILED LOGGING") + " " + Toggle(prefs.detailed_logging);
            case 3: return Text("Browse games");
            case 4: return Text("Renderer") + " >";
            case 5: return Text("Controls") + " >";
            case 6: return Text("Diagnostics") + " >";
            case 7: return Text("Multiplayer") + " >";
            }
        } else if (tab == 1) return GraphicsRow(row);
        else if (tab == 2) return MappingRow(row);
        else if (tab == 4) {
            return row == 0 ? Text("Multiplayer") : Text("CONTINUE PLAYING");
        } else if (tab == 3) {
            switch (row) {
            case 0: return Text("FPS OVERLAY") + (prefs.hud ? " 1" : " 0");
            case 1: return Text("DETAILED LOGGING") + (prefs.detailed_logging ? " 1" : " 0");
            case 2: return "FPS / PRESENT";
            case 3: {
                char text[25]{};
                std::snprintf(text, sizeof(text), "ID %016llX",
                              static_cast<unsigned long long>(title_id));
                return text;
            }
            }
        }
        return {};
    }
    bool PersistGame(const GameSettings& old) {
        if (SaveGameSettings(title_id, game)) {
            restart_required = true;
            notice = NextLaunchNotice();
            return true;
        }
        game = old;
        notice = Text("Could not save settings. Please try again.");
        return false;
    }
    static int Cycle(int value, int count, int direction) {
        // -1 is the inherited value; every UI choice is reversible.
        const int possibilities = count + 1;
        return (value + 1 + direction + possibilities) % possibilities - 1;
    }
    void EditGraphics(int direction) {
        const GameSettings old = game;
        int* target = nullptr;
        int count = 0;
        switch (selected) {
        case 0: target = &game.renderer; count = int(std::size(kRendererKeys)); break;
        case 1: target = &game.resolution; count = int(std::size(kResolutionKeys)); break;
        case 2: target = &game.upscaling_filter; count = 7; break; // no legacy A4K upscale aliases
        case 3: target = &game.fsr_sharpness; count = 101; break;
        case 4: target = &game.anti_aliasing; count = int(std::size(kAntiAliasingKeys)); break;
        case 5: target = &game.texture_anisotropy; count = int(std::size(kTextureAnisotropyKeys)); break;
        case 6: target = &game.refresh; count = int(std::size(kRefreshKeys)); break;
        case 7: target = &game.frame_generation; count = int(std::size(kFrameGenerationKeys)); break;
        case 8: target = &game.neural_mode; count = int(std::size(kNeuralModeKeys)); break;
        case 9: target = &game.neural_strength; count = 101; break;
        case 10: target = &game.output; count = int(std::size(kOutputKeys)); break;
        case 11: target = &game.console_mode; count = 2; break;
        default: break;
        }
        if (!target) return;
        *target = Cycle(*target, count, direction);
        // The game's authored preset is no longer exact after an individual edit.
        game.performance_profile = -1;
        PersistGame(old);
    }
    void EditMapping(int direction) {
        const GameSettings old = game;
        if (!game.own_mapping) {
            game.mapping = game.controller_layout >= 0 ?
                BaseMappingForLayout(game.controller_layout) : prefs.mapping;
            game.own_mapping = true;
            if (game.controller_layout < 0) game.controller_layout = 0;
        }
        const int current = game.mapping[selected];
        const int next = (current + direction + kPadButtons) % kPadButtons;
        for (int index = 0; index < kGameButtons; ++index) {
            if (index != selected && game.mapping[index] == next) {
                game.mapping[index] = current;
                break;
            }
        }
        game.mapping[selected] = next;
        PersistGame(old);
    }
    void ToggleFps() {
        auto previous = prefs;
        prefs.hud = !prefs.hud;
        if (!SavePreferences(prefs)) {
            prefs = previous;
            notice = Text("Could not save settings. Please try again.");
            return;
        }
        SetHudEnabled(prefs.hud);
        notice = Text("FPS OVERLAY") + " " + Toggle(prefs.hud);
    }
    void ToggleLogs() {
        auto previous = prefs;
        prefs.detailed_logging = !prefs.detailed_logging;
        if (!SavePreferences(prefs)) {
            prefs = previous;
            notice = Text("Could not save settings. Please try again.");
            return;
        }
        NativeLogs::SetDetailed(prefs.detailed_logging);
        notice = Text("DETAILED LOGGING") + " " + Toggle(prefs.detailed_logging);
    }
    void Rebuild() const {
        Frame result;
        result.visible = visible;
        if (!visible) {
            Publish(result);
            return;
        }
        result.style = StyleId(prefs.color_palette,prefs.accent_color,
                               prefs.high_contrast,prefs.ui_theme==1);
        const auto line = [&](std::string_view value, std::uint32_t mode) {
            if (result.count >= kMaxRows) return;
            const auto index = result.count++;
            result.text[index].Assign(value);
            auto& dst = result.rows[index];
            dst.glyphs = EncodeMenuText(value, prefs.language);
            dst.width = 680;
            dst.loading = StyledMode(mode,result.style);
        };
        line("EDEN ENCORE / O " + Text("Back"), kRow);
        // Category names come from the same 31 maintained launcher catalogs.
        // Technical L1/R1 and page numbers stay language-neutral.
        const std::array<std::string, kOverlayTabs> headings{
            "L1 / " + Text("Game settings") + " 1/5 / R1",
            "L1 / " + Text("Renderer") + " 2/5 / R1",
            "L1 / " + Text("Controls") + " 3/5 / R1",
            "L1 / " + Text("Diagnostics") + " 4/5 / R1",
            "L1 / " + Text("Multiplayer") + " 5/5 / R1"};
        line(headings[static_cast<std::size_t>(tab)], kSelectedRow);
        line(LanguageLine(), kRow);
        const int start = std::clamp(selected - 3, 0, std::max(0, Count() - kVisibleRows));
        for (int index = 0; index < kVisibleRows; ++index) {
            const int item = start + index;
            line(item < Count() ? Row(item) : "",
                 item == selected ? kSelectedRow : kRow);
        }
        line("X " + Text("Change") + " / O " + Text("Back"), kRow);
        line(tab == 4 && !multiplayer_confirm ? Text("Confirm this action?") : notice, kRow);
        // A persistent banner uses an already-maintained localized launcher
        // key; no second quick-menu-only translation catalogue exists.
        line(restart_required ? NextLaunchNotice() : "",
             restart_required ? kWarningRow : kRow);
        Publish(result);
    }
};
} // namespace Eden::QuickOverlay
