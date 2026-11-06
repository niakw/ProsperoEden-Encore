// SPDX-License-Identifier: MIT
// DLSSNR-AMD native-plan parser and safe FSwin segment extraction.
#include <cassert>
#include <cstdint>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_native_plan_bridge.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    // Real model row schema: 19 fields + two tile shifts. The example
    // deliberately includes incompatible input/downsample families.
    const std::string text=R"PLAN(
# NativePlan from the recovered layer manifest; synthetic short subset.
15 0 16 120 67 8640 9 15 1 256 8 256 256 0 1 14 -1 CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_inpview_fp8 0 0
16 0 16 120 67 8640 9 15 1 256 8 256 256 1 1 15 -1 CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 -1 -1
17 0 16 120 67 8640 9 15 1 256 8 256 256 1 1 16 -1 CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 -1 0
18 0 16 120 67 8640 9 15 1 256 8 256 512 1 1 17 -1 CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_ds_fp8 0 -1
19 0 16 120 67 8640 9 15 1 256 8 256 256 0 1 18 -1 CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 0 0
20 0 16 120 67 8640 9 15 1 256 8 256 256 1 1 19 -1 CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 -1 0
21 0 32 60 33 2560 5 8 2 512 4 512 512 0 1 20 -1 CCSplitSwin16HFfwd cc_split_swin_16h_ffwd_512_fp8 0 0
)PLAN";
    std::vector<NativePlanStep> rows;
    std::uint32_t error_line=0u;
    assert(ParseNativePlan(text,rows,&error_line)==NativePlanError::Ok);
    assert(rows.size()==7u&&error_line==0u);
    assert(rows[1].block==16u&&rows[1].layer==0u);
    assert(rows[1].grid_x==9u&&rows[1].grid_y==15u);
    assert(rows[1].shift_x==-1&&rows[2].shift_y==0);
    const auto segments=ExtractNativeFSwinSegments(rows);
    assert(segments.size()==2u);
    assert(segments[0].layers.size()==2u);
    assert(segments[1].layers.size()==2u);
    assert(segments[0].layers[0].weight_prefix==
        "unpacked/block16.layer0.layer");
    assert(segments[0].layers[1].weight_prefix==
        "unpacked/block17.layer0.layer");
    assert(segments[0].layers[0].windows==135u);
    assert(segments[0].layers[0].channels==256u);
    const auto& first=segments[0].layers;
    std::vector<FSwinWindowLayout> layouts{
        first[0].layout,first[1].layout};
    assert(CanFSwinChainWindowLayouts(layouts,135u));
    assert(FSwinNeedsWindowRepack(layouts[0],layouts[1]));
    assert(!NativePlainFSwin(rows[0])); // input view
    assert(!NativePlainFSwin(rows[3])); // downsample
    assert(!NativePlainFSwin(rows[6])); // split-Swin
    // High-resolution raster: valid plan metadata, but no unsafe attempt to
    // initialize the existing FSwin runtime capped at 256 windows.
    auto large=rows[1];
    large.grid_x=68u;large.grid_y=120u;
    assert(!NativePlainFSwin(large));
    // Legacy 19-field rows are accepted, but no shift is guessed.
    const std::string legacy=
        "1 0 2 960 540 522240 68 120 1 32 1 32 32 0 1 0 -1 "
        "CCTinlayoutFusedSwin1H cc_tinlayout_fused_swin_1h_32_1_fp8";
    assert(ParseNativePlan(legacy,rows)==NativePlanError::Ok);
    assert(rows.size()==1u&&rows[0].shift_x==100);
    assert(ExtractNativeFSwinSegments(rows).empty());
    // Strict rejection, with no partial output and a line diagnostic.
    assert(ParseNativePlan(text+"broken\n",rows,&error_line)==
        NativePlanError::MalformedRow);
    assert(rows.empty()&&error_line==10u);
    assert(ParseNativePlan("  \n# empty\n",rows)==NativePlanError::Empty);
    assert(rows.empty());
    std::string invalid=
        "1 0 16 120 67 8640 9 15 1 256 8 256 256 1 1 99 -1 "
        "CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 -1 0";
    assert(ParseNativePlan(invalid,rows)==NativePlanError::InvalidDependency);
    invalid=
        "1 0 16 20000 67 8640 9 15 1 256 8 256 256 1 1 0 -1 "
        "CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 -1 0";
    assert(ParseNativePlan(invalid,rows)==NativePlanError::InvalidShape);
    invalid=
        "1 0 16 120 67 8640 9 15 1 256 8 256 256 1 1 0 -1 "
        "CCTinlayoutFusedSwin8H cc_tinlayout_fused_swin_8h_256_8_fp8 -1 0";
    invalid += "\n"+invalid;
    assert(ParseNativePlan(invalid,rows)==NativePlanError::InvalidOrder);
}
