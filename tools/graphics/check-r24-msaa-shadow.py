#!/usr/bin/env python3
"""R24 native Vulkan shadow attachment safety audit (source-level).

No driver/PS5 rendering is claimed by passing this check.
"""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--vendor-root",type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[2]
src=(a.vendor_root/"encore-active/eden-vulkan/msaa_color_shadow_pass.cpp").read_text()
hdr=(a.vendor_root/"encore-active/eden-vulkan/include/video_core/renderer_vulkan/msaa_color_shadow_pass.h").read_text()
cmake=(root/"headless/vulkan.cmake").read_text()
policy=(root/"extras/graphics/msaa_force_policy.h").read_text()

for phrase in [
    "msaa_image=allocator.CreateImage(VkImageCreateInfo",
    ".samples=samples",
    "VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT",
    "VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT",
    "VK_IMAGE_LAYOUT_UNDEFINED",
    "key.resolve_color=true;",
    "key.color_clear_mask=1;",
    "key.color_discard_mask=1;",
    "target.guest_view",
    "attachments",
    "framebuffer=device.GetLogical().CreateFramebuffer",
    "scheduler.RequestOutsideRenderPassOperationContext()",
    "cmd.PipelineBarrier(",
    "scheduler.Finish()",
    "catch (const vk::Exception&)",
    "guest_pass.render_target_count != 1",
    "target.clear_entire_target",
    "guest_pass.uses_depth",
    "guest_pass.storage_or_alias_attachments",
    "MaxwellToVK::SurfaceFormat",
]:
    assert phrase in src,phrase
for phrase in [
    "std::optional<Prepared> TryPrepare",
    "MsaaForce::Requested samples",
    "VkImageView guest_view",
    "bool clear_entire_target",
]:
    assert phrase in hdr,phrase
assert "msaa_color_shadow_pass.cpp" in cmake
assert "msaa_color_shadow_pass.h" in cmake
assert "ShadowRendererNotImplemented" in policy
assert "NativeGuestSamplesAlreadySatisfy" in policy
assert "VK_EXT_multisampled_render_to_single_sampled" in (
    root/"docs/ENCORE_R24_MSAA_FORCE_VULKAN_SHADOW.md").read_text()
assert not (root/"headless/settings_store.h").read_text().find(
    "force_msaa_samples")>=0
print("PASS R24 native MSAA shadow: dedicated multisample attachment, resolve to original guest view, full-clear gate, depth/alias rejection, scheduler lifetime and native CMake compilation")
print("NOT YET CONNECTED: guest draw pipeline sample-count overrides")
