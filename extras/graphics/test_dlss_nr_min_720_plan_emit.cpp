// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_720_plan_emit.h"
#include "r09_native_plans.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
using namespace Eden::Graphics::DlssNrMin;
static void Check(std::string_view reference,bool original){
    EmittedR09Min720Plan plan{};
    assert(EmitR09Min720NativePlan(reference,plan));
    assert(plan.exact_native_round_trip);
    assert(!plan.gpu_executable);
    assert(plan.rows==(original?152u:76u));
    assert(!plan.text.empty());
    std::vector<NR::NativePlanStep> decoded{};
    assert(NR::ParseNativePlan(plan.text,decoded)==NR::NativePlanError::Ok);
    assert(decoded.size()==plan.rows);
    assert(decoded.front().width==1280u);
    assert(decoded.front().height==720u);
    assert(decoded.back().width==640u);
    assert(decoded.back().height==360u);
    // The source plans remain 1080p-only references. A 720p plan must
    // NOT be incorrectly recognized as an authentic 1080p input.
    Route720Trial invalid{};
    assert(!BuildR09Min720Routes(plan.text,invalid));
    assert(invalid.rows.empty()&&!invalid.ready_to_enable_720p);
    EmittedR09Min720Plan second{};
    assert(EmitR09Min720NativePlan(reference,second));
    assert(second.text==plan.text);
    assert(second.rows==plan.rows&&!second.gpu_executable);
    std::cout<<"R09_MIN_720P_NATIVE_SERIALIZATION_ROUNDTRIP_PASS "
             <<(original?"Original":"Compact")
             <<" rows="<<plan.rows<<" bytes="<<plan.text.size()
             <<" GPU_DISABLED\n";
}
int main(){
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
    EmittedR09Min720Plan missing{};
    assert(!EmitR09Min720NativePlan("",missing));
    assert(missing.text.empty()&&!missing.gpu_executable);
    std::string malformed{Eden::NeuralPlans::Original};
    auto pos=malformed.find("1920 1080 2073600");
    assert(pos!=std::string::npos);
    malformed.replace(pos,17u,"1280 720 921600");
    assert(!EmitR09Min720NativePlan(malformed,missing));
    assert(missing.text.empty()&&!missing.gpu_executable);
}
