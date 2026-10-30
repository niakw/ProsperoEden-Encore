// SPDX-License-Identifier: GPL-3.0-or-later
// Synthetic request fixtures: no SDK, firmware, content, PS5 execution or GPU submission.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <span>
#include "core/hle/service/am/service/gpu_memory_registration.h"
#include "core/hle/service/am/service/graphics_supervisor_protocol.h"
#include "core/hle/service/am/service/native_image_layout.h"
#include "core/hle/service/nvdrv/devices/native_gpu_kind.h"
#include "core/hle/service/nvdrv/devices/native_gpu_context.h"
#include "core/hle/service/am/service/graphics_syncpoint_cache.h"

static int assertions=0;
static void require(bool condition,const char* desc){
    ++assertions;
    if(!condition){std::fprintf(stderr,"NS2 HLE fixture FAILED: %s\n",desc);std::exit(1);}
}
int main(){
    using namespace Service::AM;
    namespace P=Service::AM::GraphicsSupervisorProtocol;
    namespace N=Service::Nvidia::Devices;
    const std::array<u32,8> reg{0x75,6,0x1000,0,0x2fff,0,0xaabbcc05,0xff000006};
    const auto r=DecodeGpuMemoryRegistration(reg);
    require(r && r->begin==0x1000 && r->end==0x2fff,"GPU registration bounds");
    require(r && r->flags==5 && r->device==6,"GPU registration padding ignored");
    require(!DecodeGpuMemoryRegistration(std::span<const u32>(reg.data(),7)),
            "GPU registration rejects short request");
    auto badreg=reg;badreg[1]=5;
    require(!DecodeGpuMemoryRegistration(badreg),"GPU registration rejects wrong size");
    badreg=reg;badreg[0]=0x76;
    require(!DecodeGpuMemoryRegistration(badreg),"GPU registration rejects wrong command");

    std::array<u32,16> bootstrap{};
    bootstrap[0]=0x14; bootstrap[1]=0x8000000c;bootstrap[2]=2;
    bootstrap[3]=0x1234;bootstrap[4]=0xabc;bootstrap[6]=5;bootstrap[7]=0x80000000;
    auto br=P::DecodeBootstrap(bootstrap);
    require(br && br->process_handle==0x1234 && br->applet_resource_user_id==0xabc,
            "bootstrap handle and application resource ID");
    require(br && br->flags==0x8000000000000005ULL && P::IsLocalBootstrap(*br),
            "bootstrap native profile 0x807");
    require(P::NativeGpuProfileForBootstrap(br->flags)==0x807,"GPU profile 0x807");
    bootstrap[6]=6;
    br=P::DecodeBootstrap(bootstrap);
    require(br && P::NativeGpuProfileForBootstrap(br->flags)==0x808,
            "GPU profile 0x808");
    bootstrap[8]=1;
    br=P::DecodeBootstrap(bootstrap);
    require(br && !P::IsLocalBootstrap(*br),"nonzero remote memory rejected");
    bootstrap[8]=0;bootstrap[2]=1;
    require(!P::DecodeBootstrap(bootstrap),"bootstrap handle mode rejected");
    bootstrap[2]=2;bootstrap[1]=0;
    require(!P::DecodeBootstrap(bootstrap),"bootstrap malformed header rejected");

    const std::array<u32,5> duplicate{0x30,0x80000001,2,0x99,3};
    auto dup=P::DecodeRequestGroupEventDuplicate(duplicate);
    require(dup && dup->group==3 && dup->copied_handle==0x99,"request group duplicate");
    require(P::ClassifyRequestGroupEventDuplicate(3,true,true,true)==
            P::RequestGroupDuplicateStatus::Ready,"valid request group");
    require(P::ClassifyRequestGroupEventDuplicate(8,true,true,true)==
            P::RequestGroupDuplicateStatus::OutOfRange,"request group out of range");
    require(P::ClassifyRequestGroupEventDuplicate(3,false,true,true)==
            P::RequestGroupDuplicateStatus::NotConfigured,"unconfigured request group");
    require(P::ClassifyRequestGroupEventDuplicate(3,true,false,true)==
            P::RequestGroupDuplicateStatus::MissingEvent,"missing request event");
    require(P::ClassifyRequestGroupEventDuplicate(3,true,true,false)==
            P::RequestGroupDuplicateStatus::IdentityMismatch,"request event identity mismatch");
    const std::array<u32,7> sync{0xd9,5,3,~u32{9},123,0,0};
    auto wait=P::DecodeSyncpointWait(sync);
    require(wait && wait->slot==3 && wait->id==9 && wait->threshold==123 && !wait->wide,
            "syncpoint packet decoding");
    require(P::IsSyncpointWaitSatisfied(124,123,false),"modular syncpoint satisfied");
    require(!P::IsSyncpointWaitSatisfied(122,123,false),"modular syncpoint pending");
    require(!P::IsSyncpointWaitSatisfied(1,0x100000001ULL,true),
            "wide syncpoint checks full threshold");
    require(P::DecodeBufferSlot(0x1234)==0x34,"packed buffer slot");

    std::array<u32,16> preferences{};
    preferences[0]=0;preferences[1]=1;preferences[2]=(63<<16)|127; // 128x64
    preferences[3]=0;preferences[4]=4;preferences[5]=8;preferences[6]=1;
    preferences[7]=1;
    const auto req=CalculateNativeImageRequirements(preferences,2);
    require(req && req->size==65536 && req->alignment==4096,
            "RGBA image block height/stride and count");
    require(!CalculateNativeImageRequirements(preferences,0),"reject zero image count");
    preferences[5]=7;
    require(!CalculateNativeImageRequirements(preferences,1),"reject short pitch");
    preferences[5]=8;preferences[8]=1;
    require(!CalculateNativeImageRequirements(preferences,1),"reject extra format flags");
    preferences[8]=0;preferences[4]=9;
    require(!CalculateNativeImageRequirements(preferences,1),"reject unsupported block height");
    preferences[4]=4;preferences[6]=0;
    require(!CalculateNativeImageRequirements(preferences,1),"reject unknown color layout");

    // Sparse NVGPU MMU ABI and mapping lifetime, sourced from latest pinned NS2.
    N::NativeSparseRemapEntry entry{};
    entry.flags=0x1000;entry.kind=6;entry.fallback_kind=6;
    entry.handle=7;entry.source_pages=2;entry.destination_pages=0x10;entry.pages=4;
    auto decoded=N::DecodeNativeSparseRemap(entry);
    require(decoded && decoded->address==0x10000 && decoded->size==0x4000 &&
            decoded->source_offset==0x2000 && decoded->handle==7,
            "native sparse 4-KiB mapping");
    entry.flags=0x2000;entry.pages=1;
    decoded=N::DecodeNativeSparseRemap(entry);
    require(decoded && decoded->size==0x10000,"native sparse 64-KiB page size");
    entry.flags=0x3000;
    require(!N::DecodeNativeSparseRemap(entry),"reject multiple page-size flags");
    entry.flags=0x1000;entry.pages=0;
    require(!N::DecodeNativeSparseRemap(entry),"reject empty sparse mapping");
    entry.pages=4;entry.source_pages=~u64{0};
    require(!N::DecodeNativeSparseRemap(entry),"reject sparse source overflow");
    entry.source_pages=2;entry.handle=0;
    require(!N::DecodeNativeSparseRemap(entry),"reject source on unmapped handle");
    entry.handle=7;entry.reserved=1;
    require(!N::DecodeNativeSparseRemap(entry),"reject sparse reserved field");
    entry.reserved=0;entry.flags=0x1000;
    require(N::DecodeNativeSparseRemap(entry).has_value(),"accept restored mapping");

    N::NativeSparseMappingTable table;
    table.Replace({0x1000,0x4000,0x10000,7});
    table.Replace({0x2000,0x1000,0x20000,9});
    const auto& ranges=table.Ranges();
    require(ranges.size()==3,"split overlapping sparse mapping into three regions");
    require(ranges.at(0x1000).size==0x1000 && ranges.at(0x1000).handle==7,
            "preserve left sparse fragment");
    require(ranges.at(0x2000).size==0x1000 && ranges.at(0x2000).handle==9,
            "insert overlapping sparse owner");
    require(ranges.at(0x3000).size==0x2000 &&
            ranges.at(0x3000).source_offset==0x12000,
            "advance right fragment physical offset");
    require(table.ReferencedHandles().size()==2,"both sparse backing handles pinned");
    table.Replace({std::numeric_limits<u64>::max()-0xff,0x200,0,44});
    table.Replace({0x6000,0,0,44});
    table.Replace({0x6000,0x200,std::numeric_limits<u64>::max()-0xff,44});
    require(table.Ranges().size()==3 && table.ReferencedHandles().size()==2,
            "reject overflowing and empty sparse mapping without dropping handles");
    table.Replace({0x2000,0x1000,0,0});
    require(table.Ranges().size()==2 && table.ReferencedHandles().size()==1 &&
            table.ReferencedHandles().contains(7),
            "unmap sparse middle range and release old handle");

    GpuSparseMapRequest gm{};
    gm.address=0x10000;gm.size=0x2000;gm.kind=6;
    gm.fallback_kind=6;gm.cache=1;gm.memory=7;gm.source_offset=0x4000;
    const auto gpuMap=DecodeGpuSparseMap(gm);
    require(gpuMap && gpuMap->flags==0x1004 &&
            gpuMap->destination_pages==0x10 && gpuMap->source_pages==4,
            "GPU request maps to 4-KiB sparse ioctl entry");
    gm.address=0x10001;
    require(!DecodeGpuSparseMap(gm),"reject unaligned sparse destination");
    gm.address=0x10000;gm.read_only=1;
    require(!DecodeGpuSparseMap(gm),"reject unsupported sparse read-only flag");
    gm.read_only=0;gm.comptag_mode=1;
    require(!DecodeGpuSparseMap(gm),"reject unsupported sparse compression tag");
    gm.comptag_mode=0;gm.cache=2;
    require(!DecodeGpuSparseMap(gm),"reject unsupported sparse caching mode");
    gm.cache=1;gm.reserved2=1;
    require(!DecodeGpuSparseMap(gm),"reject unknown sparse extension");

    std::array<u32,12> region{0xe6,10,8,0x10000,0,0x1ffff,0,12,0,1,0,0};
    auto regionReq=DecodeGpuSparseRegion(region);
    require(regionReq && regionReq->address_space==8 &&
            IsValidGpuSparseRegionRange(*regionReq),"valid sparse region boundary");
    region[5]=0x1ffe0;
    regionReq=DecodeGpuSparseRegion(region);
    require(regionReq && !IsValidGpuSparseRegionRange(*regionReq),
            "reject unaligned sparse end");
    region[5]=0x1ffff;region[7]=15;
    regionReq=DecodeGpuSparseRegion(region);
    require(regionReq && !IsValidGpuSparseRegionRange(*regionReq),
            "reject unsupported sparse page shift");
    region[7]=12;region[5]=0xffffffff;region[6]=0xffffffff;
    regionReq=DecodeGpuSparseRegion(region);
    require(regionReq && !IsValidGpuSparseRegionRange(*regionReq),
            "reject inclusive maximum end overflow");
    require(!DecodeGpuSparseRegion(std::span<const u32>(region.data(),11)),
            "reject truncated sparse region request");

    std::array<u8,4> legacyTsg{21,0,0,0};
    auto tsg=N::DecodeNativeTsgBinding(legacyTsg,false);
    require(tsg && tsg->channel_fd==21 && tsg->subcontext_id==0,
            "legacy native GPU binding");
    require(!N::DecodeNativeTsgBinding(legacyTsg,true),
            "reject short extended native GPU binding");
    legacyTsg.fill(0xff);
    require(!N::DecodeNativeTsgBinding(legacyTsg,false),
            "reject negative GPU file descriptor");
    std::array<u8,24> extendedTsg{};
    extendedTsg[0]=21;extendedTsg[4]=63;
    tsg=N::DecodeNativeTsgBinding(extendedTsg,true);
    require(tsg && tsg->channel_fd==21 && tsg->subcontext_id==63,
            "largest native GPU subcontext id");
    extendedTsg[4]=64;
    require(!N::DecodeNativeTsgBinding(extendedTsg,true),
            "reject out of range native GPU subcontext");
    extendedTsg[4]=63;extendedTsg[23]=1;
    require(!N::DecodeNativeTsgBinding(extendedTsg,true),
            "reject nonzero native GPU extension bytes");
    extendedTsg[23]=0;
    require(!N::DecodeNativeTsgBinding(
        std::span<const u8>(extendedTsg.data(),23),true),
        "reject truncated GPU binding");
    require(N::GetNativeGpuContextSlot(0xc797)==std::optional<u32>{1} &&
            N::GetNativeGpuContextSlot(0xc7c0)==std::optional<u32>{2} &&
            N::GetNativeGpuContextSlot(0xc7b5)==std::optional<u32>{4} &&
            N::GetNativeGpuContextSlot(0xc56f)==std::optional<u32>{5},
            "native context identities");
    require(!N::GetNativeGpuContextSlot(0xb197),
            "legacy Maxwell context is not native");
    namespace Cache=Service::AM::GraphicsSyncpointCache;
    static_assert(Cache::CounterCount==192 && Cache::GroupCount==3);
    require(Cache::Header[0]==1 && Cache::Header[2]==191,
            "graphics syncpoint memory layout");
    require(Cache::ExtendCounter(Cache::Unallocated,12)==12,
            "first syncpoint sample");
    require(Cache::ExtendCounter(0x1fffffffeULL,1)==0x200000001ULL,
            "extend 32-bit syncpoint across counter wrap");
    Cache::CounterValue syncCounter{};
    require(syncCounter.Observe(std::nullopt)==Cache::Unallocated,
            "empty syncpoint observation");
    require(syncCounter.Observe(0xfffffffe)==0xfffffffeULL,
            "initial near-wrap counter");
    require(syncCounter.Observe(1)==0x100000001ULL,
            "syncpoint counter wrap");
    require(syncCounter.Observe(std::nullopt)==Cache::Unallocated &&
            syncCounter.previous==0x100000001ULL,
            "missing counter should not clear last observed value");

    const auto generic=N::SelectNativeMemoryKind(6,6);
    require(generic && generic->selected==6 &&
            generic->backend==static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2),
            "generic uncompressed native MMU kind");
    require(N::SelectNativeMemoryKind(8,6).has_value(),
            "compressed kind explicitly negotiates generic fallback");
    require(!N::SelectNativeMemoryKind(8,7).has_value(),
            "no silent fallback for unknown MMU kind");
    require(!N::SelectNativeMemoryKind(0xfe,0xfe).has_value(),
            "do not confuse legacy generic kind with native GPU kind");
    require(!N::SelectNativeMemoryKind(2,2).has_value(),
            "do not advertise unsupported native kind");
    std::printf("NS2 graphics HLE protocol, image layout, MMU kind: %d assertions PASS\n",
                assertions);
}
