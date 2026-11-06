// SPDX-License-Identifier: MIT
// Original=16 and Compact=4 native Split blocks, 2 runs each.
// Build with actual 152/76-row MIT shape fixtures; no trained weights.
#include "rdna2_nr_split_native_routes_policy.h"
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
void Check(const char* path,bool original){
    std::ifstream stream(path,std::ios::binary);
    assert(stream);
    const std::string data{std::istreambuf_iterator<char>{stream},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> source;
    assert(ParseNativePlan(data,source)==NativePlanError::Ok);
    NativeSplitRoutes routes;
    assert(BuildNativeSplitRoutes(source,routes)==SplitNativeRoutesError::Ok);
    assert(routes.count==(original?16u:4u));
    assert(routes.run_count==2u);
    assert(routes.runs[0].count==(original?8u:2u));
    assert(routes.runs[1].count==(original?8u:2u));
    assert(routes.blocks[0].block==(original?23u:9u));
    assert(routes.blocks[routes.runs[1].start].block==
           (original?40u:20u));
    assert(routes.blocks[routes.count-1u].block==(original?47u:21u));
    assert(routes.blocks[0].input_view);
    assert(routes.blocks[routes.count-1u].output_view);
    std::uint32_t shifted=0u,pooled=0u;
    for(std::uint32_t i=0u;i<routes.count;++i){
        const auto& b=routes.blocks[i];
        const auto& p=b.plan;
        assert(p.windows==40u);
        assert(p.window_grid_x==5u&&p.window_grid_y==8u);
        assert(b.native_compute_tokens==2160u);
        assert(b.raster_width==33u&&b.raster_height==60u);
        assert(b.layer_count==(p.has_pooled_projection?5u:4u));
        const bool has_shift=p.attention_shift_x||p.attention_shift_y;
        shifted+=has_shift;
        pooled+=p.has_pooled_projection;
        // Every extracted real block shape has a directly preflightable
        // GPU capacity plan, including native signed QKV shifts.
        const std::uint64_t extent=40ull*64u*512u;
        SplitBlockCapacity caps{
            extent,extent,extent,extent,extent,extent,
            extent,extent,extent,extent*4u};
        if(has_shift){
            caps.shifted_input=extent;
            caps.unshifted_context=extent;
        }
        if(p.has_pooled_projection){
            caps.pooled=2160ull*512u;
            caps.final_fp32=2160ull*1024u*4u;
            caps.final_fp8=2160ull*1024u;
            assert(p.pool_width==33u&&p.pool_height==60u);
            assert(p.pool_windows_x==5u&&p.pool_windows_y==8u);
            assert(p.pool_output_tokens==2160u);
            assert(p.final_head_tokens==2160u);
        }
        assert(CanSplitBlock(p,caps));
    }
    assert(shifted>0u&&pooled==1u);
    const auto& pool=routes.blocks[routes.runs[0].count-1u];
    assert(pool.block==(original?30u:10u));
    assert(pool.plan.has_pooled_projection);
    assert(!routes.blocks[routes.count-1u].plan.has_pooled_projection);

    auto broken=source;
    for(auto& x:broken)if(x.type=="CCSplitSwin16HQKVAttn"){
        x.shift_x=100;break;
    }
    assert(BuildNativeSplitRoutes(broken,routes)==
           SplitNativeRoutesError::InvalidShift);
    assert(routes.count==0u);
    broken=source;
    for(auto& x:broken)if(x.type=="CCSplitSwin16HQKVAttn"){
        x.grid_x=6u;break;
    }
    assert(BuildNativeSplitRoutes(broken,routes)==
           SplitNativeRoutesError::InvalidShape);
    assert(routes.count==0u);
    broken=source;
    for(auto& x:broken)if(x.type=="CCSplitSwin16HFfwdProj"){
        x.input0=0;break;
    }
    assert(BuildNativeSplitRoutes(broken,routes)!=
           SplitNativeRoutesError::Ok);
    assert(routes.count==0u);
    broken=source;
    for(auto& x:broken)if(x.type=="CCSplitSwin16HFinalHead"){
        x.type="CCSplitSwin16HProj";break;
    }
    assert(BuildNativeSplitRoutes(broken,routes)!=
           SplitNativeRoutesError::Ok);
    assert(routes.count==0u);
}
int main(int argc,char** argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
