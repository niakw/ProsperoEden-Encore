// SPDX-License-Identifier: MIT
#include "rdna2_nr_proxy_feature_policy.h"
#include <cassert>
#include <cstdint>
#include <limits>
using namespace Eden::Graphics::NeuralRDNA2;
int main() {
    constexpr NeuralProxyFeatures normal{
        1920u,1080u,1920u,1080u,1920u,1080u,7u,
        0.0f,0.0f,0.0f,0.0f,0.0f
    };
    constexpr NeuralProxyStorage buffers{
        1920ull*1080u*16u,1920ull*1080u*32u
    };
    static_assert(sizeof(NeuralProxyFeatures)==12u*sizeof(std::uint32_t));
    static_assert(CanNeuralProxyFeatures(normal,buffers));
    assert(!CanNeuralProxyFeatures(normal,{
        buffers.proxy_bytes-1u,buffers.feature_bytes}));
    assert(!CanNeuralProxyFeatures(normal,{
        buffers.proxy_bytes,buffers.feature_bytes-1u}));
    auto altered=normal;
    altered.full_height=1152u;
    assert(CanNeuralProxyFeatures(altered,{
        buffers.proxy_bytes,1920ull*1152u*32u}));
    altered.full_height=2161u;
    assert(!CanNeuralProxyFeatures(altered,{
        UINT64_MAX,UINT64_MAX}));
    altered=normal;altered.valid_width=0u;
    assert(!CanNeuralProxyFeatures(altered,{UINT64_MAX,UINT64_MAX}));
    altered=normal;altered.source_width=0u;
    assert(!CanNeuralProxyFeatures(altered,{UINT64_MAX,UINT64_MAX}));
    altered=normal;altered.style=-1.0f;
    assert(!CanNeuralProxyFeatures(altered,{UINT64_MAX,UINT64_MAX}));
    altered=normal;altered.auto_mask=
        std::numeric_limits<float>::quiet_NaN();
    assert(!CanNeuralProxyFeatures(altered,{UINT64_MAX,UINT64_MAX}));
    // Reference mirror and midpoint resampling stay within the valid
    // image for the entire 1920x1152 padded field.
    altered=normal;altered.full_height=1152u;
    for(std::uint32_t y=0u;y<altered.full_height;++y){
        const auto sy=y<altered.valid_height?y:
            2u*altered.valid_height-y-2u;
        assert(sy<altered.valid_height);
        const auto sample=((2u*sy+1u)*altered.source_height)/
                          (2u*altered.valid_height);
        assert(sample<altered.source_height);
    }
}
