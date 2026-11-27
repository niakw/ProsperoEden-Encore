#!/usr/bin/env python3
"""F03/F04 ordered texture patch ownership on the canonical active source.

The complete patch stack is replayed by install-vendored-eden-backports.py.
This check proves ordering and that each reviewed texture patch contract is
still present in the final canonical owner without incorrectly replaying a
partial stack against pristine Eden.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = Path("src/video_core/texture_cache/texture_cache.h")
ACTIVE = ROOT / "vendor/encore-active/eden" / REL
PATCH_NAMES = (
    "eden-ps5-texture-tic-layer-bounds.patch",
    "eden-ps5-texture-remapped-view-rebind.patch",
    "eden-ps5-texture-remap-target-invalidation.patch",
    "eden-ps5-texture-missing-channel-slot-guard.patch",
)
installer = (ROOT / "tools/apply-eden-backports.sh").read_text()
positions = [installer.index(f'apply_one "$root/headless/backports/{name}"') for name in PATCH_NAMES]
assert positions == sorted(positions), "texture patch replay order changed"
patches = [ROOT / "headless/backports" / name for name in PATCH_NAMES]
assert all(p.is_file() for p in patches)

active = ACTIVE.read_text()
contracts = {
    PATCH_NAMES[0]: "static_cast<u64>(config.BaseLayer()) * info.layer_stride",
    PATCH_NAMES[1]: "is_remapped_view(pair->second)",
    PATCH_NAMES[2]: "framebuffer_affected",
    PATCH_NAMES[3]: "image_view_ids.insert_or_assign(map_index, NULL_IMAGE_VIEW_ID)",
}
for patch in patches:
    marker = contracts[patch.name]
    patch_text = patch.read_text()
    assert marker in patch_text, ("reviewed patch contract drift", patch.name, marker)
    assert marker in active, ("canonical owner lost patch contract", patch.name, marker)

replay = (ROOT / "tools/install-vendored-eden-backports.py").read_text()
assert "apply-eden-backports.sh" in replay and "EDEN_COMPLETE_PATCH_REPLAY_OK" in replay
print("ENCORE_F03_F04_TEXTURE_ORDERED_OWNER_PASS patches=4 full_replay_delegated=1")
