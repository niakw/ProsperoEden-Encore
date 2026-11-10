// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_720_route_trial.h"
#include "r09_native_plans.h"
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
    assert(r.unqualified_specialized>40u);
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
