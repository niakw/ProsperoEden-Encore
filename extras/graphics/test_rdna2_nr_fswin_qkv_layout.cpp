// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <span>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_fswin_qkv_layout.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u}){
        std::vector<std::uint8_t> source(3u*C*C);
        for(std::uint32_t row=0;row<3u*C;++row)
            for(std::uint32_t col=0;col<C;++col)
                source[row*C+col]=std::uint8_t((row*13u+col*7u)&255u);
        std::vector<std::uint8_t> target;
        assert(ReorderFSwinQkvRowMajor(source,C,target));
        assert(target.size()==source.size());
        for(std::uint32_t h=0;h<C/32u;++h)
            for(std::uint32_t p=0;p<3u;++p)
                for(std::uint32_t c=0;c<32u;++c)
                    for(std::uint32_t k=0;k<C;++k)
                        assert(target[(h*96u+p*32u+c)*C+k]==
                               source[(p*C+h*32u+c)*C+k]);
        if(C==32u)assert(source==target);
        assert(!ReorderFSwinQkvRowMajor(source,512u,target));
        assert(target.empty());
        assert(!ReorderFSwinQkvRowMajor(
            std::span(source.data(),source.size()-1u),C,target));
    }
}
