// SPDX-License-Identifier: GPL-3.0-or-later
// Actual pinned FSwinGraphPlan plus per-layer tensor allocation policy.
// Both models are structural 720p candidates; no PS5 Vulkan activation.
#include "dlss_nr_min_720_fswin_tensor_audit.h"
#include "dlss_nr_min_720_session_buffer_audit.h"
#include "dlss_nr_min_720_post_fsr_bytes.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <iostream>
using namespace Eden::Graphics::DlssNrMin;
static void Check(std::string_view reference,bool original) {
    FSwin720TensorEstimate fs{};
    assert(AuditFSwin720OwnedTensorBuffers(reference,fs));
    assert(fs.issue==FSwin720TensorIssue::None);
    assert(fs.chain_count==8u);
    assert(fs.layers==(original?44u:16u));
    assert(fs.buffer_count==(original?256u:92u));
    assert(fs.requested_bytes==
           (original?1097072640ull:477757440ull));
    assert(fs.bytes_by_channels[0]==
           (original?450ull:225ull)*1048576ull);
    assert(fs.bytes_by_channels[1]==
           (original?258750ull:129375ull)*1048576ull/1000ull);
    assert(fs.bytes_by_channels[2]==
           (original?2025ull:675ull)*1048576ull/10ull);
    assert(fs.bytes_by_channels[3]==
           (original?135000ull:33750ull)*1048576ull/1000ull);
    assert(fs.largest_buffer>0u&&fs.largest_buffer<=(256ull<<20));
    assert(fs.largest_layer>0u&&fs.largest_layer<=(512ull<<20));
    assert(!fs.includes_gpu_weights&&!fs.gpu_executable);
    NativeSessionBufferBudget external{};
    assert(AuditNativeSession720BufferRequests(reference,external));
    assert(external.issue==NativeSessionBudgetIssue::None);
    const auto fsr=CountNominalPostFsrImages({3840u,2160u},3u);
    assert(fsr.valid);
    // EXACT nominal sum for two explicit allocation owners plus the
    // known post-neural FSR textures. NOT all resident Vulkan memory.
    const auto with_fsr_three_slots=
        3ull*(fs.requested_bytes+external.external_bytes)+fsr.all_slots;
    assert(with_fsr_three_slots==
           (original?5690941440ull:3594117120ull));
    std::cout<<"R09_MIN_720_FSWIN_ALL_LAYER_TENSORS_PASS "
             <<(original?"Original":"Compact")
             <<" layers="<<fs.layers
             <<" buffers="<<fs.buffer_count
             <<" bytes_per_slot="<<fs.requested_bytes
             <<" plus_external_per_slot="<<external.external_bytes
             <<" three_slots_with_4k_fsr="<<with_fsr_three_slots
             <<" includes_weights=NO measured_gpu_vram=NO"
             <<" runtime=DISABLED\n";
}
int main(){
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
    FSwin720TensorEstimate invalid{};
    assert(!AuditFSwin720OwnedTensorBuffers("",invalid));
    assert(invalid.issue==FSwin720TensorIssue::Graph);
    assert(invalid.requested_bytes==0u);
}
