// SPDX-License-Identifier: MIT
#include "video_core/renderer_vulkan/nr_rdna2_split_residual_weight_loader.h"
#include "rdna2_nr_vit_epilogue_policy.h"
#include "rdna2_nr_projection_policy.h"
#include <cassert>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    std::vector<std::uint8_t> matrix(512u*512u,0x38u);
    std::vector<std::uint8_t> gain(1024u);
    // Exact FP16 representation of +1.0 for all 512 skip channels.
    for(std::size_t i=0;i<512u;++i){
        gain[2u*i]=0u;
        gain[2u*i+1u]=0x3cu;
    }
    matrix[0]=0x00u; // existing model requantization +0 -> -0
    SplitResidualWeights staged;
    assert(DecodeSplitResidualWeights(matrix,gain,staged));
    assert(staged.matrix.size()==512u*512u);
    assert(staged.gain_f16.size()==1024u);
    assert(staged.matrix[0]==0x80u);
    assert(staged.matrix[1]==0x38u);
    assert(staged.gain_f16[1]==0x3cu);
    const Projection proj{2160u,512u,512u,512u,512u,0u,0u};
    const Storage caps{2160ull*512u,512u*512u,
                       2160ull*512u*4u,2160ull*512u*4u};
    assert(CanDispatch(proj,caps));
    const VitResidual residual{2160u,512u,0u,0u,0u,0u};
    const VitEpilogueStorage rcaps{
        caps.output_bytes,2160ull*512u,1024u,2160ull*512u};
    assert(CanVitResidual(residual,rcaps));
    assert(!CanVitResidual(residual,{caps.output_bytes,
        2160ull*512u,1023u,2160ull*512u}));
    assert(!DecodeSplitResidualWeights(
        std::span<const std::uint8_t>{matrix.data(),matrix.size()-1u},
        gain,staged));
    assert(staged.matrix.empty()&&staged.gain_f16.empty());
    assert(!DecodeSplitResidualWeights(matrix,
        std::span<const std::uint8_t>{gain.data(),gain.size()-1u},
        staged));
    assert(staged.matrix.empty()&&staged.gain_f16.empty());
    matrix[100u]=0x7fu;
    assert(!DecodeSplitResidualWeights(matrix,gain,staged));
    assert(staged.matrix.empty()&&staged.gain_f16.empty());
    matrix[100u]=0x38u;
    // NaN FP16 (0x7e00) must be rejected by the gain decoder.
    gain[0]=0u;gain[1]=0x7eu;
    assert(!DecodeSplitResidualWeights(matrix,gain,staged));
    assert(staged.matrix.empty()&&staged.gain_f16.empty());
}
