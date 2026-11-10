// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_policy.h"
#include <cassert>
using namespace Eden::Graphics::DlssNrMin;

int main() {
    static_assert(IsValid16x9(kCurrentR09Graph));
    static_assert(IsValid16x9(kCandidateMinRaster));
    static_assert(!IsValid16x9({1920u, 1200u}));
    static_assert(!IsValid16x9({0u, 0u}));
    static_assert(!IsValid16x9({0xffffffffu, 0xffffffffu}));
    static_assert(Pixels(kCurrentR09Graph) == 2073600ull);
    static_assert(Pixels(kCandidateMinRaster) == 921600ull);
    static_assert(PotentialPixelReduction(
        kCurrentR09Graph, kCandidateMinRaster) == 1152000ull);
    static_assert(PotentialPixelReduction(
        kCandidateMinRaster, kCurrentR09Graph) == 0ull);
    constexpr auto full = ProposeSpatial(kCurrentR09Graph);
    static_assert(full.valid);
    static_assert(full.work.width == 1728u && full.work.height == 972u);
    static_assert(full.center.width == 1536u && full.center.height == 864u);
    static_assert(full.work_pixels == 1679616ull);
    constexpr auto reduced = ProposeSpatial(kCandidateMinRaster);
    static_assert(reduced.valid && reduced.work.width == 1152u);
    static_assert(reduced.work.height == 648u);
    static_assert(reduced.work_pixels == 746496ull);
    static_assert(!ProposeSpatial({1920u, 1200u}).valid);
    static_assert(!ProposeSpatial(kCurrentR09Graph, 101u, 80u).valid);
    static_assert(!ProposeSpatial(kCurrentR09Graph, 70u, 80u).valid);
    static_assert(!ProposeSpatial(kCurrentR09Graph, 90u, 0u).valid);

    constexpr std::uint64_t mib = 1024ull * 1024ull;
    static_assert(FitsMeasuredGpuBudget(1000*mib, 500*mib, 250*mib));
    static_assert(!FitsMeasuredGpuBudget(700*mib, 500*mib, 250*mib));
    static_assert(!FitsMeasuredGpuBudget(250*mib, 1*mib, 250*mib));
    static_assert(!FitsMeasuredGpuBudget(1000*mib, 0u, 250*mib));
    TrialEvidence e{};
    assert(PlanTrial(e, true, true) == TrialReason::MissingFrameHandoff);
    e.guest_frame_handoff = true;
    assert(PlanTrial(e, true, true) == TrialReason::MissingCompleteGraph);
    e.complete_original_graph = true;
    assert(PlanTrial(e, true, true) == TrialReason::NeedsDynamicPlan);
    assert(PlanTrial(e, false, false) ==
           TrialReason::MissingValidatedResourceLifetime);
    e.variable_raster_graph = true;
    assert(PlanTrial(e, true, true) == TrialReason::MissingTemporalInputs);
    e.motion_vectors_and_depth = true;
    e.temporal_reprojection_validated = true;
    assert(PlanTrial(e, true, true) ==
           TrialReason::MissingValidatedResourceLifetime);
    e.resource_lifetime_and_fences = true;
    assert(PlanTrial(e, true, true) == TrialReason::MissingMeasuredBudget);
    e.gpu_budget_measured_and_fits = true;
    assert(PlanTrial(e, true, true) == TrialReason::MissingVulkanProof);
    e.vk_spatial_warp_validated = true;
    assert(PlanTrial(e, true, true) ==
           TrialReason::EligibleForHostExperiment);
    assert(!kPs5MinRuntimeQualified);
    assert(!CanExecuteOnPs5(e)); // Host proof cannot enable console.
}
