// SPDX-License-Identifier: GPL-3.0-or-later
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <random>
#include <vector>
#include "video_core/texture_cache/ns2_astc_layer_plan.h"
using Eden::NS2::Eglantine::AstcDirtyLayerPlanner;
using Eden::NS2::Eglantine::LayerPlanStatus;
static void Basic() {
    constexpr std::uint64_t base=0x200000, stride=21ULL<<20, count=68;
    AstcDirtyLayerPlanner p(base,stride*count,stride,count,0,64ULL<<20);
    assert(p.Valid());
    assert(p.Snapshot().status==LayerPlanStatus::FullUpload);
    assert(p.ResetAfterFullUpload());
    assert(p.Snapshot().status==LayerPlanStatus::NoChanges);
    for (const auto layer:{0U,1U,2U,20U,42U,65U,66U}) {
        assert(p.MarkWrite(base+layer*stride+1024,4096));
    }
    const auto before=p.Snapshot();
    assert(before.status==LayerPlanStatus::Partial);
    assert(before.copies.size()==7);
    assert(before.batch_bytes.size()==3);
    assert(before.batch_bytes[0]==3*stride && before.batch_bytes[1]==3*stride);
    for (const auto& c:before.copies) {
        assert(c.bytes==stride && c.guest_offset==c.layer*stride);
        assert(c.staging_offset+c.bytes<=before.batch_bytes[c.batch]);
        assert(before.batch_bytes[c.batch]<=64ULL<<20);
    }
    assert(p.MarkWrite(base+3*stride,128));
    assert(!p.Commit(before)); // a concurrent new write must not be discarded
    assert(p.Snapshot().copies.size()==8);
    auto next=p.Snapshot();
    assert(p.Commit(next));
    assert(p.Snapshot().status==LayerPlanStatus::NoChanges);
    p.Invalidate();
    assert(p.Snapshot().status==LayerPlanStatus::FullUpload);
    assert(!p.Commit(next));
}
static void Edge() {
    const auto max=(std::numeric_limits<std::uint64_t>::max)();
    assert(!AstcDirtyLayerPlanner(max-64,128,32,4,0,64).Valid()); // GPU base+size overflow
    assert(!AstcDirtyLayerPlanner(0,1024,0,4,0,512).Valid());
    assert(!AstcDirtyLayerPlanner(0,1024,128,4,128,512).Valid());
    assert(!AstcDirtyLayerPlanner(0,1024,128,4,0,120).Valid());
    assert(!AstcDirtyLayerPlanner(0,1024,128,0,0,512).Valid());
    assert(!AstcDirtyLayerPlanner(0,1024,128,4097,0,512).Valid());
    // high address: a write wrapping UINT64_MAX clamps at its last valid byte.
    AstcDirtyLayerPlanner p(max-1024,1024,256,4,32,256);
    assert(p.Valid() && p.ResetAfterFullUpload());
    assert(p.MarkWrite(max-100,200)); // clamped, last layer only
    auto q=p.Snapshot();
    assert(q.status==LayerPlanStatus::Partial);
    assert(q.copies.size()==1 && q.copies[0].layer==3);
    assert(p.MarkWrite(max-500,800)); // clamped to end of valid image
}
static void Randomized() {
    std::mt19937_64 rng(0xA57C2247U);
    for (unsigned round=0;round<1600;++round) {
        const std::uint32_t n=2+(rng()%127);
        const std::uint64_t stride=4096*(1+(rng()%31));
        const std::uint64_t base=0x200000;
        AstcDirtyLayerPlanner p(base,stride*n,stride,n,0,stride*3);
        assert(p.Valid() && p.ResetAfterFullUpload());
        std::vector<bool> dirty(n,false);
        for(unsigned op=0;op<25;++op){
            const auto first=static_cast<std::uint32_t>(rng()%n);
            const auto last=static_cast<std::uint32_t>(first+(rng()%(n-first)));
            const auto start=base+first*stride+1;
            const auto length=(last-first)*stride+8;
            assert(p.MarkWrite(start,length));
            const auto begin=first;
            const auto end=static_cast<std::uint32_t>((start-base+length-1)/stride);
            for(auto k=begin;k<=end;++k)dirty[k]=true;
        }
        auto q=p.Snapshot();
        std::size_t expected=0;
        for(bool v:dirty)expected+=v;
        if(expected==n)assert(q.status==LayerPlanStatus::FullUpload);
        else {
            assert(q.status==LayerPlanStatus::Partial);
            assert(q.copies.size()==expected);
            for(const auto& c:q.copies){
                assert(c.layer<n && dirty[c.layer]);
                assert(c.guest_offset==static_cast<std::uint64_t>(c.layer)*stride);
                assert(c.staging_offset+c.bytes<=q.batch_bytes[c.batch]);
                assert(q.batch_bytes[c.batch]<=stride*3);
            }
            assert(p.Commit(q));
            assert(p.Snapshot().status==LayerPlanStatus::NoChanges);
        }
    }
}
int main(){Basic();Edge();Randomized();std::puts("N55_ASTC_LAYER_UPLOAD_PLAN_PASS");}
