// SPDX-License-Identifier: GPL-3.0-or-later
// ABI of the standalone (not integrated) Vulkan 1.1 Min spatial shaders.
// This estimates staging IMAGES ONLY, not learned tensor/descriptor memory.
#pragma once
#include "dlss_nr_min_policy.h"
#include <cstddef>
#include <cstdint>

namespace Eden::Graphics::DlssNrMin {
struct alignas(8) SpatialShaderPush {
    std::uint32_t original_width{},original_height{};
    std::uint32_t work_width{},work_height{};
    float center_fraction_x{0.8f},center_fraction_y{0.8f};
    float work_fraction_x{0.9f},work_fraction_y{0.9f};
};
static_assert(sizeof(SpatialShaderPush)==32u);
static_assert(offsetof(SpatialShaderPush,original_width)==0u);
static_assert(offsetof(SpatialShaderPush,work_width)==8u);
static_assert(offsetof(SpatialShaderPush,center_fraction_x)==16u);
static_assert(offsetof(SpatialShaderPush,work_fraction_x)==24u);

struct SpatialStagingBytes {
    std::uint64_t base_rgba16f{}, enhanced_rgba16f{};
    std::uint64_t output_rgba32f{}, total{};
    bool valid{};
};
[[nodiscard]] constexpr SpatialStagingBytes EstimateStandaloneSpatialStaging(
    Extent original,Extent work) noexcept {
    if(!IsValid16x9(original)||!work.width||!work.height||
       work.width>original.width||work.height>original.height||
       work.width>4096u||work.height>4096u) return {};
    // Two distinct FP16 work images and one FP32 native-res result.
    // This is an UPPER BOUND for these THREE images if no buffers alias.
    // It is NOT a bound for R09's tensor graph or total resident memory.
    const auto work_bytes=Pixels(work)*8u;
    const auto output_bytes=Pixels(original)*16u;
    return {work_bytes,work_bytes,output_bytes,
            2u*work_bytes+output_bytes,true};
}
[[nodiscard]] constexpr bool CanStageSpatialSurfaces(
    Extent original,Extent work,std::uint64_t measured_free_bytes,
    std::uint64_t safety_reserve_bytes) noexcept {
    const auto estimate=EstimateStandaloneSpatialStaging(original,work);
    return estimate.valid && safety_reserve_bytes>0u && FitsMeasuredGpuBudget(
        measured_free_bytes,estimate.total,safety_reserve_bytes);
}
} // namespace Eden::Graphics::DlssNrMin
