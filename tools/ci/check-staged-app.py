#!/usr/bin/env python3
"""Validate a staged PPSA99008 artifact without requiring compile-directory metadata."""
from pathlib import Path
import json
import os
import sys

root = Path(__file__).resolve().parents[2]
app = Path(sys.argv[1] if len(sys.argv) > 1 else root / "build/release/PPSA99008").resolve()
assert app.name == "PPSA99008" and app.is_dir(), app

base = {
    "eboot.bin", "core-homebrew.nro", "sandbox-elevator.elf", "self-updater.elf",
    "encore-release.json", "mihawkgen/network.fgw", "network-hosts.txt",
    "sce_module/libc.prx", "sce_sys/param.json", "sce_sys/icon0.png", "sce_sys/icon0.dds",
    "sce_sys/pic0.dds", "sce_sys/pic1.dds", "sce_sys/snd0.at9",
}
source_ui = root / "headless/prosperoeden/ui"
# A successful installable release must contain the real retail-scan lookup.
# Its absence previously produced a green emulator build but three permanent
# fallback thumbnails; do not silently accept that as a validated package.
case_index_source = source_ui / "box-art-index.tsv"
case_index_staged = app / "ui/box-art-index.tsv"
assert case_index_staged.is_file(), "retail case index missing from installable application"
case_index_text = case_index_staged.read_text(encoding="utf-8")
assert case_index_text.count("\n") > 1000, "retail case index is empty/truncated"
assert "eu:9524e5f7-ccc8-4ce6-a581-03f82c51825e.jpg" in case_index_text, (
    "reference physical front missing from installed scan catalog"
)
ui_expected = {
    "ui/" + p.relative_to(source_ui).as_posix()
    for p in source_ui.rglob("*") if p.is_file()
}
ui_expected.discard("ui/art/backdrop-blur.tga")
ui_expected.discard("ui/art/backdrop.tga")
ui_expected.discard("ui/art/brand.tga")
ui_expected.discard("ui/art/controller.tga")
ui_expected.add("ui/art/controller.webp")
ui_expected.add("ui/art/backdrop.webp")
ui_expected.add("ui/art/brand.webp")
for variant in ("noneon", "white", "dark"):
    ui_expected.add(f"ui/art/brand-{variant}.webp")
# Fixed user-supplied insert sources become lossless WebP at packaging time.
# Encoded source PNG text is deliberately not installed.
for stem in ("switch-logo", "switch-rear-footer", "ns2-head"):
    ui_expected.discard(f"ui/art/{stem}.png.b64")
    ui_expected.add(f"ui/art/{stem}.webp")

# Resumed builds restore the already staged catalog from an earlier Actions
# run: the source-tree index is not regenerated during a stage resume.
ui_expected.add("ui/box-art-index.tsv")

for source in (source_ui / "lang").glob("*.po"):
    ui_expected.add("ui/lang/" + source.with_suffix(".txt").name)
legal_source = root / "LICENSES"
legal_expected = {"legal/LICENSE", "legal/THIRD_PARTY_NOTICES.md", "legal/LIBWEBP_LICENSE.txt", "legal/LIBWEBP_PATENTS.txt", "legal/MIHAWKGEN_LICENSE.md", "legal/MIHAWKGEN_THIRD_PARTY_NOTICES.txt", "legal/FSR3_OPTICAL_LICENSE.txt", "legal/FSR3_OPTICAL_SHADER_LICENSE.txt"} | {
    "legal/LICENSES/" + p.name for p in legal_source.iterdir() if p.is_file()
}
expected = base | ui_expected | legal_expected
actual = {p.relative_to(app).as_posix() for p in app.rglob("*") if p.is_file()}
# Daily art downloads belong only to the user's opt-in data directory;
# neither a first install nor a release update may stage them.
assert not any(x.startswith("ui/art/daily/") for x in actual), (
    "daily art must not be packaged: first user selection owns its download"
)
missing = sorted(expected - actual)
extra = sorted(actual - expected)
assert not missing and not extra, f"package inventory mismatch missing={missing} extra={extra}"
if case_index_source.is_file():
    assert case_index_staged.read_bytes() == case_index_source.read_bytes(), (
        "installed retail index differs from generated host index"
    )
assert (app / "network-hosts.txt").read_bytes() == (root / "headless/network-hosts.txt").read_bytes(), "stale/missing packaged network denylist"
for name in expected:
    p = app / name
    assert not p.is_symlink(), name
    assert p.stat().st_size > 0, name
# All shipped large UI artwork is compressed. Reject accidental regressions
# to uncompressed TGA, extension-only renames and truncated WebP RIFF files.
for image in sorted((app / "ui/art").glob("*.webp")):
    data = image.read_bytes()
    assert len(data) >= 30 and len(data) <= 16 * 1024 * 1024, image
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP", image
    assert int.from_bytes(data[4:8], "little") + 8 == len(data), image
for legacy in ("backdrop.tga", "brand.tga", "controller.tga",
               "brand-noneon.tga", "brand-white.tga", "brand-dark.tga",
               "switch-logo.tga", "switch-rear-footer.tga"):
    assert not (app / "ui/art" / legacy).exists(), legacy

param = json.loads((app / "sce_sys/param.json").read_text())
assert param["titleId"] == "PPSA99008"
assert param["contentId"].endswith("PROSPEROEDEN0001")
assert param["localizedParameters"]["en-US"]["titleName"] == "Prospero.Eden Encore"
assert (app / "sce_sys/icon0.png").read_bytes() == (root / "assets/icon0.png").read_bytes()
assert (app / "sce_sys/icon0.dds").read_bytes() == (root / "assets/icon0.dds").read_bytes()
source_lang = sorted((source_ui / "lang").glob("*.po"))
staged_lang = sorted((app / "ui/lang").glob("*.po"))
assert len(source_lang) == 31, f"expected 31 PS5 launcher catalogs, got {len(source_lang)}"
assert [p.name for p in staged_lang] == [p.name for p in source_lang], "launcher catalog inventory differs"
assert any(p.name == "fr-FR.po" for p in staged_lang), "fr-FR launcher catalog missing"
for source in source_lang:
    staged = app / "ui/lang" / source.name
    companion = app / "ui/lang" / source.with_suffix(".txt").name
    assert staged.read_bytes() == source.read_bytes(), f"stale/corrupt launcher catalog: {source.name}"
    assert companion.read_bytes() == source.read_bytes(), f"stale/corrupt launcher catalog companion: {companion.name}"
assert (app / "sandbox-elevator.elf").stat().st_size > 0
eboot = (app / "eboot.bin").read_bytes()
assert len(eboot) > 1024 * 1024
# The earlier "Nlib hero cached for " diagnostic was intentionally removed when
# banner/icon/screens requests became concurrent for every installed game.
# Keep the authoritative, still-compiled EDEN_NLIB_RESULT and live Nlib API
# endpoint markers. Do NOT insist on historical debug strings in shipping code.
# The native build cache once shipped a stale launcher while packaging current art/catalogs.
# These literals prove the redesigned Home, in-binary French fallback, Nlib enrichment and PS5 HID
# watchdog were all compiled into the shipping binary rather than merely present in the checkout.
for text in (
    "QUICK SETTINGS", "SELECTED GAME", "Confirm this action?", "PARAMÈTRES RAPIDES",
    "api.nlib.cc", "EDEN_NLIB_RESULT title_id=",
    "EDEN_CASE_INDEX status=", "EDEN_CASE_LOOKUP title=", "EDEN_CASE_FETCH status=",
    "/banner/1080p", "/screen/", "fields=name,intro,description,publisher,developer,releaseDate",
    "BUTTON PROFILE", "PlayStation", "Custom PS5", "Custom Switch",
    "EDEN_PAD_MAPPING_FIXED title=", "EDEN_PAD_MAPPING_LOCKED scope=session mode=static game_actions=guest_owned",
    "Minimum", "Recommended", "High", "Ultra",
    "EDEN_HID_NPAD update={}", "EDEN_JIT_ALIAS rx=",
):
    marker = text.encode("utf-8")
    assert marker in eboot, f"stale launcher binary: missing {marker!r}"

nlib_source = (root / "headless/prosperoeden/eden_services.cpp").read_text()
assert 'const int wanted_screens = std::clamp(screen_count, 0, 3);' in nlib_source, "all advertised Nlib screens must be fetched"
assert 'std::vector<std::future<bool>> downloads;' in nlib_source, "complete media downloads must be concurrent"
home_source = (root / "headless/prosperoeden/pe/ui/home.cpp").read_text()
library_source = (root / "headless/prosperoeden/pe/ui/library.cpp").read_text()
assert "Confirmation::launch_game" not in home_source + library_source, "launch still asks for confirmation"
assert "open_game_settings_at_file" in home_source, "Home Triangle no longer opens per-game settings"
assert "recent.hero" in home_source, "recent-game Nlib artwork is not used by Home"
assert "hero_description;" in home_source and "hero_intro" not in home_source, "Home must use Nlib long description only"
assert "game->screenshots" in library_source, "Nlib screenshots are not used by Library"
assert "VIEW ALL GAMES" not in home_source, "removed Home pseudo-link returned"
assert all(marker in home_source for marker in (
    "kHomeQuickPanel", "kHomeQuickFirst", "kHomeStorage", "kHomeControllers", "kHomeFullSettings",
)), "final Home navigation/utility contract missing"
assert "const Rect hero{0.0f, 0.0f, 1920.0f, 1080.0f}" in home_source, "reference hero is not full bleed"
assert "const Cover hero_picture = c.textures.cover(hero_artwork, 1920.0f)" in home_source, "Nlib hero is not full bleed"
assert "utility_card(3" in home_source, "reference four utilities missing"
assert "Cross launches" not in library_source, "text-only controller hint returned"
print(f"Staged Encore artifact PASS ({len(actual)} files, current launcher/runtime markers present)")
