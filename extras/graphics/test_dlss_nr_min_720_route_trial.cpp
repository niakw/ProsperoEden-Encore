// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_720_route_trial.h"
#include "r09_native_plans.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
using namespace Eden::Graphics::DlssNrMin;
static void Check(std::string_view plan,bool original){
    Route720Trial r{};
    assert(BuildR09Min720Routes(plan,r));
    assert(r.issue==Route720Issue::None);
    assert(r.rows.size()==(original?152u:76u));
    assert(r.schedule.instructions.size()==r.rows.size());
    assert(r.fswin_segments==8u);
    assert(r.mapped_fswin_dispatches==(original?44u:16u));
    assert(r.mapped_split_dispatches>8u);
    // Identify precisely which native steps are still using inherited
    // specialized launch geometry. This is an explicit GPU admission
    // blocker, NOT a reason to redo the already validated 720p route.
    std::vector<NR::NativePlanStep> reference_rows{};
    assert(NR::ParseNativePlan(plan,reference_rows)==NR::NativePlanError::Ok);
    assert(reference_rows.size()==r.rows.size());
    std::array<std::uint32_t,5u> vit_counts{};
    std::uint32_t decoder_count{},specialized_count{};
    for(std::size_t i=0u;i<r.rows.size();++i) {
        const auto op=NR::ClassifyNativeNrOp(r.rows[i]);
        const bool is_vit=NR::IsNativeNrVitOp(op);
        const bool is_decoder=op==NR::NativeNrOp::DecoderUpsample;
        if(!is_vit&&!is_decoder)continue;
        ++specialized_count;
        // The CPU candidate does not invent GPU launch dimensions.
        // These fields still match the 1080p reference, even though
        // the token count and raster dimensions have changed.
        assert(r.rows[i].grid_x==reference_rows[i].grid_x);
        assert(r.rows[i].grid_y==reference_rows[i].grid_y);
        assert(r.rows[i].grid_z==reference_rows[i].grid_z);
        if(is_vit) {
            const auto index=static_cast<std::uint32_t>(op)-
                             static_cast<std::uint32_t>(
                                 NR::NativeNrOp::VitFfwdExpand);
            assert(index<vit_counts.size());
            ++vit_counts[index];
            assert(r.rows[i].tokens==r.padded_vit_tokens);
        } else {
            ++decoder_count;
            assert(r.rows[i].tokens==r.padded_vit_tokens);
        }
    }
    assert(specialized_count==41u);
    assert(r.unqualified_specialized==specialized_count);
    for(const auto count:vit_counts)assert(count==8u);
    assert(decoder_count==1u);
    std::cout<<"R09_MIN_720P_SPECIALIZED_GPU_GAPS "
             <<(original?"Original":"Compact")
             <<" vit_rows=40 decoder_rows=1"
             <<" inherited_launch_grids=41 GPU_DISABLED\n";
    assert(r.skips.count==4u);
    assert(r.split.run_count==2u);
    assert(r.vit.count==8u);
    assert(r.vit.tokens==960u);
    assert(r.vit.raster_width==22u&&r.vit.raster_height==40u);
    assert(r.logical_vit_tokens==880u);
    assert(r.padded_vit_tokens==960u);
    assert(r.rows.front().width==1280u&&r.rows.front().height==720u);
    assert(r.rows.front().tokens==921600u);
    assert(r.rows.back().width==640u&&r.rows.back().height==360u);
    assert(r.rows.back().tokens==230400u);
    assert(r.rows.front().grid_x==90u&&r.rows.front().grid_y==160u);
    assert(r.rows.back().grid_x==90u&&r.rows.back().grid_y==160u);
    assert(!r.gpu_dispatch_qualified&&!r.ready_to_enable_720p);
    std::uint32_t upsamples{};
    for(const auto& s:r.rows)
        if(s.kernel.ends_with("_upsample_fp8")&&
           s.type.starts_with("CCTinlayoutFusedSwin")){
            assert(s.grid_x>=Ceil8(s.height));
            assert(s.grid_y>=Ceil8(s.width));
            ++upsamples;
        }
    assert(upsamples==4u);
    std::cout<<"R09_MIN_720P_STRUCTURAL_ROUTE_PASS "
             <<(original?"Original":"Compact")
             <<" rows="<<r.rows.size()
             <<" vit_padded="<<r.padded_vit_tokens
             <<" vit_real="<<r.logical_vit_tokens
             <<" GPU_DISABLED\n";
}
int main(){
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
    Route720Trial r{};
    assert(!BuildR09Min720Routes("",r));
    assert(r.rows.empty()&&!r.ready_to_enable_720p);
    auto invalid=std::string{Eden::NeuralPlans::Original};
    const auto marker=invalid.find("1920 1080 2073600");
    assert(marker!=std::string::npos);
    invalid.replace(marker,17u,"1280 720 921600");
    assert(!BuildR09Min720Routes(invalid,r));
    assert(r.rows.empty()&&!r.gpu_dispatch_qualified);
}
