// SPDX-License-Identifier: GPL-3.0-or-later
// PS5/RDNA2 host-only preparation. NOT a neural renderer, model or shipping mode.
#pragma once
#include <cstdint>

namespace Eden::Graphics::DlssNrMin {

struct Extent {
    std::uint32_t width{}, height{};
};
inline constexpr Extent kCurrentR09Graph{1920u, 1080u};
inline constexpr Extent kCandidateMinRaster{1280u, 720u};
inline constexpr std::uint32_t kWorkPercent = 90u;
inline constexpr std::uint32_t kNativeCenterPercent = 80u;

[[nodiscard]] constexpr bool IsValid16x9(Extent e) noexcept {
    return e.width != 0u && e.height != 0u &&
           e.width <= 4096u && e.height <= 4096u &&
           std::uint64_t(e.width) * 9u == std::uint64_t(e.height) * 16u;
}
[[nodiscard]] constexpr std::uint64_t Pixels(Extent e) noexcept {
    return std::uint64_t(e.width) * e.height;
}

// Geometry proposal from optimizer-fps-dlss5, NOT GPU spatial warp.
// Center maintains its uncompressed pixel density; model work extent
// shrinks in both axes. R09 still needs a fully validated dynamic plan.
struct SpatialProposal {
    Extent native{}, work{}, center{};
    std::uint64_t native_pixels{}, work_pixels{};
    bool valid{};
};
[[nodiscard]] constexpr SpatialProposal ProposeSpatial(
    Extent native, std::uint32_t work_percent = kWorkPercent,
    std::uint32_t center_percent = kNativeCenterPercent) noexcept {
    if (!IsValid16x9(native) || work_percent > 100u ||
        work_percent < 50u || center_percent > work_percent ||
        center_percent == 0u) return {};
    const Extent work{
        static_cast<std::uint32_t>(
            ((std::uint64_t(native.width) * work_percent / 100u) / 4u) * 4u),
        static_cast<std::uint32_t>(
            ((std::uint64_t(native.height) * work_percent / 100u) / 4u) * 4u)};
    const Extent center{
        static_cast<std::uint32_t>(
            ((std::uint64_t(native.width) * center_percent / 100u) / 4u) * 4u),
        static_cast<std::uint32_t>(
            ((std::uint64_t(native.height) * center_percent / 100u) / 4u) * 4u)};
    if (!work.width || !work.height || !center.width || !center.height ||
        center.width > work.width || center.height > work.height) return {};
    return {native, work, center, Pixels(native), Pixels(work), true};
}

// This is a pixel-count estimate, NOT an FPS, memory or GPU-time promise.
[[nodiscard]] constexpr std::uint64_t PotentialPixelReduction(
    Extent before, Extent after) noexcept {
    return Pixels(before) >= Pixels(after)
               ? Pixels(before) - Pixels(after) : 0u;
}

// Vulkan memory heap size != measured free memory. Only admit a future
// pass with a measured free budget and measured R09 peak with reserve.
[[nodiscard]] constexpr bool FitsMeasuredGpuBudget(
    std::uint64_t available_bytes,
    std::uint64_t measured_peak_bytes,
    std::uint64_t reserve_bytes) noexcept {
    return available_bytes > reserve_bytes && measured_peak_bytes != 0u &&
           measured_peak_bytes <= available_bytes - reserve_bytes;
}

enum class TrialReason {
    EligibleForHostExperiment,
    MissingFrameHandoff,
    MissingCompleteGraph,
    NeedsDynamicPlan,
    MissingTemporalInputs,
    MissingValidatedResourceLifetime,
    MissingMeasuredBudget,
    MissingVulkanProof
};
struct TrialEvidence {
    bool guest_frame_handoff{};
    bool complete_original_graph{};
    bool variable_raster_graph{};
    bool motion_vectors_and_depth{};
    bool temporal_reprojection_validated{};
    bool resource_lifetime_and_fences{};
    bool gpu_budget_measured_and_fits{};
    bool vk_spatial_warp_validated{};
};

// Evidence gate; never interpreted as permission to run on console.
[[nodiscard]] constexpr TrialReason PlanTrial(
    TrialEvidence e, bool reduced_resolution, bool cadence_gt_one) noexcept {
    if (!e.guest_frame_handoff) return TrialReason::MissingFrameHandoff;
    if (!e.complete_original_graph) return TrialReason::MissingCompleteGraph;
    if (reduced_resolution && !e.variable_raster_graph)
        return TrialReason::NeedsDynamicPlan;
    if (cadence_gt_one &&
        (!e.motion_vectors_and_depth || !e.temporal_reprojection_validated))
        return TrialReason::MissingTemporalInputs;
    if (!e.resource_lifetime_and_fences)
        return TrialReason::MissingValidatedResourceLifetime;
    if (!e.gpu_budget_measured_and_fits)
        return TrialReason::MissingMeasuredBudget;
    if (!e.vk_spatial_warp_validated)
        return TrialReason::MissingVulkanProof;
    return TrialReason::EligibleForHostExperiment;
}
// Explicit safety gate: cannot be enabled by a successful host-only test.
inline constexpr bool kPs5MinRuntimeQualified = false;
[[nodiscard]] constexpr bool CanExecuteOnPs5(TrialEvidence e) noexcept {
    return kPs5MinRuntimeQualified &&
           PlanTrial(e, true, true) == TrialReason::EligibleForHostExperiment;
}
} // namespace Eden::Graphics::DlssNrMin
