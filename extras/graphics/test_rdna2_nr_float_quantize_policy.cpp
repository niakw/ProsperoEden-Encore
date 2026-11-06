// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include "rdna2_nr_float_quantize_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(const std::uint32_t count:{4u,64u*4u,2560u*512u,
                                   2560u*1024u,2560u*4096u}){
        const FloatQuantize p{count,0u,0u,0u};
        const FloatQuantizeStorage s{std::uint64_t(count)*4u,count};
        assert(CanFloatQuantize(p,s));
        assert(FloatQuantizeGroups(p)==(count/4u+63u)/64u);
        assert(!CanFloatQuantize(p,{s.input_bytes-1u,s.output_bytes}));
        assert(!CanFloatQuantize(p,{s.input_bytes,s.output_bytes-1u}));
    }
    const FloatQuantizeStorage max{256ull<<20,256ull<<20};
    assert(CanFloatQuantize({256u,4u,16u,0u},max));
    assert(!CanFloatQuantize({256u,4u,15u,0u},max));
    assert(!CanFloatQuantize({256u,4u,16u,1u},max));
    assert(!CanFloatQuantize({256u,4u,16u,0u},{0u,max.output_bytes}));
    assert(!CanFloatQuantize({0u,0u,0u,0u},max));
    assert(!CanFloatQuantize({3u,0u,0u,0u},max));
    assert(!CanFloatQuantize({16777216u,0u,0u,0u},max)); // >65535 groups
    assert(!CanFloatQuantize({4u,UINT32_MAX,0u,0u},max));
    assert(!CanFloatQuantize({4u,0u,UINT32_MAX,0u},max));
}
