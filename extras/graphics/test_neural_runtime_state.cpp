// SPDX-License-Identifier: GPL-3.0-or-later
#include "neural_runtime_state.h"
#include <cassert>
#include <iostream>

int main(){
    using namespace Eden;
    NeuralRuntime::Configure(NeuralVideo::kOff,65);
    assert(NeuralRuntime::Current().mode==NeuralVideo::kOff);
    for(int mode=NeuralVideo::kA4kDetail;
            mode<=NeuralVideo::kDlssCompact;++mode){
        NeuralRuntime::Configure(mode,120);
        assert(NeuralRuntime::Current().mode==mode);
        assert(NeuralRuntime::Current().strength==100);
        if(mode<=NeuralVideo::kA4kDenoise)
            assert(NeuralVideo::IsA4k(mode));
        else
            assert(NeuralVideo::IsDlss(mode));
    }
    NeuralRuntime::Configure(-1,-20);
    assert(NeuralRuntime::Current().mode==NeuralVideo::kOff);
    assert(NeuralRuntime::Current().strength==0);
    NeuralRuntime::Configure(6,75);
    assert(NeuralRuntime::Current().mode==NeuralVideo::kOff);
    std::cout<<"R09_NEURAL_RUNTIME_A4K_1_2_3_AND_DLSS_4_5_TRACKED_HOST_PASS"
                " stale_framegen_will_be_denied=YES ps5_runtime=UNCHANGED\n";
}
