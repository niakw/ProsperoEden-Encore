// SPDX-License-Identifier: GPL-3.0-or-later
#include "loading_artwork_transfer.hpp"
#include <algorithm>
#include <cassert>
#include <vector>
int main() {
    using namespace Eden::LoadingArtwork;
    using Eden::LaunchHandoff::Frame;
    constexpr auto full = Fit(1920, 1080, 3840, 2160);
    static_assert(full.x == 0 && full.y == 0 && full.width == 3840 && full.height == 2160);
    constexpr auto portrait = Fit(2, 4, 8, 4);
    static_assert(portrait.x == 3 && portrait.width == 2 && portrait.height == 4);
    constexpr auto wide = Fit(4, 2, 4, 8);
    static_assert(wide.y == 3 && wide.width == 4 && wide.height == 2);
    static_assert(Fit(0, 1, 1, 1).width == 0);
    const Frame input{2, 2, {
        255, 0, 0, 0, 0, 255, 0, 128,
        0, 0, 255, 255, 255, 255, 255, 0
    }};
    std::vector<std::uint8_t> rgba(16, 0xcc);
    assert(Repack(input, 2, 2, PixelOrder::RGBA, rgba));
    assert((rgba == std::vector<std::uint8_t>{
        255,0,0,255, 0,255,0,255, 0,0,255,255, 255,255,255,255}));
    assert(Repack(input, 2, 2, PixelOrder::BGRA, rgba));
    assert((rgba == std::vector<std::uint8_t>{
        0,0,255,255, 0,255,0,255, 255,0,0,255, 255,255,255,255}));
    std::vector<std::uint8_t> out(4 * 2 * 4 + 4, 0xcc);
    assert(Repack(input, 4, 2, PixelOrder::RGBA, out));
    assert(out[0] == 255 && out[4] == 255 && out[8] == 0 && out[12] == 0);
    assert(out[16+2] == 255 && out[20+2] == 255 && out[24+0] == 255);
    assert(std::all_of(out.end()-4, out.end(), [](auto v){return v == 0xcc;}));
    const auto before = out;
    assert(!Repack(input, 4097, 2, PixelOrder::RGBA, out));
    assert(!Repack(input, 4, 3, PixelOrder::RGBA, out));
    assert(!Repack(Frame{2,2,{1,2,3}}, 1, 1, PixelOrder::RGBA, out));
    assert(out == before);
}
