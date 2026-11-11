// SPDX-License-Identifier: GPL-3.0-or-later
// Dry-run mirror of native FrameSession::State::Make() for both 720p plans.
// Includes only caller-owned external VMA buffers, not a complete VRAM peak.
#include "dlss_nr_min_720_session_buffer_audit.h"
#include "dlss_nr_min_720_post_fsr_bytes.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
using namespace Eden::Graphics::DlssNrMin;
namespace NR=Eden::Graphics::NeuralRDNA2;
static void Check(std::string_view plan,bool original){
    NativeSessionBufferBudget q{};
    assert(AuditNativeSession720BufferRequests(plan,q));
    assert(q.issue==NativeSessionBudgetIssue::None);
    assert(q.buffer_count>95u);
    assert(q.external_bytes>180ull*1024u*1024u);
    assert(q.external_bytes<=kNativeMaxFrameBuffers);
    assert(q.largest_buffer<=kNativeMaxOneBuffer);
    assert(!q.source_lifetime_qualified&&!q.gpu_executable);
    unsigned counted{};
    std::uint64_t total{};
    for(const auto& stage:q.stages){
        counted+=stage.buffers;
        total+=stage.requested_bytes;
    }
    assert(counted==q.buffer_count&&total==q.external_bytes);
    const auto& pre=q.stages[static_cast<unsigned>(
        NativeSessionStage::Preblock)];
    assert(pre.buffers==6u);
    assert(pre.requested_bytes==921600ull*184ull);
    const auto& vit=q.stages[static_cast<unsigned>(
        NativeSessionStage::EightVitBlocks)];
    assert(vit.buffers==65u);
    assert(vit.requested_bytes==185ull*960ull*1024ull);
    const auto& dec=q.stages[static_cast<unsigned>(
        NativeSessionStage::Decoder)];
    assert(dec.buffers==6u);
    assert(dec.requested_bytes==
         960ull*1024ull+880ull*1024ull+
         880ull*512ull*4ull+880ull*512ull*2ull+
         2ull*960ull*512ull);
    const auto& post=q.stages[static_cast<unsigned>(
        NativeSessionStage::Postblock)];
    assert(post.buffers==5u);
    assert(post.requested_bytes==921600ull*176ull);
    const auto& split0=q.stages[static_cast<unsigned>(
        NativeSessionStage::SplitBeforeVit)];
    const auto& split1=q.stages[static_cast<unsigned>(
        NativeSessionStage::SplitAfterVit)];
    assert(split0.buffers>0&&split1.buffers>0);
    assert(split0.requested_bytes>0&&split1.requested_bytes>0);
    assert(q.split_blocks>0&&q.vit_blocks==8u);
    const auto surfaces=CountNominalPostFsrImages({3840u,2160u},3u);
    assert(surfaces.valid&&!surfaces.measured_gpu_vram);
    // Each slot's frame-owned VMA buffers may survive until its GPU tick,
    // so adding a separate per-slot FSR image charge is a useful NECESSARY
    // nominal envelope. FSwin-internal VMA, weights, VMA overhead and
    // guest/swapchain are not included, so never use as admission proof.
    const std::uint64_t nominated_slots=3ull*q.external_bytes+
                                         surfaces.all_slots;
    assert(nominated_slots>surfaces.all_slots);
    std::cout<<"R09_MIN_720_NATIVE_SESSION_BUFFER_AUDIT_PASS "
             <<(original?"Original":"Compact")
             <<" external_buffers="<<q.buffer_count
             <<" split_blocks="<<q.split_blocks
             <<" external_bytes_per_slot="<<q.external_bytes
             <<" with_4k_fsr_three_slots_bytes="<<nominated_slots
             <<" fswin_internals=EXCLUDED weights=EXCLUDED "
             <<"gpu_vram=UNMEASURED runtime=DISABLED\n";
}
int main(){
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
    NativeSessionBufferBudget invalid{};
    assert(!AuditNativeSession720BufferRequests("",invalid));
    assert(invalid.issue==NativeSessionBudgetIssue::InvalidRoute);
    assert(invalid.external_bytes==0u);
    std::string malformed{Eden::NeuralPlans::Original};
    const auto pos=malformed.find("CCVit1DQKV");
    assert(pos!=std::string::npos);
    malformed.replace(pos,std::string("CCVit1DQKV").size(),"BAD_VIT");
    assert(!AuditNativeSession720BufferRequests(malformed,invalid));
    assert(invalid.issue==NativeSessionBudgetIssue::InvalidRoute);
    assert(invalid.external_bytes==0u);
    assert(!kPs5MinRuntimeQualified);
}
