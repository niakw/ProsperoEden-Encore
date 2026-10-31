#!/usr/bin/env python3
"""N57: source-conservative native PS5 Vulkan ASTC layer decoder overlay."""
from pathlib import Path
import argparse

def once(text, old, replacement):
    if text.count(old)!=1:
        raise RuntimeError("N57 native PS5 Vulkan source drift: "+old[:120])
    return text.replace(old,replacement)

def produce(tex_cpp, compute_cpp, tex_h, compute_h):
    t=tex_cpp
    c=compute_cpp
    th=tex_h
    ch=compute_h
    t=once(t,'''[[nodiscard]] vk::ImageView MakeStorageView(const vk::Device& device, u32 level, VkImage image,
                                            VkFormat format) {''',
'''[[nodiscard]] vk::ImageView MakeStorageView(const vk::Device& device, u32 level, VkImage image,
                                            VkFormat format, u32 base_layer = 0,
                                            u32 layer_count = VK_REMAINING_ARRAY_LAYERS) {''')
    t=once(t,'''            .baseArrayLayer = 0,
            .layerCount = VK_REMAINING_ARRAY_LAYERS,
        },
    });
}

[[nodiscard]] VkImageAspectFlags ImageAspectMask''',
'''            .baseArrayLayer = base_layer,
            .layerCount = layer_count,
        },
    });
}

[[nodiscard]] VkImageAspectFlags ImageAspectMask''')
    t=once(t,'''bool Image::IsRescaled() const noexcept {''',"VkImageView Image::StorageImageLayerView(s32 level, u32 layer) {\n    if (level < 0 || static_cast<size_t>(level) >= storage_image_views.size() ||\n        layer >= static_cast<u32>(info.resources.layers)) {\n        throw std::out_of_range(\"NS2 ASTC layer view outside image bounds\");\n    }\n    const size_t count = static_cast<size_t>(info.resources.layers);\n    if (storage_layer_views.empty()) {\n        storage_layer_views.resize(storage_image_views.size() * count);\n    }\n    auto& view = storage_layer_views[static_cast<size_t>(level) * count + layer];\n    if (!view) {\n        view = MakeStorageView(runtime->device.GetLogical(), level, *(this->*current_image),\n                               VK_FORMAT_A8B8G8R8_UNORM_PACK32, layer, 1);\n    }\n    return *view;\n}\n\n"+'''bool Image::IsRescaled() const noexcept {''')
    t=once(t,'''void TextureCacheRuntime::TransitionImageLayout(Image& image) {''',
"void TextureCacheRuntime::AccelerateImageUploadLayers(\n    Image& image, const StagingBufferRef& map,\n    std::span<const VideoCommon::SwizzleParameters> swizzles,\n    std::span<const u32> layers) {\n    if (!astc_decoder_pass || !IsPixelFormatASTC(image.info.format) ||\n        !WillUseAcceleratedAstcDecode(device, image.info)) {\n        throw std::runtime_error(\"NS2 ASTC layer decoder is not enabled for this image\");\n    }\n    astc_decoder_pass->AssembleLayers(image, map, swizzles, layers);\n}\n\n"+'''void TextureCacheRuntime::TransitionImageLayout(Image& image) {''')
    th=once(th,'''    void InsertUploadMemoryBarrier() {}''',
'''    void AccelerateImageUploadLayers(Image&, const StagingBufferRef&,
                                      std::span<const VideoCommon::SwizzleParameters>,
                                      std::span<const u32> layers);

    void InsertUploadMemoryBarrier() {}''')
    th=once(th,'''    VkImageView StorageImageView(s32 level) noexcept;''',
'''    VkImageView StorageImageView(s32 level) noexcept;
    VkImageView StorageImageLayerView(s32 level, u32 layer);
    [[nodiscard]] bool IsInitializedForLayerUpload() const noexcept { return initialized; }''')
    th=once(th,'''    std::vector<vk::ImageView> storage_image_views;''',
'''    std::vector<vk::ImageView> storage_image_views;
    std::vector<vk::ImageView> storage_layer_views;''')
    ch=once(ch,'''    void Assemble(Image& image, const StagingBufferRef& map,
                  std::span<const VideoCommon::SwizzleParameters> swizzles);''',
'''    void Assemble(Image& image, const StagingBufferRef& map,
                  std::span<const VideoCommon::SwizzleParameters> swizzles);
    void AssembleLayers(Image& image, const StagingBufferRef& map,
                        std::span<const VideoCommon::SwizzleParameters> swizzles,
                        std::span<const u32> layers);''')
    c=once(c,'''#include "video_core/renderer_vulkan/vk_compute_pass.h"''',
'''#include "video_core/renderer_vulkan/vk_compute_pass.h"
#include <stdexcept>\n#include "video_core/renderer_vulkan/ns2_astc_decode_preflight.h"''')
    c=once(c,'''constexpr u32 BL3D_BINDING_INPUT_BUFFER  = 0;''',
"void ASTCDecoderPass::AssembleLayers(\n    Image& image, const StagingBufferRef& map,\n    std::span<const VideoCommon::SwizzleParameters> swizzles,\n    std::span<const u32> layers) {\n    using namespace VideoCommon::Accelerated;\n    // Partial decoding is only valid after a successful full initialization.\n    // No speculative UNDEFINED -> GENERAL transition may discard other layers.\n    if (!image.IsInitializedForLayerUpload() ||\n        image.info.type != VideoCommon::ImageType::e2D ||\n        image.info.resources.layers <= 1 || image.info.resources.levels <= 0) {\n        throw std::runtime_error(\"NS2 ASTC partial decode requires initialized 2D array\");\n    }\n    const u64 stride = image.info.layer_stride;\n    std::vector<Eden::NS2::Eglantine::AstcMipSlice> mips;\n    mips.reserve(swizzles.size());\n    for (const auto& swizzle : swizzles) {\n        if (swizzle.level < 0) {\n            throw std::runtime_error(\"NS2 ASTC negative mip level\");\n        }\n        mips.push_back({swizzle.buffer_offset, static_cast<u32>(swizzle.level)});\n    }\n    if (!Eden::NS2::Eglantine::PreflightAstcLayerDecode(\n            static_cast<u32>(image.info.resources.layers),\n            static_cast<u32>(image.info.resources.levels), stride,\n            map.mapped_span.size_bytes(), layers, mips)) {\n        throw std::runtime_error(\"NS2 ASTC invalid partial staging or layer selection\");\n    }\n    const std::array<u32, 2> block_dims{\n        VideoCore::Surface::DefaultBlockWidth(image.info.format),\n        VideoCore::Surface::DefaultBlockHeight(image.info.format),\n    };\n    scheduler.RequestOutsideRenderPassOperationContext();\n    const VkPipeline vk_pipeline = *pipeline;\n    const VkImageAspectFlags aspect_mask = image.AspectMask();\n    const VkImage vk_image = image.Handle();\n    scheduler.Record([vk_pipeline, vk_image, aspect_mask](vk::CommandBuffer cmdbuf) {\n        const VkImageMemoryBarrier barrier{\n            .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,\n            .pNext = nullptr,\n            .srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT,\n            .dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT,\n            .oldLayout = VK_IMAGE_LAYOUT_GENERAL,\n            .newLayout = VK_IMAGE_LAYOUT_GENERAL,\n            .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,\n            .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,\n            .image = vk_image,\n            .subresourceRange{\n                .aspectMask = aspect_mask,\n                .baseMipLevel = 0,\n                .levelCount = VK_REMAINING_MIP_LEVELS,\n                .baseArrayLayer = 0,\n                .layerCount = VK_REMAINING_ARRAY_LAYERS,\n            },\n        };\n        cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                               VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, barrier);\n        cmdbuf.BindPipeline(VK_PIPELINE_BIND_POINT_COMPUTE, vk_pipeline);\n    });\n    for (size_t index = 0; index < layers.size(); ++index) {\n        for (const auto& swizzle : swizzles) {\n            const VkDeviceSize input_offset =\n                map.offset + index * stride + swizzle.buffer_offset;\n            compute_pass_descriptor_queue.Acquire(scheduler, 2);\n            compute_pass_descriptor_queue.AddBuffer(\n                map.buffer, input_offset, stride - swizzle.buffer_offset);\n            compute_pass_descriptor_queue.AddImage(\n                image.StorageImageLayerView(swizzle.level, layers[index]));\n            const void* const descriptor_data{compute_pass_descriptor_queue.UpdateData()};\n            const auto params = MakeBlockLinearSwizzle2DParams(swizzle, image.info);\n            ASSERT(params.origin == (std::array<u32, 3>{0, 0, 0}));\n            ASSERT(params.destination == (std::array<s32, 3>{0, 0, 0}));\n            ASSERT(params.bytes_per_block_log2 == 4);\n            const u32 dx = Common::DivCeil(swizzle.num_tiles.width, 8U);\n            const u32 dy = Common::DivCeil(swizzle.num_tiles.height, 8U);\n            scheduler.Record([this, dx, dy, block_dims, params, descriptor_data](\n                                 vk::CommandBuffer cmdbuf) {\n                const AstcPushConstants uniforms{\n                    .blocks_dims = block_dims,\n                    .layer_stride = params.layer_stride,\n                    .block_size = params.block_size,\n                    .x_shift = params.x_shift,\n                    .block_height = params.block_height,\n                    .block_height_mask = params.block_height_mask,\n                };\n                const VkDescriptorSet set = descriptor_allocator.Commit();\n                device.GetLogical().UpdateDescriptorSet(set, *descriptor_template, descriptor_data);\n                cmdbuf.BindDescriptorSets(VK_PIPELINE_BIND_POINT_COMPUTE, *layout, 0, set, {});\n                cmdbuf.PushConstants(*layout, VK_SHADER_STAGE_COMPUTE_BIT, uniforms);\n                cmdbuf.Dispatch(dx, dy, 1);\n            });\n        }\n    }\n    scheduler.Record([vk_image, aspect_mask](vk::CommandBuffer cmdbuf) {\n        const VkImageMemoryBarrier barrier{\n            .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,\n            .pNext = nullptr,\n            .srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT,\n            .dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT,\n            .oldLayout = VK_IMAGE_LAYOUT_GENERAL,\n            .newLayout = VK_IMAGE_LAYOUT_GENERAL,\n            .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,\n            .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,\n            .image = vk_image,\n            .subresourceRange{\n                .aspectMask = aspect_mask,\n                .baseMipLevel = 0,\n                .levelCount = VK_REMAINING_MIP_LEVELS,\n                .baseArrayLayer = 0,\n                .layerCount = VK_REMAINING_ARRAY_LAYERS,\n            },\n        };\n        cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,\n                               vk::PIPELINE_STAGE_GRAPHICS_COMPUTE, 0, barrier);\n    });\n    { auto timer = Eden::Performance::VulkanTimer(12); scheduler.Flush(); }\n}\n\n"+'''constexpr u32 BL3D_BINDING_INPUT_BUFFER  = 0;''')
    return {"vk_texture_cache_cost.cpp":t, "vk_compute_pass_cost.cpp":c,
            "include/video_core/renderer_vulkan/vk_texture_cache.h":th,
            "include/video_core/renderer_vulkan/vk_compute_pass.h":ch}

def main():
    p=argparse.ArgumentParser()
    for x in ("texture_cpp","compute_cpp","texture_h","compute_h","output"):
        p.add_argument("--"+x.replace("_","-"),required=True)
    args=p.parse_args()
    sources=[Path(getattr(args,x)).read_text() for x in
             ("texture_cpp","compute_cpp","texture_h","compute_h")]
    out=Path(args.output)
    for name,body in produce(*sources).items():
        f=out/name
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(body)
    print("N57_NATIVE_ASTC_LAYER_SOURCE_OVERLAY_CREATED")

if __name__=="__main__":main()
