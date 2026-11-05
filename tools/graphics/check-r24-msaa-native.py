#!/usr/bin/env python3
"""R24: verify REAL guest-controlled Vulkan MSAA, not fake post-AA toggles.

Requires a concrete extracted checkout of the emulator core; this is a
SOURCE CONTRACT check, not a claim of PS5 driver support or image-quality proof.
"""
import argparse
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument("--engine-src",type=Path,required=True,
                    help="Path to exact pinned vendor/sources/eden/src")
args=parser.parse_args()
src=args.engine_src/"video_core/renderer_vulkan"
needed={
  "mode":src/"maxwell_to_vk.cpp",
  "graphics":src/"vk_graphics_pipeline.cpp",
  "texture":src/"vk_texture_cache.cpp",
  "renderpass":src/"vk_render_pass_cache.cpp",
  "blit":src/"blit_image.cpp",
}
data={key:path.read_text() for key,path in needed.items()}
mode=data["mode"]
assert "VkSampleCountFlagBits MsaaMode" in mode
for suffix in ("1_BIT","2_BIT","4_BIT","8_BIT"):
    assert f"VK_SAMPLE_COUNT_{suffix}" in mode
for name in ("Msaa1x1","Msaa2x1","Msaa2x2","Msaa4x2"):
    assert name in mode
graphics=data["graphics"]
assert "MaxwellToVK::MsaaMode(state.msaa_mode)" in graphics
assert ".rasterizationSamples = MaxwellToVK::MsaaMode(key.state.msaa_mode)" in graphics
tex=data["texture"]
assert ".samples = ConvertSampleCount(info.num_samples)" in tex
assert "const bool msaa_to_non_msaa = src.info.num_samples > 1" in tex
assert "CopyImageMSAA(" in tex or "CopyMSAA(" in tex
rp=data["renderpass"]
assert "key.samples != VK_SAMPLE_COUNT_1_BIT" in rp
assert "pResolveAttachments" in rp
assert "SupportsDepthStencilResolve(" in rp
assert "VK_STRUCTURE_TYPE_SUBPASS_DESCRIPTION_DEPTH_STENCIL_RESOLVE" in rp or "VkSubpassDescriptionDepthStencilResolve" in rp
blit=data["blit"]
assert "CopyMSAA(" in blit
assert "CONVERT_MSAA_TO_NON_MSAA_FRAG_SPV" in blit
assert "CONVERT_NON_MSAA_TO_MSAA_FRAG_SPV" in blit
print("PASS R24 native guest MSAA: 1x/2x/4x/8x modes, guest raster state, multisampled images, color/depth resolve, MSAA format conversion")
print("LIMIT: cannot force 2x/4x/8x when the guest renders to 1x surfaces; PS5 capabilities and performance not yet measured")
