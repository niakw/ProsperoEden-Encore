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
assert 'services_.enrich_game_media(std::move(copy), &media_cancel_)' in selected_worker
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
assert 'services_.enrich_game_media(std::move(copy), &media_cancel_)' in lib
assert 'if (media_cancel_.load(std::memory_order_acquire)' in lib
assert 'home_.last_hero = enriched.hero' in lib
assert 'home_.last_max_players = enriched.max_players' in lib
assert 'recent.max_players = enriched.max_players' in lib
assert 'finish_home_media();' in launch
assert 'home_media_scan_.wait();' in launch
assert 'artwork_tasks' not in svc
assert 'A library enumeration itself must remain local/cache-only' in svc
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
native_icon = svc.split("pe::ui::Game EdenServices::enrich_home_icon(", 1)[1].split("pe::ui::Game EdenServices::enrich_game_media(", 1)[0]
assert "NlibTitleMutex(game.title_id), std::try_to_lock" in native_icon
assert '"/icon/512"' in native_icon and "CachedNlibIcon(game.title_id)" in native_icon
assert "EnsureRetailCase" not in native_icon and "EnsureNlibEnrichment" not in native_icon
assert "const std::string& art = recent.cover;" in home
assert "cover(c, art, icon, 20.0f, 0.0f)" in home
assert "home_icon_scan_.wait();" in launch and "finish_home_icons();" in launch
print('Selected-only complete Nlib media, bounded visible icon worker and aspect-safe Home tiles PASS')

# Test the exact current worker, including both historic request branches.
# Async execution uses a deterministic in-memory service, not network or PS5.
import shutil
import subprocess
import tempfile
worker = lib.split("void Launcher::start_home_media()", 1)[1].split(
    "void Launcher::finish_home_media()", 1)[0]
assert "screen_ != Screen::home" in worker
assert worker.index("screen_ != Screen::home") < worker.index("home_media_next_retry_[title_id]")
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
    std::unordered_map<std::uint64_t,std::chrono::steady_clock::time_point> home_media_next_retry_;
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
    assert(l.home_media_scan_.valid() && l.home_media_scan_title_id_==101);
    l.start_home_media();
    auto last=l.home_media_scan_.get();
    assert(last.title_id==101 && last.file=="last" && last.max_players==2 && l.services_.calls==1);
    l.start_home_media(); assert(!l.home_media_scan_.valid()); // cooldown
    Recent recent; recent.title_id=202; recent.file="new"; recent.screenshot="shot";
    l.home_.recents.push_back(recent); l.home_recent_=0;
    l.screen_=Screen::library; l.start_home_media(); // late Home completion/restart
    assert(!l.home_media_scan_.valid() && l.home_media_next_retry_.count(202)==0);
    l.screen_=Screen::home; l.start_home_media();
    auto selected=l.home_media_scan_.get();
    assert(selected.title_id==202 && selected.file=="new" && selected.screenshots.size()==1);
    assert(l.services_.calls==2);
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
icon_methods = lib[lib.index("void Launcher::start_home_icons()"):lib.index("void Launcher::start_home_media()")]
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
struct Game { std::uint64_t title_id=0; std::string file,name,cover; bool artwork_changed=false; };
struct Recent { std::uint64_t title_id=0; std::string file,title,cover; };
struct Home { bool setup_ready=true; std::uint64_t last_title_id=0; std::string last_file,last_cover; std::vector<Recent> recents; };
struct Services {
    unsigned calls=0;
    Game enrich_home_icon(Game g,const std::atomic<bool>* cancel) {
        assert(cancel && !cancel->load()); ++calls;
        g.cover="nlib-icon-"+std::to_string(g.title_id); g.artwork_changed=true;
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
    std::uint64_t home_icon_scan_title_id_=0, home_media_scan_title_id_=1;
    std::unordered_map<std::uint64_t,std::chrono::steady_clock::time_point> home_icon_next_retry_;
    std::vector<Game> games_;
    void start_home_icons();
    void finish_home_icons();
};
""" + icon_methods + r"""
int main() {
    Launcher l;
    l.home_.recents={{1,"selected","A",""},{2,"two","B",""},{3,"three","C","/box-front-3.webp"},{4,"four","D","local-icon"}};
    l.home_.last_title_id=2; l.home_.last_file="two";
    l.games_={{2,"two","B","",false},{3,"three","C","",false},{3,"different-file","C","unchanged",false}};
    l.start_home_icons(); assert(!l.home_icon_scan_.valid());
    l.screen_=Screen::home; l.media_cancel_=true;
    l.start_home_icons(); assert(!l.home_icon_scan_.valid());
    l.media_cancel_=false; l.start_home_icons();
    assert(l.home_icon_scan_.valid() && l.home_icon_scan_title_id_==2);
    l.start_home_icons(); l.home_icon_scan_.wait(); l.finish_home_icons();
    assert(l.home_.last_cover=="nlib-icon-2" && l.home_.recents[1].cover=="nlib-icon-2");
    assert(l.games_[0].cover=="nlib-icon-2" && l.services_.calls==1);
    l.start_home_icons(); assert(l.home_icon_scan_title_id_==3);
    l.home_icon_scan_.wait(); l.finish_home_icons();
    assert(l.games_[1].cover=="nlib-icon-3" && l.games_[2].cover=="unchanged");
    assert(l.home_.recents[2].cover=="nlib-icon-3" && l.textures_.invalidations==2);
    l.start_home_icons(); assert(!l.home_icon_scan_.valid() && l.services_.calls==2);
    l.home_.recents[1].cover.clear(); l.start_home_icons();
    assert(!l.home_icon_scan_.valid()); // retry not every frame
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
print("HOME_VISIBLE_ICONS_HOST_PASS independent=1 selected_only_full_media=1 exact_identity=1 cancellation=1 cooldown=1 actual_owner=1")
