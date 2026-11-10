// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_spatial_abi.h"
#include <cassert>
using namespace Eden::Graphics::DlssNrMin;
int main() {
    constexpr auto native=ProposeSpatial(kCurrentR09Graph);
    constexpr auto min=ProposeSpatial(kCandidateMinRaster);
    static_assert(native.valid && min.valid);
    constexpr auto high=EstimateStandaloneSpatialStaging(
        native.native,native.work);
    constexpr auto low=EstimateStandaloneSpatialStaging(
        min.native,min.work);
    static_assert(high.valid && low.valid);
    static_assert(high.base_rgba16f==1679616ull*8u);
    static_assert(high.output_rgba32f==2073600ull*16u);
    static_assert(low.base_rgba16f==746496ull*8u);
    static_assert(low.output_rgba32f==921600ull*16u);
    static_assert(high.total==high.base_rgba16f*2u+
                  high.output_rgba32f);
    static_assert(low.total==low.base_rgba16f*2u+
                  low.output_rgba32f);
    static_assert(low.total<high.total);
    static_assert(!EstimateStandaloneSpatialStaging(
        {1920u,1080u},{3840u,2160u}).valid);
    static_assert(!EstimateStandaloneSpatialStaging(
        {1920u,1200u},{1280u,720u}).valid);
    static_assert(!CanStageSpatialSurfaces(
        native.native,native.work,high.total,0u));
    static_assert(CanStageSpatialSurfaces(
        native.native,native.work,high.total+1u,1u));
    constexpr std::uint64_t mib=1024ull*1024ull;
    assert(!CanStageSpatialSurfaces(
        native.native,native.work,100u*mib,64u*mib));
    assert(CanStageSpatialSurfaces(
        min.native,min.work,128u*mib,64u*mib));
    // No claim that estimated extra surfaces represent peak R09 GPU VRAM.
    assert(!kPs5MinRuntimeQualified);
}
