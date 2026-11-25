#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
hpp=(root/'headless/prosperoeden/pe/ui/launcher.hpp').read_text()
lib=(root/'headless/prosperoeden/pe/ui/library.cpp').read_text()
home=(root/'headless/prosperoeden/pe/ui/home.cpp').read_text()
launch=(root/'headless/prosperoeden/pe/ui/launcher.cpp').read_text()
svc=(root/'headless/prosperoeden/eden_services.cpp').read_text()
for needle in ('start_home_media()', 'finish_home_media()', 'home_media_scan_', 'home_media_next_retry_'):
    assert needle in hpp, needle
assert 'start_home_media();\n}' in home
# Full media work is selected-only, never a background Nlib sweep of
# every installed title. The selected title still gets all 3 screens.
assert 'home_media_priority' not in svc + lib + hpp
assert 'const int wanted_screens = std::clamp(screen_count, 0, 3);' in svc
selected_worker = lib.split('void Launcher::start_selected_media()', 1)[1].split(
    'void Launcher::finish_selected_media()', 1)[0]
assert 'screen_ != Screen::library' in selected_worker
assert 'library_.selected < 0' in selected_worker
assert 'games_[static_cast<std::size_t>(library_.selected)]' in selected_worker
assert 'for (std::size_t offset = 0; offset < games_.size(); ++offset)' not in selected_worker
assert 'services_.enrich_game_media(std::move(copy), &selected_media_cancel_)' in selected_worker
textures_hpp=(root/'headless/prosperoeden/pe/ui/textures.hpp').read_text()
textures_cpp=(root/'headless/prosperoeden/pe/ui/textures.cpp').read_text()
assert 'Cover cover(const std::string &path, float size, bool urgent = false);' in textures_hpp
assert 'bool priority_queued = false;' in textures_hpp
assert 'if (urgent && !it->second.priority_queued && !it->second.loaded)' in textures_cpp
assert 'queue_.erase(queued);' in textures_cpp
assert 'queue_.push_front(key);' in textures_cpp
assert 'it->second.priority_queued = true;' in textures_cpp
assert 'if (urgent || it->second.priority_queued ||' in textures_cpp
assert 'const Cover picture = c.textures.cover(' in home
assert 'art, std::max(card_w - 8.0f, card_h - 8.0f), true);' in home
assert 'constexpr float card_h = card_w;' in home
assert 'start_selected_media();' in lib[lib.index('void Launcher::apply_games'):lib.index('void Launcher::name_home_games')]
assert 'artwork_files.resize(6)' not in svc
assert 'Only Home/recent titles' not in svc
# Both Nlib workers must propagate the session cancellation token. An old
# single-argument check rejected the correct cancellation-aware code.
assert 'services_.enrich_game_media(std::move(request), &media_cancel_)' in lib
assert 'services_.enrich_game_media(std::move(copy), &selected_media_cancel_)' in lib
assert 'if (media_cancel_.load(std::memory_order_acquire)' in lib
assert 'home_.last_hero = enriched.hero' in lib
assert 'home_.last_max_players = enriched.max_players' in lib
assert 'recent.max_players = enriched.max_players' in lib
for field in ('addons', 'language'):
    assert f'game.{field} = enriched.{field}' in lib, field
assert 'game.addons_short = enriched.addons_short' in lib
assert 'game.language_note = enriched.language_note' in lib
assert 'finish_home_media();' in launch
assert 'home_media_scan_.wait();' in launch
assert 'artwork_tasks' not in svc
assert 'Enumerate local/cache-only assets immediately.' in svc
assert 'belongs to the selected-title worker' in svc
assert 'Home separately requests at most one' in svc
assert 'Disk scanning itself must stay network-free.' in svc
assert 'Library enumeration remains' in svc
assert 'local/cache-only; selected-title media and bounded Home icon workers run' in svc
# A damaged/unavailable native ROM directory must not replace an existing
# title snapshot with an empty result; the scan worker reports and throws.
assert 'EDEN_ROM_SCAN entries=' in svc
assert 'EDEN_ROM_SCAN stat_failed=' in svc
assert 'throw std::system_error(directory_error, "ROM directory scan failed")' in svc
assert 'const Rect hero{0.0f, 0.0f, 1920.0f, 1080.0f};' in home
for needle in ('quick settings overlay', 'recently played: seven-ish large artwork tiles',
               'utility cards: the four Home actions', 'hero_button(details_rect, "..."'):
    assert needle in home, needle
assert 'recent.max_players' not in home
assert 'const Cover hero_picture = c.textures.cover(hero_artwork, 1920.0f)' in home
# The visible rail has its independent icon-only worker, not a second full media sweep.
icons = lib.split("void Launcher::start_home_icons()", 1)[1].split("void Launcher::finish_home_icons()", 1)[0]
assert "screen_ != Screen::home" in icons and "media_cancel_.load" in icons
assert "for (const Recent& recent : home_.recents)" in icons
assert "home_icon_scan_.valid()" in icons and "home_icon_next_retry_" in icons
assert "services_.enrich_home_icon(std::move(request), &media_cancel_)" in icons
assert "enrich_game_media" not in icons
native_home = svc.split("pe::ui::Home EdenServices::home(const std::atomic<bool>* cancel)", 1)[1].split("std::string EdenServices::clock()", 1)[0]
assert "ExtractedLocalCover(" in native_home
assert 'const bool deconstructed = Eden::IsDeconstructedGameSelection(home.last_file);' in native_home
assert 'else if (!has_cover)' in native_home
assert 'if (!deconstructed && played.contains(name))' in native_home
assert 'recent.cover = EnsureCover(name);' in native_home
assert 'if (!recent.cover.empty()) recent.tile_icon = recent.cover;' in native_home
# No generic package metadata extraction may run for an ExeFS /main.
assert 'if (cover.empty()) cover = EnsureCover(home.last_file, &title);' not in native_home
assert 'if (!nlib.icon.empty() && recent.tile_icon.empty()' in native_home
native_icon = svc.split("pe::ui::Game EdenServices::enrich_home_icon(", 1)[1].split("pe::ui::Game EdenServices::enrich_game_media(", 1)[0]
assert "NlibTitleMutex(game.title_id), std::try_to_lock" in native_icon
assert '"/icon/512"' in native_icon and "CachedNlibIcon(game.title_id)" in native_icon
assert "EnsureRetailCase" not in native_icon and "EnsureNlibEnrichment" not in native_icon
assert "const std::string& art = recent.tile_icon.empty() ? recent.cover : recent.tile_icon;" in home
assert 'CachedGamesDbSquare(recent.title_id, second_generation)' in svc
assert 'CachedGamesDbSquare(title_id, second_generation)' in svc
assert 'EnsureGamesDbSquare(game.title_id' in native_icon
full_media = svc.split("pe::ui::Game EdenServices::enrich_game_media(pe::ui::Game game,\n", 1)[1]
assert 'NlibEnrichment enrichment = EnsureNlibEnrichment(game.title_id, language_choice, cancel);' in full_media
assert 'const bool second_generation = UseNs2CaseIndex(game);' in native_icon
assert 'game.cover = CachedNlibIcon(game.title_id);' in native_icon
assert native_icon.index("CachedNlibIcon(game.title_id)") < native_icon.index("EnsureGamesDbSquare(game.title_id")
assert 'game.cover == CachedGamesDbSquare(game.title_id, second_generation)' in full_media
assert '? NlibEnrichment{}' not in full_media
# NLIB screenshot must outrank GamesDB fanart when the banner is missing.
assert 'home.last_hero = !nlib.hero.empty() ? nlib.hero :' in native_home
assert '!home.last_screenshot.empty() ? home.last_screenshot :' in native_home
assert 'recent.hero = !nlib.hero.empty() ? nlib.hero :' in native_home
assert '!recent.screenshot.empty() ? recent.screenshot :' in native_home
assert 'else if (nlib_screenshots) game.hero = enrichment.screenshots.front();' in full_media
assert 'game.hero = CachedGamesDbHero(game.title_id, second_generation);' in full_media
assert 'recent.tile_icon = square;' in svc
assert 'recent.cover = box_art(recent.title_id).front;' not in svc
assert 'home.last_cover = box_art(title_id).front;' not in svc
assert 'recent.tile_icon = box_art' not in svc
assert 'game.box_front' not in native_icon
assert "!recent.tile_icon.empty()" in icons
assert "home_media_scan_title_id_" not in icons
assert 'recent.cover.find("/box-front-")' not in icons
assert 'recent.cover = !game.cover.empty() ? game.cover : game.box_front;' not in lib
assert 'switch_game_tile(c,!g.cover.empty()?g.cover:g.box_front' not in (root/'headless/prosperoeden/pe/ui/switch_theme.cpp').read_text()
assert "recent.tile_icon = previous.tile_icon;" in lib
assert "cover(c, art, icon, 20.0f, 0.0f)" in home
assert "home_icon_scan_.wait();" in launch and "finish_home_icons();" in launch
# A generated image or a full media response must never cross an NS1/NS2
# installed-file boundary merely because the emulator sees the same TitleID.
home_completed = lib.split("void Launcher::finish_home_media()", 1)[1].split(
    "void Launcher::start_selected_media()", 1)[0]
selected_completed = lib.split("void Launcher::finish_selected_media()", 1)[1].split(
    "void Launcher::start_selected_size()", 1)[0]
for owner, identity in ((home_completed, "home_media_scan_file_"),
                        (selected_completed, "media_scan_file_")):
    assert f"enriched.file != {identity}" in owner, identity
    assert "game.file != enriched.file" in owner, identity
assert "recent.title_id != enriched.title_id || recent.file != enriched.file" in home_completed
assert "enriched.file == home_.last_file" in home_completed
assert "media_next_retry_[game.file]" in lib
assert "home_media_next_retry_[file]" in lib
assert "home_icon_scan_extra_file_ == recent.file" in home
assert "std::unordered_map<std::string, std::chrono::steady_clock::time_point> media_next_retry_" in hpp
print('Selected-only complete Nlib media, bounded visible icon worker and aspect-safe Home tiles PASS')

# Test the exact current worker, including both historic request branches.
# Async execution uses a deterministic in-memory service, not network or PS5.
import shutil
import subprocess
import tempfile
worker = lib.split("void Launcher::start_home_media()", 1)[1].split(
    "void Launcher::finish_home_media()", 1)[0]
assert "screen_ != Screen::home" in worker
assert worker.index("screen_ != Screen::home") < worker.index("home_media_next_retry_[file]")
cpp = r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <future>
#include <string>
#include <utility>
#include <unordered_map>
#include <vector>
enum class Screen { home, library, settings };
struct Game {
    std::uint64_t title_id=0;
    std::string file,name,cover,hero,intro;
    std::vector<std::string> screenshots;
    int max_players=0;
};
struct Recent {
    std::uint64_t title_id=0;
    std::string file,title,cover,hero,screenshot,intro;
    int max_players=0;
};
struct Home {
    std::uint64_t last_title_id=0;
    std::string last_file,last_title,last_cover,last_hero,last_screenshot,last_intro;
    int last_max_players=0;
    std::vector<Recent> recents;
};
struct Services {
    std::atomic<unsigned> calls{0};
    Game enrich_game_media(Game game,const std::atomic<bool>* cancel) {
        assert(cancel!=nullptr && !cancel->load()); ++calls; return game;
    }
};
struct Launcher {
    Screen screen_=Screen::library;
    Home home_;
    int home_recent_=-1;
    std::atomic<bool> media_cancel_{false};
    Services services_;
    std::future<Game> home_media_scan_;
    std::uint64_t home_media_scan_title_id_=0;
    std::string home_media_scan_file_;
    std::unordered_map<std::string,std::chrono::steady_clock::time_point> home_media_next_retry_;
    void start_home_media();
};
""" + "void Launcher::start_home_media()" + worker + r"""
int main() {
    Launcher l;
    l.home_.last_title_id=101; l.home_.last_file="last"; l.home_.last_max_players=2;
    for(auto screen:{Screen::library,Screen::settings}) {
        l.screen_=screen; l.start_home_media(); assert(!l.home_media_scan_.valid());
        assert(l.home_media_next_retry_.empty() && l.services_.calls==0);
    }
    l.screen_=Screen::home; l.media_cancel_=true; l.start_home_media();
    assert(!l.home_media_scan_.valid() && l.home_media_next_retry_.empty());
    l.media_cancel_=false; l.start_home_media();
    assert(l.home_media_scan_.valid() && l.home_media_scan_title_id_==101 &&
           l.home_media_scan_file_=="last");
    l.start_home_media();
    auto last=l.home_media_scan_.get();
    assert(last.title_id==101 && last.file=="last" && last.max_players==2 && l.services_.calls==1);
    l.start_home_media(); assert(!l.home_media_scan_.valid()); // cooldown
    Recent recent; recent.title_id=202; recent.file="new"; recent.screenshot="shot";
    l.home_.recents.push_back(recent); l.home_recent_=0;
    l.screen_=Screen::library; l.start_home_media(); // late Home completion/restart
    assert(!l.home_media_scan_.valid() && l.home_media_next_retry_.count("new")==0);
    l.screen_=Screen::home; l.start_home_media();
    auto selected=l.home_media_scan_.get();
    assert(selected.title_id==202 && selected.file=="new" && selected.screenshots.size()==1);
    assert(l.home_media_scan_file_=="new");
    assert(l.services_.calls==2);
    // A second installed edition with the SAME TitleID is not blocked by
    // the first edition's network retry cooldown.
    Recent other; other.title_id=101; other.file="other-edition";
    l.home_.recents.push_back(other); l.home_recent_=1;
    l.start_home_media();
    assert(l.home_media_scan_.valid() && l.home_media_scan_file_=="other-edition");
    auto edition=l.home_media_scan_.get();
    assert(edition.title_id==101 && edition.file=="other-edition");
    assert(l.services_.calls==3);
    l.home_recent_=0;
    l.home_.recents[0].title_id=0; l.start_home_media(); assert(!l.home_media_scan_.valid());
}
"""
compiler = shutil.which("clang++") or shutil.which("c++")
assert compiler
with tempfile.TemporaryDirectory(prefix="home-media-visible-") as tmp:
    src=Path(tmp)/"test.cpp"
    src.write_text(cpp)
    for opt in ("-O0","-O2"):
        exe=Path(tmp)/"test"
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror","-pthread",
                        str(src),"-o",str(exe)],check=True,timeout=60)
        subprocess.run([str(exe)],check=True,timeout=10)
print("HOME_MEDIA_VISIBLE_WORKER_PASS hidden=2 cancellation=1 cooldown=1 return=1 actual_owner=1")

# Execute both real icon-worker methods without HTTP, disk or a GPU.
icon_methods = lib[lib.index("void Launcher::start_home_icons()"):lib.rindex("} // namespace pe::ui")]
icon_cpp = r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <future>
#include <string>
#include <unordered_map>
#include <vector>
#include <utility>
enum class Screen { home, library, settings };
struct Game { std::uint64_t title_id=0; std::string file,name,cover; bool artwork_changed=false; bool artwork_deferred=false; };
struct Recent { std::uint64_t title_id=0; std::string file,title,cover; std::string tile_icon{}; };
struct Home { bool setup_ready=true; std::uint64_t last_title_id=0; std::string last_file,last_cover; std::vector<Recent> recents; };
struct Services {
    std::atomic<unsigned> calls{0};
    Game enrich_home_icon(Game g,const std::atomic<bool>* cancel) {
        assert(cancel && !cancel->load());
        calls.fetch_add(1);
        g.cover="nlib-icon-"+std::to_string(g.title_id)+"-"+g.file;
        g.artwork_changed=true;
        return g;
    }
};
struct Textures { unsigned invalidations=0; void invalidate(const std::string&) { ++invalidations; } };
namespace sys { template<class... T> void log(T...) {} }
struct Launcher {
    Screen screen_=Screen::library;
    Home home_;
    std::atomic<bool> media_cancel_{false};
    Services services_;
    Textures textures_;
    std::future<Game> home_icon_scan_;
    std::future<Game> home_icon_scan_extra_;
    std::uint64_t home_icon_scan_title_id_=0, home_icon_scan_extra_title_id_=0;
    std::uint64_t home_media_scan_title_id_=1;
    std::string home_icon_scan_file_, home_icon_scan_extra_file_;
    std::unordered_map<std::string,std::chrono::steady_clock::time_point> home_icon_next_retry_;
    std::vector<Game> games_;
    void start_home_icons();
    void finish_home_icons();
};
""" + icon_methods + r"""
int main() {
    Launcher l;
    l.home_.recents={{1,"selected","A",""},{2,"two","B",""},{3,"three","C","/box-front-3.webp"},{4,"four","D","local-icon"},{3,"different-file","C","fallback","fallback"},{5,"cached","E","fallback","canonical-5"}};
    l.home_.last_title_id=2; l.home_.last_file="two";
    l.games_={{2,"two","B","",false},{3,"three","C","",false},{3,"different-file","C","unchanged",false}};
    l.start_home_icons(); assert(!l.home_icon_scan_.valid());
    l.screen_=Screen::home; l.media_cancel_=true;
    l.start_home_icons(); assert(!l.home_icon_scan_.valid());
    l.media_cancel_=false;
    l.start_home_icons();
    // A slow first title must not block the next title's first square.
    assert(l.home_icon_scan_.valid() && l.home_icon_scan_extra_.valid());
    assert(l.home_icon_scan_file_=="selected" && l.home_icon_scan_extra_file_=="two");
    l.home_icon_scan_.wait(); l.home_icon_scan_extra_.wait();
    l.finish_home_icons();
    assert(l.home_.recents[0].tile_icon=="nlib-icon-1-selected");
    assert(l.home_.recents[1].tile_icon=="nlib-icon-2-two");
    assert(l.home_.last_cover=="nlib-icon-2-two");
    assert(l.games_[0].cover=="nlib-icon-2-two");
    assert(l.services_.calls.load()==2 && l.textures_.invalidations==2);
    assert(l.home_icon_scan_file_.empty() && l.home_icon_scan_extra_file_.empty());

    l.start_home_icons();
    assert(l.home_icon_scan_title_id_==3 && l.home_icon_scan_file_=="three");
    assert(l.home_icon_scan_extra_title_id_==4 && l.home_icon_scan_extra_file_=="four");
    l.home_icon_scan_.wait(); l.home_icon_scan_extra_.wait();
    l.finish_home_icons();
    assert(l.games_[1].cover=="nlib-icon-3-three");
    assert(l.games_[2].cover=="unchanged");
    assert(l.home_.recents[2].cover=="nlib-icon-3-three");
    // Same numeric program ID but a different edition/file is untouched.
    assert(l.home_.recents[4].tile_icon=="fallback");
    assert(l.home_.recents[4].cover=="fallback");
    assert(l.textures_.invalidations==4);

    // The other installed edition may request its OWN square immediately.
    // A TitleID-wide cooldown previously suppressed it for two minutes.
    l.home_.recents[4].tile_icon.clear();
    l.start_home_icons();
    assert(l.home_icon_scan_.valid() && l.home_icon_scan_title_id_==3);
    assert(l.home_icon_scan_file_=="different-file");
    l.home_icon_scan_.wait(); l.finish_home_icons();
    assert(l.games_[2].cover=="nlib-icon-3-different-file");
    assert(l.games_[1].cover=="nlib-icon-3-three");
    assert(l.home_.recents[4].tile_icon=="nlib-icon-3-different-file");
    assert(l.textures_.invalidations==5);

    // A completed request cannot publish after launcher teardown starts.
    l.home_.recents.push_back({6,"cancel","F",""});
    l.start_home_icons(); assert(l.home_icon_scan_file_=="cancel");
    l.home_icon_scan_.wait();
    l.media_cancel_=true;
    l.finish_home_icons();
    assert(l.home_.recents.back().tile_icon.empty());
    l.media_cancel_=false;
    l.home_.recents[1].tile_icon.clear();
    l.home_.recents[1].cover.clear();
    l.start_home_icons();
    assert(!l.home_icon_scan_.valid()); // per-file cooldown, not per-frame retry
    assert(l.services_.calls.load()==6);
}
"""
with tempfile.TemporaryDirectory(prefix="home-icon-visible-") as tmp:
    source=Path(tmp)/"test.cpp"
    source.write_text(icon_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(tmp)/"test"
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror","-pthread",
                        str(source),"-o",str(exe)],check=True,timeout=60)
        subprocess.run([str(exe)],check=True,timeout=10)
print("HOME_VISIBLE_ICONS_HOST_PASS parallel=2 per_file_identity=1 cancellation=1 cooldown=1 actual_owner=1")
