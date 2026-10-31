#!/usr/bin/env python3
"""Strict N57 vendor Vulkan parity: reconstruct the precise original F07 owners.

The N57 additions exist only in versioned vendor C++ plus the one small
ASTC assemble include. No executable code generator or replacement TU is used.
"""
from pathlib import Path
import subprocess

OWNER = Path("vendor/encore-active/eden-vulkan")
ASTC = Path("vendor/encore-active/ns2-astc/include/video_core/renderer_vulkan")
BASELINE = {
    "vk_texture_cache_cost.cpp": ("b2b08b577c3a3f9a4aeda10beb208a1b6d0a07e6",
                                  "3e8c9b250fc97d2d8366cacee3d1b089d3945149"),
    "vk_compute_pass_cost.cpp": ("f6de3b8406e0c312a84b677f6a1c4637ec0cc0f2",
                                 "596f86f2d27c1190f5d57ce6a591e32d419c7f08"),
}
AUXILIARY = {
    "vk_texture_cache.h": "80d2f99e44b13b79d1485cdc8c56e96b457a748d",
    "vk_compute_pass.h": "38e94f9e6c40853829172e2feded3b4d68b9089d",
    "ns2_astc_assemble_layers.inc": "528dd4f4ba78a40a894d9f7c86ad125878201156",
}

def git_blob(data: bytes) -> str:
    import hashlib
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, ("N57 vendor source drift", old[:90])
    return text.replace(old, new)

def normalized(root: Path) -> dict[str, str]:
    for name, expected in AUXILIARY.items():
        path = root / ASTC / name
        assert git_blob(path.read_bytes()) == expected, ("N57 auxiliary source drift", name)

    extra = (root / ASTC / "ns2_astc_assemble_layers.inc").read_text()
    for signature in ("void ASTCDecoderPass::AssembleLayers(", "PreflightAstcLayerDecode(",
                      "image.StorageImageLayerView(", "cmdbuf.Dispatch(dx, dy, 1)",
                      "scheduler.Flush();"):
        assert signature in extra, ("N57 layer decode contract", signature)
    assert "image.host_level_offset" not in extra

    result = {}
    for name, (current_sha, previous_sha) in BASELINE.items():
        text = (root / OWNER / name).read_text()
        assert git_blob(text.encode()) == current_sha, ("N57 maintained source drift", name)
        if name == "vk_texture_cache_cost.cpp":
            # N49's single vendor-owner addition, reversed without masking F07.
            text = once(text,
                '#include "video_core/renderer_vulkan/vk_texture_cache.h"\n'
                '#ifdef EDEN_NS2_VIEW_DIMENSION_GUARD\n'
                '#include "video_core/renderer_vulkan/ns2_view_type_guard.h"\n#endif',
                '#include "video_core/renderer_vulkan/vk_texture_cache.h"')
            start = '#ifdef EDEN_NS2_VIEW_DIMENSION_GUARD\n    // Keep physical 2D/3D dimensionality'
            end = '#endif\n    if (texture_type) {'
            assert text.count(start) == text.count(end) == 1, "N49 guard differs"
            i = text.index(start)
            j = text.index(end, i)
            text = text[:i] + '    if (texture_type) {' + text[j + len(end):]
            assert git_blob(text.encode()) == "46be65804131d8ffcc4951fc70d2cc6a449c2e85", "N49 touched unrelated PS5 GPU source"
            text = once(text, '#include "performance.h"\n#ifdef EDEN_NS2_ASTC_LAYER_DECODE\n#include <stdexcept>\n#endif',
                        '#include "performance.h"')
            text = once(text,
                "                                            VkFormat format, u32 base_layer = 0,\n"
                "                                            u32 layer_count = VK_REMAINING_ARRAY_LAYERS) {",
                "                                            VkFormat format) {")
            text = once(text,
                "            .baseArrayLayer = base_layer,\n            .layerCount = layer_count,",
                "            .baseArrayLayer = 0,\n            .layerCount = VK_REMAINING_ARRAY_LAYERS,")
            begin = "#ifdef EDEN_NS2_ASTC_LAYER_DECODE\nVkImageView Image::StorageImageLayerView("
            end = "#endif\n\nbool Image::IsRescaled() const noexcept {"
            assert text.count(begin) == text.count(end) == 1
            i, j = text.index(begin), text.index(end)
            text = text[:i] + "bool Image::IsRescaled() const noexcept {" + text[j + len(end):]
            begin = "#ifdef EDEN_NS2_ASTC_LAYER_DECODE\nvoid TextureCacheRuntime::AccelerateImageUploadLayers("
            end = "#endif\n\nvoid TextureCacheRuntime::TransitionImageLayout(Image& image) {"
            assert text.count(begin) == text.count(end) == 1
            i, j = text.index(begin), text.index(end)
            text = text[:i] + "void TextureCacheRuntime::TransitionImageLayout(Image& image) {" + text[j + len(end):]
        else:
            text = once(text,
                '#include "video_core/renderer_vulkan/vk_compute_pass.h"\n'
                '#ifdef EDEN_NS2_ASTC_LAYER_DECODE\n#include <stdexcept>\n'
                '#include "video_core/renderer_vulkan/ns2_astc_decode_preflight.h"\n#endif',
                '#include "video_core/renderer_vulkan/vk_compute_pass.h"')
            text = once(text,
                '#ifdef EDEN_NS2_ASTC_LAYER_DECODE\n'
                '#include "video_core/renderer_vulkan/ns2_astc_assemble_layers.inc"\n'
                '#endif\nconstexpr u32 BL3D_BINDING_INPUT_BUFFER  = 0;',
                'constexpr u32 BL3D_BINDING_INPUT_BUFFER  = 0;')
        assert git_blob(text.encode()) == previous_sha, ("N57 changed unrelated F07 native bytes", name)
        result[name] = text
    return result
