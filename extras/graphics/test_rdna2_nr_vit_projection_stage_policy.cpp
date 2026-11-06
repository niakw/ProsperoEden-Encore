// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_projection_stage_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(
    VitProjectionKind kind,std::uint32_t N,std::uint32_t K,
    std::uint32_t tokens) {
    const VitProjectionStageCapacity c{
        std::uint64_t(tokens)*K,std::uint64_t(N)*K,
        std::uint64_t(1024u)*N*4u,
        kind==VitProjectionKind::Expand?0u:
            std::uint64_t(tokens)*N,
        kind==VitProjectionKind::Expand?0u:
            std::uint64_t(N)*2u,
        std::uint64_t(tokens)*N};
    VitProjectionStageBatches p{};
    assert(BuildVitProjectionStage(kind,tokens,c,p));
    assert(ValidateVitProjectionStage(p));
    assert(p.count==(tokens+1023u)/1024u);
    std::uint32_t done=0u;
    for(std::uint32_t i=0u;i<p.count;++i){
        const auto& step=p.slices[i];
        assert(step.gemm.tokens<=1024u);
        assert(step.gemm.a_base_bytes==done*K);
        assert(step.gemm.channels==N&&step.gemm.inner==K);
        if(kind==VitProjectionKind::Expand){
            assert(step.activation.output_offset_bytes==done*N);
            assert(step.activation.channels==N);
        }else {
            assert(step.residual.output_offset_bytes==done*N);
            assert(step.residual.residual_offset_bytes==done*N);
            assert(step.residual.channels==N);
        }
        done+=step.gemm.tokens;
    }
    assert(done==tokens);
    auto invalid=p;
    invalid.slices[p.count-1u].gemm.a_base_bytes=0u;
    if(p.count>1u)assert(!ValidateVitProjectionStage(invalid));
    invalid=p;
    invalid.slices[p.count-1u].gemm.tokens++;
    assert(!ValidateVitProjectionStage(invalid));
    auto broken=c;
    broken.scratch_bytes=0u;
    assert(!BuildVitProjectionStage(kind,tokens,broken,invalid));
    assert(invalid.count==0u);
    broken=c;
    broken.weights_bytes--;
    assert(!BuildVitProjectionStage(kind,tokens,broken,invalid));
    broken=c;
    broken.output_bytes--;
    assert(!BuildVitProjectionStage(kind,tokens,broken,invalid));
    if(kind!=VitProjectionKind::Expand){
        broken=c;
        broken.residual_bytes--;
        assert(!BuildVitProjectionStage(kind,tokens,broken,invalid));
        broken=c;
        broken.gain_bytes--;
        assert(!BuildVitProjectionStage(kind,tokens,broken,invalid));
    }
    broken=c;
    broken.input_bytes--;
    assert(!BuildVitProjectionStage(kind,tokens,broken,invalid));
}
int main() {
    Check(VitProjectionKind::Expand,4096u,1024u,2560u);
    Check(VitProjectionKind::Contract,1024u,4096u,2560u);
    Check(VitProjectionKind::ResidualProjection,1024u,1024u,2560u);
    Check(VitProjectionKind::Expand,4096u,1024u,4096u);
    Check(VitProjectionKind::Contract,1024u,4096u,4096u);
    Check(VitProjectionKind::ResidualProjection,1024u,1024u,4096u);
    VitProjectionStageBatches p{};
    constexpr VitProjectionStageCapacity tiny{
        4096ull*1024u,4096ull*1024u,
        255ull*4096u*4u,0u,0u,4096ull*4096u};
    assert(!BuildVitProjectionStage(VitProjectionKind::Expand,4096u,tiny,p));
    assert(p.count==0u);
    assert(!BuildVitProjectionStage(VitProjectionKind::Expand,0u,tiny,p));
    assert(!BuildVitProjectionStage(VitProjectionKind::Expand,4097u,tiny,p));
}
