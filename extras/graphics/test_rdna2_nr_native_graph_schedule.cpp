// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_native_graph_schedule.h"
using namespace Eden::Graphics::NeuralRDNA2;
void Check(const char* file,bool original) {
    std::ifstream in(file,std::ios::binary);assert(in);
    const std::string source{std::istreambuf_iterator<char>{in},
                             std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(source,rows)==NativePlanError::Ok);
    NativeNrSchedule schedule;
    std::uint32_t error_row=1000u;
    assert(BuildNativeNrSchedule(rows,schedule,&error_row)==NativeNrGraphError::Ok);
    assert(error_row==0u);
    assert(schedule.instructions.size()==(original?152u:76u));
    auto need=[&](NativeNrOp op,std::uint32_t count){
        assert(schedule.Count(op)==count);
    };
    need(NativeNrOp::PreImage,1u);
    need(NativeNrOp::Fswin,original?28u:0u);
    need(NativeNrOp::FswinInput,4u);
    need(NativeNrOp::FswinOutput,4u);
    need(NativeNrOp::FswinDown,4u);
    need(NativeNrOp::FswinUp,4u);
    need(NativeNrOp::SplitFfwd,original?16u:4u);
    need(NativeNrOp::SplitFfwdProjection,original?16u:4u);
    need(NativeNrOp::SplitQkvAttention,original?16u:4u);
    need(NativeNrOp::SplitProjection,original?15u:3u);
    need(NativeNrOp::SplitProjectionPool,1u);
    need(NativeNrOp::SplitFinalHead,1u);
    need(NativeNrOp::VitFfwdExpand,8u);
    need(NativeNrOp::VitFfwdContract,8u);
    need(NativeNrOp::VitQkv,8u);
    need(NativeNrOp::VitAttention,8u);
    need(NativeNrOp::VitProjection,8u);
    need(NativeNrOp::DecoderUpsample,1u);
    need(NativeNrOp::PostImage,1u);
    for(std::size_t i=0;i<rows.size();++i) {
        const auto& row=rows[i];
        const auto& ins=schedule.instructions[i];
        assert(ins.row==i&&ins.block==row.block&&ins.layer==row.layer);
        assert(ins.source0==row.input0&&ins.source1==row.input1);
        assert(ins.operation==ClassifyNativeNrOp(row));
    }
    auto bad=rows;
    bad[1].type="unknown";
    assert(BuildNativeNrSchedule(bad,schedule,&error_row)==NativeNrGraphError::Unrecognized);
    assert(error_row==1u&&schedule.instructions.empty());
    bad=rows;
    for(auto& row:bad)if(row.type=="CCVit1DFfnExpand"){
        row.output_channels=2048u;break;
    }
    assert(BuildNativeNrSchedule(bad,schedule)==NativeNrGraphError::InvalidShape);
    assert(schedule.instructions.empty());
    bad=rows;bad[1].input0=511;
    assert(BuildNativeNrSchedule(bad,schedule)==NativeNrGraphError::MissingPredecessor);
    assert(schedule.instructions.empty());
    bad=rows;bad.pop_back();
    assert(BuildNativeNrSchedule(bad,schedule)==NativeNrGraphError::InvalidBoundary);
    assert(schedule.instructions.empty());
    bad=rows;bad.erase(bad.begin());
    assert(BuildNativeNrSchedule(bad,schedule)==NativeNrGraphError::MissingPredecessor);
    assert(schedule.instructions.empty());
}
int main(int argc,char**argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
