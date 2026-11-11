// SPDX-License-Identifier: GPL-3.0-or-later
// 720p native decoder/skip and tile packing policy, all host-only.
// Proves 22x40 live raster -> 960 padded tokens for Original/Compact.
#include "dlss_nr_min_720_route_trial.h"
#include "rdna2_nr_decoder_projection_policy.h"
#include "rdna2_nr_decoder_upsample_policy.h"
#include "rdna2_nr_split_decoder_skip_repack_policy.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>
namespace NR=Eden::Graphics::NeuralRDNA2;
using namespace Eden::Graphics::DlssNrMin;

static void Check(std::string_view native,bool original){
    Route720Trial trial{};
    assert(BuildR09Min720Routes(native,trial));
    constexpr std::uint32_t width=22u,height=40u;
    constexpr std::uint64_t pixels=880u,padded=960u;
    assert(trial.vit.raster_width==width);
    assert(trial.vit.raster_height==height);
    assert(trial.vit.tokens==padded);
    assert(NR::DecoderTileTokens(width,height)==padded);
    const NR::DecoderProjectionCapacity cap{
        pixels*1024u,512u*1024u,1024u*512u*4u,
        padded*512u*2u};
    NR::DecoderProjectionBatches batches{};
    assert(NR::BuildDecoderProjectionBatches(width,height,cap,batches));
    assert(NR::ValidDecoderProjectionBatches(batches));
    assert(batches.count==1u&&batches.pixels==pixels&&
           batches.tokens==padded);
    assert(batches.slices[0].projection.tokens==pixels);
    assert(batches.slices[0].convert.width==width&&
           batches.slices[0].convert.height==height);
    for(std::uint32_t role=0u;role<4u;++role){
        auto small=cap;
        if(role==0u)--small.linear_input;
        if(role==1u)--small.weights;
        if(role==2u)small.fp32_scratch=0u;
        if(role==3u)--small.fp16_projected;
        assert(!NR::BuildDecoderProjectionBatches(
            width,height,small,batches));
        assert(batches.count==0u);
    }
    const NR::SplitDecoderSkipRepack shape{
        width,height,(width+7u)/8u,(height+7u)/8u,512u};
    assert(shape.windows_x==3u&&shape.windows_y==5u);
    assert(NR::SplitSkipInputTokens(shape)==padded);
    assert(NR::SplitSkipOutputTokens(shape)==padded);
    const NR::SplitDecoderSkipStorage buf{
        padded*512u,padded*512u};
    assert(NR::CanSplitDecoderSkipRepack(shape,buf));
    assert(!NR::CanSplitDecoderSkipRepack(
        shape,{buf.source_bytes-1u,buf.destination_bytes}));
    assert(!NR::CanSplitDecoderSkipRepack(
        shape,{buf.source_bytes,buf.destination_bytes-1u}));
    const NR::DecoderUpsample command{0u,0u,0u,0u,width,width,height};
    const NR::DecoderStorage storage{
        padded*512u*2u,padded*512u,padded*512u,1024u};
    assert(NR::CanDecoderUpsample(command,storage));
    assert(NR::DecoderOutputTileTokens(command)==padded);
    assert(!NR::CanDecoderUpsample(command,{
        storage.projected_bytes,storage.skip_bytes,
        storage.output_bytes-1u,storage.gain_bytes}));
    assert(!NR::CanDecoderUpsample(command,{
        storage.projected_bytes,storage.skip_bytes,
        storage.output_bytes,storage.gain_bytes-1u}));
    // Check every live 4x4 tile address is unique and inside the
    // 960-token buffer; exactly 80 padded tail positions stay unwritten.
    std::vector<bool> occupied(padded,false);
    for(std::uint32_t y=0u;y<height;++y){
        for(std::uint32_t x=0u;x<width;++x){
            const auto index=((y/4u)*((width+3u)/4u)+(x/4u))*16u+
                             (y%4u)*4u+(x%4u);
            assert(index<occupied.size()&&!occupied[index]);
            occupied[index]=true;
        }
    }
    std::uint32_t used{};
    for(const auto present:occupied)used+=present?1u:0u;
    assert(used==pixels&&occupied.size()-used==80u);
    assert(!trial.gpu_dispatch_qualified&&!trial.ready_to_enable_720p);
    std::cout<<"R09_MIN_720P_REAL_DECODER_POLICIES_PASS "
             <<(original?"Original":"Compact")
             <<" pixels="<<pixels<<" padded="<<padded
             <<" projection_batches=1 GPU_DISABLED\n";
}
int main(){
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
}
