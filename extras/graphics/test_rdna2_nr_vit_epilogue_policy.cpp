// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_epilogue_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr auto n=2560u;
    constexpr VitActivation expand{n,4096u,0u,0u};
    constexpr std::uint64_t e=std::uint64_t(n)*4096u;
    assert(CanVitActivation(expand,{e*4u,0u,0u,e}));
    assert(!CanVitActivation(expand,{e*4u-1u,0u,0u,e}));
    assert(!CanVitActivation(expand,{e*4u,0u,0u,e-1u}));
    assert(VitEpilogueGroups(n,4096u)==(e+511u)/512u);
    constexpr VitResidual vit{n,1024u,0u,0u,0u,0u};
    constexpr std::uint64_t v=std::uint64_t(n)*1024u;
    assert(CanVitResidual(vit,{v*4u,v,2048u,v}));
    assert(!CanVitResidual(vit,{v*4u,v-1u,2048u,v}));
    assert(!CanVitResidual(vit,{v*4u,v,2047u,v}));
    assert(!CanVitResidual(vit,{v*4u,v,2048u,v-1u}));
    // Split-Swin 512-channel projection uses the same residual primitive.
    constexpr VitResidual split{2160u,512u,0u,0u,0u,0u};
    constexpr std::uint64_t s=2160ull*512u;
    assert(CanVitResidual(split,{s*4u,s,1024u,s}));
    assert(!CanVitResidual({2160u,513u,0u,0u,0u,0u},
                           {UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    assert(!CanVitResidual({0u,512u,0u,0u,0u,0u},
                           {UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    assert(!CanVitResidual({4097u,512u,0u,0u,0u,0u},
                           {UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    assert(!CanVitResidual({2160u,512u,0u,1u,0u,0u},
                           {UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    assert(!CanVitResidual({2160u,512u,0u,0u,2u,0u},
                           {UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    auto offset=split;offset.input_offset_floats=4u;
    assert(CanVitResidual(offset,{(s+4u)*4u,s,1024u,s}));
    offset=split;offset.gain_offset_halfwords=2u;
    assert(CanVitResidual(offset,{s*4u,s,1028u,s}));
    assert(!CanVitResidual(offset,{s*4u,s,1024u,s}));
    offset=split;offset.gain_offset_halfwords=UINT32_MAX;
    assert(!CanVitResidual(offset,{
        UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    assert(!CanVitActivation({1u,1024u,0u,UINT32_MAX-2u},{
        UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
}
