// SPDX-License-Identifier: MIT
// R09: independently recovered FP16 C64/128/256 split into real model slices.
#include "video_core/renderer_vulkan/nr_rdna2_weight_decode.h"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;

static void CheckWide(std::uint32_t c) {
    std::vector<float> residual(c+16u),short_gain(c-16u),merged{999.0f};
    for(std::uint32_t i=0;i<c;++i)residual[i]=float(i)/8.0f;
    for(std::uint32_t i=0;i<16u;++i)residual[c+i]=500.0f+float(i);
    for(std::uint32_t i=0;i<c-16u;++i)short_gain[i]=516.0f+float(i);
    assert(NeuralRecoverUpsampleGains(short_gain,residual,c,merged));
    assert(merged.size()==c);
    for(std::uint32_t i=0;i<c;++i)
        assert(merged[i]==500.0f+float(i));
    std::vector<float> recovered_residual;
    assert(NeuralWideUpsampleResidual(residual,c,recovered_residual));
    assert(recovered_residual.size()==c);
    for(std::uint32_t i=0;i<c;++i)
        assert(recovered_residual[i]==float(i)/8.0f);
    // Accept full source data; it must not be prepended twice.
    assert(NeuralRecoverUpsampleGains(merged,residual,c,recovered_residual));
    assert(recovered_residual==merged);
    auto broken=short_gain;
    broken.pop_back();
    assert(!NeuralRecoverUpsampleGains(broken,residual,c,merged));
    assert(merged.empty());
    auto extra=residual;
    extra.pop_back();
    assert(!NeuralRecoverUpsampleGains(short_gain,extra,c,merged));
    assert(merged.empty());
    assert(!NeuralWideUpsampleResidual(extra,c,recovered_residual));
    assert(recovered_residual.empty());
    extra=residual;
    extra[c]=std::numeric_limits<float>::quiet_NaN();
    assert(!NeuralRecoverUpsampleGains(short_gain,extra,c,merged));
    assert(merged.empty());
    extra=residual;
    extra[0]=std::numeric_limits<float>::infinity();
    assert(!NeuralWideUpsampleResidual(extra,c,recovered_residual));
    assert(recovered_residual.empty());
    broken=short_gain;
    broken[0]=std::numeric_limits<float>::infinity();
    assert(!NeuralRecoverUpsampleGains(broken,residual,c,merged));
    assert(merged.empty());
}
int main(){
    std::vector<float> gain32(32),output;
    for(std::uint32_t i=0;i<32u;++i)gain32[i]=float(i);
    assert(NeuralRecoverUpsampleGains(gain32,{},32u,output));
    assert(output==gain32);
    assert(!NeuralRecoverUpsampleGains(gain32,{},64u,output));
    assert(output.empty());
    assert(!NeuralRecoverUpsampleGains(gain32,{},48u,output));
    assert(output.empty());
    CheckWide(64u);
    CheckWide(128u);
    CheckWide(256u);
}
