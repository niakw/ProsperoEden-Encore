#!/usr/bin/env python3
"""R09: validate that three user A4K presets map to distinct pinned CNNs.
Host-only: no PS5, ROM or NVIDIA runtime needed.
"""
import argparse
import hashlib
import re
from pathlib import Path

LABELS = (
    "A4K — Détails améliorés",
    "A4K — Image adoucie",
    "A4K — Image nettoyée",
)
IDS = ("anime4k_3d", "anime4k_soft", "anime4k_denoise")
MODELS = {
    "Anime4K_3DGraphics_Upscale_x2_US.glsl":
        "ccfd16fa65908fbafe27114cf65ddc043bc746d4086716c2a85e97a283d9fe5e",
    "Anime4K_Restore_CNN_Soft_S.glsl":
        "9f6867f2ef42786729522d86fe24147cb4ea145418e3974df70496acf52dc392",
    "Anime4K_Upscale_Denoise_CNN_x2_S.glsl":
        "1a45ad3aa20d8368399f2fd46791deed957c2fd0a4afd131cc92516827abab93",
}
EXPECTED = {
    "Details": ((-1, -1, 0), (0, -1, 1), (1, -1, 0), (-1, 0, 3)),
    "Soft": ((-1, -1, 0), (0, -1, 1), (1, -1, 0), (-1, 0, 2),
             (2, -1, 0), (0, -1, 1), (1, -1, 0), (2, 0, 3)),
    "Denoise": ((-1, -1, 0), (0, -1, 1), (1, -1, 0), (0, -1, 1), (-1, 1, 3)),
}

def validate(root: Path, vendor: Path) -> None:
    store = (root / "headless/settings_store.h").read_text()
    fake = (root / "headless/prosperoeden/host/fake_services.cpp").read_text()
    main = (root / "headless/main.cpp").read_text()
    config = (root / "headless/vulkan.cmake").read_text()
    launcher = (root / "headless/vulkan_present_layer_r24.cpp").read_text()
    guides = (root / "headless/prosperoeden/pe/ui/video_guidance.hpp").read_text()
    enum = (vendor / "sources/eden/src/common/settings_enums.h").read_text()
    native = (vendor / "encore-active/eden-vulkan/anime4k_3d.cpp").read_text()
    shaders = vendor / "encore-active/eden-vulkan/r09_anime4k_3d"
    assert all(f'"{i}"' in store for i in IDS), "Persisted A4K keys missing"
    assert all(label in store and label in fake and label in guides
               for label in LABELS), "Inconsistent human-readable A4K labels"
    assert '"Anime4K 3D CNN x2"' not in store
    assert "SgsrEdge, Anime4K3D, Anime4KSoft, Anime4KDenoise);" in enum
    assert "ScalingFilter::Anime4KDenoise" in main
    for profile in ("Details", "Soft", "Denoise"):
        assert "Anime4K3D::Profile::" + profile in launcher
        assert "case Profile::" + profile + ":" in native
    assert "compile_anime4k_profiles.py" in config
    assert "EDEN_R09_PROFILE_HEADERS" in config
    for filename, sha in MODELS.items():
        content = (shaders / filename).read_bytes()
        assert content.startswith(b"// MIT License"), filename
        assert hashlib.sha256(content).hexdigest() == sha, filename
    for profile, expected in EXPECTED.items():
        a = native.index("case Profile::" + profile + ":")
        b = native.index("break;", a)
        block = native[a:b]
        n = re.search(r"stage_count\s*=\s*(\d+)", block)
        assert n and int(n.group(1)) == len(expected), profile
        stage_start = block.index("stages = {{")
        stage_end = block.index("}};", stage_start)
        actual = tuple(tuple(map(int, triple)) for triple in re.findall(
            r"\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}",
            block[stage_start:stage_end]))
        assert actual == expected, (profile, actual, expected)
        written = set()
        for number, (source, feature, destination) in enumerate(actual):
            assert destination not in (source, feature), (profile, number, "read/write alias")
            assert source < 0 or source in written, (profile, number, "uninitialized source")
            assert feature < 0 or feature in written, (profile, number, "uninitialized feature")
            assert destination in (0, 1, 2, 3), (profile, number, "bad scratch slot")
            assert destination != 3 or number == len(actual)-1, (profile, number, "early output")
            written.add(destination)
        assert actual[-1][2] == 3, (profile, "missing output")
    print("A4K_3_PROFILES_CONFIG_LABELS_PINNED_MODELS_AND_GRAPH_HAZARDS_OK")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--vendor", type=Path, required=True)
    args = p.parse_args()
    validate(args.root, args.vendor)
