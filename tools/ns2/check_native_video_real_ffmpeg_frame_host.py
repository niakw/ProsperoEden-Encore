#!/usr/bin/env python3
"""H05: execute the actual maintained Nx2VideoDecoder::Render on a real FFmpeg
encoded/decoded video frame, including guest NV12/RGBA bytes and negative bounds.

No console and no fabricated decoder output. The service/guest-fence lifecycle
still needs a separate executed-owner IPC witness before H05 can close.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/"vendor/encore-active/ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.cpp"
SERVICE=ROOT/"vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp"
SYNC_OWNER=ROOT/"vendor/encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp"
SYNC_HEADER=ROOT/"vendor/sources/eden/src/video_core/host1x/syncpoint_manager.h"
assert "void SyncpointManager::IncrementGuest(" in SYNC_OWNER.read_text()
assert "bool IsReadyGuest(u32 syncpoint_id, u32 expected_value) const" in SYNC_HEADER.read_text()
original=OWNER.read_text()
begin="bool Nx2VideoDecoder::Render("
end="\n}\n\n} // namespace Tegra::Host1x"
assert original.count(begin)==original.count(end)==1
real=begin+original.split(begin,1)[1].split(end,1)[0]+"\n}"
service=SERVICE.read_text()
assert "m_decoder->Render(frame.picture," in service
assert service.index("m_owner->WriteVideoSurface(next.id, *target, pixels)") < service.index(
    "syncpoints.IncrementGuest(m_syncpoint);")
assert "if (!m_decoder->Render(frame.picture," in service
GUEST_SURFACE=ROOT/"vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp"
surface_source=GUEST_SURFACE.read_text()
surface_begin="bool IGraphicsSupervisor::WriteVideoSurface("
surface_end="\n// 901 and 1001 are the SDK's video codec/server-context admission calls."
assert surface_source.count(surface_begin)==surface_source.count(surface_end)==1
surface_write=surface_begin+surface_source.split(surface_begin,1)[1].split(surface_end,1)[0]
assert "GetMemory().WriteBlock(" in surface_write
assert surface_write.index("GetMemory().WriteBlock(") < surface_write.index("system.GPU().InvalidateRegion(")
pump_start="void IGraphicsVideoDecoderSession::Pump() {"
pump_end="\nvoid IGraphicsVideoDecoderSession::SubmitInput("
assert service.count(pump_start)==service.count(pump_end)==1
pump=pump_start+service.split(pump_start,1)[1].split(pump_end,1)[0]

cpp=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <deque>
#include <limits>
#include <new>
#include <optional>
#include <set>
#include <memory>
#include <map>
#include <mutex>
#include <utility>
#include <span>
#include <vector>
#include <vulkan/vulkan.h>
#include "video_core/host1x/syncpoint_manager.h"
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/pixdesc.h>
#include <libswscale/swscale.h>
}
using u8=std::uint8_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
#define LOG_ERROR(...) ((void)0)
constexpr int HW_GPU=0;
namespace FFmpeg {
class Frame {
    AVFrame* frame;
public:
    explicit Frame(AVFrame* p):frame(p) {assert(frame);}
    ~Frame(){av_frame_free(&frame);}
    const AVFrame* GetFrame() const {return frame;}
};
}
namespace Tegra::Host1x {
struct Nx2Picture {
    u32 width{}, height{};
    u64 pts{};
    std::shared_ptr<FFmpeg::Frame> frame;
};
enum class Nx2PictureFormat : u32 {Nv12,Rgba8,Bgra8};
class Nx2VideoDecoder {
    struct Impl {
        SwsContext* scaler{};
        ~Impl(){sws_freeContext(scaler);}
    };
    std::unique_ptr<Impl> impl{std::make_unique<Impl>()};
public:
    bool Render(const Nx2Picture&, Nx2PictureFormat,u32,u32,u64,u64,std::span<u8>);
};
__REAL_OWNER__
} // namespace Tegra::Host1x

// Encode real planar pixels with FFmpeg's in-tree MPEG4 encoder; then decode
// the compressed packet with FFmpeg's genuine decoder. No fake AVFrame.
AVFrame* CodecRoundTrip() {
    const AVCodec* encoder=avcodec_find_encoder(AV_CODEC_ID_MPEG4);
    const AVCodec* decoder=avcodec_find_decoder(AV_CODEC_ID_MPEG4);
    assert(encoder && decoder);
    AVCodecContext* enc=avcodec_alloc_context3(encoder);
    assert(enc);
    enc->width=16; enc->height=16; enc->pix_fmt=AV_PIX_FMT_YUV420P;
    enc->time_base=AVRational{1,30}; enc->gop_size=1; enc->max_b_frames=0;
    assert(avcodec_open2(enc,encoder,nullptr)==0);
    AVFrame* input=av_frame_alloc();
    assert(input);
    input->format=AV_PIX_FMT_YUV420P;input->width=16;input->height=16;input->pts=1;
    assert(av_frame_get_buffer(input,32)==0);
    assert(av_frame_make_writable(input)==0);
    for(int y=0;y<16;++y)
        std::memset(input->data[0]+y*input->linesize[0],82,16);
    for(int y=0;y<8;++y){
        std::memset(input->data[1]+y*input->linesize[1],90,8);
        std::memset(input->data[2]+y*input->linesize[2],240,8);
    }
    assert(avcodec_send_frame(enc,input)==0);
    AVPacket* packet=av_packet_alloc();
    assert(packet);
    int ret=avcodec_receive_packet(enc,packet);
    if(ret==AVERROR(EAGAIN)){
        assert(avcodec_send_frame(enc,nullptr)==0);
        ret=avcodec_receive_packet(enc,packet);
    }
    assert(ret==0 && packet->size>0);
    AVCodecContext* dec=avcodec_alloc_context3(decoder);
    assert(dec && avcodec_open2(dec,decoder,nullptr)==0);
    assert(avcodec_send_packet(dec,packet)==0);
    AVFrame* output=av_frame_alloc();
    assert(output);
    ret=avcodec_receive_frame(dec,output);
    if(ret==AVERROR(EAGAIN)){
        assert(avcodec_send_packet(dec,nullptr)==0);
        ret=avcodec_receive_frame(dec,output);
    }
    assert(ret==0 && output->width==16 && output->height==16);
    assert(output->format==AV_PIX_FMT_YUV420P);
    av_frame_free(&input);
    av_packet_free(&packet);
    avcodec_free_context(&enc);
    avcodec_free_context(&dec);
    return output;
}

// A real host Vulkan command and VkFence drive guest release readiness.
// The decoder's production Pump, NVMap/guest memory and Host1x syncpoint
// owners remain source-extracted/compiled below. This is NOT a live PS5 TIPC.
class VulkanVideoRelease {
    VkInstance instance{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    VkBuffer buffer{};
    VkDeviceMemory memory{};
    VkCommandPool pool{};
    VkCommandBuffer command{};
    VkFence fence{};
    u32* mapped{};
public:
    VulkanVideoRelease() {
        VkApplicationInfo ai{}; ai.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;
        ai.apiVersion = VK_API_VERSION_1_1;
        VkInstanceCreateInfo ci{}; ci.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
        ci.pApplicationInfo = &ai;
        assert(vkCreateInstance(&ci,nullptr,&instance)==VK_SUCCESS);
        u32 count{};
        assert(vkEnumeratePhysicalDevices(instance,&count,nullptr)==VK_SUCCESS && count);
        std::vector<VkPhysicalDevice> devs(count);
        assert(vkEnumeratePhysicalDevices(instance,&count,devs.data())==VK_SUCCESS);
        u32 family{};
        bool found{};
        for(auto p:devs) {
            u32 queues{};
            vkGetPhysicalDeviceQueueFamilyProperties(p,&queues,nullptr);
            std::vector<VkQueueFamilyProperties> properties(queues);
            vkGetPhysicalDeviceQueueFamilyProperties(p,&queues,properties.data());
            for(u32 i=0;i<queues;++i) {
                if(properties[i].queueCount &&
                   (properties[i].queueFlags & VK_QUEUE_TRANSFER_BIT)) {
                    physical=p;family=i;found=true;break;
                }
            }
            if(found)break;
        }
        assert(found);
        const float priority=1.0f;
        VkDeviceQueueCreateInfo qi{}; qi.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
        qi.queueFamilyIndex=family;qi.queueCount=1;qi.pQueuePriorities=&priority;
        VkDeviceCreateInfo di{}; di.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
        di.queueCreateInfoCount=1;di.pQueueCreateInfos=&qi;
        assert(vkCreateDevice(physical,&di,nullptr,&device)==VK_SUCCESS);
        vkGetDeviceQueue(device,family,0,&queue);
        VkBufferCreateInfo bi{}; bi.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bi.size=sizeof(u32);bi.usage=VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        assert(vkCreateBuffer(device,&bi,nullptr,&buffer)==VK_SUCCESS);
        VkMemoryRequirements requirements{};
        vkGetBufferMemoryRequirements(device,buffer,&requirements);
        VkPhysicalDeviceMemoryProperties memory_properties{};
        vkGetPhysicalDeviceMemoryProperties(physical,&memory_properties);
        u32 type=memory_properties.memoryTypeCount;
        for(u32 i=0;i<memory_properties.memoryTypeCount;++i) {
            if((requirements.memoryTypeBits & (1U<<i)) &&
                (memory_properties.memoryTypes[i].propertyFlags &
                (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                 VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
                (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                 VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {type=i;break;}
        }
        assert(type<memory_properties.memoryTypeCount);
        VkMemoryAllocateInfo mai{}; mai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        mai.allocationSize=requirements.size;mai.memoryTypeIndex=type;
        assert(vkAllocateMemory(device,&mai,nullptr,&memory)==VK_SUCCESS);
        assert(vkBindBufferMemory(device,buffer,memory,0)==VK_SUCCESS);
        void* raw{};
        assert(vkMapMemory(device,memory,0,sizeof(u32),0,&raw)==VK_SUCCESS);
        mapped=static_cast<u32*>(raw);
        *mapped=0;
        VkCommandPoolCreateInfo pci{}; pci.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        pci.queueFamilyIndex=family;
        pci.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        assert(vkCreateCommandPool(device,&pci,nullptr,&pool)==VK_SUCCESS);
        VkCommandBufferAllocateInfo bai{}; bai.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        bai.commandPool=pool;bai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        bai.commandBufferCount=1;
        assert(vkAllocateCommandBuffers(device,&bai,&command)==VK_SUCCESS);
        VkFenceCreateInfo fi{}; fi.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        assert(vkCreateFence(device,&fi,nullptr,&fence)==VK_SUCCESS);
    }
    void Submit(u32 guest_release_value) {
        assert(vkResetCommandBuffer(command,0)==VK_SUCCESS);
        assert(vkResetFences(device,1,&fence)==VK_SUCCESS);
        VkCommandBufferBeginInfo begin{}; begin.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        assert(vkBeginCommandBuffer(command,&begin)==VK_SUCCESS);
        vkCmdFillBuffer(command,buffer,0,sizeof(u32),guest_release_value);
        VkBufferMemoryBarrier barrier{}; barrier.sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER;
        barrier.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
        barrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
        barrier.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        barrier.buffer=buffer;barrier.offset=0;barrier.size=sizeof(u32);
        vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_TRANSFER_BIT,
                             VK_PIPELINE_STAGE_HOST_BIT,0,0,nullptr,1,&barrier,0,nullptr);
        assert(vkEndCommandBuffer(command)==VK_SUCCESS);
        VkSubmitInfo info{}; info.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
        info.commandBufferCount=1;info.pCommandBuffers=&command;
        assert(vkQueueSubmit(queue,1,&info,fence)==VK_SUCCESS);
    }
    u32 Retire() {
        assert(vkWaitForFences(device,1,&fence,VK_TRUE,10000000000ULL)==VK_SUCCESS);
        return *mapped; // Coherent host buffer only after genuine VkFence.
    }
    ~VulkanVideoRelease() {
        if(device)vkDeviceWaitIdle(device);
        if(fence)vkDestroyFence(device,fence,nullptr);
        if(pool)vkDestroyCommandPool(device,pool,nullptr);
        if(mapped)vkUnmapMemory(device,memory);
        if(buffer)vkDestroyBuffer(device,buffer,nullptr);
        if(memory)vkFreeMemory(device,memory,nullptr);
        if(device)vkDestroyDevice(device,nullptr);
        if(instance)vkDestroyInstance(instance,nullptr);
    }
};

namespace Tegra::Texture {
// The RGB block-linear branch has a separate true round-trip witness.
// This test exercises a real decoded FFmpeg NV12 image through guest
// ownership, readiness and publication, without claiming GPU tiling.
std::size_t CalculateSize(bool,u32,u32,u32,u32,u32,u32) {return 0;}
void SwizzleTexture(std::vector<u8>&,const std::vector<u8>&,u32,u32,u32,u32,u32,u32) {}
}
namespace Common { struct ProcessAddress { u64 address; }; }
namespace Service::AM {
using GuestSyncpoints=Tegra::Host1x::SyncpointManager;
struct FakeHost1x {
    GuestSyncpoints sync;
    GuestSyncpoints& GetSyncpointManager(){return sync;}
};
struct FakeGPU {
    unsigned invalidations{};
    u64 address{};
    std::size_t bytes{};
    void InvalidateRegion(u64 addr,std::size_t n) {++invalidations;address=addr;bytes=n;}
};
struct FakeSystem {
    FakeHost1x host{};
    FakeGPU gpu{};
    FakeHost1x& Host1x(){return host;}
    FakeGPU& GPU(){return gpu;}
};
struct FakeSurface {
    struct Layout {
        std::size_t image_bytes{384};
        u32 cpu_kind{10};
        u32 row_bytes{16};
        u64 chroma_offset{256};
        bool nv12{true};
    } layout;
    u32 width{16},height{16};
    u32 image_id{9}; u64 backing{12},address{0x2000};
    bool gpu_mapped{};
};
using VideoSurface=FakeSurface;
struct VideoPoolView {u64 backing{};std::size_t offset{},size{};};
struct VideoPool {
    std::optional<VideoPoolView> view;
    std::optional<VideoPoolView> Lookup(u32 id){return id==9?view:std::nullopt;}
};
struct MemoryRecord {bool bound{};u64 guest_address{};std::size_t size{};};
struct NativeMemory {
    std::optional<MemoryRecord> record;
    std::optional<MemoryRecord> Get(u64 id){return id==12?record:std::nullopt;}
};
struct GuestMemory {
    bool valid{true},writable{true},throw_write{};
    std::vector<u8> bytes=std::vector<u8>(384,0xCC);
    unsigned writes{};
    bool IsValidVirtualAddressRange(Common::ProcessAddress a,std::size_t n){
        return valid&&a.address==0x2000&&n<=bytes.size();
    }
    bool WriteBlock(Common::ProcessAddress a,const u8* src,std::size_t n){
        if(throw_write)throw std::bad_alloc{};
        if(!writable||a.address!=0x2000||n>bytes.size())return false;
        std::memcpy(bytes.data(),src,n);
        ++writes;return true;
    }
};
struct KProcess {GuestMemory memory;GuestMemory& GetMemory(){return memory;}};
struct NvMapHandle {bool allocated{};u64 address{},d_address{};u32 session_id{};};
struct NvMapFile {
    std::optional<NvMapHandle> handle;
    const NvMapHandle* GetHandle(u64 id){return id==12&&handle?&*handle:nullptr;}
};
struct Session {KProcess* process{};};
struct ModuleContainer {
    NvMapFile nvmap;Session session;
    NvMapFile& GetNvMapFile(){return nvmap;}
    const Session* GetSession(u32 id)const{return id==34?&session:nullptr;}
};
struct NativeModule {ModuleContainer container;ModuleContainer& GetContainer(){return container;}};
struct Mapping {unsigned references{};};
struct IGraphicsSupervisor {
    std::mutex m_native_memory_mutex;
    VideoPool m_video_pools;
    NativeMemory m_native_memory;
    NativeModule module;
    KProcess process;
    NativeModule* m_native_module{&module};
    KProcess* m_process{&process};
    std::map<std::pair<u32,u32>,Mapping> m_video_mappings;
    FakeSystem& system;
    std::shared_ptr<FakeSurface> surface=std::make_shared<FakeSurface>();
    explicit IGraphicsSupervisor(FakeSystem& owner_system):system(owner_system) {
        m_video_pools.view=VideoPoolView{12,0,384};
        m_native_memory.record=MemoryRecord{true,0x2000,384};
        module.container.nvmap.handle=NvMapHandle{true,0x2000,0x9000,34};
        module.container.session.process=&process;
    }
    std::shared_ptr<FakeSurface> LookupVideoSurface(u32 id) {return id==9?surface:nullptr;}
    bool WriteVideoSurface(u32,const VideoSurface&,std::span<const u8>);
};
using FakeOwner=IGraphicsSupervisor;
__REAL_SURFACE_WRITE__
struct FakeReady {
    bool room{};
    unsigned notifications{};
    void SetRoom(bool v){room=v;}
    void Notify(){++notifications;}
};
class IGraphicsVideoDecoderSession {
public:
    static constexpr u32 NoSyncpoint=~u32{0};
    static constexpr std::size_t MaxFrames=16,MaxOutputs=128;
    struct ReleaseFence{u32 id{},value{};};
    struct AvailableImage{u32 id{};std::optional<ReleaseFence> release;};
    struct PendingPicture{Tegra::Host1x::Nx2Picture picture;bool eos{};};
    struct Output{u32 image{},width{},height{};u64 pts{};bool eos{};};
    FakeSystem system;
    std::shared_ptr<FakeOwner> m_owner=std::make_shared<FakeOwner>(system);
    std::shared_ptr<FakeReady> m_ready=std::make_shared<FakeReady>();
    std::unique_ptr<Tegra::Host1x::Nx2VideoDecoder> m_decoder{
        std::make_unique<Tegra::Host1x::Nx2VideoDecoder>()};
    std::deque<PendingPicture> m_pending;
    std::deque<AvailableImage> m_available;
    std::deque<Output> m_outputs;
    std::set<u32> m_registered,m_guest_owned;
    u32 m_syncpoint{5};
    bool m_started{true};
    void Pump();
};
__REAL_PUMP__
} // namespace Service::AM

int main(){
    using namespace Tegra::Host1x;
    auto frame=std::make_shared<FFmpeg::Frame>(CodecRoundTrip());
    const auto* f=frame->GetFrame();
    const Nx2Picture picture{16,16,123,frame};
    Nx2VideoDecoder dec;
    constexpr std::size_t luma=16*16;
    constexpr std::size_t size=luma+16*8;
    std::vector<u8> nv12(size+16,0xA5);
    assert(dec.Render(picture,Nx2PictureFormat::Nv12,16,16,16,luma,
                      std::span<u8>(nv12.data(),size)));
    for(int y=0;y<16;++y)
        for(int x=0;x<16;++x)
            assert(nv12[y*16+x]==f->data[0][y*f->linesize[0]+x]);
    for(int y=0;y<8;++y)
        for(int x=0;x<8;++x){
            assert(nv12[luma+y*16+x*2]==f->data[1][y*f->linesize[1]+x]);
            assert(nv12[luma+y*16+x*2+1]==f->data[2][y*f->linesize[2]+x]);
        }
    assert(std::all_of(nv12.begin()+size,nv12.end(),[](u8 x){return x==0xA5;}));
    constexpr std::size_t rgba_size=16*16*4;
    std::vector<u8> rgba(rgba_size+16,0xA5);
    assert(dec.Render(picture,Nx2PictureFormat::Rgba8,16,16,64,0,
                      std::span<u8>(rgba.data(),rgba_size)));
    assert(std::any_of(rgba.begin(),rgba.begin()+rgba_size,
                       [](u8 x){return x!=0xA5;}));
    assert(std::all_of(rgba.begin()+rgba_size,rgba.end(),
                       [](u8 x){return x==0xA5;}));
    std::vector<u8> invalid(size+16,0xEE);
    auto reject=[&](Nx2PictureFormat format,u32 width,u32 height,u64 pitch,
                    u64 chroma,std::size_t available){
        std::fill(invalid.begin(),invalid.end(),0xEE);
        assert(!dec.Render(picture,format,width,height,pitch,chroma,
                           std::span<u8>(invalid.data(),available)));
        assert(std::all_of(invalid.begin(),invalid.end(),
                           [](u8 x){return x==0xEE;}));
    };
    reject(Nx2PictureFormat::Nv12,16,16,15,luma,size);
    reject(Nx2PictureFormat::Nv12,16,16,16,luma-1,size);
    reject(Nx2PictureFormat::Nv12,16,16,16,luma,size-1);
    reject(Nx2PictureFormat::Rgba8,16,16,63,0,size);
    reject(Nx2PictureFormat::Nv12,0,16,16,luma,size);
    reject(Nx2PictureFormat::Nv12,16,16,
           static_cast<u64>(std::numeric_limits<int>::max())+1,0,size);
    std::puts("H05_REAL_FFMPEG_DECODED_FRAME_RENDER_PASS "
              "codec=MPEG4 pixels=FFmpeg decoded NV12=exact RGBA=converted "
              "oob_pitch_offset_size=refused guest_fence=not_exercised");
    // The ACTUAL maintained AM session Pump runs on real decoded pixels
    // and the exact GraphicsSupervisor guest-write owner. A real Vulkan
    // queue/fence now gates the release readiness, not a synthetic completion.
    VulkanVideoRelease release_gpu;
    using Service::AM::IGraphicsVideoDecoderSession;
    IGraphicsVideoDecoderSession session;
    session.m_registered.insert(9);
    session.m_pending.push_back({picture,true});
    session.m_available.push_back({8,{{7,99}}}); // blocked older image
    session.m_available.push_back({9,{{7,10}}}); // ready only at fence 10
    release_gpu.Submit(10); // actual vkCmdFillBuffer + vkQueueSubmit
    session.Pump(); // guest fence must not advance on submission alone
    assert(session.m_outputs.empty() && session.m_pending.size()==1);
    assert(session.system.host.sync.GetGuestSyncpointValue(5)==0 &&
           session.m_owner->process.memory.writes==0);
    assert(session.system.host.sync.GetGuestSyncpointValue(7)==0);
    const u32 completed_release = release_gpu.Retire();
    assert(completed_release==10);
    for(u32 i=0;i<completed_release;++i)
        session.system.host.sync.IncrementGuest(7);
    assert(session.system.host.sync.GetGuestSyncpointValue(7)==10);
    session.m_owner->process.memory.writable=false;
    session.Pump();
    assert(session.m_outputs.empty() && session.m_pending.size()==1 &&
           session.m_guest_owned.empty());
    assert(session.m_owner->process.memory.writes==0 && session.system.host.sync.GetGuestSyncpointValue(5)==0);
    session.m_owner->process.memory.writable=true;
    // Exercise the ACTUAL maintained Pump through a late host allocation
    // failure after metadata/guest ownership have already been staged.
    session.m_owner->process.memory.throw_write=true;
    session.Pump();
    assert(session.m_outputs.empty() && session.m_pending.size()==1 &&
           session.m_guest_owned.empty() && session.m_available.size()==2);
    assert(session.system.host.sync.GetGuestSyncpointValue(5)==0);
    session.m_owner->process.memory.throw_write=false;
    session.Pump();
    assert(session.m_owner->process.memory.writes==1 && session.system.host.sync.GetGuestSyncpointValue(5)==1);
    assert(session.system.gpu.invalidations==1 && session.system.gpu.address==0x9000 &&
           session.system.gpu.bytes==384);
    assert(session.m_outputs.size()==1 && session.m_outputs.front().image==9 &&
           session.m_outputs.front().pts==123 && session.m_outputs.front().eos);
    assert(session.m_pending.empty() && session.m_guest_owned.contains(9));
    assert(session.m_available.size()==1 && session.m_available.front().id==8);
    assert(session.m_owner->process.memory.bytes.size()==size);
    for(int y=0;y<16;++y)
       for(int x=0;x<16;++x)
          assert(session.m_owner->process.memory.bytes[y*16+x]==f->data[0][y*f->linesize[0]+x]);
    for(int y=0;y<8;++y)
       for(int x=0;x<8;++x) {
          assert(session.m_owner->process.memory.bytes[luma+y*16+2*x]==f->data[1][y*f->linesize[1]+x]);
          assert(session.m_owner->process.memory.bytes[luma+y*16+2*x+1]==f->data[2][y*f->linesize[2]+x]);
       }
    // An impossible guest image is retired without fabricating an output.
    session.m_pending.push_back({picture,false});
    release_gpu.Submit(99);
    session.Pump(); // blocked older image still cannot complete early
    assert(session.m_outputs.size()==1 && session.m_pending.size()==1);
    assert(session.system.host.sync.GetGuestSyncpointValue(5)==1);
    const u32 second_release = release_gpu.Retire();
    assert(second_release==99);
    for(u32 i=10;i<second_release;++i)
        session.system.host.sync.IncrementGuest(7);
    assert(session.system.host.sync.GetGuestSyncpointValue(7)==99);
    session.Pump();
    assert(session.m_outputs.size()==1 && session.m_pending.size()==1);
    assert(session.system.host.sync.GetGuestSyncpointValue(5)==1 &&
           session.m_available.empty());
    // A bad stride cannot write or acknowledge a pending guest frame.
    session.m_owner->surface->layout.row_bytes=14;
    session.m_available.push_back({9,std::nullopt});
    session.Pump();
    assert(session.m_pending.size()==1 && session.m_outputs.size()==1 &&
           session.system.host.sync.GetGuestSyncpointValue(5)==1);
    session.m_owner->surface->layout.row_bytes=16;
    session.Pump();
    assert(session.m_pending.empty() && session.m_outputs.size()==2 &&
           session.system.host.sync.GetGuestSyncpointValue(5)==2 && session.m_owner->process.memory.writes==2);
    assert(session.system.gpu.invalidations==2);
    std::puts("H05_REAL_FFMPEG_PUMP_OWNER_PASS decoded_nv12=exact "
              "blocked_release=held no_head_of_line=1 failed_write=rolled_back "
              "guest_syncpoint_real_owner_after_write=1 invalid_stride=no_completion "
              "dead_image=retired write_oom=rolled_back owner_nvmap_guest_write=1 real_host_vk_fence_to_guest_syncpoint=1 live_TIPC=not_exercised");
}
""".replace("__REAL_OWNER__",real).replace("__REAL_PUMP__",pump).replace("__REAL_SURFACE_WRITE__",surface_write)
compilers=list(dict.fromkeys(x for x in
    (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h05-ffmpeg-pixels-") as temp:
    src=Path(temp)/"render.cpp"
    src.write_text(cpp)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-Wno-unused-variable","-fsanitize=undefined",
                 "-fno-sanitize-recover=all",
                 "-I"+str(ROOT/"vendor/sources/eden/src"),
                 str(src),str(SYNC_OWNER),"-o",str(exe),
                 "-pthread","-lavcodec","-lavutil","-lswscale","-lvulkan"]
            built=subprocess.run(cmd,text=True,capture_output=True,
                                 timeout=75,env=os.environ.copy())
            assert built.returncode==0,(cc,built.stderr[-5000:])
            run=subprocess.run([str(exe)],text=True,capture_output=True,
                               timeout=25,env=os.environ.copy())
            assert run.returncode==0,(cc,run.stderr[-5000:])
            print(Path(cc).name,opt,run.stdout.strip(),flush=True)
