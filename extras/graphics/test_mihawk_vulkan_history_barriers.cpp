// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_vulkan_history_barriers.h"
#include <cassert>
#include <cstdint>

using namespace Eden::FeatureLab;
int main() {
    const auto src = reinterpret_cast<VkImage>(static_cast<uintptr_t>(0x1010));
    const auto dst = reinterpret_cast<VkImage>(static_cast<uintptr_t>(0x2020));
    const auto out = reinterpret_cast<VkImage>(static_cast<uintptr_t>(0x3030));
    auto before = BeforeHistoryCopy(src, dst, false);
    assert(before.source.oldLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(before.source.newLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(before.source.srcAccessMask == VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
    assert(before.history.oldLayout == VK_IMAGE_LAYOUT_UNDEFINED);
    assert(before.history.dstAccessMask == VK_ACCESS_TRANSFER_WRITE_BIT);
    assert(before.source.image != before.history.image);
    before = BeforeHistoryCopy(src, dst, true);
    assert(before.history.oldLayout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);
    assert(before.history.srcAccessMask == VK_ACCESS_SHADER_READ_BIT);
    const auto after = AfterHistoryCopy(src, dst);
    assert(after.source.newLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(after.history.newLayout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);
    assert(after.history.dstAccessMask == VK_ACCESS_SHADER_READ_BIT);
    const auto init = BeforeNeuralOutput(dst, false);
    assert(init.oldLayout == VK_IMAGE_LAYOUT_UNDEFINED);
    assert(init.newLayout == VK_IMAGE_LAYOUT_GENERAL);
    const auto reinit = BeforeNeuralOutput(dst, true);
    assert(reinit.oldLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(reinit.dstAccessMask == VK_ACCESS_SHADER_WRITE_BIT);
    const auto convert = BeforeGeneratedBlit(dst, out);
    assert(convert.source.oldLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(convert.source.newLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(convert.history.oldLayout == VK_IMAGE_LAYOUT_UNDEFINED);
    assert(convert.history.newLayout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    assert(AfterGeneratedBlit(out).newLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(AfterGeneratedBlit(out).srcAccessMask == VK_ACCESS_TRANSFER_WRITE_BIT);
}
