// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only negative/positive proof of the NON-EXECUTABLE ViT reuse map.
#include "dlss_nr_min_vit_reuse_policy.h"
#include "r09_native_plans.h"
#include <cassert>
#include <string>
using namespace Eden::Graphics::DlssNrMin;

int main() {
    constexpr std::uint64_t mib=1024ull*1024ull;
    for(const auto plan : {Eden::NeuralPlans::Original,
                           Eden::NeuralPlans::Compact}) {
        for(const auto raster : {kCurrentR09Graph,kCandidateMinRaster}) {
            VitReuseProposal candidate{};
            assert(MakeVitReuseProposal(plan,raster,candidate));
            assert(candidate.reason==VitReuseReject::None);
            assert(candidate.is_non_executable_proposal);
            assert(candidate.physical_buffers==9u);
            assert(IsValidVitReuseMap(candidate.blocks));
            assert(candidate.candidate_requested_bytes==
                   candidate.plane_bytes*kVitReusePlanes);
            assert(candidate.baseline_requested_bytes==
                   candidate.plane_bytes*185u);
            assert(candidate.candidate_difference_bytes==
                   candidate.plane_bytes*161u);
            assert(candidate.candidate_requested_bytes<
                   candidate.baseline_requested_bytes);
            if(raster.width==1920u) {
                assert(candidate.candidate_requested_bytes==60ull*mib);
                assert(candidate.candidate_difference_bytes==4025ull*mib/10u);
            } else {
                assert(candidate.candidate_requested_bytes==225ull*mib/10u);
                assert(candidate.candidate_difference_bytes==1509375ull*mib/10000u);
            }
            // Each block's eight other roles are not aliased with its input,
            // but must not be shared across blocks without explicit barriers.
            for(std::uint32_t i=0;i<kVitBlocks;++i) {
                const auto& b=candidate.blocks[i];
                assert(HasDistinctHandlesWithinBlock(b));
                assert(b.handle[0]!=(b.handle[4]));
                assert(b.handle[1]==2u&&b.handle[5]==5u);
                if(i)assert(b.handle[0]==candidate.blocks[i-1u].handle[4]);
            }
            auto corruption=candidate.blocks;
            corruption[2u].handle[6u]=corruption[2u].handle[7u];
            assert(!IsValidVitReuseMap(corruption));
            corruption=candidate.blocks;
            corruption[4u].handle[0u]=corruption[4u].handle[4u];
            assert(!IsValidVitReuseMap(corruption));
            corruption=candidate.blocks;
            corruption[3u].handle[0u]=9u;
            assert(!IsValidVitReuseMap(corruption));

            VitReuseEvidence proof{};
            assert(CheckVitReuseEvidence(candidate,proof)==
                   VitReuseReject::ConcurrentFrameOrQueue);
            proof.blocks_recorded_serially=true;
            proof.no_concurrent_frame_or_queue=true;
            assert(CheckVitReuseEvidence(candidate,proof)==
                   VitReuseReject::MissingComputeBarrier);
            proof.compute_barrier_after_block.fill(true);
            proof.compute_barrier_after_block[3u]=false;
            assert(CheckVitReuseEvidence(candidate,proof)==
                   VitReuseReject::MissingComputeBarrier);
            proof.compute_barrier_after_block[3u]=true;
            assert(CheckVitReuseEvidence(candidate,proof)==
                   VitReuseReject::MissingLiveRangeProof);
            proof.no_external_consumer_of_temporary_buffers=true;
            proof.no_async_readback_of_shared_buffers=true;
            proof.no_live_descriptor_update_or_rebind_hazard=true;
            assert(CheckVitReuseEvidence(candidate,proof)==
                   VitReuseReject::NotQualifiedOnHardware);
            proof.positive_gpu_validation=true;
            proof.negative_gpu_validation=true;
            assert(!kVitReuseQualifiedForPs5);
            assert(CheckVitReuseEvidence(candidate,proof)==
                   VitReuseReject::NotQualifiedOnHardware);
            // Synthetic flags cannot ever grant live PS5 allocation reuse.
        }
    }
    VitReuseProposal bad{};
    assert(!MakeVitReuseProposal(Eden::NeuralPlans::Original,
             {3840u,2160u},bad));
    assert(bad.reason==VitReuseReject::InvalidModel);
    assert(bad.physical_buffers==0u);
    std::string broken{Eden::NeuralPlans::Compact};
    const auto pos=broken.find("CCVit1DQKV");
    assert(pos!=std::string::npos);
    broken.replace(pos,std::string("CCVit1DQKV").size(),"BROKEN_VIT");
    assert(!MakeVitReuseProposal(broken,kCurrentR09Graph,bad));
    assert(bad.reason==VitReuseReject::InvalidModel);
}
