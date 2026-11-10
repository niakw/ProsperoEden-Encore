// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_vit_memory_audit.h"
#include "r09_native_plans.h"
#include <cassert>
#include <string>
using namespace Eden::Graphics::DlssNrMin;

int main() {
    constexpr std::uint64_t mib=1024ull*1024ull;
    for(const auto plan : {Eden::NeuralPlans::Original,
                           Eden::NeuralPlans::Compact}) {
        VitMemoryAudit ref{};
        assert(AuditVitRequestedBufferBytes(plan,kCurrentR09Graph,ref));
        assert(ref.issue==VitAuditIssue::None);
        assert(ref.vit_blocks==8u && ref.vit_rows==40u);
        assert(ref.tokens==2560u);
        assert(ref.requested_buffers==65u);
        assert(ref.plane_bytes==2560ull*1024u);
        assert(ref.requested_bytes==185ull*2560u*1024u);
        assert(ref.requested_bytes==4625ull*mib/10u);
        assert(!ref.runtime_qualified);

        VitMemoryAudit reduced{};
        assert(AuditVitRequestedBufferBytes(plan,kCandidateMinRaster,reduced));
        assert(reduced.issue==VitAuditIssue::None);
        assert(reduced.vit_blocks==ref.vit_blocks);
        assert(reduced.vit_rows==ref.vit_rows);
        assert(reduced.tokens==960u);
        assert(reduced.requested_buffers==ref.requested_buffers);
        assert(reduced.requested_bytes==185ull*960u*1024u);
        assert(reduced.requested_bytes==1734375ull*mib/10000u);
        assert(ref.requested_bytes-reduced.requested_bytes==
               303104000ull);
        assert(!reduced.runtime_qualified);
    }
    VitMemoryAudit invalid{};
    assert(!AuditVitRequestedBufferBytes(
        Eden::NeuralPlans::Original,{3840u,2160u},invalid));
    assert(invalid.issue==VitAuditIssue::GraphRejected);
    assert(invalid.requested_bytes==0u);
    assert(!AuditVitRequestedBufferBytes("",kCandidateMinRaster,invalid));
    assert(invalid.issue==VitAuditIssue::GraphRejected);
    // An incomplete recovered model schedule is not an optimization.
    std::string incomplete{Eden::NeuralPlans::Compact};
    const auto line=incomplete.find("CCVit1DQKV");
    assert(line!=std::string::npos);
    incomplete.replace(line,std::string("CCVit1DQKV").size(),"CCVitBAD");
    assert(!AuditVitRequestedBufferBytes(incomplete,kCandidateMinRaster,invalid));
    assert(invalid.issue==VitAuditIssue::GraphRejected);
    assert(invalid.requested_bytes==0u);
}
