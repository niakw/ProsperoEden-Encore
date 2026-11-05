#!/usr/bin/env python3
"""R10: host source audit for the dedicated HD packs / vendor RomFS bridge.

Requires a checked out vendor tree, not merely a gitlink or a PR title.
Does not claim PS5 compilation, Vulkan interception or console performance.
"""
import argparse
from pathlib import Path
root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument("--vendor-tree", type=Path, required=True)
args=parser.parse_args()
patch=args.vendor_tree/"encore-active/eden-core/src/core/file_sys/patch_manager.cpp"
if not patch.is_file(): raise SystemExit("Maintained vendor patch manager missing")
source=patch.read_text()
game=(root/"headless/main.cpp").read_text()
pack=(root/"tools/graphics/package-hd-textures.py").read_text()
catalogue=(root/"headless/hd_texture_packs.h").read_text()
settings=(root/"headless/settings_store.h").read_text()
launcher=(root/"headless/prosperoeden/pe/ui/library.cpp").read_text()
switch=(root/"headless/prosperoeden/pe/ui/switch_theme.cpp").read_text()
assert "GetEncoreHdTextureLayers(" in source
assert 'parent_path() / "textures"' in source
assert '"@hd:" + name' in source
assert '"encore-hd-textures.json"' in source
assert 'nlohmann::json::parse(bytes.begin(), bytes.end(), nullptr, false)' in source
assert 'matches("title_id", fmt::format("{:016X}", title_id))' in source
assert 'count->get<u64>() > 10000' in source
assert 'type == ContentRecordType::Program' in source
assert 'type == ContentRecordType::Data' in source
assert 'layers.insert(layers.end(), hd_layers.begin(), hd_layers.end());' in source
assert 'std::filesystem::is_symlink(pack_path' in source
assert 'auto romfs_dir = FindSubdirectoryCaseless(pack, "romfs");' in source
assert source.index('layers.insert(layers.end(), hd_layers') < source.index('layers.emplace_back(std::move(extracted));')
assert 'Eden::AssetsPath("textures")' in game
assert 'Eden::HdTextures::List(' in game
assert 'Eden::LoadEnabledHdTexturePacks(title)' in game
assert 'mods_off.push_back(' in game and 'HdTextures::kDisabledPrefix' in game
assert '"@hd:"' in catalogue and 'LoadEnabledHdTexturePacks' in settings
assert 'hd_textures_on' in settings and 'mods_off' in settings
assert '"--textures-root"' in pack and '"--mods-root"' not in pack
assert 'modal_=modal_shown_=Modal::textures' in launcher
assert 'services_.set_hd_texture_enabled(' in launcher
assert 'row_textures' in launcher
assert 'TR("HD textures")' in switch
assert 'Modal::textures' in switch
print("PASS R10 SOURCE: textures/ separate from mods/, native data-only RomFS, per-title disabled-by-default whitelist, distinct UI and migration-free workflow")
