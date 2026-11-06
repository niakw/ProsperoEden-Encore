// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_session_resize.h"
#include <cassert>
using namespace Eden::FeatureLab;

int main() {
    constexpr auto bgra = VK_FORMAT_B8G8R8A8_UNORM;
    constexpr auto rgba = VK_FORMAT_R8G8B8A8_UNORM;
    const auto choose = [](bool ready, unsigned w, unsigned h, VkFormat old_fmt,
                           unsigned nw, unsigned nh, VkFormat new_fmt) {
        return ChooseMihawkSessionAction(ready, w, h, old_fmt, nw, nh, new_fmt);
    };
    assert(choose(false, 0, 0, bgra, 1920, 1080, bgra) ==
           MihawkSessionAction::Initialize);
    assert(choose(true, 1920, 1080, bgra, 1920, 1080, bgra) ==
           MihawkSessionAction::Keep);
    assert(choose(true, 1920, 1080, bgra, 2560, 1440, bgra) ==
           MihawkSessionAction::RecreateAfterGpuIdle);
    assert(choose(true, 1920, 1080, bgra, 1920, 1080, rgba) ==
           MihawkSessionAction::RecreateAfterGpuIdle);
    assert(choose(true, 2560, 1440, rgba, 1920, 1080, bgra) ==
           MihawkSessionAction::RecreateAfterGpuIdle);
    assert(choose(true, 1920, 1080, bgra, 0, 1080, bgra) ==
           MihawkSessionAction::InvalidTarget);
    assert(choose(false, 0, 0, bgra, 7680, 4320, rgba) ==
           MihawkSessionAction::InvalidTarget);
    assert(choose(false, 0, 0, bgra, 1920, 1080, VK_FORMAT_UNDEFINED) ==
           MihawkSessionAction::InvalidTarget);
    assert(choose(true, 3840, 2160, rgba, 3840, 2160, rgba) ==
           MihawkSessionAction::Keep);
}
