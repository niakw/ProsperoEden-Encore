// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only R09 720p native-plan serializer, no vendor or runtime changes.
// Never admit this emission to a Vulkan frame until all specialized launch
// dimensions, input/output surfaces and learned graph are independently proven.
#pragma once
#include "dlss_nr_min_720_route_trial.h"
#include <cstdint>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace Eden::Graphics::DlssNrMin {
struct EmittedR09Min720Plan {
    std::string text{};
    std::uint32_t rows{};
    bool exact_native_round_trip{};
    bool gpu_executable{false};
};
[[nodiscard]] inline bool EqualNativeStep(
    const NR::NativePlanStep& a,const NR::NativePlanStep& b) noexcept {
    return a.block==b.block&&a.layer==b.layer&&a.div==b.div&&
           a.width==b.width&&a.height==b.height&&a.tokens==b.tokens&&
           a.grid_x==b.grid_x&&a.grid_y==b.grid_y&&a.grid_z==b.grid_z&&
           a.channels==b.channels&&a.heads==b.heads&&
           a.input_channels==b.input_channels&&
           a.output_channels==b.output_channels&&
           a.shifted==b.shifted&&a.inputs==b.inputs&&
           a.input0==b.input0&&a.input1==b.input1&&
           a.type==b.type&&a.kernel==b.kernel&&
           a.shift_x==b.shift_x&&a.shift_y==b.shift_y;
}
[[nodiscard]] inline bool EmitR09Min720NativePlan(
    std::string_view original_1080,EmittedR09Min720Plan& result) {
    result={};
    Route720Trial trial{};
    if(!BuildR09Min720Routes(original_1080,trial)||
       trial.gpu_dispatch_qualified||trial.ready_to_enable_720p)
        return false;
    std::ostringstream text{};
    for(const auto& s:trial.rows) {
        text<<s.block<<' '<<s.layer<<' '<<s.div<<' '
            <<s.width<<' '<<s.height<<' '<<s.tokens<<' '
            <<s.grid_x<<' '<<s.grid_y<<' '<<s.grid_z<<' '
            <<s.channels<<' '<<s.heads<<' '
            <<s.input_channels<<' '<<s.output_channels<<' '
            <<(s.shifted?1u:0u)<<' '<<s.inputs<<' '
            <<s.input0<<' '<<s.input1<<' '
            <<s.type<<' '<<s.kernel;
        // Native plan parser accepts optional signed tile shifts.
        if(s.shift_x!=100||s.shift_y!=100)
            text<<' '<<s.shift_x<<' '<<s.shift_y;
        text<<'\n';
    }
    const auto emitted=text.str();
    if(emitted.empty()||emitted.size()>1u<<20u)return false;
    std::vector<NR::NativePlanStep> decoded{};
    if(NR::ParseNativePlan(emitted,decoded)!=NR::NativePlanError::Ok||
       decoded.size()!=trial.rows.size())return false;
    for(std::size_t i=0u;i<decoded.size();++i)
        if(!EqualNativeStep(decoded[i],trial.rows[i]))return false;
    NR::NativeNrSchedule instructions{};
    NR::NativeUNetSkipMap skips{};
    NR::NativeSplitRoutes split{};
    NR::NativeVitRoute vit{};
    if(NR::BuildNativeNrSchedule(decoded,instructions)!=
           NR::NativeNrGraphError::Ok ||
       NR::BuildNativeUNetSkipMap(decoded,skips)!=
           NR::NativeUNetSkipError::Ok ||
       NR::BuildNativeSplitRoutes(decoded,split)!=
           NR::SplitNativeRoutesError::Ok ||
       NR::BuildNativeVitRoute(decoded,vit)!=
           NR::NativeVitRouteError::Ok ||
       vit.count!=8u||vit.tokens!=960u||skips.count!=4u||
       split.run_count!=2u)return false;
    EmittedR09Min720Plan staged{};
    staged.text=emitted;
    staged.rows=static_cast<std::uint32_t>(decoded.size());
    staged.exact_native_round_trip=true;
    staged.gpu_executable=false;
    result=std::move(staged);
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
