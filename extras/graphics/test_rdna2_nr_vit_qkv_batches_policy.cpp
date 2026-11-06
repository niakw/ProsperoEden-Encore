// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_qkv_batches_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr std::uint64_t T=4096u,N=3072u,K=1024u;
    const VitQkvBuffersCapacity caps{
        T*K,N*K,2048u*N*4u,128u,T*K,T*K,T*K,T*K};
    VitQkvBatches plan{};
    assert(BuildVitQkvBatches(4096u,caps,plan));
    assert(ValidVitQkvBatches(plan));
    assert(plan.count==2u&&plan.total_tokens==4096u);
    assert(plan.slices[0].gemm.tokens==2048u);
    assert(plan.slices[1].gemm.tokens==2048u);
    assert(plan.slices[1].gemm.a_base_bytes==2048u*K);
    assert(plan.slices[1].normalize.q_base_bytes==2048u*K);
    assert(plan.slices[1].normalize.k_base_bytes==2048u*K);
    assert(plan.slices[1].normalize.v_base_bytes==2048u*K);
    auto bad=plan;bad.slices[1].normalize.k_base_bytes=0u;
    assert(!ValidVitQkvBatches(bad));
    bad=plan;bad.slices[0].gemm.a_base_bytes+=4u;
    assert(!ValidVitQkvBatches(bad));
    // The 2560-token 1080p native plan remains one dispatch pair if
    // its whole FP32 result fits into the available transient.
    auto full=caps;full.fp32=2560u*N*4u;
    assert(BuildVitQkvBatches(2560u,full,plan));
    assert(plan.count==1u&&plan.slices[0].gemm.tokens==2560u);
    assert(ValidVitQkvBatches(plan));
    // A 1024-token transient now supports 4,096 tokens via 4 ordered slices.
    full.fp32=1024u*N*4u;
    assert(BuildVitQkvBatches(4096u,full,plan));
    assert(plan.count==4u&&ValidVitQkvBatches(plan));
    // Bound is 16 slices: reject micro-batches that would silently
    // require more dispatches than retained in the plan.
    full.fp32=255u*N*4u;
    assert(!BuildVitQkvBatches(4096u,full,plan));
    assert(plan.count==0u);
    full=caps;full.fp32=0u;
    assert(!BuildVitQkvBatches(4096u,full,plan));
    full=caps;full.query=T*K-1u;
    assert(!BuildVitQkvBatches(4096u,full,plan));
    full=caps;full.weights=N*K-1u;
    assert(!BuildVitQkvBatches(4096u,full,plan));
    full=caps;full.temperatures=127u;
    assert(!BuildVitQkvBatches(4096u,full,plan));
    assert(!BuildVitQkvBatches(4097u,caps,plan));
    assert(!BuildVitQkvBatches(0u,caps,plan));
}
