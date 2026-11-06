// SPDX-License-Identifier: GPL-3.0-or-later
#include "aa_source_extent.h"
#include <cassert>
#include <cstdint>
#include <initializer_list>
using Eden::Graphics::AaExtent;
using Eden::Graphics::AaSourceExtent;
using Eden::Graphics::AaValid;
using Eden::Graphics::AaExtentChanged;
static_assert(AaValid({1280, 720}));
static_assert(!AaValid({0, 720}));
static_assert(!AaValid({8193, 720}));
static_assert(AaSourceExtent(false, {1280,720}, {1920,1080}).width == 1280);
static_assert(AaSourceExtent(true, {1280,720}, {1920,1080}).width == 1920);
static_assert(AaSourceExtent(true, {1280,720}, {0,0}).width == 0);
static_assert(AaExtentChanged({1280,720},{1920,1080}));
static_assert(!AaExtentChanged({1920,1080},{1920,1080}));
int main() {
    for (std::uint32_t w: {0u,1u,1280u,1920u,3840u,8192u,8193u}) {
        for (std::uint32_t h: {0u,1u,720u,1080u,2160u,8192u,8193u}) {
            const auto raw=AaSourceExtent(false,{w,h},{8192,8192});
            const auto scaled=AaSourceExtent(true,{8192,8192},{w,h});
            if (w==0 || h==0 || w>8192 || h>8192) {
                assert(!AaValid(raw));
                assert(!AaValid(scaled));
            } else {
                assert(raw.width==w && raw.height==h);
                assert(scaled.width==w && scaled.height==h);
            }
        }
    }
    // Change detected independent of upstream source selector. A dynamic
    // resolution adjustment MUST rebuild AA images and descriptors.
    AaExtent last{1920,1080};
    AaExtent next{1600,900};
    assert(AaExtentChanged(last,next));
    last=next;
    assert(!AaExtentChanged(last,next));
    return 0;
}
