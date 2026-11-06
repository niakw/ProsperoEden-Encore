// SPDX-License-Identifier: MIT
// Exact 2D feature-raster <-> FSwin quadrant-window roundtrip.
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <vector>
#include "rdna2_nr_fswin_raster_layout_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(std::uint32_t width,std::uint32_t height,
                  std::uint32_t channels){
    const auto wx=(width+7u)/8u,wy=(height+7u)/8u;
    const auto wp=channels/4u;
    FSwinRasterLayout p{width,height,wx,wy,channels,0};
    const auto raster_size=std::uint64_t(width)*height*channels;
    const auto window_size=std::uint64_t(wx)*wy*64u*channels;
    assert(CanFSwinRasterLayout(p,{raster_size,window_size}));
    assert(FSwinRasterLayoutGridX(p)==wp);
    std::vector<std::uint32_t> raster(raster_size/4u);
    for(std::size_t i=0;i<raster.size();++i)
        raster[i]=std::uint32_t(i*181u+7u);
    std::vector<std::uint32_t> packed(window_size/4u,0xffffffffu);
    for(std::uint32_t w=0;w<wx*wy;++w)
      for(std::uint32_t t=0;t<64u;++t)
       for(std::uint32_t cw=0;cw<wp;++cw){
        const auto q=t/16u,s=t%16u;
        const auto x=(w%wx)*8u+(q%2u)*4u+s%4u;
        const auto y=(w/wx)*8u+(q/2u)*4u+s/4u;
        const auto dst=(w*64u+t)*wp+cw;
        packed[dst]=x<width&&y<height?
            raster[(y*width+x)*wp+cw]:0u;
       }
    p.direction=1u;
    assert(CanFSwinRasterLayout(p,{window_size,raster_size}));
    std::vector<std::uint32_t> output(raster.size(),0xdeadbeefu);
    for(std::uint32_t w=0;w<wx*wy;++w)
      for(std::uint32_t t=0;t<64u;++t)
       for(std::uint32_t cw=0;cw<wp;++cw){
        const auto q=t/16u,s=t%16u;
        const auto x=(w%wx)*8u+(q%2u)*4u+s%4u;
        const auto y=(w/wx)*8u+(q/2u)*4u+s/4u;
        if(x<width&&y<height)
            output[(y*width+x)*wp+cw]=packed[(w*64u+t)*wp+cw];
       }
    assert(output==raster);
    assert(!CanFSwinRasterLayout(p,{window_size-1u,raster_size}));
    p.direction=0u;
    assert(!CanFSwinRasterLayout(p,{raster_size,window_size-1u}));
    p.width=p.windows_x*8u+1u;
    assert(!CanFSwinRasterLayout(p,{UINT64_MAX,UINT64_MAX}));
}
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u}) {
        Check(1,1,C);
        Check(8,8,C);
        Check(9,9,C);
        Check(7,13,C);
        Check(31,17,C);
        Check(64,16,C);
    }
    const FSwinRasterLayout fullhd{1920,1080,240,135,32,0};
    const auto input=std::uint64_t{1920}*1080u*32u;
    const auto output=std::uint64_t{240}*135u*64u*32u;
    assert(CanFSwinRasterLayout(fullhd,{input,output}));
    assert(FSwinRasterLayoutGridX(fullhd)==8u);
    // GPU input-boundary raster produced by the previous DS stage.
    // The plan's raster axes are 540x960; its grid is 68x120.
    const FSwinRasterLayout canonical{540,960,68,120,32,0};
    const auto source=std::uint64_t{540}*960u*32u;
    const auto destination=std::uint64_t{68}*120u*64u*32u;
    assert(CanFSwinRasterLayout(canonical,{source,destination}));
    assert(FSwinRasterLayoutGridX(canonical)==8u);
    auto fail=canonical;fail.windows_x=120u;
    assert(!CanFSwinRasterLayout(fail,{source,destination}));
    fail=canonical;fail.direction=1u;
    assert(!CanFSwinRasterLayout(fail,{source,destination}));
    const FSwinRasterLayout bad{2049,2048,257,256,256,0};
    assert(!CanFSwinRasterLayout(bad,{UINT64_MAX,UINT64_MAX}));
    const FSwinRasterLayout bad_channels{8,8,1,1,16,0};
    assert(!CanFSwinRasterLayout(bad_channels,{UINT64_MAX,UINT64_MAX}));
    const FSwinRasterLayout bad_mode{8,8,1,1,32,2};
    assert(!CanFSwinRasterLayout(bad_mode,{UINT64_MAX,UINT64_MAX}));
    const FSwinRasterLayout zero{0,1,0,1,32,0};
    assert(!CanFSwinRasterLayout(zero,{UINT64_MAX,UINT64_MAX}));
}
