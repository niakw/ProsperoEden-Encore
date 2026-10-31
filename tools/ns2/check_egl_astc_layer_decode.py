#!/usr/bin/env python3
"""N57: verify exact vendor Vulkan ASTC source and run fail-closed preflight."""
from pathlib import Path
import subprocess
import tempfile
from native_astc_vendor_parity import normalized

ROOT = Path(__file__).resolve().parents[2]
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
BASE = ROOT / "vendor/encore-active/ns2-astc/include/video_core/renderer_vulkan"
SHARED = ROOT / "vendor/encore-active/ns2-helpers/include"
assert 'EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL OR' in CMAKE
assert 'EDEN_NS2_ASTC_LAYER_DECODE=1' in CMAKE
assert 'prepare_egl_astc_layer_decode.py' not in CMAKE
assert 'ns2-astc-layer' not in CMAKE
assert 'vk_compute_pass_cost.cpp' in CMAKE
assert 'vk_texture_cache_cost.cpp' in CMAKE
assert 'target_include_directories(video_core BEFORE PUBLIC' in CMAKE
assert 'GetSparseImageMemoryRequirements' not in (BASE / "vk_compute_pass.h").read_text()
old_owners = normalized(ROOT)
assert len(old_owners) == 2
for name in ("vk_texture_cache_cost.cpp", "vk_compute_pass_cost.cpp"):
    assert "EDEN_NS2_ASTC_LAYER_DECODE" not in old_owners[name]

cache_h = (BASE / "vk_texture_cache.h").read_text()
compute_h = (BASE / "vk_compute_pass.h").read_text()
assert "StorageImageLayerView(s32 level, u32 layer)" in cache_h
assert "std::vector<vk::ImageView> storage_layer_views;" in cache_h
assert "IsInitializedForLayerUpload()" in cache_h
assert "AssembleLayers(Image& image" in compute_h
assert "#ifdef EDEN_NS2_ASTC_LAYER_DECODE" in compute_h
with tempfile.TemporaryDirectory(prefix="n57-vendor-astc-") as t:
    out = Path(t)
    for cxx in ("clang++", "g++"):
        exe = out / ("n57-" + cxx.replace("+", "p"))
        subprocess.run([cxx, "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        "-I", str(SHARED),
                        str(ROOT / "tools/ns2/test_egl_astc_decode_contract.cpp"),
                        "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
print("N57_NATIVE_VENDOR_ASTC_LAYER_OWNER_AND_HOST_CONTRACT_PASS")
