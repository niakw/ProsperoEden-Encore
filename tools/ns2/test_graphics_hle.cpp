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
