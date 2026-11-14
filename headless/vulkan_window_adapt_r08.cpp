// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// SPDX-FileCopyrightText: Copyright 2024 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include <algorithm>
#include <cstdint>
#include <boost/container/small_vector.hpp>

#include "core/frontend/framebuffer_layout.h"
#include "hud.h"
#include "in_game_overlay.h"
#include "vulkan_hud_shaders.h"
#include "video_core/framebuffer_config.h"
#include "video_core/host_shaders/vulkan_present_vert_spv.h"
#include "video_core/renderer_vulkan/present/layer.h"
#include "video_core/renderer_vulkan/present/present_push_constants.h"
#include "video_core/renderer_vulkan/present/util.h"
#include "video_core/renderer_vulkan/present/window_adapt_pass.h"
#include "video_core/renderer_vulkan/vk_present_manager.h"
#include "video_core/renderer_vulkan/vk_shader_util.h"
#include "video_core/vulkan_common/vulkan_device.h"
#include "video_core/vulkan_common/vulkan_memory_allocator.h"

namespace Vulkan {

// The quick menu is composited in the already-owned framebuffer. It does not
// touch guest images or add a second swapchain/present. Closed sessions never
// enter this draw path.
static void DrawQuickOverlay(vk::CommandBuffer cmdbuf,
                             VkPipeline pipeline, VkPipelineLayout layout,
                             VkExtent2D extent, const Eden::QuickOverlay::Frame& quick) {
    if (!quick.visible) return;
    const auto units = [h = extent.height](std::uint32_t value) { return value * h / 1080u; };
    const auto draw = [&](VkRect2D scissor, Eden::HudSnapshot constants) {
        const VkViewport viewport{static_cast<float>(scissor.offset.x),
                                  static_cast<float>(scissor.offset.y),
                                  static_cast<float>(scissor.extent.width),
                                  static_cast<float>(scissor.extent.height), 0.0f, 1.0f};
        cmdbuf.SetViewport(0, viewport);
        cmdbuf.SetScissor(0, scissor);
        cmdbuf.BindPipeline(VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        cmdbuf.PushConstants(layout, VK_SHADER_STAGE_FRAGMENT_BIT, constants);
        cmdbuf.Draw(4, 1, 0, 0);
    };
    Eden::HudSnapshot backdrop{};
    backdrop.width = extent.height;
    backdrop.x = extent.width;
    backdrop.y = extent.height;
    backdrop.loading = Eden::QuickOverlay::StyledMode(
        Eden::QuickOverlay::kBackdrop,quick.style);
    draw(VkRect2D{{0, 0}, extent}, backdrop);

    const std::uint32_t x = extent.width * 56u / 100u;
    const std::uint32_t panel_width = extent.width * 40u / 100u;
    if (panel_width <= units(40)) return;
    for (std::uint32_t i = 0; i < quick.count && i < quick.rows.size(); ++i) {
        const std::uint32_t top = units(112u + i * 62u);
        if (top >= extent.height) break;
        const std::uint32_t height = std::min(units(52), extent.height - top);
        if (!height) continue;
        const VkRect2D row{
            {static_cast<std::int32_t>(x + units(12)), static_cast<std::int32_t>(top)},
            {panel_width - units(24), height}
        };
        auto constants = quick.rows[i];
        constants.x = row.offset.x + units(22);
        constants.y = top + units(15);
        constants.width = extent.height;
        draw(row, constants);
    }
}

WindowAdaptPass::WindowAdaptPass(const Device& device, VkFormat frame_format, vk::Sampler&& sampler_, vk::ShaderModule&& fragment_shader_)
    : sampler(std::move(sampler_))
    , fragment_shader(std::move(fragment_shader_))
{
    CreateDescriptorSetLayout(device);
    CreatePipelineLayout(device);
    CreateVertexShader(device);
    CreateRenderPass(device, frame_format);
    hud_overlay_render_pass =
        CreateWrappedRenderPass(device, frame_format, VK_IMAGE_LAYOUT_GENERAL);
    CreatePipelines(device);
}

WindowAdaptPass::~WindowAdaptPass() = default;

void WindowAdaptPass::Draw(const Device& device, RasterizerVulkan& rasterizer, Scheduler& scheduler, size_t image_index,
                           std::list<Layer>& layers,
                           std::span<const Tegra::FramebufferConfig> configs,
                           const Layout::FramebufferLayout& layout, Frame* dst, bool draw_hud) {

    const VkFramebuffer host_framebuffer{*dst->framebuffer};
    const VkRenderPass renderpass{*render_pass};
    const VkPipelineLayout graphics_pipeline_layout{*pipeline_layout};
    const VkExtent2D render_area{
        .width = dst->width,
        .height = dst->height,
    };

    const size_t layer_count = configs.size();
    struct LayerDraw {
        PresentPushConstants push_constants;
        VkDescriptorSet descriptor_set;
        VkPipeline graphics_pipeline;
    };
    // The usual single-layer frame needs no heap storage. Larger frames
    // share one allocation, transferred to the deferred draw command.
    boost::container::small_vector<LayerDraw, 1> draws(layer_count);

    auto layer_it = layers.begin();
    for (size_t i = 0; i < layer_count; i++) {
        auto& draw = draws[i];
        switch (configs[i].blending) {
        case Tegra::BlendMode::Opaque:
        default:
            draw.graphics_pipeline = *opaque_pipeline;
            break;
        case Tegra::BlendMode::Premultiplied:
            draw.graphics_pipeline = *premultiplied_pipeline;
            break;
        case Tegra::BlendMode::Coverage:
            draw.graphics_pipeline = *coverage_pipeline;
            break;
        }

        layer_it->ConfigureDraw(device, &draw.push_constants, &draw.descriptor_set, rasterizer, *sampler,
                                image_index, configs[i], layout);
        layer_it++;
    }

    const auto hud = draw_hud ? Eden::GetVulkanHud() : Eden::HudSnapshot{};
    const auto quick = draw_hud ? Eden::QuickOverlay::Snapshot() : Eden::QuickOverlay::Frame{};
    if ((hud.width || quick.visible) && !hud_pipeline) {
        const VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(hud)};
        hud_layout = device.GetLogical().CreatePipelineLayout(VkPipelineLayoutCreateInfo{
            .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
            .pushConstantRangeCount = 1,
            .pPushConstantRanges = &range,
        });
        auto vertex = BuildShader(device, EDEN_HUD_VERT_SPV);
        auto fragment = BuildShader(device, EDEN_HUD_FRAG_SPV);
        hud_pipeline = CreateWrappedCoverageBlendingPipeline(
            device, render_pass, hud_layout, std::tie(vertex, fragment));
    }
    // When both overlays are hidden, neither lazy resource exists yet.
    // Null handles are never bound: both draw branches are skipped.
    const VkPipeline hud_graphics_pipeline = hud_pipeline ? *hud_pipeline : VK_NULL_HANDLE;
    const VkPipelineLayout hud_pipeline_layout = hud_layout ? *hud_layout : VK_NULL_HANDLE;

    scheduler.Record([=, draws = std::move(draws)](vk::CommandBuffer cmdbuf) {
        const f32 bg_red = Settings::values.bg_red.GetValue() / 255.0f;
        const f32 bg_green = Settings::values.bg_green.GetValue() / 255.0f;
        const f32 bg_blue = Settings::values.bg_blue.GetValue() / 255.0f;
        const VkClearAttachment clear_attachment{
            .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
            .colorAttachment = 0,
            .clearValue =
                {
                    .color = {.float32 = {bg_red, bg_green, bg_blue, 1.0f}},
                },
        };
        const VkClearRect clear_rect{
            .rect =
                {
                    .offset = {0, 0},
                    .extent = render_area,
                },
            .baseArrayLayer = 0,
            .layerCount = 1,
        };

        BeginRenderPass(cmdbuf, renderpass, host_framebuffer, render_area);
        cmdbuf.ClearAttachments({clear_attachment}, {clear_rect});

        for (size_t i = 0; i < layer_count; i++) {
            const auto& draw = draws[i];
            cmdbuf.BindPipeline(VK_PIPELINE_BIND_POINT_GRAPHICS, draw.graphics_pipeline);
            cmdbuf.PushConstants(graphics_pipeline_layout, VK_SHADER_STAGE_VERTEX_BIT,
                                 draw.push_constants);
            cmdbuf.BindDescriptorSets(VK_PIPELINE_BIND_POINT_GRAPHICS, graphics_pipeline_layout, 0,
                                      draw.descriptor_set, {});
            cmdbuf.Draw(4, 1, 0, 0);
        }

        // The overlay is laid out for a picture 1080 rows high and scaled to this one.
        const auto hud_units = [rows = render_area.height](uint32_t value) { return value * rows / 1080u; };
        if (hud.width && (hud.loading || (render_area.width >= hud_units(hud.width + 16) &&
                                          render_area.height >= hud_units(64)))) {
            const VkRect2D scissor = hud.loading ? VkRect2D{{0, 0}, render_area} :
                VkRect2D{{static_cast<int32_t>(hud_units(16)), static_cast<int32_t>(hud_units(16))},
                         {hud_units(hud.width), hud_units(48)}};
            const VkViewport viewport{static_cast<float>(scissor.offset.x), static_cast<float>(scissor.offset.y),
                static_cast<float>(scissor.extent.width), static_cast<float>(scissor.extent.height), 0, 1};
            cmdbuf.SetViewport(0, viewport);
            cmdbuf.SetScissor(0, scissor);
            cmdbuf.BindPipeline(VK_PIPELINE_BIND_POINT_GRAPHICS, hud_graphics_pipeline);
            auto constants = hud;
            if (hud.loading) {
                // The loading scene fills the picture: tell it how large that is.
                constants.x = render_area.width;
                constants.y = render_area.height;
            } else {
                // Where the text starts in this picture, and the picture's height for its size.
                constants.x = hud_units(hud.x);
                constants.y = hud_units(hud.y);
                constants.width = render_area.height;
            }
            cmdbuf.PushConstants(hud_pipeline_layout, VK_SHADER_STAGE_FRAGMENT_BIT, constants);
            cmdbuf.Draw(4, 1, 0, 0);
        }
        DrawQuickOverlay(cmdbuf, hud_graphics_pipeline, hud_pipeline_layout, render_area, quick);

        cmdbuf.EndRenderPass();
    });
}

void WindowAdaptPass::DrawHudOverlay(const Device& device, Scheduler& scheduler,
                                     Frame* dst, const Eden::HudSnapshot& hud) {
    // Does not clear the target. Both interpolated and real frames are
    // already GENERAL after copy/blit barriers, so LOAD preserves image.
    const auto quick = Eden::QuickOverlay::Snapshot();
    if ((!hud.width && !quick.visible) || !dst || !dst->framebuffer) return;
    if (!hud_overlay_pipeline) {
        const VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(hud)};
        hud_overlay_layout = device.GetLogical().CreatePipelineLayout(VkPipelineLayoutCreateInfo{
            .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
            .pushConstantRangeCount = 1,
            .pPushConstantRanges = &range,
        });
        auto vertex = BuildShader(device, EDEN_HUD_VERT_SPV);
        auto fragment = BuildShader(device, EDEN_HUD_FRAG_SPV);
        hud_overlay_pipeline = CreateWrappedCoverageBlendingPipeline(
            device, hud_overlay_render_pass, hud_overlay_layout, std::tie(vertex, fragment));
    }

    const VkFramebuffer fb = *dst->framebuffer;
    const VkRenderPass rp = *hud_overlay_render_pass;
    const VkPipeline pipeline = *hud_overlay_pipeline;
    const VkPipelineLayout layout = *hud_overlay_layout;
    const VkExtent2D size{dst->width, dst->height};
    scheduler.Record([=](vk::CommandBuffer cmdbuf) {
        const auto units = [rows = size.height](std::uint32_t v) { return v * rows / 1080u; };
        BeginRenderPass(cmdbuf, rp, fb, size);
        if (hud.width &&
            (hud.loading || (size.width >= units(hud.width + 16) && size.height >= units(64)))) {
            // Loading owns the whole picture in both backends. The prior
            // jacket path clipped this same shader to a lower band, producing
            // the visible purple strip reported on PS5.
            const VkRect2D scissor = hud.loading
                ? VkRect2D{{0, 0}, size}
                : VkRect2D{{static_cast<int32_t>(units(16)),
                             static_cast<int32_t>(units(16))},
                            {units(hud.width), units(48)}};
            const VkViewport viewport{
                static_cast<float>(scissor.offset.x),
                static_cast<float>(scissor.offset.y),
                static_cast<float>(scissor.extent.width),
                static_cast<float>(scissor.extent.height), 0, 1};
            cmdbuf.SetViewport(0, viewport);
            cmdbuf.SetScissor(0, scissor);
            cmdbuf.BindPipeline(VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
            auto constants = hud;
            if (hud.loading) {
                constants.x = size.width;
                constants.y = size.height;
            } else {
                constants.x = units(hud.x);
                constants.y = units(hud.y);
                constants.width = size.height;
            }
            cmdbuf.PushConstants(layout, VK_SHADER_STAGE_FRAGMENT_BIT, constants);
            cmdbuf.Draw(4, 1, 0, 0);
        }
        DrawQuickOverlay(cmdbuf, pipeline, layout, size, quick);
        cmdbuf.EndRenderPass();
    });
}

VkDescriptorSetLayout WindowAdaptPass::GetDescriptorSetLayout() {
    return *descriptor_set_layout;
}

VkRenderPass WindowAdaptPass::GetRenderPass() {
    return *render_pass;
}

void WindowAdaptPass::CreateDescriptorSetLayout(const Device& device) {
    descriptor_set_layout =
        CreateWrappedDescriptorSetLayout(device, {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER});
}

void WindowAdaptPass::CreatePipelineLayout(const Device& device) {
    const VkPushConstantRange range{
        .stageFlags = VK_SHADER_STAGE_VERTEX_BIT,
        .offset = 0,
        .size = sizeof(PresentPushConstants),
    };

    pipeline_layout = device.GetLogical().CreatePipelineLayout(VkPipelineLayoutCreateInfo{
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
        .pNext = nullptr,
        .flags = 0,
        .setLayoutCount = 1,
        .pSetLayouts = descriptor_set_layout.address(),
        .pushConstantRangeCount = 1,
        .pPushConstantRanges = &range,
    });
}

void WindowAdaptPass::CreateVertexShader(const Device& device) {
    vertex_shader = BuildShader(device, VULKAN_PRESENT_VERT_SPV);
}

void WindowAdaptPass::CreateRenderPass(const Device& device, VkFormat frame_format) {
    render_pass = CreateWrappedRenderPass(device, frame_format, VK_IMAGE_LAYOUT_UNDEFINED);
}

void WindowAdaptPass::CreatePipelines(const Device& device) {
    opaque_pipeline = CreateWrappedPipeline(device, render_pass, pipeline_layout,
                                            std::tie(vertex_shader, fragment_shader));
    premultiplied_pipeline = CreateWrappedPremultipliedBlendingPipeline(
        device, render_pass, pipeline_layout, std::tie(vertex_shader, fragment_shader));
    coverage_pipeline = CreateWrappedCoverageBlendingPipeline(
        device, render_pass, pipeline_layout, std::tie(vertex_shader, fragment_shader));
}

} // namespace Vulkan
