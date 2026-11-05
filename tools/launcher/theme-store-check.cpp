// UI theme persistence round-trip: run on host only, never touches a console.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "settings_store.h"
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <unistd.h>

int main() {
    char temp[] = "/tmp/encore-theme-XXXXXX";
    assert(mkdtemp(temp) != nullptr);
    const std::string file = std::string(temp) + "/theme.json";
    assert(Eden::LoadPreferences(file).ui_theme == 0);

    Eden::Preferences prefs = Eden::LoadPreferences(file);
    prefs.volume = 37;
    prefs.controller_layout = 0;
    prefs.ui_theme = 1;
    prefs.color_palette = 3; // independently persisted, even with Switch layout
    prefs.logo_choice = 4;
    prefs.accent_color = 2;
    prefs.background_style = 5;
    prefs.glow_enabled = false;
    prefs.glow_strength = 30;
    prefs.background_color = 0x145678;
    prefs.background_color2 = 0x987654;
    prefs.show_game_background = false;
    prefs.wallpaper_file = "user-screenshot.png";
    prefs.check_updates_on_start = true;
    assert(Eden::SavePreferences(prefs, file));
    auto result = Eden::LoadPreferences(file);
    assert(result.ui_theme == 1);
    assert(result.volume == 37 && result.controller_layout == 0);
    assert(result.color_palette == 3 && result.logo_choice == 4 && result.accent_color == 2);
    assert(result.background_style == 5 && !result.glow_enabled &&
           result.glow_strength == 30);
    assert(result.background_color == 0x145678 && result.background_color2 == 0x987654);
    assert(!result.show_game_background && result.wallpaper_file == "user-screenshot.png");
    assert(result.check_updates_on_start);

    std::ifstream stream(file);
    const std::string json((std::istreambuf_iterator<char>(stream)),
                           std::istreambuf_iterator<char>());
    assert(json.find("\"theme\": \"switch\"") != std::string::npos);

    result.ui_theme = 0;
    assert(Eden::SavePreferences(result, file));
    assert(Eden::LoadPreferences(file).ui_theme == 0);

    result.ui_theme = 2;
    assert(!Eden::SavePreferences(result, file));
    result.ui_theme = -1;
    assert(!Eden::SavePreferences(result, file));

    const std::string unexpected = std::string(temp) + "/invalid.json";
    std::ofstream(unexpected) << R"({"appearance":{"theme":"surprise"}})";
    assert(Eden::LoadPreferences(unexpected).ui_theme == 0);
    // New installs get a nonblocking stable-release check; old opted-out
    // profiles still keep /app_updates/check_on_start=false.
    assert(Eden::LoadPreferences(unexpected).check_updates_on_start);
    std::ofstream(unexpected) << R"({"appearance":{"palette":999,"background":999,"wallpaper":"../../other.png"}})";
    const auto invalid = Eden::LoadPreferences(unexpected);
    assert(invalid.color_palette == 0 && invalid.background_style == 0);
    assert(invalid.wallpaper_file.empty());
    assert(Eden::LoadPreferences(file).volume == 37);

    (void)std::remove(file.c_str());
    (void)std::remove(unexpected.c_str());
    (void)rmdir(temp);
    return 0;
}
