// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only conservative FSwin scratch pool: keep all per-layer inputs
// (Upload) and outputs (DeviceLocal) private; share only inner scratch in
// a SINGLE sequential chain. Never binds real VkBuffer/VkDescriptorSet.
#include "dlss_nr_min_720_fswin_scratch_pool.h"
#include "dlss_nr_min_720_session_buffer_audit.h"
#include "dlss_nr_min_720_post_fsr_bytes.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>

using namespace Eden::Graphics::DlssNrMin;
static void Check(std::string_view text, bool original) {
    FSwinScratchPoolPlan p{};
    assert(MakeFSwinScratchPool720Candidate(text,p));
    assert(p.issue==FSwinScratchPoolIssue::None);
    assert(p.chain_count==8u);
    assert(p.layers==(original?44u:16u));
    assert(p.reference_buffers==(original?256u:92u));
    assert(p.proposed_buffers==(original?118u:62u));
    assert(p.reference_bytes==
           (original?1097072640ull:477757440ull));
    assert(p.saved_bytes==
           (original?657653760ull:182517760ull));
    assert(p.proposed_bytes==
           (original?439418880ull:295239680ull));
    assert(!p.runtime_wired&&!p.sync_qualified);
    unsigned input_output{},scratch{},chain_count{};
    std::uint64_t total{},saved{};
    for(const auto& c:p.chains) {
        assert(c.layers>0u&&c.channels>0u&&c.windows>0u);
        assert(c.private_input_output&&!c.cross_chain_aliasing);
        assert(c.private_buffers==2u*c.layers);
        assert(c.pool_buffers==(c.channels==32u?3u:4u));
        assert(c.pooled_scratch_bytes[0]>0u);
        assert(c.pooled_scratch_bytes[1]==0u || c.channels!=32u);
        assert(c.pooled_scratch_bytes[2]>0u);
        assert(c.pooled_scratch_bytes[3]>0u);
        assert(c.proposed_bytes+c.saved_bytes==c.reference_bytes);
        assert(c.private_input_bytes>0u&&c.private_output_bytes>0u);
        input_output+=c.private_buffers;
        scratch+=c.pool_buffers;
        saved+=c.saved_bytes;
        total+=c.proposed_bytes;
        ++chain_count;
    }
    assert(chain_count==8u);
    assert(input_output==2u*p.layers);
    assert(input_output+scratch==p.proposed_buffers);
    assert(total==p.proposed_bytes&&saved==p.saved_bytes);
    NativeSessionBufferBudget ext{};
    assert(AuditNativeSession720BufferRequests(text,ext));
    const auto fsr=CountNominalPostFsrImages({3840u,2160u},3u);
    assert(fsr.valid);
    // Conservative per-frame slot accounting, excluding weights, VMA
    // overhead, staging and real console budget.
    const auto baseline=ext.external_bytes+p.reference_bytes+
                        fsr.per_slot;
    const auto candidate=ext.external_bytes+p.proposed_bytes+
                         fsr.per_slot;
    assert(baseline-candidate==p.saved_bytes);
    assert(candidate<baseline);
    std::cout<<"R09_MIN_720_FSWIN_SCRATCH_CHAIN_CANDIDATE_PASS "
             <<(original?"Original":"Compact")
             <<" chains="<<p.chain_count
             <<" scratch_only_buffers="<<scratch
             <<" retained_private_io_buffers="<<input_output
             <<" saved_bytes="<<p.saved_bytes
             <<" fswin_bytes="<<p.proposed_bytes
             <<" with_external_and_4k_fsr_per_slot_bytes="<<candidate
             <<" native_buffer_rebind=NOT_IMPLEMENTED"
             <<" sync=NOT_PROVEN PS5=NOT_TESTED\n";
}
int main() {
    Check(Eden::NeuralPlans::Original,true);
    Check(Eden::NeuralPlans::Compact,false);
    FSwinScratchPoolPlan invalid{};
    assert(!MakeFSwinScratchPool720Candidate("",invalid));
    assert(invalid.issue==FSwinScratchPoolIssue::BadReference);
    assert(invalid.saved_bytes==0u&&!invalid.runtime_wired);
    std::string broken{Eden::NeuralPlans::Original};
    auto pos=broken.find("CCVit1DQKV");
    assert(pos!=std::string::npos);
    broken.replace(pos,std::string("CCVit1DQKV").size(),"BAD_PLAN");
    assert(!MakeFSwinScratchPool720Candidate(broken,invalid));
    assert(invalid.issue==FSwinScratchPoolIssue::BadReference);
    assert(invalid.saved_bytes==0u);
}
