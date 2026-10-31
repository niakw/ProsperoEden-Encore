// SPDX-License-Identifier: GPL-3.0-or-later
// N69 executes the exact versioned vendor sparse bind transaction.
#include <cassert>
#include <array>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <span>
#include <vector>
#include "video_core/renderer_vulkan/ns2_sparse_bind_transaction.h"
using namespace Eden::NS2::Eglantine;
static SparseImageSpec Spec(){
    return {1024,1024,11,68,64,64,3,65536,131072,
        SparseLayerBudget::CapForDeviceMemory(6ULL<<30),false};
}
struct FakeAllocator {
    struct SparseMemoryAllocation {
        void* allocation{};
        VkDeviceMemory memory{};
        VkDeviceSize offset{};
    };
    int allocations{},releases{};
    bool fail{};
    VkMemoryRequirements last{};
    bool AllocateSparseMemory(const VkMemoryRequirements& req,SparseMemoryAllocation& out) {
        last=req;
        if(fail)return false;
        ++allocations;
        out={reinterpret_cast<void*>(0x1234),
             reinterpret_cast<void*>(0x5678),131072};
        return true;
    }
    void ReleaseSparseMemory(SparseMemoryAllocation& p) {
        assert(p.allocation&&p.memory);
        ++releases;
        p={};
    }
};
struct FakeFence {
    VkResult status=VK_NOT_READY,wait_result=VK_SUCCESS;
    mutable int waited{};
    operator VkFence() const {return reinterpret_cast<void*>(0x789a);}
    VkResult GetStatus() const {return status;}
    VkResult Wait(std::uint64_t timeout) const {assert(timeout);++waited;return wait_result;}
};
struct FakeQueue {
    mutable int calls{};
    mutable std::vector<VkSparseImageMemoryBind> tiles;
    mutable std::vector<VkSparseMemoryBind> tails;
    mutable VkSemaphore last_wait{},last_signal{};
    VkResult result=VK_SUCCESS;
    template<class T,class U>
    VkResult BindSparseImage(VkImage image,const T& t,const U& u,VkFence fence,
                             VkSemaphore wait,VkSemaphore signal) const {
        assert(image && fence);
        ++calls;tiles.assign(t.begin(),t.end());tails.assign(u.begin(),u.end());
        last_wait=wait;last_signal=signal;
        return result;
    }
};
struct FakeDevice {VkResult result=VK_SUCCESS;mutable int calls{};
    VkResult WaitIdle() const {++calls;return result;}
};
static VkSparseImageMemoryRequirements Sparse(const SparseImageSpec& s){
    VkSparseImageMemoryRequirements r{};
    r.formatProperties.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
    r.formatProperties.imageGranularity={s.tile_width,s.tile_height,1};
    r.formatProperties.flags=s.single_mip_tail?
        VK_SPARSE_IMAGE_FORMAT_SINGLE_MIPTAIL_BIT:0;
    r.imageMipTailFirstLod=s.tail_first_lod;
    r.imageMipTailSize=s.tail_bytes;
    r.imageMipTailOffset=134217728;
    r.imageMipTailStride=s.single_mip_tail?0:131072;
    return r;
}
static std::vector<VkSparseImageMemoryRequirements> Requirements(const SparseImageSpec& s){return {Sparse(s)};}
static VkMemoryRequirements Memory(){
    return {268435456,65536,7};
}
static VkImage Image(){return reinterpret_cast<void*>(0xabcd);}
static void Successful(){
    auto s=Spec();SparseLayerBudget b(s);FakeAllocator a;
    SparseBindOwner<FakeAllocator> owner(a,b,s);
    FakeQueue q;FakeFence fence;
    const auto request=b.Plan(std::vector<std::uint32_t>{1,2});
    auto mem=Memory();
    const auto wait=reinterpret_cast<VkSemaphore>(0x4567);
    const auto signal=reinterpret_cast<VkSemaphore>(0x5678);
    assert(owner.Bind(Image(),mem,Requirements(s),request,q,fence,wait,signal)==VK_SUCCESS);
    assert(owner.ReadyForSampling()&&owner.HasLiveBacking()&&fence.waited==1);
    assert(a.allocations==1&&a.releases==0&&b.BoundBytes()==request.bytes_new);
    assert(q.calls==1 && q.tiles.size()==672 && q.tails.size()==2);
    assert(q.last_wait==wait&&q.last_signal==signal);
    assert(q.tiles.front().subresource.arrayLayer==1);
    assert(q.tiles.front().memory==reinterpret_cast<void*>(0x5678));
    assert(q.tiles.front().memoryOffset==131072);
    assert(q.tiles[1].memoryOffset==196608);
    assert(q.tails[0].resourceOffset==134217728+131072);
    assert(q.tails[1].resourceOffset==134217728+262144);
    assert(q.tails[1].memoryOffset+q.tails[1].size==
           131072+request.bytes_new);
    assert(owner.Bind(Image(),mem,Requirements(s),request,q,fence)==
           VK_ERROR_INITIALIZATION_FAILED);
    assert(q.calls==1);
    auto next=b.Plan(std::vector<std::uint32_t>{3});
    assert(owner.Bind(Image(),mem,Requirements(s),next,q,fence)==VK_SUCCESS);
    assert(a.allocations==2 && b.IsBound(3));
    FakeDevice dev;
    bool dropped=false;
    assert(owner.RetireAfterDeviceIdle(dev,[&]{dropped=true;}));
    assert(dropped && dev.calls==1 && a.releases==2);
    assert(!owner.HasLiveBacking()&&!owner.ReadyForSampling()&&!b.IsBound(1));
}
static void Failures(){
    const auto s=Spec();FakeAllocator a;FakeQueue q;FakeFence f;
    FakeDevice d;
    SparseLayerBudget b(s);
    SparseBindOwner<FakeAllocator> owner(a,b,s);
    auto req=b.Plan(std::vector<std::uint32_t>{0});
    auto mem=Memory();
    auto sparse=Requirements(s);
    sparse[0].formatProperties.imageGranularity.width=32;
    assert(owner.Bind(Image(),mem,sparse,req,q,f)==VK_ERROR_INITIALIZATION_FAILED);
    assert(a.allocations==0&&q.calls==0);
    sparse=Requirements(s);
    // A separate metadata aspect must not be silently ignored.
    auto multi=sparse;
    multi.push_back(sparse.front());
    multi.back().formatProperties.aspectMask=2;
    assert(owner.Bind(Image(),mem,multi,req,q,f)==VK_ERROR_INITIALIZATION_FAILED);
    assert(a.allocations==0&&q.calls==0);
    mem.memoryTypeBits=0;
    assert(owner.Bind(Image(),mem,sparse,req,q,f)==VK_ERROR_INITIALIZATION_FAILED);
    mem=Memory();
    f.status=VK_SUCCESS;
    assert(owner.Bind(Image(),mem,sparse,req,q,f)==VK_ERROR_INITIALIZATION_FAILED);
    f.status=VK_NOT_READY;
    a.fail=true;
    assert(owner.Bind(Image(),mem,sparse,req,q,f)==VK_ERROR_OUT_OF_DEVICE_MEMORY);
    assert(!owner.HasLiveBacking()&&!b.Poisoned());
    a.fail=false;
    q.result=VK_ERROR_DEVICE_LOST;
    assert(owner.Bind(Image(),mem,sparse,req,q,f)==VK_ERROR_DEVICE_LOST);
    assert(owner.HasLiveBacking() && b.Poisoned() && !owner.ReadyForSampling());
    assert(a.releases==0);
    d.result=VK_ERROR_DEVICE_LOST;
    assert(!owner.RetireAfterDeviceIdle(d,[]{assert(false);}));
    assert(a.releases==0 && owner.HasLiveBacking());
    d.result=VK_SUCCESS;
    assert(owner.RetireAfterDeviceIdle(d,[]{}));
    assert(a.releases==1 && !b.Poisoned());
}
static void TimeoutAndSharedTail(){
    auto s=Spec();s.single_mip_tail=true;s.tail_bytes=65536;
    SparseLayerBudget b(s);FakeAllocator a;FakeQueue q;FakeFence f;
    SparseBindOwner<FakeAllocator> owner(a,b,s);
    const auto req=b.Plan(std::vector<std::uint32_t>{1,2});
    f.wait_result=VK_TIMEOUT;
    assert(owner.Bind(Image(),Memory(),Requirements(s),req,q,f)==VK_TIMEOUT);
    assert(owner.HasLiveBacking()&&b.Poisoned()&&!b.IsBound(1));
    assert(q.tiles.size()==672 && q.tails.size()==1);
    assert(q.tails[0].resourceOffset==134217728);
    FakeDevice d;
    assert(owner.RetireAfterDeviceIdle(d,[]{}));
    assert(a.releases==1&&!owner.HasLiveBacking());
    f.wait_result=VK_SUCCESS;
    auto fresh=b.Plan(std::vector<std::uint32_t>{1});
    assert(owner.Bind(Image(),Memory(),Requirements(s),fresh,q,f)==VK_SUCCESS);
    assert(owner.ReadyForSampling());
    assert(owner.RetireAfterDeviceIdle(d,[]{}));
}
int main(){Successful();Failures();TimeoutAndSharedTail();
    std::puts("N69_NATIVE_VMA_SPARSE_BIND_TRANSACTION_PASS");}
