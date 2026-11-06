// SPDX-License-Identifier: GPL-3.0-or-later
#include "neural_video_policy.h"
#include <cassert>
using namespace Eden::NeuralVideo;
int main(){
    static_assert(!kRuntimeValidated);
    assert(Check(kOff,1,0,1,0)==Reason::Disabled);
    assert(Check(kRdna2,1,0,1,0)==Reason::EngineIncomplete);
    assert(!CanEnable(1,0,1,0));
    assert(!RuntimeParametersEnabled(kRdna2));
    assert(PresetsMayBeStored(0,0)&&PresetsMayBeStored(1,100));
    assert(!PresetsMayBeStored(2,80)&&!PresetsMayBeStored(0,101));
    assert(Check(kRdna2,0,0,1,0,true)==Reason::RequiresVulkan);
    assert(Check(kRdna2,1,1,1,0,true)==Reason::NeedsExclusiveUpscaler);
    assert(Check(kRdna2,1,7,1,0,true)==Reason::NeedsExclusiveUpscaler);
    assert(Check(kRdna2,1,0,6,0,true)==Reason::MsaaUnverified);
    assert(Check(kRdna2,1,0,1,2,true)==Reason::FrameGenerationUnverified);
    assert(Check(kRdna2,1,0,1,0,true)==Reason::Available);
}
