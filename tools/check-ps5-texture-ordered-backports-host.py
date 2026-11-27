#!/usr/bin/env python3
"""F03/F04 ordered texture patch replay from frozen source plus canonical-owner parity."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REL = Path("src/video_core/texture_cache/texture_cache.h")
SOURCE = ROOT / "vendor/sources/eden" / REL
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

with tempfile.TemporaryDirectory(prefix="encore-texture-stack-replay-") as td:
    stage = Path(td)
    target = stage / REL
    target.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE, target)
    for patch in patches:
        for args in (["--check", str(patch)], [str(patch)]):
            run = subprocess.run(["git", "apply", *args], cwd=stage,
                                 capture_output=True, text=True, timeout=25)
            assert run.returncode == 0, (patch.name, args, run.stderr[-3500:])
    replayed = target.read_text()

active = ACTIVE.read_text()
contracts = (
    "static_cast<u64>(config.BaseLayer()) * info.layer_stride",
    "is_remapped_view(pair->second)",
    "framebuffer_affected",
    "image_view_ids.insert_or_assign(map_index, NULL_IMAGE_VIEW_ID)",
)
for marker in contracts:
    assert marker in replayed, ("frozen replay lost contract", marker)
    assert marker in active, ("canonical owner lost contract", marker)
print("ENCORE_F03_F04_TEXTURE_ORDERED_REPLAY_PASS patches=4 canonical_owner=1")
