// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_volk.h"
#include "fsr3_optical_session.h"
#include "ps5_framegen.h"
#include "mihawk_vulkan_history_barriers.h"
#include "diagnostics.h"
#include <array>
#include <memory>
#include <string>

namespace Eden::FeatureLab {
namespace {
VkImageSubresourceLayers ColorLayers() noexcept {
    VkImageSubresourceLayers x{};
    x.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    x.layerCount = 1;
    return x;
}
VkImageMemoryBarrier Transition(VkImage image, VkImageLayout from,
                                 VkImageLayout to, VkAccessFlags src,
                                 VkAccessFlags dst) noexcept {
    return MakeImageBarrier(image, src, dst, from, to);
}
}

Fsr3OpticalSession::~Fsr3OpticalSession() { Destroy(); }

bool Fsr3OpticalSession::Ready() const noexcept {
    return engine_ && engine_->ready();
}

void Fsr3OpticalSession::Destroy() noexcept {
    // Renderer must have drained the command worker before destruction.
    if (engine_ && device_ && vkDeviceWaitIdle)
        (void)vkDeviceWaitIdle(device_);
    engine_.reset();
    device_ = VK_NULL_HANDLE;
    width_ = height_ = 0;
    format_ = VK_FORMAT_UNDEFINED;
}

bool Fsr3OpticalSession::Create(PFN_vkGetInstanceProcAddr proc, VkInstance instance,
                                VkPhysicalDevice physical, VkDevice device,
                                std::uint32_t width, std::uint32_t height,
                                VkFormat format) {
    Destroy();
    if (!proc || !instance || !physical || !device ||
        width < 128 || height < 128 || width > 3840 || height > 2160 ||
        (format != VK_FORMAT_R8G8B8A8_UNORM &&
         format != VK_FORMAT_B8G8R8A8_UNORM))
        return false;
    volkInitializeCustom(proc);
    volkLoadInstance(instance);
    volkLoadDevice(device);
    if (!vkGetPhysicalDeviceFeatures || !vkGetPhysicalDeviceProperties2 ||
        !vkGetPhysicalDeviceFormatProperties || !vkCreateComputePipelines ||
        !vkCmdDispatch || !vkCmdPipelineBarrier || !vkCmdCopyImage ||
        !vkCmdBlitImage || !vkDeviceWaitIdle)
        return false;
    VkPhysicalDeviceFeatures features{};
    vkGetPhysicalDeviceFeatures(physical, &features);
    VkPhysicalDeviceSubgroupProperties subgroup{};
    subgroup.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_PROPERTIES;
    VkPhysicalDeviceProperties2 properties{};
    properties.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;
    properties.pNext = &subgroup;
    vkGetPhysicalDeviceProperties2(physical, &properties);
    if (!features.shaderStorageImageExtendedFormats ||
        !(subgroup.supportedStages & VK_SHADER_STAGE_COMPUTE_BIT) ||
        !(subgroup.supportedOperations & VK_SUBGROUP_FEATURE_QUAD_BIT)) {
        Eden::Report("framegen",
            "FSR3 optical flow requires extended storage images and subgroup quad");
        return false;
    }
    VkFormatProperties output_props{}, present_props{};
    vkGetPhysicalDeviceFormatProperties(
        physical, VK_FORMAT_R8G8B8A8_UNORM, &output_props);
    vkGetPhysicalDeviceFormatProperties(physical, format, &present_props);
    if (!(output_props.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_SRC_BIT) ||
        !(present_props.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_DST_BIT))
        return false;

    auto candidate = std::make_unique<ps5::framegen::interpolator>();
    std::string error;
    if (!candidate->create(physical, device, width, height, error, format)) {
        Eden::Report("framegen", ("FSR3 optical flow: " + error).c_str());
        return false;
    }
    candidate->set_generated(1); // conservative single midpoint
    device_ = device;
    width_ = width;
    height_ = height;
    format_ = format;
    engine_ = std::move(candidate);
    Eden::Report("framegen", "FSR3 optical-flow Vulkan session initialized");
    return true;
}

bool Fsr3OpticalSession::Record(VkCommandBuffer cmd, VkImage real,
                                VkImage synthetic, bool generate) noexcept {
    if (!Ready() || !cmd || !real ||
        (generate && (!synthetic || synthetic == real)))
        return false;
    engine_->prepare(cmd);
    const VkImage owned = engine_->frame_image();
    if (!owned || owned == real || owned == synthetic)
        return false;
    const std::array before{
        Transition(real, VK_IMAGE_LAYOUT_GENERAL,
                   VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                   VK_ACCESS_TRANSFER_READ_BIT),
        Transition(owned, VK_IMAGE_LAYOUT_GENERAL,
                   VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                   VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_TRANSFER_READ_BIT,
                   VK_ACCESS_TRANSFER_WRITE_BIT)
    };
    vkCmdPipelineBarrier(cmd,
        VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |
            VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr,
        static_cast<std::uint32_t>(before.size()), before.data());

    VkImageCopy copy{};
    copy.srcSubresource = copy.dstSubresource = ColorLayers();
    copy.extent = {width_, height_, 1};
    vkCmdCopyImage(cmd, real, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   owned, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
    const std::array after{
        Transition(real, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   VK_IMAGE_LAYOUT_GENERAL, VK_ACCESS_TRANSFER_READ_BIT,
                   VK_ACCESS_TRANSFER_READ_BIT |
                       VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                       VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT),
        Transition(owned, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                   VK_IMAGE_LAYOUT_GENERAL, VK_ACCESS_TRANSFER_WRITE_BIT,
                   VK_ACCESS_SHADER_READ_BIT)
    };
    vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_TRANSFER_BIT |
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        0, 0, nullptr, 0, nullptr,
        static_cast<std::uint32_t>(after.size()), after.data());

    const bool made = engine_->record(cmd, !generate);
    if (generate && made) {
        const auto prepare = Transition(
            synthetic, VK_IMAGE_LAYOUT_GENERAL,
            VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_TRANSFER_WRITE_BIT);
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT,
                             VK_PIPELINE_STAGE_TRANSFER_BIT,
                             0, 0, nullptr, 0, nullptr, 1, &prepare);
        VkImageBlit blit{};
        blit.srcSubresource = blit.dstSubresource = ColorLayers();
        blit.srcOffsets[1] = {
            static_cast<std::int32_t>(width_),
            static_cast<std::int32_t>(height_), 1};
        blit.dstOffsets[1] = blit.srcOffsets[1];
        vkCmdBlitImage(cmd, engine_->output_image(), VK_IMAGE_LAYOUT_GENERAL,
                       synthetic, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                       1, &blit, VK_FILTER_NEAREST);
        const auto ready = Transition(
            synthetic, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            VK_IMAGE_LAYOUT_GENERAL, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_ACCESS_TRANSFER_READ_BIT |
                VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT |
                VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            0, 0, nullptr, 0, nullptr, 1, &ready);
    }
    engine_->advance();
    return !generate || made;
}
} // namespace Eden::FeatureLab
