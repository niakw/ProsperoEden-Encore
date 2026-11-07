// SPDX-License-Identifier: MIT
#include "rdna2_nr_image_feature_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr ImageFeatureCapacity native{
        1920ull*1080u*32u,1024u,1920ull*1080u*32u};
    static_assert(CanImageFeatureStage({1920u,1080u,0u},native));
    static_assert(CanImageFeatureStage({1920u,1080u,1u},native));
    static_assert(!CanImageFeatureStage({1920u,1080u,2u},native));
    assert(!CanImageFeatureStage({1920u,1080u,0u},{
        native.input_bytes-1u,1024u,native.output_bytes}));
    assert(!CanImageFeatureStage({1920u,1080u,0u},{
        native.input_bytes,1023u,native.output_bytes}));
    assert(!CanImageFeatureStage({1920u,1080u,0u},{
        native.input_bytes,1024u,native.output_bytes-1u}));
    assert(!CanImageFeatureStage({0u,1080u,0u},native));
    assert(!CanImageFeatureStage({1920u,0u,1u},native));
    constexpr ImageFeatureCapacity uhd{
        3840ull*2160u*32u,1024u,3840ull*2160u*32u};
    static_assert(CanImageFeatureStage({3840u,2160u,0u},uhd));
    assert(!CanImageFeatureStage({4096u,2160u,0u},{
        UINT64_MAX,UINT64_MAX,UINT64_MAX}));
}
