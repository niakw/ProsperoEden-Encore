// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// SPDX-FileCopyrightText: Copyright 2024 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <list>

#include "common/math_util.h"
#include "video_core/vulkan_common/vulkan_wrapper.h"

namespace Layout {
struct FramebufferLayout;
}

namespace Tegra {
struct FramebufferConfig;
}

namespace Eden { struct HudSnapshot; }

namespace Vulkan {

class Device;
struct Frame;
class Layer;
class Scheduler;
class RasterizerVulkan;

class WindowAdaptPass final {
public:
    explicit WindowAdaptPass(const Device& device, VkFormat frame_format, vk::Sampler&& sampler,
                             vk::ShaderModule&& fragment_shader);
    ~WindowAdaptPass();

    void Draw(const Device& device, RasterizerVulkan& rasterizer, Scheduler& scheduler, size_t image_index,
              std::list<Layer>& layers, std::span<const Tegra::FramebufferConfig> configs,
              const Layout::FramebufferLayout& layout, Frame* dst, bool draw_hud = false);

    // Draw Encore's own HUD AFTER neural generation on either real or
    // synthetic image. Does not touch guest framebuffer/UI embedded in it.
    // The attachment's current layout must be GENERAL, contents preserved.
    void DrawHudOverlay(const Device& device, Scheduler& scheduler,
                        Frame* dst, const Eden::HudSnapshot& hud);

    VkDescriptorSetLayout GetDescriptorSetLayout();
    VkRenderPass GetRenderPass();

private:
    void CreateDescriptorSetLayout(const Device& device);
    void CreatePipelineLayout(const Device& device);
    void CreateVertexShader(const Device& device);
    void CreateRenderPass(const Device& device, VkFormat frame_format);
    void CreatePipelines(const Device& device);

    vk::DescriptorSetLayout descriptor_set_layout;
    vk::PipelineLayout pipeline_layout;
    vk::Sampler sampler;
    vk::ShaderModule vertex_shader;
    vk::ShaderModule fragment_shader;
    vk::RenderPass render_pass;
    vk::Pipeline opaque_pipeline;
    vk::Pipeline premultiplied_pipeline;
    vk::Pipeline coverage_pipeline;
    vk::PipelineLayout hud_layout;
    vk::Pipeline hud_pipeline;
    // LOAD_OP_LOAD and GENERAL preserve the interpolated/real pixels;
    // this overlay renderpass is framebuffer-compatible with render_pass.
    vk::RenderPass hud_overlay_render_pass;
    vk::PipelineLayout hud_overlay_layout;
    vk::Pipeline hud_overlay_pipeline;
};

} // namespace Vulkan
