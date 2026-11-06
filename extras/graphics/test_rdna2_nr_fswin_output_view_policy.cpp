// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "video_core/renderer_vulkan/nr_rdna2_fswin_output_view_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u})
        for(std::uint32_t WX:{1u,2u,8u,68u}){
            const auto WY=WX==68u?120u:3u;
            const FSwinWindowLayout l{WX,WY,0,-1};
            const auto bytes=std::uint64_t(WX)*WY*64u*C;
            const auto dest=std::uint64_t(WX*8u-4u)*WY*8u*C;
            FSwinOutputViewPlan p{};
            assert(MakeFSwinOutputViewPlan(l,C,WX*8u-4u,WY*8u,
                                          bytes,dest,p));
            assert(p.shifted&&p.repack.src_shift_y==-1);
            assert(p.repack.dst_shift_y==0&&p.raster.direction==1u);
            assert(p.raster_storage.input_bytes==bytes);
            assert(p.raster_storage.output_bytes==dest);
            assert(FSwinWindowRepackGridX(p.repack)==C/4u);
            assert(FSwinRasterLayoutGridX(p.raster)==C/4u);
            assert(!MakeFSwinOutputViewPlan(l,C,WX*8u-4u,WY*8u,
                                            bytes-1u,dest,p));
            assert(!MakeFSwinOutputViewPlan(l,C,WX*8u-4u,WY*8u,
                                            bytes,dest-1u,p));
            assert(!MakeFSwinOutputViewPlan(l,C,WX*8u+1u,WY*8u,
                                            bytes,dest,p));
            auto bad=l;bad.shift_y=-2;
            assert(!MakeFSwinOutputViewPlan(bad,C,WX*8u-4u,WY*8u,
                                            bytes,dest,p));
        }
    constexpr FSwinWindowLayout native{68u,120u,0,-1};
    constexpr auto bytes=std::uint64_t{68}*120u*64u*32u;
    constexpr auto raster=std::uint64_t{540}*960u*32u;
    FSwinOutputViewPlan p{};
    assert(MakeFSwinOutputViewPlan(native,32u,540u,960u,bytes,raster,p));
    assert(p.shifted&&p.raster.windows_x==68u&&p.raster.windows_y==120u);
    constexpr FSwinWindowLayout plain{2u,2u,0,0};
    assert(MakeFSwinOutputViewPlan(plain,64u,13u,9u,
                                  2u*2u*64u*64u,13u*9u*64u,p));
    assert(!p.shifted);
    constexpr FSwinWindowLayout invalid{65535u,2u,0,0};
    assert(!MakeFSwinOutputViewPlan(invalid,32u,1u,1u,
                                   UINT64_MAX,UINT64_MAX,p));
}
