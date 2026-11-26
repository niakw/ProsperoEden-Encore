#!/usr/bin/env python3
"""Host compiler smoke for NS2 offline title identity + launcher integration."""
from pathlib import Path
import shutil
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
header=(root/"headless/ns2_title_catalog.h").read_text()
services=(root/"headless/prosperoeden/eden_services.cpp").read_text()
assert '#include "ns2_title_catalog.h"' in services
assert 'Eden::Ns2Catalog::Find(game.title_id)' in services
assert 'return FetchKnownNs2Front(title_id, cancel)' not in services
assert 'return 0u;' in services
# CodeQL #17: the old substring assertion searched *C++ source text*,
# not a runtime URL. Extract the precise C++ assignment and compare entire
# trusted origins instead, including all URL components.
from urllib.parse import urlsplit
import re
hosts = re.search(
    r'const char\* image_host\s*=\s*r2\s*\?\s*"([^"\n]+)"\s*:\s*"([^"\n]+)"\s*;',
    services,
)
assert hosts is not None, "CDN host selector missing"
actual = hosts.groups()
expected = ("https://gamesdb-images.launchbox.gg", "https://images.launchbox-app.com")
assert actual == expected, (actual, expected)
for candidate in actual:
    parsed = urlsplit(candidate)
    assert parsed.scheme == "https" and parsed.netloc in (
        "gamesdb-images.launchbox.gg", "images.launchbox-app.com"
    )
    assert not (parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password)

assert 'EDEN_NS2_TITLE_RESOLVED' in services
assert 'game.cover.empty() && !game.box_front.empty()' not in services
# Behavior, not comments: the initial list must not promote physical case
# media into the square application-icon field.
games_owner = services.split(
    "std::vector<pe::ui::Game> EdenServices::games(const std::atomic<bool>* cancel)", 1
)[1].split("\npe::ui::Game EdenServices::enrich_home_icon(", 1)[0]
assert 'game.cover = game.box_front' not in games_owner
assert 'const pe::ui::BoxArt cached_case = box_art(game.title_id);' not in games_owner
# Preserve extracted Control icon before either square-only cache fallback.
nlib_fallback = 'if (game.cover.empty()) game.cover = CachedNlibIcon(game.title_id);'
gamesdb_fallback = 'if (game.cover.empty()) game.cover = CachedGamesDbSquare(game.title_id, UseNs2CaseIndex(game));'
assert nlib_fallback in games_owner and gamesdb_fallback in games_owner
assert games_owner.index('game.cover = ExtractedLocalCover(') < games_owner.index(nlib_fallback) < games_owner.index(gamesdb_fallback)
assert 'base/exefs/icon.jpg' in services and 'exefs/icon.png' in services
assert 'IsSafeExtractedDirectory(parent)' in services
assert 'icon_' in services and 'std::memcmp(signature,' in services
assert 'IsSafeExtractedDirectory(ancestor)' in services
# The shared CDN artwork encoder was migrated to bounded WebP output.
# Verify the current encode + atomic publish path, not the obsolete TGA name.
fetch = services.split("bool FetchCaseFace(", 1)[1].split("unsigned EnsureRetailCase(", 1)[0]
assert 'WriteJpegWebP(' in fetch and '(require_square || logo) ? 512 : 0' in fetch
assert 'body, staged, !require_square && !logo, &decode_failed,' in fetch
assert 'if (decode_failed)' in fetch
assert fetch.index('const bool encoded = WriteJpegWebP(') < fetch.index('std::rename(staged.c_str(), destination.c_str())')
assert 'if (encoded && std::rename(staged.c_str(), destination.c_str()) == 0)' in fetch
assert 'WebPGetInfo(compressed, length, &checked_w, &checked_h)' in services
assert 'std::rename(staged.c_str(), destination.c_str())' in services
assert 'std::rename(staged.c_str(), destination.c_str())' in services
assert 'FetchKnownNs2Front' not in services
assert 'front_host' not in header and 'front_path' not in header
compiler=shutil.which("clang++") or shutil.which("g++")
if not compiler: raise SystemExit("No native C++20 compiler")
source=r"""
#include <cassert>
#include <cstdint>
#include <string_view>
#include "ns2_title_catalog.h"
int main() {
    using Eden::Ns2Catalog::Find;
    static_assert(Eden::Ns2Catalog::kTitles.size() == 18);
    const auto* mkw = Find(0x0400C3F00006E000ULL);
    const auto* dk = Find(0x040074A01BF12000ULL);
    assert(mkw && mkw->name == "Mario Kart World");
    assert(dk && dk->name == "Donkey Kong Bananza");
    assert(!Find(0x0100C49025D3E000ULL));
    using Eden::Ns2Catalog::SelectDescription;
    assert(SelectDescription(0x0100000000001000ULL, true, "", "").empty());
    assert(SelectDescription(0x0100000000001000ULL, true, "Si vous achetez la version numérique", "").empty());
    assert(SelectDescription(0x0100000000001000ULL, true, "Si vous achetez la version numérique", "Un vrai résumé") == "Un vrai résumé");
    assert(SelectDescription(0x0100000000001000ULL, true, "Un vrai résumé", "") == "Un vrai résumé");
    for (const auto& item : Eden::Ns2Catalog::kTitles) {
        assert(!item.name.empty() && (item.id >> 56) == 4);
        assert(item.id != 0 && !item.name.empty());
    }
    for (std::size_t i = 0; i < Eden::Ns2Catalog::kTitles.size(); ++i)
        for (std::size_t j = i+1; j < Eden::Ns2Catalog::kTitles.size(); ++j)
            assert(Eden::Ns2Catalog::kTitles[i].id != Eden::Ns2Catalog::kTitles[j].id);
}
"""
with tempfile.TemporaryDirectory(prefix="encore-ns2-catalog-") as tmp:
    cpp=Path(tmp)/"test.cpp"
    cpp.write_text(source)
    exe=Path(tmp)/"test"
    subprocess.run([compiler,"-std=c++20","-Wall","-Wextra","-Werror",
                    "-I",str(root/"headless"),str(cpp),"-o",str(exe)],
                   check=True,timeout=30)
    subprocess.run([str(exe)],check=True,timeout=10)
print("ENCORE_NS2_TITLE_CATALOG_HOST_PASS IDs=18 safety=1 launch_integration=1")

# Portrait retail scans remain physical-case media, never square tile art.
assert 'switch_game_tile(c,!g.cover.empty()?g.cover:g.box_front' not in (root/'headless/prosperoeden/pe/ui/switch_theme.cpp').read_text()
assert 'recent.cover = !game.cover.empty() ? game.cover : game.box_front;' not in (root/'headless/prosperoeden/pe/ui/library.cpp').read_text()
