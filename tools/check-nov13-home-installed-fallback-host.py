#!/usr/bin/env python3
"""Compile the real Home tile reconciliation and guard real MRU order.

This is a host test of production C++ methods plus native source contracts,
not a claim that a PS5 storage mount or on-screen layout has been tested.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
lib = (ROOT / "headless/prosperoeden/pe/ui/library.cpp").read_text()
services = (ROOT / "headless/prosperoeden/eden_services.cpp").read_text()
home = (ROOT / "headless/prosperoeden/pe/ui/home.cpp").read_text()
switch = (ROOT / "headless/prosperoeden/pe/ui/switch_theme.cpp").read_text()

native_home = services.split(
    "pe::ui::Home EdenServices::home(const std::atomic<bool>* cancel)", 1
)[1].split("std::string EdenServices::clock()", 1)[0]
assert "const std::unordered_set<std::string> played(history.begin(), history.end());" in native_home
assert "Eden::ReadNativeDirectory(" in native_home
assert "Eden::FindGameFolderInput(entry.path())" in native_home
assert "Eden::ValidRomFilename(name)" in native_home
assert "std::sort(unplayed_installed.begin(), unplayed_installed.end());" in native_home
assert "history.insert(history.end(), unplayed_installed.begin()," in native_home
assert "for (const auto& name : history)" in native_home
assert "if (played.contains(name))" in native_home
assert "if (IsFile(cached_cover)) recent.cover = cached_cover;" in native_home
assert "if (home.recents.size() == 7) break;" in native_home
assert "SaveRecentGame(name)" not in native_home
assert "EnsureNlibEnrichment" not in native_home
assert "ExtractedBaseBytes" not in native_home
assert 'constexpr int kHomeRecentMax = 7;' in home
assert 'constexpr int kHomeGameSlots = 6;' in switch
finish_home = lib.split("void Launcher::finish_home_scan()", 1)[1].split(
    "void Launcher::check_games_present()", 1
)[0]
assert "if (games_loaded_) name_home_games();" in finish_home
assert "if (initial && !home_.last_exists && !home_.recents.empty())" in finish_home
assert "home_recent_ = 0;" in finish_home
apply = lib.split("void Launcher::apply_games(", 1)[1].split(
    "void Launcher::sync_home_game(", 1
)[0]
assert "name_home_games();" in apply

# Pull BOTH real member implementations directly out of production library.cpp,
# and compile against compatible model fields. This catches bad C++ syntax
# and verifies ordering and deduplication rather than copying the algorithm.
methods = lib.split("void Launcher::sync_home_game(const Game& game)", 1)[1].split(
    "void Launcher::start_diagnostics(", 1
)[0]
methods = "void Launcher::sync_home_game(const Game& game)" + methods
assert methods.count("void Launcher::name_home_games()") == 1
harness = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>
struct Game {
    std::string file, name, cover, box_front, hero, intro, description, addons, language;
    std::vector<std::string> screenshots;
    std::uint64_t title_id = 0;
    int mods = 0, mods_on = 0, max_players = 0;
};
struct Recent {
    std::string file, title, cover, hero, screenshot, intro, description, addons, language;
    std::uint64_t title_id = 0;
    int max_players = 0;
};
struct Home {
    bool setup_ready = true;
    bool last_exists = false;
    std::string last_file, last_title, last_cover, last_hero, last_screenshot, last_intro, last_description;
    std::vector<Recent> recents;
    int last_mods = 0, last_mods_on = 0, last_max_players = 0;
};
struct Launcher {
    Home home_;
    std::vector<Game> games_;
    void sync_home_game(const Game&);
    void name_home_games();
};
""" + methods + r"""
int main() {
    Launcher fresh;
    for (int i = 0; i < 10; ++i) {
        Game game;
        game.file = "game" + std::to_string(i) + ".nsp";
        game.name = "Title " + std::to_string(i);
        game.title_id = static_cast<std::uint64_t>(i + 1);
        game.cover = "icon" + std::to_string(i) + ".webp";
        fresh.games_.push_back(std::move(game));
    }
    fresh.name_home_games();
    assert(fresh.home_.recents.size() == 7);
    for (int i = 0; i < 7; ++i) {
        assert(fresh.home_.recents[i].file == "game" + std::to_string(i) + ".nsp");
        assert(fresh.home_.recents[i].cover == "icon" + std::to_string(i) + ".webp");
    }
    fresh.name_home_games();
    assert(fresh.home_.recents.size() == 7); // idempotent, no duplicate tiles

    Launcher history;
    history.games_ = fresh.games_;
    Recent latest;
    latest.file = "game8.nsp";
    latest.title = "Played most recently";
    history.home_.recents.push_back(std::move(latest));
    Recent prior;
    prior.file = "game3.nsp";
    history.home_.recents.push_back(std::move(prior));
    history.name_home_games();
    assert(history.home_.recents.size() == 7);
    assert(history.home_.recents[0].file == "game8.nsp");
    assert(history.home_.recents[1].file == "game3.nsp");
    assert(history.home_.recents[2].file == "game0.nsp");
    assert(history.home_.recents[3].file == "game1.nsp");
    assert(history.home_.recents[4].file == "game2.nsp");
    assert(history.home_.recents[5].file == "game4.nsp");
    assert(history.home_.recents[6].file == "game5.nsp");
    assert(history.home_.recents[0].cover == "icon8.webp");
    history.name_home_games();
    assert(history.home_.recents.size() == 7);
    assert(history.home_.recents[0].file == "game8.nsp");

    Launcher unavailable;
    unavailable.home_.setup_ready = false;
    unavailable.games_ = fresh.games_;
    unavailable.name_home_games();
    assert(unavailable.home_.recents.empty()); // keep setup-recovery view

    Launcher returned;
    returned.home_.last_file = "game2.nsp";
    returned.games_ = fresh.games_;
    returned.name_home_games();
    assert(returned.home_.last_title == "Title 2");
    assert(returned.home_.last_cover == "icon2.webp");
}
"""
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-home-installed-") as tmp:
    source = Path(tmp) / "home.cpp"
    binary = Path(tmp) / "home"
    source.write_text(harness)
    subprocess.run([compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", str(source), "-o", str(binary)], check=True,
                   timeout=30)
    subprocess.run([str(binary)], check=True, timeout=10)
print("ENCORE_HOME_INSTALLED_MRU_HOST_PASS rail=7 switch=6 order=real-history-first no-fake-play=1")