// SPDX-License-Identifier: GPL-3.0-or-later
// Exact one-owner-per-native-model-row HOST coverage for the entire 720p
// Original (152) and Compact (76) graphs. Structural, not Vulkan Record().
#include "dlss_nr_min_720_route_trial.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>

namespace NR=Eden::Graphics::NeuralRDNA2;
using namespace Eden::Graphics::DlssNrMin;

static void Check(std::string_view plan,bool original) {
    Route720Trial r{};
    assert(BuildR09Min720Routes(plan,r));
    const auto rows=r.rows.size();
    assert(rows==(original?152u:76u));
    assert(r.schedule.instructions.size()==rows);
    std::vector<unsigned> references(rows,0u);
    unsigned pre{},post{},down{},up{},regular_fswin{},
             split{},vit{},decoder{};
    const auto mark=[&](std::size_t row) {
        assert(row<rows);
        assert(references[row]==0u);
        ++references[row];
    };
    // Every FSwin model operation must correspond to exactly one layer
    // in one of the 4 down / 4 up native chain segments.
    const auto sections=NR::ExtractNativeFSwinSegments(r.rows);
    assert(sections.size()==8u);
    for(const auto& section:sections) {
        assert(!section.layers.empty());
        for(const auto& layer:section.layers){
            std::size_t matched=rows;
            for(std::size_t i=0u;i<rows;++i)
                if(r.rows[i].block==layer.block&&
                   r.rows[i].layer==layer.layer){
                    assert(matched==rows);
                    matched=i;
                }
            assert(matched<rows);
            const auto kind=NR::ClassifyNativeNrOp(r.rows[matched]);
            assert(NR::IsNativeNrFswinOp(kind));
            mark(matched);
            if(kind==NR::NativeNrOp::FswinDown)++down;
            else if(kind==NR::NativeNrOp::FswinUp)++up;
            else ++regular_fswin;
        }
    }
    assert(down==4u&&up==4u);
    // Each Split-Swin block has 4 or 5 native model instructions,
    // including its pooled FinalHead. Claim each one explicitly.
    assert(r.split.run_count==2u);
    unsigned pool_blocks{};
    for(std::uint32_t k=0;k<r.split.count;++k) {
        const auto& block=r.split.blocks[k];
        assert(block.layer_count==4u||block.layer_count==5u);
        assert(block.plan.has_pooled_projection==
               (block.layer_count==5u));
        pool_blocks+=block.plan.has_pooled_projection;
        for(std::uint32_t off=0u;off<block.layer_count;++off) {
            const auto idx=std::size_t(block.first_row)+off;
            assert(idx<rows);
            assert(NR::IsNativeNrSplitOp(
                NR::ClassifyNativeNrOp(r.rows[idx])));
            assert(r.rows[idx].block==block.block);
            mark(idx);++split;
        }
    }
    assert(pool_blocks==1u);
    // Every ViT op belongs to precisely one eight-block 5-op route.
    assert(r.vit.count==8u&&r.vit.tokens==960u);
    for(std::uint32_t k=0u;k<r.vit.count;++k) {
        const auto& block=r.vit.blocks[k];
        for(std::uint32_t off=0u;off<5u;++off) {
            const auto idx=std::size_t(block.first_row)+off;
            assert(idx<rows);
            assert(NR::IsNativeNrVitOp(
                NR::ClassifyNativeNrOp(r.rows[idx])));
            assert(r.rows[idx].block==block.block);
            mark(idx);++vit;
        }
    }
    assert(vit==40u);
    // The preblock, learned decoder and postblock each own one row.
    for(std::size_t i=0u;i<rows;++i){
        const auto op=NR::ClassifyNativeNrOp(r.rows[i]);
        if(op==NR::NativeNrOp::PreImage){mark(i);++pre;}
        if(op==NR::NativeNrOp::DecoderUpsample){mark(i);++decoder;}
        if(op==NR::NativeNrOp::PostImage){mark(i);++post;}
    }
    assert(pre==1u&&decoder==1u&&post==1u);
    unsigned all{};
    for(std::size_t i=0u;i<rows;++i){
        assert(r.schedule.instructions[i].row==i);
        assert(r.schedule.instructions[i].operation==
               NR::ClassifyNativeNrOp(r.rows[i]));
        assert(references[i]==1u);
        all+=references[i];
    }
    assert(all==rows);
    assert(std::uint32_t(all)==pre+regular_fswin+down+up+split+
                               vit+decoder+post);
    assert(r.unqualified_specialized==41u);
    assert(!r.gpu_dispatch_qualified&&!r.ready_to_enable_720p);
    std::cout<<"R09_MIN_720_FULL_NATIVE_OWNER_COVERAGE_PASS "
             <<(original?"Original":"Compact")
             <<" rows="<<all<<" missing=0 duplicate=0"
             <<" fswin="<<(regular_fswin+down+up)
             <<" split="<<split<<" vit="<<vit
             <<" pre="<<pre<<" decoder="<<decoder<<" post="<<post
             <<" runtime=DISABLED\n";
}
int main(){
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
    Route720Trial reject{};
    auto malformed=std::string{Eden::NeuralPlans::Original};
    const auto target=malformed.find("CCVit1DAttention");
    assert(target!=std::string::npos);
    malformed.replace(target,std::string("CCVit1DAttention").size(),
                      "CCVit1DBROKEN");
    assert(!BuildR09Min720Routes(malformed,reject));
    assert(reject.rows.empty()&&!reject.ready_to_enable_720p);
}
