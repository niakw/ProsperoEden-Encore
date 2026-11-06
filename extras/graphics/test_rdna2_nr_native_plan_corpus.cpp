// SPDX-License-Identifier: MIT
// Complete 152/76-step MIT DLSSNR-AMD graph structural coverage check.
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_native_plan_coverage.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(const char* path,bool original){
    std::ifstream f(path,std::ios::binary);
    assert(f);
    const std::string text{std::istreambuf_iterator<char>{f},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    std::uint32_t line=0u;
    assert(ParseNativePlan(text,rows,&line)==NativePlanError::Ok);
    assert(line==0u);
    const auto c=AuditNativePlan(rows);
    const std::uint32_t total=original?152u:76u;
    const std::uint32_t plain=original?28u:0u;
    assert(c.total==total && rows.size()==total);
    assert(c.Classified()==total && c.other==0u);
    assert(c.pre_image==1u && c.post_image==1u && c.decoder==1u);
    assert(c.vit==40u && c.split_swin==(original?65u:17u));
    assert(c.fswin_plain==plain && c.fswin_ready==plain);
    assert(c.fswin_blocked==0u);
    assert(c.fswin_input_view==4u && c.fswin_output_view==4u);
    assert(c.fswin_input_view_ready==4u &&
           c.fswin_output_view_ready==4u);
    assert(c.CanonicalFSwinReady()==plain+8u);
    assert(c.fswin_down==4u && c.fswin_up==4u);
    assert(c.fswin_unknown==0u && c.FSwinSpecial()==16u);
    assert(c.compatible_segments==8u);
    assert(c.Uncovered()==total-plain-8u);
    const auto segments=ExtractNativeFSwinSegments(rows);
    for(const auto& segment:segments){
        assert(!segment.layers.empty());
        for(std::size_t i=0;i<segment.layers.size();++i){
            const auto view=segment.layers[i].view;
            if(view==NativeFSwinView::InputView)assert(i==0u);
            if(view==NativeFSwinView::OutputView)
                assert(i+1u==segment.layers.size());
        }
    }
    for(const auto& s:rows)
        if(NativePlainFSwin(s)){
            const auto windows=std::uint64_t(s.grid_x)*s.grid_y;
            assert(windows<=65535u);
            assert(windows*64u*4u*s.channels<=(256ull<<20));
        }
}
int main(int argc,char**argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
