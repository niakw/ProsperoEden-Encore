#!/usr/bin/env python3
"""Prove that native software-blitter source preserves the shipping backport."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
backport = (root / "vendor/encore-active/eden-backports/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
upstream = (root / "vendor/sources/eden/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
maintained = (root / "vendor/encore-active/eden-core/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
decoder = (root / "vendor/sources/eden/src/video_core/textures/decoders.cpp").read_text()
module = (root / "headless/gpu_native_observability.cmake").read_text()

assert upstream != backport, "shipping 2D pixel-index backport disappeared"
assert "floor/ceil yield ordinary pixel coordinates" in backport
changes = json.loads(r'''[["static_cast<size_t>(surface.pitch * surface.height)","static_cast<size_t>(surface.pitch) * surface.height"],["const size_t src_copy_size = src_extent_x * src_extent_y * src_bytes_per_pixel;","const size_t src_copy_size = static_cast<size_t>(src_extent_x) * src_extent_y * src_bytes_per_pixel;"],["const size_t dst_copy_size = dst_extent_x * dst_extent_y * dst_bytes_per_pixel;","const size_t dst_copy_size = static_cast<size_t>(dst_extent_x) * dst_extent_y * dst_bytes_per_pixel;"]]''')
for before, after in changes:
    assert backport.count(before) == 1, ("shipping blitter changed", before)
    backport = backport.replace(before, after)

# Lichii #2121 / 23e5a91: Switch 2 block-linear Fermi2D copies must use
# MemoryManager's native-tiling mode on both source and destination transforms.
# Keep this composition exact so unrelated maintained-source drift still fails.
native_tiling_changes = [
    (
        "                         src.block_height, src.block_depth, src_extent_x * src_bytes_per_pixel);",
        "                         src.block_height, src.block_depth, src_extent_x * src_bytes_per_pixel,\n"
        "                         memory_manager.UsesNativeTiling());",
    ),
    (
        "                       dst.block_height, dst.block_depth, dst_extent_x * dst_bytes_per_pixel);",
        "                       dst.block_height, dst.block_depth, dst_extent_x * dst_bytes_per_pixel,\n"
        "                       memory_manager.UsesNativeTiling());",
    ),
]
for before, after in native_tiling_changes:
    assert backport.count(before) == 1, ("shipping blitter native-tiling anchor changed", before)
    backport = backport.replace(before, after)
assert maintained == backport, (
    "complete maintained source diverges from shipping baseline plus three widened "
    "arithmetic expressions and Lichii #2121 native-tiling forwarding"
)
for token in ("src.depth, config.src_x0", "dst.depth, config.dst_x0",
              "static_cast<size_t>(surface.pitch) * surface.height",
              "const size_t src_copy_size = static_cast<size_t>(src_extent_x)",
              "const size_t dst_copy_size = static_cast<size_t>(dst_extent_x)"):
    assert token in maintained, token
assert "static constexpr u32 origin_z = 0;" in decoder
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_NATIVE_BLITTER}")' in module
assert 'list(FILTER sw_blitter_sources EXCLUDE REGEX "engines/sw_blitter/blitter[.]cpp$")' in module
assert 'write_derived("${PORT_BUILD_DIR}/sw_blitter_sized.cpp"' not in module
assert 'file(READ "${PROJECT_SOURCE_DIR}/src/video_core/engines/sw_blitter/blitter.cpp"' not in module
assert "EDEN_UNQUALIFIED_FERMI2D_COPY" in module
print("VENDOR_MAINTAINED_SW_BLITTER_PARITY_PASS: shipping backport plus 3 arithmetic corrections plus Lichii_2121_native_tiling=2")
