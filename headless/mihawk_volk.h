// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Isolated Vulkan dispatch namespace for native MihawkGen; do not alias
// RADV's actual vkGetInstanceProcAddr function with a volk global pointer.
#define VK_NO_PROTOTYPES 1
#define VOLK_NAMESPACE 1
#include "../third_party/PS5_MihawkGen/ps5/third_party/volk/volk.h"
using namespace volk;
