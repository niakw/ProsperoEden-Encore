// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_graph_geometry.h"
#include "r09_native_plans.h"
#include <cassert>
#include <string>

using namespace Eden::Graphics::DlssNrMin;
int main() {
    for(const auto variant : {Eden::NeuralPlans::Original,
                              Eden::NeuralPlans::Compact}) {
        const bool original=variant==Eden::NeuralPlans::Original;
        GeometryAudit native{};
        assert(AuditNativeR09Candidate(variant,kCurrentR09Graph,native));
        assert(native.issue==GeometryIssue::None);
        assert(native.rows.size()==(original?152u:76u));
        assert(native.standard_fswin==(original?40u:12u));
        assert(native.upsample_fswin==4u);
        assert(native.specialized==(original?108u:60u));
        assert(!native.complete_gpu_plan);
        assert(native.rows.front().width==1920u);
        assert(native.rows.front().height==1080u);
        assert(native.rows.front().padded_tokens==2073600u);
        assert(native.rows.back().width==960u);
        assert(native.rows.back().height==540u);
        assert(native.rows.back().padded_tokens==522240u);

        GeometryAudit min{};
        assert(AuditNativeR09Candidate(variant,kCandidateMinRaster,min));
        assert(min.issue==GeometryIssue::None);
        assert(min.rows.size()==native.rows.size());
        assert(min.standard_fswin==native.standard_fswin);
        assert(min.upsample_fswin==native.upsample_fswin);
        assert(min.specialized==native.specialized);
        assert(min.aggregate_padded_tokens<native.aggregate_padded_tokens);
        assert(min.rows.front().width==1280u&&
               min.rows.front().height==720u);
        assert(min.rows.front().padded_tokens==921600u);
        assert(min.rows.back().width==640u&&
               min.rows.back().height==360u);
        assert(min.rows.back().padded_tokens==230400u);
        assert(!min.complete_gpu_plan);
        for(std::size_t i=0u;i<min.rows.size();++i) {
            const auto& before=native.rows[i];
            const auto& after=min.rows[i];
            assert(before.block==after.block);
            assert(before.layer==after.layer);
            assert(before.divisor==after.divisor);
            assert(after.padded_tokens<=before.padded_tokens);
            assert(after.input_dispatch_x<=before.input_dispatch_x);
            assert(after.input_dispatch_y<=before.input_dispatch_y);
            assert(!after.vulkan_dispatch_qualified);
            if(after.fswin_upsample) {
                assert(after.input_dispatch_x>=after.canonical_windows_x);
                assert(after.input_dispatch_y>=after.canonical_windows_y);
            }
        }
    }
    GeometryAudit rejected{};
    assert(!AuditNativeR09Candidate(Eden::NeuralPlans::Original,
                                   {3840u,2160u},rejected));
    assert(rejected.issue==GeometryIssue::UnsupportedRaster);
    assert(rejected.rows.empty());
    assert(!AuditNativeR09Candidate(Eden::NeuralPlans::Original,
                                   {854u,480u},rejected));
    assert(rejected.issue==GeometryIssue::UnsupportedRaster);
    assert(rejected.rows.empty());
    assert(!AuditNativeR09Candidate(Eden::NeuralPlans::Original,
                                   {1920u,1200u},rejected));
    assert(rejected.issue==GeometryIssue::UnsupportedRaster);
    assert(!AuditNativeR09Candidate("",kCandidateMinRaster,rejected));
    assert(rejected.issue==GeometryIssue::InvalidReference);
    // A reference whose row shape disagrees with the authentic 1080p
    // schedule must not be used as the basis for a reduced native graph.
    std::string malformed{Eden::NeuralPlans::Original};
    const auto pos=malformed.find("1920 1080 2073600");
    assert(pos!=std::string::npos);
    malformed.replace(pos,std::string("1920 1080 2073600").size(),
                      "1920 900 2073600");
    assert(!AuditNativeR09Candidate(malformed,kCandidateMinRaster,rejected));
    assert(rejected.issue==GeometryIssue::ReferenceGeometryMismatch ||
           rejected.issue==GeometryIssue::InvalidNativeSchedule);
    assert(rejected.rows.empty());
}
