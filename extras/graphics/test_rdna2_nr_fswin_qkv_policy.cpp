// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "rdna2_nr_fswin_qkv_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u}){
        const auto heads=C/32u;
        const FSwinQkv p{0,0,0,0,0,0,1,C,heads};
        const auto a=64u*C,w=3u*C*C,o=64u*C;
        const FSwinQkvStorage s{a,w,heads*4u,o,o,o};
        assert(CanFSwinQkv(p,s));
        assert(!CanFSwinQkv(p,{a-1u,w,heads*4u,o,o,o}));
        assert(!CanFSwinQkv(p,{a,w-1u,heads*4u,o,o,o}));
        assert(!CanFSwinQkv(p,{a,w,heads*4u-1u,o,o,o}));
        assert(!CanFSwinQkv(p,{a,w,heads*4u,o-1u,o,o}));
        assert(!CanFSwinQkv(p,{a,w,heads*4u,o,o-1u,o}));
        assert(!CanFSwinQkv(p,{a,w,heads*4u,o,o,o-1u}));
        auto bad=p;bad.heads++;assert(!CanFSwinQkv(bad,s));
        bad=p;bad.windows=257;assert(!CanFSwinQkv(bad,s));
        bad=p;bad.a_base_bytes=1;assert(!CanFSwinQkv(bad,s));
        bad=p;bad.channels=16;assert(!CanFSwinQkv(bad,s));
    }
}
