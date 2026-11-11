// SPDX-License-Identifier: GPL-3.0-or-later
// Exact NOMINAL image byte accounting for a 720p neural pass followed by
// the pinned Eden FSR EASU+RCAS two RGBA16F presentation images per slot.
// This does NOT model allocator padding, tiling, mips, swapchain, the guest
// image, neural tensors/weights, memory fragmentation or peak GPU VRAM.
#pragma once
#include "dlss_nr_min_720_present_handoff.h"
#include <cstdint>
#include <limits>

namespace Eden::Graphics::DlssNrMin {
struct NominalPostFsrImages {
    std::uint64_t nr_output_per_slot{};
    std::uint64_t easu_per_slot{};
    std::uint64_t rcas_per_slot{};
    std::uint64_t per_slot{};
    std::uint64_t all_slots{};
    std::uint32_t slots{};
    bool valid{},measured_gpu_vram{false};
};

[[nodiscard]] constexpr NominalPostFsrImages
CountNominalPostFsrImages(Extent output,std::uint32_t image_slots) noexcept {
    NominalPostFsrImages r{};
    if(!ValidPresent720Output(output)||!image_slots||image_slots>8u)
        return r;
    constexpr std::uint64_t kNrPixels=1280ull*720ull;
    // VK_FORMAT_R32G32B32A32_SFLOAT: 4 x 32-bit floats.
    r.nr_output_per_slot=kNrPixels*16ull;
    // Eden FSR::CreateImages creates TWO RGBA16F images (EASU and RCAS),
    // 4 x 16-bit floats = 8 bytes per pixel for each output-sized image.
    const auto pixel_count=std::uint64_t(output.width)*output.height;
    if(pixel_count>std::numeric_limits<std::uint64_t>::max()/8ull)
        return {};
    r.easu_per_slot=pixel_count*8ull;
    r.rcas_per_slot=r.easu_per_slot;
    if(r.easu_per_slot>
       (std::numeric_limits<std::uint64_t>::max()-r.nr_output_per_slot)/2ull)
        return {};
    r.per_slot=r.nr_output_per_slot+2ull*r.easu_per_slot;
    if(r.per_slot>std::numeric_limits<std::uint64_t>::max()/image_slots)
        return {};
    r.all_slots=r.per_slot*image_slots;
    r.slots=image_slots;
    r.valid=true;
    return r;
}
[[nodiscard]] constexpr bool FitsNominalPostFsrReserve(
    const NominalPostFsrImages& images,std::uint64_t available_bytes,
    std::uint64_t reserve_bytes) noexcept {
    // Necessary, not sufficient: caller must separately obtain a true
    // free-VRAM measurement and include all non-image neural allocations.
    return images.valid&&reserve_bytes>0u&&available_bytes>reserve_bytes&&
           images.all_slots<=available_bytes-reserve_bytes;
}
} // namespace Eden::Graphics::DlssNrMin
