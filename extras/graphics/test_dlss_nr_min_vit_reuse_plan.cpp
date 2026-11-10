// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_vit_reuse_plan.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <string>
using namespace Eden::Graphics::DlssNrMin;

int main() {
    constexpr std::uint64_t mib=1024ull*1024ull;
    for(auto native : {Eden::NeuralPlans::Original,
                       Eden::NeuralPlans::Compact}) {
        for(const auto raster : {kCurrentR09Graph,kCandidateMinRaster}) {
            VitReuseCandidate plan{};
            assert(BuildVitCrossBlockReuseCandidate(native,raster,plan));
            assert(plan.blocks.size()==8u);
            assert(plan.pool_slots.size()==9u);
            assert(plan.in_block_distinct);
            assert(plan.previous_output_matches_next_input);
            assert(!plan.gpu_barriers_proven && !plan.gpu_fences_proven);
            assert(!plan.runnable);
            const auto plane=plan.pool_slots[0].requested_bytes;
            assert(plane==plan.pool_slots[1].requested_bytes);
            assert(plan.candidate_requested_bytes==24ull*plane);
            assert(plan.baseline_requested_bytes==185ull*plane);
            assert(plan.nominal_difference_bytes==161ull*plane);
            for(std::size_t i=0u;i<plan.blocks.size();++i) {
                const auto& b=plan.blocks[i].slots;
                assert(b[static_cast<std::size_t>(VitField::Input)]==i%2u);
                assert(b[static_cast<std::size_t>(VitField::Output)]==(i+1u)%2u);
                for(std::size_t f=0u;f<kVitFieldCount;++f)
                    for(std::size_t g=0u;g<f;++g)
                        assert(b[f]!=b[g]);
                if(i) {
                    const auto& prev=plan.blocks[i-1u].slots;
                    assert(prev[static_cast<std::size_t>(VitField::Output)]==
                           b[static_cast<std::size_t>(VitField::Input)]);
                }
            }
            if(raster.width==1920u) {
                assert(plan.candidate_requested_bytes==60ull*mib);
                assert(plan.baseline_requested_bytes==4625ull*mib/10ull);
                assert(plan.nominal_difference_bytes==4025ull*mib/10ull);
            } else {
                assert(plan.candidate_requested_bytes==225ull*mib/10ull);
                assert(plan.baseline_requested_bytes==1734375ull*mib/10000ull);
                assert(plan.nominal_difference_bytes==
                       plan.baseline_requested_bytes-plan.candidate_requested_bytes);
            }
        }
    }
    VitReuseCandidate rejected{};
    assert(!BuildVitCrossBlockReuseCandidate(
        Eden::NeuralPlans::Original,{3840u,2160u},rejected));
    assert(rejected.blocks.empty() && !rejected.runnable);
    assert(!BuildVitCrossBlockReuseCandidate(
        "",kCandidateMinRaster,rejected));
    assert(rejected.blocks.empty() && !rejected.runnable);
    // Corrupt a recovered ViT dispatch name: no partial alias plan.
    std::string invalid{Eden::NeuralPlans::Original};
    auto pos=invalid.find("CCVit1DProjection");
    assert(pos!=std::string::npos);
    invalid.replace(pos,std::string("CCVit1DProjection").size(),
                    "CCVit1DInvalid");
    assert(!BuildVitCrossBlockReuseCandidate(
        invalid,kCandidateMinRaster,rejected));
    assert(rejected.blocks.empty() && !rejected.runnable);
}
