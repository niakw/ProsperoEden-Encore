// SPDX-License-Identifier: MIT
#include "rdna2_nr_split_context_repack_policy.h"
#include <cassert>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr SplitContextRepack p{40u,16u,0u,0u};
    constexpr std::uint64_t total=40ull*64u*512u;
    assert(CanSplitContextRepack(p,{total,total}));
    assert(SplitContextRepackGridX(p)==1280u);
    assert(!CanSplitContextRepack(p,{total-4u,total}));
    assert(!CanSplitContextRepack(p,{total,total-4u}));
    assert(!CanSplitContextRepack({40u,8u,0u,0u},{
        UINT64_MAX,UINT64_MAX}));
    assert(!CanSplitContextRepack({0u,16u,0u,0u},{
        UINT64_MAX,UINT64_MAX}));
    assert(!CanSplitContextRepack({1025u,16u,0u,0u},{
        UINT64_MAX,UINT64_MAX}));
    assert(!CanSplitContextRepack({40u,16u,1u,0u},{
        UINT64_MAX,UINT64_MAX}));
    assert(!CanSplitContextRepack({40u,16u,0u,1u},{
        UINT64_MAX,UINT64_MAX}));
    constexpr std::uint32_t windows=2u,heads=16u;
    std::vector<std::uint32_t> src(windows*64u*heads*8u);
    std::vector<std::uint32_t> dst(src.size(),0u);
    // Each 32-bit word is one 4-channel group (E4M3FN).
    for(std::uint32_t w=0;w<windows;++w)
      for(std::uint32_t h=0;h<heads;++h)
        for(std::uint32_t t=0;t<64u;++t)
          for(std::uint32_t lane=0;lane<8u;++lane){
            const auto pos=((w*heads+h)*64u+t)*8u+lane;
            src[pos]=1u+(w<<20u)+(t<<12u)+(h<<4u)+lane;
          }
    for(std::uint32_t w=0;w<windows;++w)
      for(std::uint32_t t=0;t<64u;++t)
        for(std::uint32_t h=0;h<heads;++h)
          for(std::uint32_t lane=0;lane<8u;++lane){
            const auto from=((w*heads+h)*64u+t)*8u+lane;
            const auto to=((w*64u+t)*heads+h)*8u+lane;
            dst[to]=src[from];
          }
    for(std::uint32_t w=0;w<windows;++w)
      for(std::uint32_t t=0;t<64u;++t)
        for(std::uint32_t h=0;h<heads;++h)
          for(std::uint32_t lane=0;lane<8u;++lane){
            const auto to=((w*64u+t)*heads+h)*8u+lane;
            assert(dst[to]==1u+(w<<20u)+(t<<12u)+(h<<4u)+lane);
          }
    assert(CanSplitContextRepack({windows,heads,0u,0u},{
        std::uint64_t(src.size())*4u,std::uint64_t(dst.size())*4u}));
}
