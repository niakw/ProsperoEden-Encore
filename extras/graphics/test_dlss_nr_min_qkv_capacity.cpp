// SPDX-License-Identifier: MIT
// Genuine R09 QKV/attention and FFN batch-policy evidence for a 1-plane QKV.
// Does not load proprietary model weights or dispatch a Vulkan GPU.
#include "rdna2_nr_vit_qkv_batches_policy.h"
#include "rdna2_nr_vit_projection_stage_policy.h"
#include <cassert>
#include <cstdint>
#include <initializer_list>
using namespace Eden::Graphics::NeuralRDNA2;

int main() {
    for (const std::uint32_t tokens : {960u,2560u,4096u}) {
        const auto plane=std::uint64_t(tokens)*1024u;
        const VitQkvBuffersCapacity compact{
            plane,3072u*1024u,4u*plane,128u,
            plane,plane,plane,plane};
        const VitQkvBuffersCapacity padded{
            plane,3072u*1024u,4u*plane,128u,
            4u*plane,4u*plane,4u*plane,plane};
        VitQkvBatches lean{},oversized{};
        assert(BuildVitQkvBatches(tokens,compact,lean));
        assert(BuildVitQkvBatches(tokens,padded,oversized));
        assert(ValidVitQkvBatches(lean));
        assert(ValidVitQkvBatches(oversized));
        assert(lean.count==oversized.count);
        assert(lean.count!=0u);
        for(std::uint32_t i=0;i<lean.count;++i) {
            // Lower Q/K/V storage must not increase GEMM/normalize batches.
            const auto& a=lean.slices[i];
            const auto& b=oversized.slices[i];
            assert(a.gemm.tokens==b.gemm.tokens);
            assert(a.normalize.tokens==b.normalize.tokens);
            assert(a.normalize.q_base_bytes==b.normalize.q_base_bytes);
            assert(a.normalize.k_base_bytes==b.normalize.k_base_bytes);
            assert(a.normalize.v_base_bytes==b.normalize.v_base_bytes);
        }
        assert(lean.attention_storage.q_bytes==plane);
        assert(lean.attention_storage.k_bytes==plane);
        assert(lean.attention_storage.v_bytes==plane);
        assert(CanVitAttention(lean.attention,lean.attention_storage));
        {
            // Exact packed E4M3FN [tokens,32,32] footprint, not 4 planes.
            const VitQkvNorm normalized{tokens,0u,0u,0u,0u,0u};
            const VitQkvNormStorage capacity{
                12u*plane,128u,plane,plane,plane};
            assert(CanVitQkvNorm(normalized,capacity));
            auto too_small=capacity;
            too_small.q_bytes=plane-4u;
            assert(!CanVitQkvNorm(normalized,too_small));
            too_small=capacity;
            too_small.k_bytes=plane-4u;
            assert(!CanVitQkvNorm(normalized,too_small));
            too_small=capacity;
            too_small.v_bytes=plane-4u;
            assert(!CanVitQkvNorm(normalized,too_small));
        }
        for(std::uint32_t r=0u;r<3u;++r) {
            auto too_small=compact;
            if(r==0u)too_small.query=plane-4u;
            if(r==1u)too_small.key=plane-4u;
            if(r==2u)too_small.value=plane-4u;
            VitQkvBatches rejected{};
            assert(!BuildVitQkvBatches(tokens,too_small,rejected));
            assert(rejected.count==0u);
        }
        {
            // Preserve all three authentic ViT learned projection plans
            // and their original FP32 scratch batch count.
            const VitProjectionStageCapacity expand{
                plane,4096u*1024u,4u*plane,
                0u,0u,4u*plane};
            const VitProjectionStageCapacity contract{
                4u*plane,1024u*4096u,4u*plane,
                plane,2048u,plane};
            const VitProjectionStageCapacity residual{
                plane,1024u*1024u,4u*plane,
                plane,2048u,plane};
            for(const auto& [kind,cap] : {
                std::pair{VitProjectionKind::Expand,expand},
                std::pair{VitProjectionKind::Contract,contract},
                std::pair{VitProjectionKind::ResidualProjection,residual}}) {
                VitProjectionStageBatches batches{};
                assert(BuildVitProjectionStage(kind,tokens,cap,batches));
                assert(ValidateVitProjectionStage(batches));
                assert(batches.count!=0u);
            }
        }
    }
}
