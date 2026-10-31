// SPDX-License-Identifier: GPL-3.0-or-later
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <random>
#include <vector>
#include "video_core/renderer_vulkan/ns2_sparse_layer_budget.h"
using namespace Eden::NS2::Eglantine;
static SparseImageSpec Spec(){
    return SparseImageSpec{
        1024,1024,11,68,64,64,3,65536,131072,
        SparseLayerBudget::CapForDeviceMemory(std::uint64_t{6}<<30),false
    };
}
static void Basic(){
    auto s=Spec();
    SparseLayerBudget b(s);
    assert(b.Valid()&&b.BoundBytes()==0);
    const std::uint64_t layer=(256+64+16)*65536ULL+131072ULL;
    auto a=b.Plan(std::vector<std::uint32_t>{0,1});
    assert(a.status==SparsePlanStatus::Ready&&a.bytes_new==layer*2);
    assert(b.Commit(a));
    assert(b.IsBound(0)&&b.IsBound(1)&&b.BoundBytes()==layer*2);
    assert(!b.Commit(a)); // stale transaction cannot double count
    auto more=b.Plan(std::vector<std::uint32_t>{1,2,3});
    assert(more.status==SparsePlanStatus::Ready&&more.new_layers.size()==2);
    assert(more.bytes_new==layer*2&&b.Commit(more));
    auto old=b.Plan(std::vector<std::uint32_t>{0,1,2});
    assert(old.status==SparsePlanStatus::AlreadyBound);
    auto nope=b.Plan(std::vector<std::uint32_t>{2,2});
    assert(nope.status==SparsePlanStatus::Invalid);
    auto beyond=b.Plan(std::vector<std::uint32_t>{68});
    assert(beyond.status==SparsePlanStatus::Invalid);
    auto fail=b.Plan(std::vector<std::uint32_t>{30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49});
    assert(fail.status==SparsePlanStatus::BudgetExceeded);
    b.Poison();assert(b.Poisoned());
    assert(b.Plan(std::vector<std::uint32_t>{4}).status==SparsePlanStatus::Poisoned);
    assert(!b.Commit(more));
    b.ResetAfterGpuRetire();
    assert(!b.Poisoned()&&!b.IsBound(1)&&b.BoundBytes()==0);
}
static void SharedTail(){
    auto s=Spec();s.single_mip_tail=true;s.tail_bytes=65536;
    SparseLayerBudget b(s);assert(b.Valid());
    auto a=b.Plan(std::vector<std::uint32_t>{2});
    assert(a.status==SparsePlanStatus::Ready&&a.bind_shared_tail);
    assert(a.bytes_new==a.layer_bytes+65536);
    assert(b.Commit(a));
    auto c=b.Plan(std::vector<std::uint32_t>{3});
    assert(c.status==SparsePlanStatus::Ready&&!c.bind_shared_tail);
    assert(c.bytes_new==c.layer_bytes&&b.Commit(c));
    assert(b.BoundBytes()==2*c.layer_bytes+65536);
}
static void Invalid(){
    auto s=Spec();
    for(auto field:{0,1,2,3,4}){
        auto t=s;
        if(field==0)t.tile_width=0;
        if(field==1)t.tile_alignment=3;
        if(field==2)t.tail_first_lod=100;
        if(field==3)t.tail_bytes=0;
        if(field==4)t.layers=10000000;
        SparseLayerBudget x(t);assert(!x.Valid());
    }
    auto t=s;t.tile_alignment=std::uint64_t{1}<<63;t.width=65536;
    t.height=65536;t.tile_width=1;t.tile_height=1;
    SparseLayerBudget overflow(t);assert(!overflow.Valid());
    assert(SparseLayerBudget::CapForDeviceMemory((std::uint64_t{7}<<30)-1)==(std::uint64_t{384}<<20));
    assert(SparseLayerBudget::CapForDeviceMemory(std::uint64_t{7}<<30)==(std::uint64_t{768}<<20));
}
static void Randomized(){
    std::mt19937 rng(0x57A53);
    auto s=Spec();SparseLayerBudget b(s);
    assert(b.Valid());
    std::uint32_t accepted=0;
    for(unsigned i=0;i<5000;++i){
        const auto layer=static_cast<std::uint32_t>(rng()%68);
        auto p=b.Plan(std::vector<std::uint32_t>{layer});
        if(p.status==SparsePlanStatus::Ready){
            assert(b.Commit(p));++accepted;
            assert(b.BoundBytes()<=s.max_bound_bytes);
        } else {
            assert(p.status==SparsePlanStatus::AlreadyBound ||
                   p.status==SparsePlanStatus::BudgetExceeded);
        }
    }
    assert(accepted>0&&accepted<68);
}
int main(){Basic();SharedTail();Invalid();Randomized();std::puts("N63_SPARSE_LAYER_BUDGET_AND_MIPTAIL_PASS");}
