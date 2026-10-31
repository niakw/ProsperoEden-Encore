// SPDX-License-Identifier: GPL-3.0-or-later
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <span>
#include <vector>
#include "video_core/texture_cache/ns2_astc_staging_bridge.h"

using namespace Eden::NS2::Eglantine;
constexpr std::uint64_t BASE=0x100000, STRIDE=21ULL<<20;
static AstcDirtyLayerPlanner Planner() {
    AstcDirtyLayerPlanner p(BASE, STRIDE*68, STRIDE, 68, 0, 64ULL<<20);
    assert(p.Valid() && p.ResetAfterFullUpload());
    for (auto i:{0U,1U,2U,20U,42U,65U,66U})
        assert(p.MarkWrite(BASE+i*STRIDE+123,16));
    return p;
}
static void Success() {
    auto p=Planner();
    std::uint32_t opened=0, decoded=0;
    std::uint64_t read_bytes=0;
    std::vector<std::uint32_t> uploaded;
    auto result=UploadAstcDirtyLayerBatches(p,BASE,
        [&](std::uint32_t batch,std::uint64_t bytes) {
            assert(batch==opened++);
            assert(bytes<=64ULL<<20 && bytes>0);
            return true;
        },
        [&](std::uint64_t address,std::uint64_t staging,std::uint64_t n) {
            assert(address>=BASE && address<BASE+STRIDE*68);
            assert(staging<64ULL<<20 && n==STRIDE);
            read_bytes+=n;return true;
        },
        [&](std::uint32_t batch,std::span<const std::uint32_t> layers) {
            assert(batch==decoded++);
            assert(layers.size()<=3);
            uploaded.insert(uploaded.end(),layers.begin(),layers.end());
            return true;
        });
    assert(result.status==AstcTransferStatus::Completed);
    assert(result.dispatched_batches==3 && opened==3 && decoded==3);
    assert(result.uploaded_bytes==7*STRIDE && read_bytes==7*STRIDE);
    assert((uploaded==std::vector<std::uint32_t>{0,1,2,20,42,65,66}));
    assert(p.Snapshot().status==LayerPlanStatus::NoChanges);
}
static void Failures() {
    for (int failing=0;failing<3;++failing) {
        auto p=Planner();
        int events=0;
        auto x=UploadAstcDirtyLayerBatches(p,BASE,
            [&](std::uint32_t,std::uint64_t) {++events;return failing!=0;},
            [&](std::uint64_t,std::uint64_t,std::uint64_t) {++events;return failing!=1;},
            [&](std::uint32_t,std::span<const std::uint32_t>) {++events;return failing!=2;});
        assert(x.status==(failing==0?AstcTransferStatus::StagingFailure:
                          failing==1?AstcTransferStatus::ReadFailure:
                          AstcTransferStatus::DispatchFailure));
        assert(p.Snapshot().status==LayerPlanStatus::FullUpload && events>0);
    }
    auto p=Planner();
    auto race=UploadAstcDirtyLayerBatches(p,BASE,
        [&](std::uint32_t,std::uint64_t) {return true;},
        [&](std::uint64_t,std::uint64_t,std::uint64_t) {return true;},
        [&](std::uint32_t,std::span<const std::uint32_t>) {
            assert(p.MarkWrite(BASE+33*STRIDE,16));
            return true;
        });
    assert(race.status==AstcTransferStatus::ConcurrentWrite);
    assert(p.Snapshot().status==LayerPlanStatus::Partial);
    AstcDirtyLayerPlanner overflow(BASE,STRIDE*68,STRIDE,68,0,64ULL<<20);
    assert(overflow.Valid() && overflow.ResetAfterFullUpload());
    assert(overflow.MarkWrite(BASE+2*STRIDE,64));
    auto result=UploadAstcDirtyLayerBatches(overflow,
        (std::numeric_limits<std::uint64_t>::max)()-100,
        [&](std::uint32_t,std::uint64_t) {return true;},
        [&](std::uint64_t,std::uint64_t,std::uint64_t) {assert(false);return true;},
        [&](std::uint32_t,std::span<const std::uint32_t>) {assert(false);return true;});
    assert(result.status==AstcTransferStatus::InvalidPlan);
    assert(overflow.Snapshot().status==LayerPlanStatus::FullUpload);
}
static void NoWork() {
    auto p=Planner();
    p.Invalidate();
    auto x=UploadAstcDirtyLayerBatches(p,BASE,
        [](auto,auto){assert(false);return true;},
        [](auto,auto,auto){assert(false);return true;},
        [](auto,std::span<const std::uint32_t>){assert(false);return true;});
    assert(x.status==AstcTransferStatus::FullUploadRequired);
    assert(p.ResetAfterFullUpload());
    x=UploadAstcDirtyLayerBatches(p,BASE,
        [](auto,auto){assert(false);return true;},
        [](auto,auto,auto){assert(false);return true;},
        [](auto,std::span<const std::uint32_t>){assert(false);return true;});
    assert(x.status==AstcTransferStatus::NoChanges);
}
int main(){Success();Failures();NoWork();std::puts("N59_BOUNDED_ASTC_UPLOAD_TRANSACTION_PASS");}
