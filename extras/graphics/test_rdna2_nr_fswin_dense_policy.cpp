// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <limits>
#include <initializer_list>
#include "rdna2_nr_fswin_dense_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u})
        for(std::uint32_t stage=0;stage<4;stage++){
            const FSwinDense p{0,0,0,0,0,1,C,stage};
            const auto in=64u*(stage==1u?4u*C:C);
            const auto wt=stage==0u?4u*C*C:stage==1u?C*128u:C*C;
            const auto out=64u*(stage==0u?4u*C:C);
            const FSwinDenseStorage s{in,wt,C*64u,C*4u,out};
            assert(CanFSwinDense(p,s));
            assert(FSwinDenseGridX(p)==(stage==0u?(C+63u)/64u:1u));
            assert(!CanFSwinDense(p,{in-1u,wt,C*64u,C*4u,out}));
            assert(!CanFSwinDense(p,{in,wt-1u,C*64u,C*4u,out}));
            assert(!CanFSwinDense(p,{in,wt,C*64u,C*4u,out-1u}));
            if(stage>=2u){
                assert(!CanFSwinDense(p,{in,wt,C*64u-1u,C*4u,out}));
                assert(!CanFSwinDense(p,{in,wt,C*64u,C*4u-1u,out}));
            }
        }
    FSwinDense p{0,0,0,0,0,257,32,0};
    const FSwinDenseStorage ample{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX};
    assert(!CanFSwinDense(p,ample));
    p.windows=1;p.channels=16;assert(!CanFSwinDense(p,ample));
    p.channels=32;p.stage=4;assert(!CanFSwinDense(p,ample));
    p.stage=0;p.x_base_bytes=1;assert(!CanFSwinDense(p,ample));
    p.x_base_bytes=0;p.w_base_bytes=UINT32_MAX-3u;
    assert(!CanFSwinDense(p,ample));
}
