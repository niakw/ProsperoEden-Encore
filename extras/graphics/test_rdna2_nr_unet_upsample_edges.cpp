// SPDX-License-Identifier: MIT
// Original and Compact exact native graph: test the four upsample edges,
// transposed raster axes, low FP8 storage and shifted first FSwin windows.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include "rdna2_nr_fswin_upsample_policy.h"
#include "rdna2_nr_fswin_window_repack_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void Test(std::string path,bool original){
    std::ifstream f(path,std::ios::binary);
    assert(f);
    const std::string input{
        std::istreambuf_iterator<char>{f},
        std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(input,rows)==NativePlanError::Ok);
    NativeUNetSkipMap map{};
    assert(BuildNativeUNetSkipMap(rows,map)==NativeUNetSkipError::Ok);
    assert(map.count==4u);
    const std::array<std::uint32_t,4> original_up{48,56,62,66};
    const std::array<std::uint32_t,4> compact_up{22,24,26,28};
    const auto& expected=original?original_up:compact_up;
    const auto segments=ExtractNativeFSwinSegments(rows);
    // Every upsample must supply its OWN FSwin body, not only the
    // prologue. Old extraction silently lost four learned layers.
    assert(segments.size()==8u);
    std::size_t shifted_count=0u;
    for(std::size_t i=0;i<4u;++i){
        const auto& edge=map.edges[i];
        assert(edge.up_block==expected[i]);
        const std::uint64_t high_w=edge.skip_height;
        const std::uint64_t high_h=edge.skip_width;
        const auto it=std::find_if(rows.begin(),rows.end(),
            [id=edge.up_block](const NativePlanStep& row){
                return row.block==id&&row.layer==0u;});
        assert(it!=rows.end()&&it->inputs==2u);
        assert(NativeUpsampleFSwin(*it));
        const auto seg=std::find_if(segments.begin(),segments.end(),
            [block=edge.up_block](const NativeFSwinSegment& candidate) {
                return !candidate.layers.empty() &&
                    candidate.layers.front().block==block;
            });
        assert(seg!=segments.end());
        assert(seg->layers.front().view==NativeFSwinView::Upsample);
        assert(seg->layers.front().layer==0u);
        assert(seg->layers.front().weight_prefix==
            "unpacked/block"+std::to_string(edge.up_block)+".layer0.layer");
        if(seg->layers.size()>1u)
            assert(seg->layers[1].block==edge.up_block+1u);
        assert(it->input0==static_cast<std::int32_t>(edge.up_input_block));
        assert(it->input1==static_cast<std::int32_t>(edge.down_block));
        assert(it->width==high_h/2u&&it->height==high_w/2u);
        assert(edge.skip_windows_x==(high_w+7u)/8u);
        assert(edge.skip_windows_y==(high_h+7u)/8u);
        assert(it->grid_x==edge.skip_windows_x&&
               it->grid_y==edge.skip_windows_y);
        const auto low=(high_w/2u)*(high_h/2u)*2u*edge.channels;
        const auto high=high_w*high_h*edge.channels;
        const auto weights=2ull*edge.channels*edge.channels;
        assert(low>0u&&high>0u);
        const FSwinUpsample stage{
            static_cast<std::uint32_t>(high_w),
            static_cast<std::uint32_t>(high_h),
            edge.skip_windows_x,edge.skip_windows_y,
            edge.channels,0u,0u,0u,0u,0u};
        assert(CanFSwinUpsample(stage,
            {low,high,weights,4u*edge.channels,high}));
        assert(!CanFSwinUpsample(stage,
            {low-1u,high,weights,4u*edge.channels,high}));
        const auto next=std::find_if(rows.begin(),rows.end(),
            [id=edge.up_block](const NativePlanStep& row){
                return row.block==id+1u&&row.layer==0u;});
        assert(next!=rows.end()&&next->input0==
               static_cast<std::int32_t>(edge.up_block));
        assert(next->grid_x==edge.skip_windows_x&&
               next->grid_y==edge.skip_windows_y);
        const FSwinWindowRepack shifted{
            .windows_x=next->grid_x,.windows_y=next->grid_y,
            .channels=next->channels,
            .src_shift_x=0,.src_shift_y=0,
            .dst_shift_x=next->shift_x,
            .dst_shift_y=next->shift_y};
        const auto padded=std::uint64_t(next->grid_x)*
            next->grid_y*64u*next->channels;
        assert(CanFSwinWindowRepack(shifted,{padded,padded}));
        if(next->shift_x||next->shift_y)++shifted_count;
        assert(next->channels==edge.channels);
        auto bad=*it;
        bad.input_channels=edge.channels;
        assert(!NativeUpsampleFSwin(bad));
        bad=*it;
        bad.input1=-1;
        assert(!NativeUpsampleFSwin(bad));
    }
    assert(shifted_count>0u); // both models need the new shifted GPU ingress
}
int main(int argc,char**argv){
    assert(argc==3);
    Test(argv[1],true);
    Test(argv[2],false);
}
