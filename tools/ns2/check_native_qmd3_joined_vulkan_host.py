#!/usr/bin/env python3
"""G10 joined host witness: extract actual GPFIFO Ampere QMD3 puller and
SEM_EXECUTE acquire owners, run through native QMD scheduler, a real Vulkan
vkCmdDispatch/VkFence and a second guest channel.

The Vulkan shader/pipeline and guest GMMU/GPFIFO worker are host fixtures,
not actual translated guest Ampere code or the production PS5 rasterizer.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch"
text=(NATIVE/"video_core/engines/puller.cpp").read_text()
dma_source=(ROOT/"vendor/encore-active/eden-core/src/video_core/dma_pusher.cpp").read_text()
def dma_owner(begin,end):
    assert dma_source.count(begin)==1 and end in dma_source.split(begin,1)[1]
    return begin+dma_source.split(begin,1)[1].split(end,1)[0]
dma_dispatch=dma_owner("void DmaPusher::DispatchCalls() {","\nbool DmaPusher::Step() {")
dma_step=dma_owner("bool DmaPusher::Step() {","\nvoid DmaPusher::ProcessCommands(")
def owner(begin,end):
    assert text.count(begin)==1 and end in text.split(begin,1)[1],(begin,end)
    return begin+text.split(begin,1)[1].split(end,1)[0]

qmd_call=owner("void Puller::ProcessNativeComputeQmd(DmaPusher& pusher,",
               "\nvoid Puller::ProcessNativeComputeQmdAt(")
qmd_dispatch=owner("void Puller::ProcessNativeComputeQmdAt(",
                   "\n/// Calls a GPU engine method.")
semaphores=owner("struct CoherentNativeSemaphoreValue {",
                 "void Puller::ProcessSemaphoreAcquire(")
assert "pusher.rasterizer->DispatchNativeCompute(*launch)" in qmd_dispatch
assert "pusher.rasterizer->SignalFence(" in qmd_dispatch
assert "NativeGpuChannelRegistry::Instance()" in qmd_dispatch
assert "ProcessNativeSemaphoreExecute" in semaphores
assert "pending_native_acquire.reset();" in semaphores

cpp=r"""
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <queue>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <exception>
#include <functional>
#include <memory>
#include <mutex>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include <vulkan/vulkan.h>
#include "video_core/native_qmd.h"
#include "video_core/engines/native_ampere_semaphore.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
using GPUVAddr=u64;
using namespace Tegra::Engines;
[[maybe_unused]] constexpr int HW_GPU=0;
#define LOG_ERROR(...) ((void)0)
namespace Eden {
inline std::exception_ptr fatal{};
void RecordGpuFailure(std::exception_ptr why){fatal=why;}
std::exception_ptr PeekGpuFailure(){return fatal;}
}
struct MemoryManager {
    Tegra::NativeQmdScheduler::Descriptor qmd{};
    u32 guest{},replacement{777};
    bool qmd_mapped{true},program_mapped{true},release_mapped{true},remapped{};
    unsigned writes{};
    bool IsMemoryDirty(u64,std::size_t)const{return false;}
    bool IsFullyMappedRange(GPUVAddr address,std::size_t length)const {
        if(address==0x2000 && length==sizeof(qmd))return qmd_mapped;
        if(address==0x5000 && length==16)return program_mapped;
        if(address==0x4000 && length==4)return release_mapped;
        return false;
    }
    std::optional<u64> GpuToCpuAddress(GPUVAddr addr,std::size_t len)const {
        return IsFullyMappedRange(addr,len) && addr==0x4000
            ?std::optional<u64>{0x9000}:std::nullopt;
    }
    void ReadBlock(u64 address,void* out,std::size_t size)const {
        if(!IsFullyMappedRange(address,size))throw std::runtime_error("QMD unmapped");
        std::memcpy(out,qmd.data(),size);
    }
    u32* GetPointer(u64 addr) {
        return IsFullyMappedRange(addr,sizeof(u32)) && addr==0x4000
           ?(remapped?&replacement:&guest):nullptr;
    }
    template<class T>T Read(u64 addr) {
        if(!GetPointer(addr))throw std::runtime_error("unmapped guest read");
        return static_cast<T>(guest);
    }
    template<class T>void Write(u64 addr,T value) {
        if(!GetPointer(addr))throw std::runtime_error("unmapped guest write");
        ++writes;guest=static_cast<u32>(value);
    }
};
struct ComputeEngine {
    struct Regs{std::array<u32,0x1000> reg_array{};}regs;
    u64 epoch{};
};
struct Payload{ComputeEngine kepler_compute;};
struct ChannelState {
    std::shared_ptr<Payload> payload=std::make_shared<Payload>();
    u64 epoch{};
};
namespace Service::Nvidia::Devices {
struct NativeGpuChannelRegistry {
    struct Ticket {
        const void* process{};
        u64 generation{},channel_generation{};
    };
    inline static int native_process=1;
    std::shared_ptr<Tegra::NativeQmdSession> qmd=
        std::make_shared<Tegra::NativeQmdSession>();
    static NativeGpuChannelRegistry& Instance() {
        static NativeGpuChannelRegistry registry;return registry;
    }
    std::optional<Ticket> CaptureTicket(const ChannelState* c)const {
        if(!c || !c->epoch)return {};
        return Ticket{&native_process,7,c->epoch};
    }
    std::optional<Ticket> CaptureComputeTicket(const ComputeEngine* e)const {
        if(!e || !e->epoch)return {};
        return Ticket{&native_process,7,e->epoch};
    }
    bool IsNative(const ChannelState* c)const{
        return CaptureTicket(c).has_value();
    }
    bool IsCurrent(const ChannelState* c,Ticket t)const {
        const auto now=CaptureTicket(c);
        return now && now->process==t.process &&
               now->generation==t.generation &&
               now->channel_generation==t.channel_generation;
    }
    bool IsComputeCurrent(const ComputeEngine* e,Ticket t)const {
        const auto now=CaptureComputeTicket(e);
        return now && now->process==t.process &&
               now->generation==t.generation &&
               now->channel_generation==t.channel_generation;
    }
    std::shared_ptr<Tegra::NativeQmdSession>
    AcquireNativeQmdSession(const ChannelState* c){
        return CaptureTicket(c)?qmd:nullptr;
    }
};
}
namespace VideoCommon {
enum class CacheType{BufferCache};
enum class QueryType{Payload};
enum class QueryPropertiesFlags{IsAFence};
}
namespace Tegra {
struct CommandHeader{u32 kind{},argument{};};
namespace Memory {
enum class GuestMemoryFlags{SafeRead,UnsafeRead};
template<class T,GuestMemoryFlags>
struct GpuGuestMemory{
    std::vector<T> values;
    GpuGuestMemory(MemoryManager&,u64,size_t count,std::vector<T>*):values(count){}
    const T* data()const{return values.data();}
    size_t size()const{return values.size();}
};
}
namespace Engines{enum class EngineTypes{KeplerCompute,Maxwell3D};}
}
namespace Engines=Tegra::Engines;
using CommandHeader=Tegra::CommandHeader;
struct CommandListHeader{u64 addr{};size_t size{};bool sync{};};
struct CommandList{
    std::vector<CommandHeader> prefetch_command_list;
    std::vector<CommandListHeader> command_lists;
};
struct EngineAdapter{bool current_dirty{};};
constexpr u32 ComputeInline=0x50,MacroRegistersStart=0x100;
namespace Settings {
bool IsDMALevelDefault(){return false;}
bool IsGPULevelHigh(){return true;}
bool IsDMALevelSafe(){return true;}
struct Flag{bool GetValue()const{return false;}};
struct Values{Flag sync_memory_operations;};
inline Values values;
}
namespace Service::Nvidia::Devices {
template<class Mapped>bool NativeGpfifoFetchMapped(u64 addr,u64 words,Mapped&& mapped){
    return words<=0x10000 && mapped(addr,words*sizeof(u32));
}
}
struct FakeGpuWorker {
    unsigned flushes{},ends{};
    void FlushCommands(){++flushes;}
    void OnCommandListEnd(){++ends;}
};
struct FakeSystem {
    FakeGpuWorker gpu{};
    bool IsPoweredOn()const{return true;}
    bool IsShuttingDown()const{return false;}
    FakeGpuWorker& GPU(){return gpu;}
}
class VulkanCompute {
    VkInstance instance{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    VkPipelineLayout pipeline_layout{};
    VkShaderModule module{};
    VkPipeline pipeline{};
    VkCommandPool pool{};
    VkCommandBuffer command{};
    VkFence fence{};
public:
    VulkanCompute() {
        VkApplicationInfo ai{};ai.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;
        ai.apiVersion=VK_API_VERSION_1_1;
        VkInstanceCreateInfo ici{};ici.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
        ici.pApplicationInfo=&ai;
        assert(vkCreateInstance(&ici,nullptr,&instance)==VK_SUCCESS);
        u32 count{};
        assert(vkEnumeratePhysicalDevices(instance,&count,nullptr)==VK_SUCCESS&&count);
        std::vector<VkPhysicalDevice> devices(count);
        assert(vkEnumeratePhysicalDevices(instance,&count,devices.data())==VK_SUCCESS);
        u32 family{};bool found{};
        for(auto p:devices){
            u32 q{};vkGetPhysicalDeviceQueueFamilyProperties(p,&q,nullptr);
            std::vector<VkQueueFamilyProperties> props(q);
            vkGetPhysicalDeviceQueueFamilyProperties(p,&q,props.data());
            for(u32 i=0;i<q;++i)
                if(props[i].queueCount && (props[i].queueFlags & VK_QUEUE_COMPUTE_BIT)){
                    physical=p;family=i;found=true;break;
                }
            if(found)break;
        }
        assert(found);
        const float priority=1.f;
        VkDeviceQueueCreateInfo qi{};qi.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
        qi.queueFamilyIndex=family;qi.queueCount=1;qi.pQueuePriorities=&priority;
        VkDeviceCreateInfo di{};di.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
        di.queueCreateInfoCount=1;di.pQueueCreateInfos=&qi;
        assert(vkCreateDevice(physical,&di,nullptr,&device)==VK_SUCCESS);
        vkGetDeviceQueue(device,family,0,&queue);
        // A genuine compute VkPipeline, but a bounded empty host shader:
        // no pretense this is the real translated guest Ampere program.
        static constexpr std::array<u32,35> spirv{
            0x07230203,0x00010000,0,6,0,
            0x00020011,1,
            0x0003000e,0,1,
            0x0005000f,5,4,0x6e69616d,0,
            0x00060010,4,17,1,1,1,
            0x00020013,2,
            0x00030021,3,2,
            0x00050036,2,4,0,3,
            0x000200f8,5,
            0x000100fd,
            0x00010038
        };
        VkShaderModuleCreateInfo sm{};sm.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        sm.codeSize=spirv.size()*sizeof(u32);sm.pCode=spirv.data();
        assert(vkCreateShaderModule(device,&sm,nullptr,&module)==VK_SUCCESS);
        VkPipelineLayoutCreateInfo li{};li.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        assert(vkCreatePipelineLayout(device,&li,nullptr,&pipeline_layout)==VK_SUCCESS);
        VkComputePipelineCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
        ci.stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        ci.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;
        ci.stage.module=module;ci.stage.pName="main";
        ci.layout=pipeline_layout;
        assert(vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&ci,nullptr,&pipeline)==VK_SUCCESS);
        VkCommandPoolCreateInfo pi{};pi.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        pi.queueFamilyIndex=family;
        pi.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        assert(vkCreateCommandPool(device,&pi,nullptr,&pool)==VK_SUCCESS);
        VkCommandBufferAllocateInfo alloc{};alloc.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        alloc.commandPool=pool;alloc.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        alloc.commandBufferCount=1;
        assert(vkAllocateCommandBuffers(device,&alloc,&command)==VK_SUCCESS);
        VkFenceCreateInfo fi{};fi.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        assert(vkCreateFence(device,&fi,nullptr,&fence)==VK_SUCCESS);
    }
    bool Submit(const Tegra::NativeComputeLaunch& launch){
        assert((launch.program_address==0x5000 && launch.grid==std::array<u32,3>{1,1,1}));
        assert(vkResetCommandBuffer(command,0)==VK_SUCCESS);
        assert(vkResetFences(device,1,&fence)==VK_SUCCESS);
        VkCommandBufferBeginInfo bi{};bi.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        assert(vkBeginCommandBuffer(command,&bi)==VK_SUCCESS);
        vkCmdBindPipeline(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
        vkCmdDispatch(command,launch.grid[0],launch.grid[1],launch.grid[2]);
        assert(vkEndCommandBuffer(command)==VK_SUCCESS);
        VkSubmitInfo submit{};submit.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
        submit.commandBufferCount=1;submit.pCommandBuffers=&command;
        return vkQueueSubmit(queue,1,&submit,fence)==VK_SUCCESS;
    }
    void Retire(){
        assert(vkWaitForFences(device,1,&fence,VK_TRUE,10000000000ULL)==VK_SUCCESS);
    }
    ~VulkanCompute(){
        if(device)vkDeviceWaitIdle(device);
        if(fence)vkDestroyFence(device,fence,nullptr);
        if(pool)vkDestroyCommandPool(device,pool,nullptr);
        if(pipeline)vkDestroyPipeline(device,pipeline,nullptr);
        if(module)vkDestroyShaderModule(device,module,nullptr);
        if(pipeline_layout)vkDestroyPipelineLayout(device,pipeline_layout,nullptr);
        if(device)vkDestroyDevice(device,nullptr);
        if(instance)vkDestroyInstance(instance,nullptr);
    }
};
struct Rasterizer {
    VulkanCompute vulkan;
    std::function<void()> callback;
    unsigned dispatches{},fences{},flushes{};
    bool dirty{};
    bool DispatchNativeCompute(const Tegra::NativeComputeLaunch& launch){
        if(callback)return false;
        if(!vulkan.Submit(launch))return false;
        ++dispatches;
        return true;
    }
    void SignalFence(std::function<void()> done){
        assert(!callback);callback=std::move(done);++fences;
    }
    void Retire(){
        vulkan.Retire();
        auto fn=std::move(callback);
        callback={};
        if(fn)fn();
        dirty=true;
    }
    bool MustFlushRegion(u64 cpu,std::size_t size,VideoCommon::CacheType)const{
        assert(cpu==0x9000&&size==4);
        return dirty;
    }
    void FlushRegion(u64 cpu,std::size_t size,VideoCommon::CacheType){
        assert(cpu==0x9000&&size==4);
        dirty=false;++flushes;
    }
    void ReleaseFences(){}
    void Query(u64,VideoCommon::QueryType,VideoCommon::QueryPropertiesFlags,u32,u32){}
};
struct Puller;
struct DmaPusher {
    struct DmaState{
        bool is_last_call{},non_incrementing{};
        u64 dma_get{};
        u32 subchannel{},method_count{},method{};
    };
    FakeSystem system;
    ChannelState channel_state;
    MemoryManager& memory_manager;
    Rasterizer* rasterizer{};
    Puller* active_puller{};
    std::queue<CommandList> dma_pushbuffer;
    std::array<EngineAdapter*,8> subchannels{};
    std::array<Engines::EngineTypes,8> subchannel_type{};
    std::vector<CommandHeader> command_headers;
    DmaState dma_state;
    bool ib_enable{true},signal_sync{},synced{};
    std::mutex sync_mutex;
    std::condition_variable sync_cv;
    size_t dma_pushbuffer_subindex{},command_resume_offset{};
    DmaPusher(MemoryManager& m,Rasterizer* r,u64 epoch)
      :channel_state{},memory_manager(m),rasterizer(r){
        channel_state.epoch=epoch;
        channel_state.payload->kepler_compute.epoch=epoch;
    }
    bool ResumeNativeAcquire();
    bool HasPendingNativeAcquire()const;
    void ProcessCommands(std::span<const CommandHeader>);
    bool Step();
    void DispatchCalls();
};
struct Puller {
    struct Regs{std::array<u32,64> reg_array{};}regs;
    struct PendingNativeAcquire {
        GPUVAddr address{};u32 value{},operation{};u64 cpu_address{};
        const void* process{};
        u64 process_generation{},channel_generation{};
    };
    std::optional<PendingNativeAcquire> pending_native_acquire;
    bool ResumeNativeAcquire(DmaPusher&);
    void ProcessNativeSemaphoreExecute(DmaPusher&,u32);
    void ProcessNativeComputeQmd(DmaPusher&,u32,u32,u32);
    void ProcessNativeComputeQmdAt(DmaPusher&,GPUVAddr,u32,u32,u32);
};
__REAL_SEMAPHORES__
__REAL_QMD_CALL__
__REAL_QMD_DISPATCH__
__REAL_DMA_DISPATCH__
__REAL_DMA_STEP__
bool DmaPusher::ResumeNativeAcquire(){
    return !active_puller || active_puller->ResumeNativeAcquire(*this);
}
bool DmaPusher::HasPendingNativeAcquire()const{
    return active_puller && active_puller->pending_native_acquire.has_value();
}
void DmaPusher::ProcessCommands(std::span<const CommandHeader> commands){
    assert(active_puller);
    for(const auto& command:commands){
        if(command.kind==1)
            active_puller->ProcessNativeComputeQmd(*this,0xb0,command.argument,0);
        else if(command.kind==2)
            active_puller->ProcessNativeSemaphoreExecute(*this,command.argument);
        else
            throw std::runtime_error("host GPFIFO header unknown");
        ++command_resume_offset;
        if(HasPendingNativeAcquire())return;
    }
}
int main(){
    MemoryManager memory;
    memory.qmd[12]=1;memory.qmd[13]=1;memory.qmd[14]=1;
    memory.qmd[18]=0x30U | (1U<<16);
    memory.qmd[19]=1U | (1U<<16);
    memory.qmd[48]=0x5000;
    memory.qmd[24]=0x4000;
    memory.qmd[25]=(1U<<23)|(1U<<30);
    memory.qmd[26]=17;
    Rasterizer gpu;
    DmaPusher producer{memory,&gpu,41},consumer{memory,&gpu,42};
    Puller qmd_puller,wait_puller;
    producer.active_puller=&qmd_puller;
    consumer.active_puller=&wait_puller;
    producer.channel_state.payload->kepler_compute.regs.reg_array[0xad]=0x20;
    wait_puller.regs.reg_array[0x17]=0x4000;
    wait_puller.regs.reg_array[0x18]=0;
    wait_puller.regs.reg_array[0x19]=17;
    // A malformed or unmapped release refuses before any Vulkan shader.
    memory.release_mapped=false;
    bool rejected=false;
    try{qmd_puller.ProcessNativeComputeQmd(producer,0xb0,3,0);}
    catch(const std::runtime_error&){rejected=true;}
    assert(rejected && gpu.dispatches==0 && memory.writes==0);
    memory.release_mapped=true;
    // Real DmaPusher::DispatchCalls and Step own both GPFIFO prefetch
    // queues. Only the method-word decoder is a host adapter.
    CommandList launch;
    launch.prefetch_command_list.push_back({1,3});
    producer.dma_pushbuffer.push(std::move(launch));
    producer.DispatchCalls();
    assert(producer.dma_pushbuffer.empty() && producer.system.gpu.ends==1 &&
           gpu.dispatches==1 && gpu.fences==1 &&
           memory.guest==0 && memory.writes==0);
    CommandList acquire;
    acquire.prefetch_command_list.push_back({2,0});
    consumer.dma_pushbuffer.push(std::move(acquire));
    consumer.DispatchCalls();
    assert(wait_puller.pending_native_acquire &&
           consumer.dma_pushbuffer.size()==1 &&
           consumer.command_resume_offset==1 &&
           !wait_puller.ResumeNativeAcquire(consumer));
    // Duplicate PCAS must not dispatch or publish a second release.
    qmd_puller.ProcessNativeComputeQmd(producer,0xb0,2,0);
    assert(gpu.dispatches==1 && gpu.fences==1 && memory.guest==0);
    gpu.Retire(); // genuine VkFence after real vkCmdDispatch, not synthetic
    consumer.DispatchCalls(); // same real GPFIFO Step resumes and retires
    assert(memory.guest==17 && memory.writes==1 &&
           consumer.dma_pushbuffer.empty() &&
           !wait_puller.pending_native_acquire && !Eden::fatal);
    // Reject an unsupported real PCAS action without a host submission.
    rejected=false;
    try{qmd_puller.ProcessNativeComputeQmd(producer,0xb0,6,0);}
    catch(const std::runtime_error&){rejected=true;}
    assert(rejected && gpu.dispatches==1 && memory.writes==1);
    // Backing replacement after an accepted real dispatch must latch a
    // native failure, leave the original guest release untouched.
    memory.qmd[26]=18;
    qmd_puller.ProcessNativeComputeQmd(producer,0xb0,3,0);
    assert(gpu.dispatches==2 && memory.guest==17);
    memory.remapped=true;
    gpu.Retire();
    assert(Eden::fatal && memory.guest==17 && memory.writes==1 &&
           memory.replacement==777);
    Eden::fatal=nullptr;memory.remapped=false;
    // A retired GPFIFO epoch must not write to a replacement guest channel.
    memory.qmd[26]=19;
    qmd_puller.ProcessNativeComputeQmd(producer,0xb0,3,0);
    assert(gpu.dispatches==3);
    ++producer.channel_state.epoch;
    ++producer.channel_state.payload->kepler_compute.epoch;
    gpu.Retire();
    assert(memory.guest==17 && memory.writes==1 && !Eden::fatal);
    wait_puller.regs.reg_array[0x19]=19;
    wait_puller.ProcessNativeSemaphoreExecute(consumer,0);
    assert(wait_puller.pending_native_acquire &&
           !wait_puller.ResumeNativeAcquire(consumer));
    std::puts("G10_JOINED_REAL_QMD3_PULLER_VULKAN_SEM_PASS"
              " qmd_pcas_owner=real compute_launch_owner=real"
              " native_semaphore_owner=real VkCmdDispatch=1 VkFence=retired"
              " guest_release_after_fence=1 cross_channel_acquire=1"
              " unmapped_release=refused duplicate_pcas=held"
              " unsupported_pcas=refused backing_reuse=latched"
              " revoked_epoch=no_completion"
              " real_dma_step_dispatchcalls=1 prefetch_queue_retired_after_fence=1"
              " host_shader_and_command_decoder_stubs=1 PS5=not_exercised");
}
"""
cpp=cpp.replace("__REAL_SEMAPHORES__",semaphores)
cpp=cpp.replace("__REAL_QMD_CALL__",qmd_call)
cpp=cpp.replace("__REAL_QMD_DISPATCH__",qmd_dispatch)
cpp=cpp.replace("__REAL_DMA_DISPATCH__",dma_dispatch)
cpp=cpp.replace("__REAL_DMA_STEP__",dma_step)
env=dict(os.environ)
icd=Path("/usr/share/vulkan/icd.d/lvp_icd.x86_64.json")
if icd.is_file():
    env["VK_ICD_FILENAMES"]=str(icd)
    env["LP_NUM_THREADS"]="2"
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-g10-qmd-vulkan-joined-") as tmp:
    src=Path(tmp)/"joined.cpp";src.write_text(cpp)
    for compiler in compilers:
        exe=Path(tmp)/(Path(compiler).name.replace("+","p"))
        cmd=[compiler,"-std=c++20","-O1","-DPS5_NATIVE=1",
             "-Wall","-Wextra","-Werror","-Wno-unused-parameter",
             "-pthread","-I"+str(NATIVE),str(src),"-o",str(exe),"-lvulkan"]
        result=subprocess.run(cmd,text=True,capture_output=True,timeout=80,env=env)
        assert result.returncode==0,(compiler,result.stderr[-7000:])
        run=subprocess.run([str(exe)],text=True,capture_output=True,timeout=45,env=env)
        assert run.returncode==0,(compiler,run.stdout[-2000:],run.stderr[-5500:])
        print(Path(compiler).name,run.stdout.strip(),flush=True)
