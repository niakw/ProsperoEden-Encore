#!/usr/bin/env python3
"""Protect the intended R10 boundary: mod loader is the sole RomFS pack installer.

R10 is about AI texture generation/conversion, not a second mods UI/loader.
This source guard is not a claim of PS5 image-quality validation.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
main = (root / "headless/main.cpp").read_text()
ui = (root / "headless/prosperoeden/pe/ui/library.cpp").read_text()
launcher = (root / "headless/prosperoeden/pe/ui/launcher.hpp").read_text()
settings = (root / "headless/settings_store.h").read_text()
roadmap = (root / "docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md").read_text()
doc = (root / "docs/ENCORE_R10_HD_TEXTURE_PACKS.md").read_text()

for obsolete in ("HdTextures::List", "LoadEnabledHdTexturePacks", "hd_texture_packs.h"):
    assert obsolete not in main
assert "Eden::Mods::List" in main
assert "Eden::Mods::Summary" in main
assert "row_mods" in ui
assert "Modal::mods" in ui and "mods, // a game" in launcher
assert "row_textures" not in ui
assert "Modal::textures" not in launcher
assert "hd_textures_on" not in settings
assert "GetEncoreHdTextureLayers" not in main
assert not (root / "headless/hd_texture_packs.h").exists()
assert not (root / "tools/graphics/package-hd-textures.py").exists()
assert "Mods" in doc and "R10" in doc
assert "**R10**" in roadmap and "À faire" in next(
    line for line in roadmap.splitlines() if line.startswith("| **R10**")
)
print("PASS R10: existing Mods/RomFS retained, no duplicated textures/ loader, AI texture creation clearly unimplemented")
