// SPDX-License-Identifier: GPL-3.0-or-later
#include "neural_a4k_spatial_launch_route.h"
#include <cassert>
#include <iostream>

int main(){
    using namespace Eden;
    using namespace Graphics::DlssNrMin;
    static_assert(!kA4kNeuralToSpatialRuntimeQualified);
    static_assert(!kPostNeuralSpatialRuntimeWired);
    static_assert(!kNeuralToFramegenRuntimeWired);
    unsigned matrix=0,legacy=0;
    for(int a4k=NeuralVideo::kA4kDetail;
            a4k<=NeuralVideo::kA4kDenoise;++a4k){
        for(int spatial=0;spatial<=6;++spatial){
            for(int fg=0;fg<=3;++fg){
                const bool selectable=NeuralVideo::CanSelect(
                    a4k,1,spatial,0,fg);
                const auto route=ResolveA4kSpatialLaunch(
                    a4k,1,spatial,0,fg,selectable);
                assert(route.selected_neural==a4k);
                assert(route.candidate);
                assert(!route.combine_enabled);
                assert(!route.needs_native_a4k_output_frame);
                assert(route.downstream_framegen==0);
                if(selectable){
                    assert(spatial==0&&fg==0);
                    assert(route.present_filter==
                           NeuralVideo::InternalA4kFilter(a4k));
                    ++legacy;
                }else{
                    assert(route.present_filter==spatial);
                }
                ++matrix;
            }
        }
    }
    assert(matrix==84&&legacy==3);
    // Non-A4K neural choice is never silently converted to A4K.
    for(int neural:{0,4,5,6,-1}){
        const auto r=ResolveA4kSpatialLaunch(neural,1,1,0,0,false);
        assert(!r.candidate&&!r.combine_enabled);
        assert(r.present_filter==1);
    }
    // No combinations are admitted under OpenGL, MSAA/FXAA, invalid FG,
    // legacy 7/8/9 filter IDs (which themselves represent A4K), or
    // out-of-range persisted settings.
    for(int a4k=1;a4k<=3;++a4k){
        for(int filter:{-1,7,8,9,10}){
            const auto r=ResolveA4kSpatialLaunch(
                a4k,1,filter,0,0,false);
            assert(!r.candidate&&!r.combine_enabled);
        }
        for(int aa=1;aa<=7;++aa)
            assert(!ResolveA4kSpatialLaunch(
                a4k,1,1,aa,0,false).candidate);
        for(int fg:{-1,4})
            assert(!ResolveA4kSpatialLaunch(
                a4k,1,1,0,fg,false).candidate);
        assert(!ResolveA4kSpatialLaunch(
            a4k,0,1,0,0,false).candidate);
    }
    std::cout<<"R09_A4K_NEURAL_SPATIAL_SELECTION_PASS "
                "modes=3 spatial=7 framegen=4 matrix="<<matrix
             <<" legacy_A4K_unchanged="<<legacy
             <<" runtime=OFF no_PS5_build\n";
}
