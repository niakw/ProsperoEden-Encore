// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_vulkan_history_barriers.h"
#include <cassert>
#include <cstdint>
template<class T> static T H(std::uintptr_t p) { return reinterpret_cast<T>(p); }
int main() {
    using namespace Eden::FeatureLab;
    const auto real = H<VkImage>(1);
    const auto history = H<VkImage>(2);
    const auto synthetic = H<VkImage>(3);
    const auto rgba = H<VkImage>(4);
    const auto prior = BeforeHistoryCopy(real, history, true);
    assert(prior.source.oldLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(prior.source.newLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    const auto post = AfterHistoryCopy(real, history);
    assert(post.source.oldLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(post.source.newLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(post.source.dstAccessMask & VK_ACCESS_COLOR_ATTACHMENT_READ_BIT);
    assert(post.source.dstAccessMask & VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
    assert(post.dst_stage & VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
    assert(post.history.newLayout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);
    const auto before_blit = BeforeGeneratedBlit(rgba, synthetic);
    assert(before_blit.history.newLayout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    const auto ready = AfterGeneratedBlit(synthetic);
    assert(ready.oldLayout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    assert(ready.newLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(ready.dstAccessMask & VK_ACCESS_COLOR_ATTACHMENT_READ_BIT);
    assert(ready.dstAccessMask & VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
    assert(ready.dstAccessMask & VK_ACCESS_TRANSFER_READ_BIT);
}
