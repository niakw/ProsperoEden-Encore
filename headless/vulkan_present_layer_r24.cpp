// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// R24 maintained native AA layer. Based on the pinned Encore Vulkan fork
// SHA256 f1b2ea6d7bc607c35a7fc7ccfbb5ff6d12ecc6dfec2adf3268a730cead382a87;
// vendor remains unchanged.
// SPDX-FileCopyrightText: Copyright 2024 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include <algorithm>
#include <array>
#include <exception>
#include <memory>
#include <string>
#include <stdexcept>
#include <variant>
#include "aa_source_extent.h"
#include "nr_display_capture_policy.h"
#include "neural_runtime_state.h"
#include "r09_native_plans.h"
#include "storage_paths.h"
#include "video_core/renderer_vulkan/nr_rdna2_frame_session.h"
#include "common/logging.h"
#include "fxaa_quality_select.h"
#include "video_core/present.h"
#include "video_core/renderer_vulkan/present/anti_alias_pass.h"
/* X11 defines */
#undef Success
#undef BadValue
#include "video_core/renderer_vulkan/vk_rasterizer.h"

#include "common/settings.h"
#include "video_core/framebuffer_config.h"
#include "video_core/renderer_vulkan/present/fsr.h"
#include "video_core/renderer_vulkan/present/sgsr.h"
#include "video_core/renderer_vulkan/present/fxaa.h"
#include "video_core/renderer_vulkan/present/layer.h"
#include "video_core/renderer_vulkan/present/present_push_constants.h"
#include "video_core/renderer_vulkan/present/smaa.h"
#include "video_core/renderer_vulkan/present/util.h"
#include "video_core/renderer_vulkan/vk_blit_screen.h"
#include "video_core/textures/decoders.h"

namespace Vulkan {

namespace {

u32 GetBytesPerPixel(const Tegra::FramebufferConfig& framebuffer) {
    using namespace VideoCore::Surface;
    return BytesPerBlock(PixelFormatFromGPUPixelFormat(framebuffer.pixel_format));
}

std::size_t GetSizeInBytes(const Tegra::FramebufferConfig& framebuffer) {
    return static_cast<std::size_t>(framebuffer.stride) *
           static_cast<std::size_t>(framebuffer.height) * GetBytesPerPixel(framebuffer);
}

VkFormat GetFormat(const Tegra::FramebufferConfig& framebuffer) {
    switch (framebuffer.pixel_format) {
    case Service::android::PixelFormat::Rgba8888:
    case Service::android::PixelFormat::Rgbx8888:
        return VK_FORMAT_A8B8G8R8_UNORM_PACK32;
    case Service::android::PixelFormat::Rgb565:
        return VK_FORMAT_R5G6B5_UNORM_PACK16;
    case Service::android::PixelFormat::Bgra8888:
        return VK_FORMAT_B8G8R8A8_UNORM;
    default:
        UNIMPLEMENTED_MSG("Unknown framebuffer pixel format: {}",
                          static_cast<u32>(framebuffer.pixel_format));
        return VK_FORMAT_A8B8G8R8_UNORM_PACK32;
    }
}

} // Anonymous namespace

Layer::Layer(const Device& device, MemoryAllocator& memory_allocator_, Scheduler& scheduler_, Tegra::MaxwellDeviceMemoryManager& device_memory_, size_t image_count_, VkExtent2D output_size, VkDescriptorSetLayout layout, const PresentFilters& filters_)
    : memory_allocator(memory_allocator_)
    , scheduler(scheduler_)
    , device_memory(device_memory_)
    , filters(filters_)
    , image_count(image_count_)
{
    CreateDescriptorPool(device);
    CreateDescriptorSets(device, layout);
    if (filters.get_scaling_filter() == Settings::ScalingFilter::Fsr) {
        sr_filter.emplace<FSR>(device, memory_allocator, image_count, output_size);
    } else if (filters.get_scaling_filter() == Settings::ScalingFilter::Sgsr) {
        sr_filter.emplace<SGSR>(device, memory_allocator, image_count, output_size, false);
    } else if (filters.get_scaling_filter() == Settings::ScalingFilter::SgsrEdge) {
        sr_filter.emplace<SGSR>(device, memory_allocator, image_count, output_size, true);
    } else if (filters.get_scaling_filter() == Settings::ScalingFilter::Anime4K3D) {
        // Real MIT Anime4K v4 3D CNN four-pass native compute backend.
        // No fake FSR3 timeline/history nor per-game shader hash.
        sr_filter.emplace<Anime4K3D>(device, memory_allocator, scheduler, image_count,
                                     output_size, Anime4K3D::Profile::Details);
    } else if (filters.get_scaling_filter() == Settings::ScalingFilter::Anime4KSoft) {
        sr_filter.emplace<Anime4K3D>(device, memory_allocator, scheduler, image_count,
                                     output_size, Anime4K3D::Profile::Soft);
    } else if (filters.get_scaling_filter() == Settings::ScalingFilter::Anime4KDenoise) {
        sr_filter.emplace<Anime4K3D>(device, memory_allocator, scheduler, image_count,
                                     output_size, Anime4K3D::Profile::Denoise);
    }
}

Layer::~Layer() {
    ReleaseRawImages();
}

void Layer::ConfigureDraw(const Device& device, PresentPushConstants* out_push_constants,
                          VkDescriptorSet* out_descriptor_set, RasterizerVulkan& rasterizer,
                          VkSampler sampler, size_t image_index,
                          const Tegra::FramebufferConfig& framebuffer,
                          const Layout::FramebufferLayout& layout) {
    const auto texture_info = rasterizer.AccelerateDisplay(
        framebuffer, framebuffer.address + framebuffer.offset, framebuffer.stride);
    const u32 texture_width = texture_info ? texture_info->width : framebuffer.width;
    const u32 texture_height = texture_info ? texture_info->height : framebuffer.height;
    const u32 scaled_width = texture_info ? texture_info->scaled_width : texture_width;
    const u32 scaled_height = texture_info ? texture_info->scaled_height : texture_height;
    const bool use_accelerated = texture_info.has_value();
    // Firmware applet layer stacks omit Recording: SGSR history belongs to
    // the game's surface, not small transient applet/keyboard overlays.
    const bool is_applet =
        (framebuffer.layer_stack_mask &
         Service::Nvnflinger::LayerStackBit(Service::Nvnflinger::LayerStackId::Recording)) == 0;

    RefreshResources(device, framebuffer);
    // AA must render at the dimensions of the actual sampled source.
    // Raw readback may be 720p while scaling is 2x; accelerated images
    // may change effective dimensions independently.
    const auto aa_source = Eden::Graphics::AaSourceExtent(
        use_accelerated, {framebuffer.width, framebuffer.height},
        {scaled_width, scaled_height});
    SetAntiAliasPass(device, {aa_source.width, aa_source.height});

    // Finish any pending renderpass
    scheduler.RequestOutsideRenderPassOperationContext();
    scheduler.Wait(resource_ticks[image_index]);
    // Each session may retain hundreds of Vulkan allocations/descriptors.
    // Do not release them until the matching presentation tick retires.
    if(image_index<neural_sessions.size())
        neural_sessions[image_index].reset();
    SCOPE_EXIT {
        resource_ticks[image_index] = scheduler.CurrentTick();
    };

    if (!use_accelerated) {
        UpdateRawImage(framebuffer, image_index);
    }

    VkImage source_image = texture_info ? texture_info->image : *raw_images[image_index];
    VkImageView source_image_view =
        texture_info ? texture_info->image_view : *raw_image_views[image_index];

    if (auto* fxaa = std::get_if<FXAA>(&anti_alias)) {
        fxaa->Draw(device, scheduler, image_index, &source_image, &source_image_view);
    } else if (auto* smaa = std::get_if<SMAA>(&anti_alias)) {
        smaa->Draw(device, scheduler, image_index, &source_image, &source_image_view);
    }

    auto crop_rect = Tegra::NormalizeCrop(framebuffer, texture_width, texture_height);
    const VkExtent2D render_extent{
        .width = scaled_width,
        .height = scaled_height,
    };

    if (auto* fsr = std::get_if<FSR>(&sr_filter)) {
        source_image_view = fsr->Draw(device, scheduler, image_index, source_image, source_image_view, render_extent, crop_rect);
        crop_rect = {0, 0, 1, 1};
    } else if (auto* sgsr = std::get_if<SGSR>(&sr_filter)) {
        if (!is_applet) {
            source_image_view = sgsr->Draw(device, scheduler, image_index, source_image,
                                           source_image_view, render_extent, crop_rect);
            crop_rect = {0, 0, 1, 1};
        }
        // Applets keep the original Vulkan view and crop, no black SGSR
        // history or forced crop when the guest overlay is closed/open.
    } else if (auto* a4k = std::get_if<Anime4K3D>(&sr_filter)) {
        if (const auto output = a4k->Draw(image_index, source_image, source_image_view,
                                          render_extent, crop_rect)) {
            source_image_view = *output;
            crop_rect = {0, 0, 1, 1};
        }
        // On incompatible crop/format/dimensions/budget, unchanged bilinear
        // presentation samples the original guest image.
    }

    // R09: the selected game's Original/Compact neural renderer is a
    // separate final image stage, not A4K, FSR or frame generation.
    // The native model plans presently exist for an exact 1920x1080
    // source without crop. Other geometries preserve existing rendering.
    const auto selected=Eden::NeuralRuntime::Current();
    if(last_neural_mode!=selected.mode){
        last_neural_mode=selected.mode;
        neural_model_failed=false;
    }
    const bool nr_selected=filters.allow_game_neural_rendering&&
        Eden::NeuralVideo::IsDlss(selected.mode);
    // Accelerated display can be the normal game path. The texture
    // cache supplies a real sampled image view and its post-scaling
    // dimensions. Only accept an exact 1080p physical view and full
    // crop; unknown source formats still fail the session's format gate.
    const bool nr_geometry=Eden::Graphics::CanR09CaptureDisplay({
        .accelerated=use_accelerated,
        .live_image=source_image!=VK_NULL_HANDLE&&
                    source_image_view!=VK_NULL_HANDLE,
        .native_width=texture_width,
        .native_height=texture_height,
        .sampled_width=render_extent.width,
        .sampled_height=render_extent.height,
        .crop_left=crop_rect.left,.crop_top=crop_rect.top,
        .crop_right=crop_rect.right,.crop_bottom=crop_rect.bottom,
        .single_sample=!use_accelerated||
            texture_info->sample_count==VK_SAMPLE_COUNT_1_BIT});
    const bool nr_exclusive=
        std::holds_alternative<std::monostate>(anti_alias)&&
        std::holds_alternative<std::monostate>(sr_filter);
    if(nr_selected&&nr_geometry&&nr_exclusive&&
       !neural_model_failed&&image_index<neural_sessions.size()&&
       image_index<neural_images.size()&&image_index<neural_views.size()) {
        const bool original=selected.mode==Eden::NeuralVideo::kDlssOriginal;
        // Accept the exact upstream NRMODEL1 package filenames from the
        // MIT extractor, without requiring users to rename the output.
        // Never scan arbitrary paths or substitute a different model.
        const std::string model_dir=Eden::ConfigDir()+"/neural/";
        const std::string configured=model_dir+
            (original?"original.nrmodel":"compact.nrmodel");
        const std::string extracted=model_dir+
            (original?"dlssnr.bin":"dlssnr-small.bin");
        // R09 DLL import now runs at game admission in headless/main.cpp,
        // before this render thread starts. NEVER deserialize or extract
        // a large proprietary model payload on a guest frame. Cached data is
        // preflighted by the native model owner, otherwise fail closed.
        const std::string model_path=Eden::FileExists(configured)?
            configured:extracted;
        if(!Eden::FileExists(model_path)){
            LOG_WARNING(Render_Vulkan,
                "R09 DLSS-NR model pack not installed; checked {} and {}",
                configured,extracted);
            neural_model_failed=true;
        }else {
            try {
                // Allocated on the same Vulkan device, on the exact slot
                // whose previous GPU tick was waited for above.
                // Retire the previous slot's image view BEFORE its
                // underlying image. The GPU tick was waited above, but
                // destroying the image while a VkImageView still exists
                // violates Vulkan object lifetime rules.
                neural_views[image_index].reset();
                neural_images[image_index].reset();
                // The neural output is a compute storage image sampled by
                // the presenter, never a render-pass color attachment.
                // Do not require COLOR_ATTACHMENT support on RGBA32F.
                const VkImageCreateInfo neural_output_ci{
                    .sType=VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
                    .pNext=nullptr,.flags=0u,
                    .imageType=VK_IMAGE_TYPE_2D,
                    .format=VK_FORMAT_R32G32B32A32_SFLOAT,
                    .extent={1920u,1080u,1u},
                    .mipLevels=1u,.arrayLayers=1u,
                    .samples=VK_SAMPLE_COUNT_1_BIT,
                    .tiling=VK_IMAGE_TILING_OPTIMAL,
                    .usage=VK_IMAGE_USAGE_STORAGE_BIT|
                           VK_IMAGE_USAGE_SAMPLED_BIT,
                    .sharingMode=VK_SHARING_MODE_EXCLUSIVE,
                    .queueFamilyIndexCount=0u,
                    .pQueueFamilyIndices=nullptr,
                    .initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
                };
                neural_images[image_index]=
                    memory_allocator.CreateImage(neural_output_ci);
                // Native output allocations are not guaranteed to succeed,
                // particularly with the guest game's VRAM already in use.
                // Never dereference a missing Vulkan image or hand a null
                // view to an owner. The surrounding catch restores the
                // original game frame and retires slot resources normally.
                if (!neural_images[image_index]) {
                    throw std::runtime_error(
                        "R09 RGBA32F neural output image allocation failed");
                }
                neural_views[image_index]=CreateWrappedImageView(
                    device,neural_images[image_index],
                    VK_FORMAT_R32G32B32A32_SFLOAT);
                if (!neural_views[image_index]) {
                    throw std::runtime_error(
                        "R09 RGBA32F neural output image view creation failed");
                }
                auto owner=std::make_unique<NrRdna2FrameSession>(
                    device,memory_allocator,scheduler);
                const auto plan=original?
                    Eden::NeuralPlans::Original:Eden::NeuralPlans::Compact;
                if(!owner->Initialize(
                       model_path,plan,source_image_view,sampler,
                       texture_info ? texture_info->sampled_format
                                    : GetFormat(framebuffer),
                       render_extent,
                       *neural_views[image_index],
                       VK_FORMAT_R32G32B32A32_SFLOAT,{1920u,1080u},
                       1.0f,float(selected.strength)/100.0f)){
                    LOG_WARNING(Render_Vulkan,
                        "R09 DLSS-NR model/session preflight rejected: {} "
                        "phase={} (no neural commands recorded)",
                        original?"Original":"Compact",
                        owner->LastInitializePhaseName());
                    neural_model_failed=true;
                    // Initialize guarantees zero queued GPU commands. All
                    // provisional stage owners have already unwound, so
                    // return this unused output view/image immediately.
                    // Record failures take a different path below: those
                    // owners MUST survive until the scheduler tick retires.
                    neural_views[image_index].reset();
                    neural_images[image_index].reset();
                }else {
                    const VkImage target=*neural_images[image_index];
                    const VkImage guest_source=source_image;
                    // The live renderer may have written the accelerated
                    // guest surface as a color target, by transfer, or with
                    // compute before this present call. The existing
                    // presentation path samples GENERAL; order all prior
                    // writes before the new neural compute texture sample.
                    // This is required for the real game image, not just
                    // the host's pre-filled test texture.
                    scheduler.RequestOutsideRenderPassOperationContext();
                    scheduler.Record([target,guest_source](vk::CommandBuffer cmd){
                        const VkImageMemoryBarrier guest{
                            .sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                            .pNext=nullptr,
                            .srcAccessMask=VK_ACCESS_MEMORY_WRITE_BIT,
                            .dstAccessMask=VK_ACCESS_SHADER_READ_BIT,
                            .oldLayout=VK_IMAGE_LAYOUT_GENERAL,
                            .newLayout=VK_IMAGE_LAYOUT_GENERAL,
                            .srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
                            .dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
                            .image=guest_source,
                            .subresourceRange={
                                .aspectMask=VK_IMAGE_ASPECT_COLOR_BIT,
                                .baseMipLevel=0u,.levelCount=1u,
                                .baseArrayLayer=0u,.layerCount=1u}};
                        cmd.PipelineBarrier(VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,guest);
                        // Fresh RGBA32F storage image. Never sample it
                        // before the neural compute-write barrier.
                        const VkImageMemoryBarrier image{
                            .sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                            .pNext=nullptr,.srcAccessMask=0u,
                            .dstAccessMask=VK_ACCESS_SHADER_WRITE_BIT,
                            .oldLayout=VK_IMAGE_LAYOUT_UNDEFINED,
                            .newLayout=VK_IMAGE_LAYOUT_GENERAL,
                            .srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
                            .dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
                            .image=target,
                            .subresourceRange={
                                .aspectMask=VK_IMAGE_ASPECT_COLOR_BIT,
                                .baseMipLevel=0u,.levelCount=1u,
                                .baseArrayLayer=0u,.layerCount=1u}};
                        cmd.PipelineBarrier(VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,image);
                    });
                    // Keep the owner live even after a failed Record:
                    // that failure may already have enqueued GPU work.
                    neural_sessions[image_index]=std::move(owner);
                    const bool r09_recorded=neural_sessions[image_index]->Record();
                    if(r09_recorded&&
                       neural_sessions[image_index]->ResultView()==
                           *neural_views[image_index]){
                        source_image_view=*neural_views[image_index];
                        crop_rect={0,0,1,1};
                    }else {
                        LOG_WARNING(Render_Vulkan,
                            "R09 DLSS-NR graph not accepted: phase={} "
                            "queued_scheduler_callbacks={} "
                            "(enqueue only, NOT GPU completion); "
                            "retaining the original guest image",
                            neural_sessions[image_index]->LastRecordPhaseName(),
                            neural_sessions[image_index]->EnqueuedSchedulerCallbacks());
                        neural_model_failed=true;
                    }
                }
            }catch(const std::exception& error){
                LOG_WARNING(Render_Vulkan,
                    "R09 DLSS-NR session failed safely: {}",error.what());
                neural_model_failed=true;
            }
        }
    }

    SetMatrixData(device, *out_push_constants, layout);
    SetVertexData(device, *out_push_constants, layout, crop_rect);

    UpdateDescriptorSet(device, source_image_view, sampler, image_index);
    *out_descriptor_set = descriptor_sets[image_index];
}

void Layer::CreateDescriptorPool(const Device& device) {
    descriptor_pool = CreateWrappedDescriptorPool(device, image_count, image_count);
}

void Layer::CreateDescriptorSets(const Device& device, VkDescriptorSetLayout layout) {
    const std::vector layouts(image_count, layout);
    descriptor_sets = CreateWrappedDescriptorSets(descriptor_pool, layouts);
}

void Layer::CreateStagingBuffer(const Device& device, const Tegra::FramebufferConfig& framebuffer) {
    const VkBufferCreateInfo ci{
        .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .pNext = nullptr,
        .flags = 0,
        .size = CalculateBufferSize(framebuffer),
        .usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT |
                 VK_BUFFER_USAGE_VERTEX_BUFFER_BIT | VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .queueFamilyIndexCount = 0,
        .pQueueFamilyIndices = nullptr,
    };

    buffer = memory_allocator.CreateBuffer(ci, MemoryUsage::Upload);
}

void Layer::CreateRawImages(const Device& device, const Tegra::FramebufferConfig& framebuffer) {
    const auto format = GetFormat(framebuffer);
    // ReleaseRawImages waited for every old timeline use. Reusing its tick
    // values after rebuilding the layer would cause redundant Wait calls on
    // newly allocated images, although those old fences have retired.
#ifdef PS5_NATIVE
    resource_ticks.assign(image_count, 0);
#else
    resource_ticks.resize(image_count);
#endif
    raw_images.resize(image_count);
    raw_image_views.resize(image_count);
    neural_sessions.resize(image_count);
    neural_images.resize(image_count);
    neural_views.resize(image_count);

    for (size_t i = 0; i < image_count; ++i) {
        raw_images[i] =
            CreateWrappedImage(memory_allocator, {framebuffer.width, framebuffer.height}, format);
        raw_image_views[i] = CreateWrappedImageView(device, raw_images[i], format);
    }
}

void Layer::RefreshResources(const Device& device, const Tegra::FramebufferConfig& framebuffer) {
    if (framebuffer.width == raw_width && framebuffer.height == raw_height &&
        framebuffer.pixel_format == pixel_format && !raw_images.empty() &&
        buffer.Mapped().size() == CalculateBufferSize(framebuffer)) {
        return;
    }
#ifdef PS5_NATIVE
    // Same dimensions and format, but the guest row pitch changed. Recycle
    // only the upload buffer after its last referenced GPU tick; AA images,
    // descriptors, renderpasses and pipelines remain valid. Do NOT trigger
    // a full-device WaitIdle or recreate the FXAA/SMAA pass on pitch changes.
    if (framebuffer.width == raw_width && framebuffer.height == raw_height &&
        framebuffer.pixel_format == pixel_format && !raw_images.empty()) {
        // All layer ticks share one monotonically increasing Vulkan GPU
        // timeline. Waiting for the maximum retires every earlier user of
        // the old upload staging buffer with one semaphore wait.
        const auto last_tick = std::max_element(resource_ticks.begin(), resource_ticks.end());
        if (last_tick != resource_ticks.end() && *last_tick != 0) {
            scheduler.Wait(*last_tick);
        }
        CreateStagingBuffer(device, framebuffer);
        return;
    }
#endif

    raw_width = framebuffer.width;
    raw_height = framebuffer.height;
    pixel_format = framebuffer.pixel_format;
#ifdef PS5_NATIVE
    if (!std::holds_alternative<std::monostate>(anti_alias)) {
        // Existing FXAA/SMAA images and descriptors may still be referenced
        // by command buffers submitted for prior presentation frames.
        scheduler.Finish();
        device.GetLogical().WaitIdle();
    }
#endif
    anti_alias.emplace<std::monostate>();

    ReleaseRawImages();
    CreateStagingBuffer(device, framebuffer);
    CreateRawImages(device, framebuffer);
}

void Layer::SetAntiAliasPass(const Device& device, VkExtent2D source_extent) {
#ifdef PS5_NATIVE
    // Invalid/unsupported zero-size input: avoid Vulkan allocations.
    const auto requested_aa =
        Eden::Graphics::AaValid({source_extent.width, source_extent.height})
        ? filters.get_anti_aliasing() : Settings::AntiAliasing::None;
    const bool enhanced = requested_aa == Settings::AntiAliasing::Fxaa &&
                          Eden::Graphics::EnhancedFxaa();
    // Disabled AA has no GPU resources to rebuild. The old guard skipped
    // only live FXAA/SMAA and reconstructed the monostate on every frame,
    // including when the filter remained disabled across thousands of draws.
    // A resize resets a live pass to monostate, so FXAA/SMAA still rebuild.
    if (anti_alias_setting == requested_aa &&
        fxaa_enhanced_setting == enhanced &&
        source_extent.width == anti_alias_extent.width &&
        source_extent.height == anti_alias_extent.height &&
        (!std::holds_alternative<std::monostate>(anti_alias) ||
         (requested_aa != Settings::AntiAliasing::Fxaa &&
          requested_aa != Settings::AntiAliasing::Smaa))) {
        return;
    }
    if (std::holds_alternative<std::monostate>(anti_alias) &&
        requested_aa == Settings::AntiAliasing::None) {
        anti_alias_setting = requested_aa;
        anti_alias_extent = source_extent;
        fxaa_enhanced_setting = enhanced;
        return;
    }
#else
    if (!std::holds_alternative<std::monostate>(anti_alias) && anti_alias_setting == filters.get_anti_aliasing())
        return;
#endif

#ifdef PS5_NATIVE
    if (!std::holds_alternative<std::monostate>(anti_alias)) {
        // Swapping the AA variant frees GPU resources, not just host state.
        scheduler.Finish();
        device.GetLogical().WaitIdle();
    }
#endif
    anti_alias_setting = requested_aa;
    anti_alias_extent = source_extent;
    fxaa_enhanced_setting = enhanced;
    const VkExtent2D render_area = source_extent;

    switch (anti_alias_setting) {
    case Settings::AntiAliasing::Fxaa:
        anti_alias.emplace<FXAA>(device, memory_allocator, image_count, render_area, enhanced);
        break;
    case Settings::AntiAliasing::Smaa:
        anti_alias.emplace<SMAA>(device, memory_allocator, image_count, render_area);
        break;
    default:
        anti_alias.emplace<std::monostate>();
        break;
    }
}

void Layer::ReleaseRawImages() {
#ifdef PS5_NATIVE
    // On this single Vulkan GPU timeline, the latest presentation resource
    // tick subsumes all preceding image uses, including out-of-order slots.
    const auto last_tick = std::max_element(resource_ticks.begin(), resource_ticks.end());
    if (last_tick != resource_ticks.end() && *last_tick != 0) {
        scheduler.Wait(*last_tick);
    }
#else
    for (const u64 tick : resource_ticks) {
        scheduler.Wait(tick);
    }
#endif
    neural_sessions.clear();
    neural_views.clear();
    neural_images.clear();
    neural_model_failed=false;
    raw_image_views.clear();
    raw_images.clear();
    buffer.reset();
}

u64 Layer::CalculateBufferSize(const Tegra::FramebufferConfig& framebuffer) const {
    return GetSizeInBytes(framebuffer) * image_count;
}

u64 Layer::GetRawImageOffset(const Tegra::FramebufferConfig& framebuffer,
                             size_t image_index) const {
    return GetSizeInBytes(framebuffer) * image_index;
}

void Layer::SetMatrixData(const Device& device, PresentPushConstants& data, const Layout::FramebufferLayout& layout) const {
    data.modelview_matrix = MakeOrthographicMatrix(f32(layout.width), static_cast<f32>(layout.height));
}

void Layer::SetVertexData(const Device& device, PresentPushConstants& data, const Layout::FramebufferLayout& layout, const Common::Rectangle<f32>& crop) const {
    // Map the coordinates to the screen.
    const auto& screen = layout.screen;
    const auto x = f32(screen.left);
    const auto y = f32(screen.top);
    const auto w = f32(screen.GetWidth());
    const auto h = f32(screen.GetHeight());

    data.vertices[0] = ScreenRectVertex(x, y, crop.left, crop.top);
    data.vertices[1] = ScreenRectVertex(x + w, y, crop.right, crop.top);
    data.vertices[2] = ScreenRectVertex(x, y + h, crop.left, crop.bottom);
    data.vertices[3] = ScreenRectVertex(x + w, y + h, crop.right, crop.bottom);
}

void Layer::UpdateDescriptorSet(const Device& device, VkImageView image_view, VkSampler sampler, size_t image_index) {
    const VkDescriptorImageInfo image_info{
        .sampler = sampler,
        .imageView = image_view,
        .imageLayout = VK_IMAGE_LAYOUT_GENERAL,
    };

    const VkWriteDescriptorSet sampler_write{
        .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
        .pNext = nullptr,
        .dstSet = descriptor_sets[image_index],
        .dstBinding = 0,
        .dstArrayElement = 0,
        .descriptorCount = 1,
        .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .pImageInfo = &image_info,
        .pBufferInfo = nullptr,
        .pTexelBufferView = nullptr,
    };

    device.GetLogical().UpdateDescriptorSets(std::array{sampler_write}, {});
}

void Layer::UpdateRawImage(const Tegra::FramebufferConfig& framebuffer, size_t image_index) {
    const std::span<u8> mapped_span = buffer.Mapped();

#ifndef PS5_NATIVE
    const u64 image_offset = GetRawImageOffset(framebuffer, image_index);
#endif

    const DAddr framebuffer_addr = framebuffer.address + framebuffer.offset;
    const u8* const host_ptr = device_memory.GetPointer<u8>(framebuffer_addr);

    // TODO(Rodrigo): Read this from HLE
    constexpr u32 block_height_log2 = 4;
    const u32 bytes_per_pixel = GetBytesPerPixel(framebuffer);
#ifdef PS5_NATIVE
    // This raw upload already resolved the guest pixel format above. Do not
    // decode that same format a second time through GetSizeInBytes every
    // time the CPU reads back a guest framebuffer.
    const u64 linear_size{
        static_cast<std::size_t>(framebuffer.stride) *
        static_cast<std::size_t>(framebuffer.height) * bytes_per_pixel};
    // Staging slots have the same guest row pitch: do not decode BPP again
    // through GetRawImageOffset for every non-accelerated presentation.
    const u64 image_offset = linear_size * image_index;
#else
    const u64 linear_size{GetSizeInBytes(framebuffer)};
#endif
#ifdef PS5_NATIVE
    // An unmapped guest framebuffer has no tiled source to measure.
    // Keep the exact raw-zero upload, but skip tiled-size/format arithmetic
    // on repeated missing-frame fallbacks (HUD, scene changes).
    const std::span<u8> linear_span = mapped_span.subspan(image_offset, linear_size);
    if (host_ptr) {
        const u64 tiled_size{Tegra::Texture::CalculateSize(
            true, bytes_per_pixel, framebuffer.stride, framebuffer.height, 1, block_height_log2, 0)};
#else
    const u64 tiled_size{Tegra::Texture::CalculateSize(
        true, bytes_per_pixel, framebuffer.stride, framebuffer.height, 1, block_height_log2, 0)};
    const std::span<u8> linear_span = mapped_span.subspan(image_offset, linear_size);
    if (host_ptr) {
#endif
        Tegra::Texture::UnswizzleTexture(
            linear_span, std::span(host_ptr, tiled_size),
            bytes_per_pixel, framebuffer.width, framebuffer.height, 1, block_height_log2, 0);
    } else {
        // Never upload stale staging bytes if the guest framebuffer is missing.
        std::fill(linear_span.begin(), linear_span.end(), u8{0});
    }
    buffer.Flush();  // Both the upload and missing-memory clear need visibility.

    const VkBufferImageCopy copy{
        .bufferOffset = image_offset,
        .bufferRowLength = 0,
        .bufferImageHeight = 0,
        .imageSubresource =
            {
                .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
                .mipLevel = 0,
                .baseArrayLayer = 0,
                .layerCount = 1,
            },
        .imageOffset = {.x = 0, .y = 0, .z = 0},
        .imageExtent =
            {
                .width = framebuffer.width,
                .height = framebuffer.height,
                .depth = 1,
            },
    };
    scheduler.Record([this, copy, index = image_index](vk::CommandBuffer cmdbuf) {
        const VkImage image = *raw_images[index];
        const VkImageMemoryBarrier base_barrier{
            .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
            .pNext = nullptr,
            .srcAccessMask = 0,
            .dstAccessMask = 0,
            .oldLayout = VK_IMAGE_LAYOUT_GENERAL,
            .newLayout = VK_IMAGE_LAYOUT_GENERAL,
            .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .image = image,
            .subresourceRange{
                .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
                .baseMipLevel = 0,
                .levelCount = 1,
                .baseArrayLayer = 0,
                .layerCount = 1,
            },
        };
        VkImageMemoryBarrier read_barrier = base_barrier;
        read_barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        read_barrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        read_barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;

        VkImageMemoryBarrier write_barrier = base_barrier;
        write_barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        write_barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        write_barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;

        cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_HOST_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0,
                               read_barrier);
        cmdbuf.CopyBufferToImage(*buffer, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, copy);
        cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_TRANSFER_BIT,
                               VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |
                                   VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                               0, write_barrier);
    });
}

} // namespace Vulkan
