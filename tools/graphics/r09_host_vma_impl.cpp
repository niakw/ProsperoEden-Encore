// SPDX-License-Identifier: MIT
// Linux R09 standalone host only. The pinned GPUOpen::VulkanMemoryAllocator
// target is header-only; exactly one translation unit must compile the real
// VMA function definitions. Do not add this to the production/PS5 runtime.
#define VMA_IMPLEMENTATION
#include "video_core/vulkan_common/vma.h"
