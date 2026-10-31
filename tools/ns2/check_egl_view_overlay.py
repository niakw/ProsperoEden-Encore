#!/usr/bin/env python3
"""N49: exact source-owner parity guard for the Eglantine Vulkan view fix."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor/sources/eden/src/video_core/renderer_vulkan/vk_texture_cache.cpp"
PORT = ROOT / "headless/ns2/eglantine/video_core/renderer_vulkan/vk_texture_cache.cpp"
CMAKE = ROOT / "headless/CMakeLists.txt"
anchor = '    VkImageViewType view_type = ImageViewType(type);\n    VkImageSubresourceRange subresource_range = MakeSubresourceRange(aspect_mask, range);\n    if (texture_type) {'
replacement = '''    VkImageViewType view_type = ImageViewType(type);
    VkImageSubresourceRange subresource_range = MakeSubresourceRange(aspect_mask, range);
    // Eglantine ca524c9: shader-declared dimensionality must not turn a
    // Vulkan 2D resource into a 3D image view or the other way around.
    if (texture_type &&
        Eden::NS2::Vulkan::CrossDimensionView(view_type, ImageViewType(*texture_type),
                                               VK_IMAGE_VIEW_TYPE_3D)) {
        LOG_WARNING(Render_Vulkan,
                    "NS2 shader image dimension mismatches physical image at 0x{:x}; "
                    "keeping the real image view type", gpu_addr);
        texture_type.reset();
    }
    if (texture_type) {'''
include = '#include "video_core/renderer_vulkan/vk_texture_cache.h"'
original = SOURCE.read_text()
assert original.count(anchor) == 1 and original.count(include) == 1, "owner changed"
expected = original.replace(anchor, replacement).replace(
    include, include + '\n#include "video_core/renderer_vulkan/ns2_view_type_guard.h"')
assert PORT.read_text() == expected, "the experimental Vulkan TU has diverged from its pinned owner"
cmake = CMAKE.read_text()
assert 'EDEN_NS2_EGLANTINE_VIEW_EXPERIMENTAL' in cmake
assert cmake.count('list(REMOVE_ITEM video_sources "renderer_vulkan/vk_texture_cache.cpp")') == 1
assert 'EDEN_NS2_EGLANTINE_VIEW_EXPERIMENTAL OR' in cmake
print("N49_VIEW_OWNER_PARITY_PASS full_pinned_owner=1 release_forbidden=1")
