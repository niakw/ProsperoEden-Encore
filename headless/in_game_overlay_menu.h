// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <iterator>
#include <string>
#include <string_view>
#include "in_game_overlay.h"
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
            notice = restart_required ? "MODIFS ENREGISTREES" : "REGLAGES DE CE JEU";
        }
        Rebuild();
    }

    Outcome Handle(std::uint32_t actions) {
        if (!visible || actions == 0) return Outcome::none;
        if (actions & back) {
            Show(false);
            return Outcome::close;
        }
        if (actions & previous_tab) {
            tab = (tab + 4) % 5;
            multiplayer_confirm = false;
            selected = 0;
        }
        if (actions & next_tab) {
            tab = (tab + 1) % 5;
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
                notice = "CONFIRMER : FERMER JEU";
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

    int Count() const {
        return tab == 0 ? 4 : tab == 1 ? kGraphicsRows : tab == 2 ? kMappingRows : tab == 3 ? 4 : 2;
    }
    static std::string Name(const char* const* keys, int count, int index) {
        return index >= 0 && index < count ? keys[index] : "AUTO";
    }
    template<std::size_t N>
    static std::string Name(const char* const (&keys)[N], int index) {
        return Name(keys, int(N), index);
    }
    static std::string Percent(int value) {
        return value < 0 ? "AUTO" : std::to_string(value) + "%";
    }
    std::string GraphicsRow(int row) const {
        switch (row) {
        case 0: return "RENDER " + Name(kRendererKeys, game.renderer);
        case 1: return "RES " + Name(kResolutionKeys, game.resolution);
        case 2: return "UPSCALE " + Name(kUpscalingFilterKeys, game.upscaling_filter);
        case 3: return "SHARP " + Percent(game.fsr_sharpness);
        case 4: return "AA " + Name(kAntiAliasingKeys, game.anti_aliasing);
        case 5: return "ANISO " + Name(kTextureAnisotropyKeys, game.texture_anisotropy);
        case 6: return "REFRESH " + Name(kRefreshKeys, game.refresh);
        case 7: return "FRAME GEN " + Name(kFrameGenerationKeys, game.frame_generation);
        case 8: return "NEURAL " + Name(kNeuralModeKeys, game.neural_mode);
        case 9: return "NR POWER " + Percent(game.neural_strength);
        case 10: return "OUTPUT " + Name(kOutputKeys, game.output);
        case 11: return "DOCKED " + std::string(game.console_mode < 0 ? "AUTO" :
                                              game.console_mode ? "YES" : "NO");
        default: return {};
        }
    }
    std::string MappingRow(int row) const {
        static constexpr const char* guest[kGameButtons] = {
            "SW A", "SW B", "SW X", "SW Y", "SW L", "SW R", "SW ZL", "SW ZR",
            "SW PLUS", "SW MINUS", "SW L3", "SW R3"};
        const auto& map = game.own_mapping ? game.mapping : prefs.mapping;
        return std::string(guest[row]) + " > " + kPadButtonKeys[map[row]];
    }
    std::string Row(int row) const {
        if (tab == 0) {
            switch (row) {
            case 0: return "REPRENDRE LE JEU";
            case 1: return prefs.hud ? "AFFICHAGE FPS OUI" : "AFFICHAGE FPS NON";
            case 2: return prefs.detailed_logging ? "LOGS DETAILLES OUI" : "LOGS DETAILLES NON";
            case 3: return "RETOUR BIBLIOTHEQUE";
            }
        } else if (tab == 1) return GraphicsRow(row);
        else if (tab == 2) return MappingRow(row);
        else if (tab == 4) {
            return row == 0 ? "OUVRIR SALON MULTI" : "RESTER DANS LE JEU";
        } else if (tab == 3) {
            switch (row) {
            case 0: return prefs.hud ? "AFFICHAGE FPS OUI" : "AFFICHAGE FPS NON";
            case 1: return prefs.detailed_logging ? "LOGS DETAILLES OUI" : "LOGS DETAILLES NON";
            case 2: return "FPS = HOST PRESENT";
            case 3: {
                char text[25]{};
                std::snprintf(text, sizeof(text), "TITLE %016llX",
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
            notice = "MODIFS ENREGISTREES";
            return true;
        }
        game = old;
        notice = "SAVE FAILED OR INCOMPAT";
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
            notice = "CANNOT SAVE FPS SETTING";
            return;
        }
        SetHudEnabled(prefs.hud);
        notice = prefs.hud ? "FPS DISPLAY ENABLED" : "FPS DISPLAY DISABLED";
    }
    void ToggleLogs() {
        auto previous = prefs;
        prefs.detailed_logging = !prefs.detailed_logging;
        if (!SavePreferences(prefs)) {
            prefs = previous;
            notice = "CANNOT SAVE LOG SETTING";
            return;
        }
        NativeLogs::SetDetailed(prefs.detailed_logging);
        notice = prefs.detailed_logging ? "DETAILED LOGS ENABLED" : "DETAILED LOGS DISABLED";
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
            dst.glyphs = HudText(value.substr(0, 24));
            dst.width = 680;
            dst.loading = StyledMode(mode,result.style);
        };
        line("EDEN ENCORE / PAD FERMER", kRow);
        // All five pages remain visible, including before the first L1/R1.
        // The highlighted second line identifies the active page and its
        // position; keep each label within the current 24-glyph HUD ABI.
        static constexpr std::string_view headings[] = {
            "L1 / JEU 1/5 / R1", "L1 / GRAPH 2/5 / R1",
            "L1 / PAD 3/5 / R1", "L1 / DIAG 4/5 / R1",
            "L1 / MULTI 5/5 / R1"};
        static_assert(std::size(headings) == 5);
        line(headings[tab], kSelectedRow);
        line("JEU GRAPH PAD DIAG MULTI", kRow);
        const int start = std::clamp(selected - 3, 0, std::max(0, Count() - kVisibleRows));
        for (int index = 0; index < kVisibleRows; ++index) {
            const int item = start + index;
            line(item < Count() ? Row(item) : "",
                 item == selected ? kSelectedRow : kRow);
        }
        line("HAUT BAS  GAUCHE DROITE", kRow);
        line(tab == 4 && !multiplayer_confirm ? "SALON = FERMER LE JEU" : notice, kRow);
        // A persistent, visually distinct banner when a per-title change
        // needs a fresh game launch (never a full PS5/system restart).
        line(restart_required ? "RELANCER LE JEU REQUIS" : "",
             restart_required ? kWarningRow : kRow);
        Publish(result);
    }
};
} // namespace Eden::QuickOverlay
