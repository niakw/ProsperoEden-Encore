// SPDX-License-Identifier: MIT
// R09: every native Original/Compact graph row MUST be assigned to one
// executable GPU stage owner, once only. STRUCTURAL proof, not GPU inference.
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
#include "video_core/renderer_vulkan/nr_rdna2_native_plan_coverage.h"
#include "rdna2_nr_split_native_routes_policy.h"
#include "rdna2_nr_vit_native_route_policy.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Mark(std::vector<std::uint8_t>& taken,std::size_t i){
    assert(i<taken.size());
    assert(taken[i]==0u); // prevent silent duplicate execution
    taken[i]=1u;
}
static void Check(const char* path,bool original){
    std::ifstream f(path,std::ios::binary);
    assert(f);
    const std::string text{std::istreambuf_iterator<char>{f},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(text,rows)==NativePlanError::Ok);
    const std::size_t expected=original?152u:76u;
    assert(rows.size()==expected);
    std::vector<std::uint8_t> taken(rows.size(),0u);
    const auto& pre=rows.front();
    const auto& post=rows.back();
    assert(pre.block==0u&&pre.layer==0u);
    assert(pre.type.starts_with("CCTinlayoutFusedPreBlock"));
    assert(post.type.starts_with("CCTinlayoutFusedPostBlock"));
    assert(post.block==(original?70u:30u));
    Mark(taken,0u);
    Mark(taken,rows.size()-1u);

    NativeUNetSkipMap skips{};
    assert(BuildNativeUNetSkipMap(rows,skips)==NativeUNetSkipError::Ok);
    assert(skips.count==4u);
    const auto fswin=ExtractNativeFSwinSegments(rows);
    assert(fswin.size()==8u);
    std::size_t fswin_count=0u,descents=0u,ascents=0u;
    for(const auto& segment:fswin){
        assert(!segment.layers.empty());
        const auto first=segment.layers.front().view;
        const auto last=segment.layers.back().view;
        if(last==NativeFSwinView::Downsample){
            assert(first==NativeFSwinView::InputView);
            ++descents;
        }else{
            assert(first==NativeFSwinView::Upsample);
            assert(last==NativeFSwinView::OutputView);
            ++ascents;
        }
        for(const auto& layer:segment.layers){
            std::size_t occurrences=0u;
            for(std::size_t i=0u;i<rows.size();++i){
                const auto& row=rows[i];
                if(row.block!=layer.block||row.layer!=layer.layer||
                   !row.type.starts_with("CCTinlayoutFusedSwin"))
                    continue;
                assert(row.channels==layer.channels);
                assert(row.grid_x*row.grid_y==layer.windows);
                Mark(taken,i);
                ++fswin_count;
                ++occurrences;
            }
            assert(occurrences==1u);
        }
    }
    assert(descents==4u&&ascents==4u);
    assert(fswin_count==(original?44u:16u));

    NativeSplitRoutes split{};
    assert(BuildNativeSplitRoutes(rows,split)==SplitNativeRoutesError::Ok);
    assert(split.run_count==2u);
    std::size_t split_count=0u;
    for(std::size_t k=0u;k<split.count;++k){
        const auto& block=split.blocks[k];
        for(std::size_t j=0u;j<block.layer_count;++j){
            const auto index=std::size_t(block.first_row)+j;
            assert(index<rows.size());
            assert(rows[index].block==block.block);
            assert(rows[index].layer==j);
            assert(rows[index].type.starts_with("CCSplitSwin"));
            Mark(taken,index);
            ++split_count;
        }
    }
    assert(split_count==(original?65u:17u));

    NativeVitRoute vit{};
    assert(BuildNativeVitRoute(rows,vit)==NativeVitRouteError::Ok);
    assert(vit.count==8u);
    std::size_t vit_count=0u;
    for(const auto& block:vit.blocks){
        for(std::size_t j=0u;j<5u;++j){
            const auto i=std::size_t(block.first_row)+j;
            assert(i<rows.size());
            assert(rows[i].block==block.block);
            assert(rows[i].layer==j);
            assert(rows[i].type.starts_with("CCVit1D"));
            Mark(taken,i);
            ++vit_count;
        }
    }
    assert(vit_count==40u);

    std::size_t decoder_count=0u;
    for(std::size_t i=0u;i<rows.size();++i){
        if(!rows[i].type.starts_with("CCDecInputUpsample"))continue;
        assert(rows[i].block==vit.decoder_block);
        Mark(taken,i);
        ++decoder_count;
    }
    assert(decoder_count==1u);
    for(const auto v:taken)assert(v==1u);
    assert(2u+fswin_count+split_count+vit_count+decoder_count==expected);
    std::cout<<"R09_"
             <<(original?"ORIGINAL":"COMPACT")
             <<"_152_OR_76_GRAPH_OWNER_COVERAGE_PASS "
             <<expected<<"/"<<expected<<"\n";
}
int main(int argc,char**argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
