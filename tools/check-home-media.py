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
print('Selected-only Nlib artwork and preserved Home worker + TV-first layout PASS')

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


# R457: independent bounded Home icon rail; full-media worker above stays unchanged.
icons=lib.split('void Launcher::start_home_icons()',1)[1].split('void Launcher::finish_home_icons()',1)[0]
assert 'for (const Recent& recent : home_.recents)' in icons
assert 'home_recent_' not in icons and 'enrich_game_media' not in icons
assert 'std::chrono::minutes(5)' in icons
assert 'services_.enrich_home_icon(title_id, &media_cancel_)' in icons
finish_icons=lib.split('void Launcher::finish_home_icons()',1)[1].split('void Launcher::start_home_media()',1)[0]
assert 'recent.title_id == home_icon_scan_title_id_' in finish_icons
assert 'recent.tile_icon = icon;' in finish_icons
owner=svc.split('std::string EdenServices::enrich_home_icon(',1)[1].split('pe::ui::Game EdenServices::enrich_game_media(',1)[0]
assert 'NlibTitleLocks()' in owner and 'CachedNlibIcon(title_id)' in owner
assert '/icon/512' in owner and 'EnsureRetailCase' not in owner and 'EnsureNlibEnrichment' not in owner
assert 'home_icon_scan_.wait();' in launch
assert 'recent.tile_icon.empty() ? recent.tile_icon' not in home
assert 'const std::string& art = !recent.tile_icon.empty() ? recent.tile_icon : recent.cover;' in home
assert 'cover_icon(c, art,' in home
# Compile the exact new queue function using the existing deterministic mock.
icon_cpp = cpp.split('void Launcher::start_home_media()',1)[0].replace('std::string file,title,cover,hero,screenshot,intro;', 'std::string file,title,cover,hero,screenshot,intro,tile_icon;').replace('std::uint64_t last_title_id=0;', 'bool setup_ready=true; std::uint64_t last_title_id=0;').replace('    std::atomic<unsigned> calls{0};','    std::atomic<unsigned> calls{0};\n    std::string enrich_home_icon(std::uint64_t id,const std::atomic<bool>* cancel) { assert(!cancel->load()); ++calls; return std::to_string(id); }').replace('    void start_home_media();','    std::future<std::string> home_icon_scan_;\n    std::uint64_t home_icon_scan_title_id_=0;\n    std::unordered_map<std::uint64_t,std::chrono::steady_clock::time_point> home_icon_next_retry_;\n    void start_home_icons();')
# The original fragment ends just before the extracted method; reconstruct the mock class.
assert 'void start_home_icons();' in icon_cpp
icon_cpp += 'void Launcher::start_home_icons()' + icons + r'''
int main() {
    Launcher l;
    for (unsigned id=1; id<=7; ++id) { Recent r; r.title_id=id; l.home_.recents.push_back(r); }
    l.home_.recents[0].tile_icon="cached";
    l.start_home_icons(); assert(!l.home_icon_scan_.valid());
    l.screen_=Screen::home; l.media_cancel_=true; l.start_home_icons(); assert(!l.home_icon_scan_.valid());
    l.media_cancel_=false;
    for (unsigned id=2;id<=7;++id) {
        l.start_home_icons(); assert(l.home_icon_scan_title_id_==id);
        l.start_home_icons(); assert(l.home_icon_scan_.get()==std::to_string(id));
    }
    l.start_home_icons(); assert(!l.home_icon_scan_.valid()); assert(l.services_.calls==6);
}
'''
with tempfile.TemporaryDirectory(prefix='home-icons-visible-') as tmp:
    src=Path(tmp)/'test.cpp'; src.write_text(icon_cpp)
    for opt in ('-O0','-O2'):
        exe=Path(tmp)/'test'
        subprocess.run([compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror','-pthread',str(src),'-o',str(exe)],check=True,timeout=60)
        subprocess.run([str(exe)],check=True,timeout=10)
print('HOME_ICON_RAIL_PASS independent=1 visible=7 cached_skip=1 cancellation=1 cooldown=1')
