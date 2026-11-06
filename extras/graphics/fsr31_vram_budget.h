// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Exact nominal FSR 3.1.4 image sizes from the versioned Vulkan backend.
// This is a *preallocation* memory budget, not proof that PS5 has enough VRAM.
// Vulkan may add heap alignment, tiling and staging-buffer overhead.
#include <algorithm>
#include <cstdint>

namespace Eden::Graphics::Fsr31Budget {
constexpr std::uint64_t MiB=1024ULL*1024;
constexpr std::uint64_t AbsoluteLimit=512*MiB;
enum class Decision : std::uint8_t {
    Allowed, InvalidDimensions, ExceedsAbsoluteLimit, InsufficientDeviceMemory,
};
struct Dimensions {
    std::uint32_t render_width{};
    std::uint32_t render_height{};
    std::uint32_t output_width{};
    std::uint32_t output_height{};
};
struct Memory {
    std::uint64_t device_local_bytes{};
    std::uint64_t used_bytes{};
    bool usage_is_known{};
};
struct Result {
    Decision decision{Decision::InvalidDimensions};
    std::uint64_t nominal_bytes{};
    std::uint64_t required_bytes{};
};
[[nodiscard]] inline Result Evaluate(Dimensions dim, Memory memory) noexcept {
    const auto rw=dim.render_width, rh=dim.render_height;
    const auto ow=dim.output_width, oh=dim.output_height;
    if (rw<64 || rh<64 || rw>8192 || rh>8192 ||
        ow<rw || oh<rh || ow>8192 || oh>8192 ||
        ow>3ULL*rw || oh>3ULL*rh)
        return {};
    const auto render=static_cast<std::uint64_t>(rw)*rh;
    const auto output=static_cast<std::uint64_t>(ow)*oh;
    const auto half=static_cast<std::uint64_t>(std::max(1U,rw/2))*
                    std::max(1U,rh/2);
    std::uint64_t nominal=0;
    // 2x accumulation R8, 2x luma R16F, 2x history RGBA8.
    nominal+=render*(2*1+2*2+2*4);
    // 2x internal output RGB16F(alpha) + final RGBA16F + new locks R8.
    nominal+=output*(2*8+8+1);
    // Farthest depth R16F + shading-change R8 @ half render size.
    nominal+=render*2 + half;
    // SPD mip chain uses R16G16F; >= 6 levels, down to 1x1.
    auto mw=std::max(1U,rw/2), mh=std::max(1U,rh/2);
    unsigned level=0;
    for (;;) {
        nominal+=static_cast<std::uint64_t>(mw)*mh*4;
        ++level;
        if (mw==1 && mh==1) break;
        mw=std::max(1U,mw/2);
        mh=std::max(1U,mh/2);
    }
    while (level++<6) nominal+=4;
    // Half-res depth + four render-size auxiliaries:
    // motion R16G16F, dilated depth R32F, nearest depth R32U, reactive RGBA8.
    nominal+=half*2+render*(4+4+4+4);
    // Frame info RGBA32F, SPD atomic uint, Lanczos R16 128x1,
    // default reactive R8.
    nominal+=16+4+256+1;
    // 12.5% image-padding overhead + 8 MiB descriptor/staging headroom.
    const auto required=nominal+nominal/8+8*MiB;
    if (required>AbsoluteLimit)
        return {Decision::ExceedsAbsoluteLimit,nominal,required};
    if (memory.device_local_bytes < required*4)
        return {Decision::InsufficientDeviceMemory,nominal,required};
    if (memory.usage_is_known) {
        // Keep at least 75% of available VRAM for textures, guest GPU
        // surfaces, shaders and frame generation. Unknown usage cannot
        // bypass AbsoluteLimit above, but has no invented free capacity.
        if (memory.device_local_bytes<=memory.used_bytes ||
            (memory.device_local_bytes-memory.used_bytes)/4<required)
            return {Decision::InsufficientDeviceMemory,nominal,required};
    }
    return {Decision::Allowed,nominal,required};
}
} // namespace Eden::Graphics::Fsr31Budget
