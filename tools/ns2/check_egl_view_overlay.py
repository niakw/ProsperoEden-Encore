#!/usr/bin/env python3
"""N49: verify single maintained native Vulkan view owner, not a second TU."""
from pathlib import Path
from native_astc_vendor_parity import normalized

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp"
HEADER = ROOT / "vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_view_type_guard.h"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
src = SOURCE.read_text()
assert "#ifdef EDEN_NS2_VIEW_DIMENSION_GUARD" in src
assert "CrossDimensionView(view_type, ImageViewType(*texture_type)" in src
assert src.count("VkImageViewType view_type = ImageViewType(type);") == 1
assert HEADER.exists()
assert "CrossDimensionView(" in HEADER.read_text()
assert "EDEN_NS2_VIEW_DIMENSION_GUARD=1" in CMAKE
assert "EDEN_NS2_VIEW_EXPERIMENTAL OR" in CMAKE
assert "eden_ns2_egl_view_file" not in CMAKE
assert "headless/ns2/eglantine/video_core/renderer_vulkan/vk_texture_cache.cpp" not in CMAKE

# N49 and N57 are both removed by the byte-strict shared F07 source oracle.
native = normalized(ROOT)
assert "EDEN_NS2_VIEW_DIMENSION_GUARD" not in native["vk_texture_cache_cost.cpp"]
assert "EDEN_NS2_ASTC_LAYER_DECODE" not in native["vk_texture_cache_cost.cpp"]
assert "EDEN_NS2_ASTC_LAYER_DECODE" not in native["vk_compute_pass_cost.cpp"]
print("N49_VIEW_NATIVE_VENDOR_PARITY_AND_DEFAULT_SOURCE_PASS")
