#!/usr/bin/env python3
"""G10: real Vulkan fence retirement across actual Ampere SEM_EXECUTE owners.

Source-extracted maintained puller is executed with two independent channels.
The release is implemented as a real vkCmdFillBuffer + vkQueueSubmit + VkFence
against a coherent guest semaphore word, not a synthetic CompleteGpuFence().
This DOES NOT execute native QMD3 nor prove PS5 guest queue completion.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch"
source=(NATIVE/"video_core/engines/puller.cpp").read_text()
start="struct CoherentNativeSemaphoreValue {"
stop="void Puller::ProcessSemaphoreAcquire("
assert source.count(start)==source.count(stop)==1
owner=start+source.split(start,1)[1].split(stop,1)[0]
for needle in ("bool Puller::ResumeNativeAcquire(",
               "void Puller::ProcessNativeSemaphoreExecute(",
               "pusher.rasterizer->Query(", "ReadCoherentNativeSemaphore("):
    assert needle in owner,needle
fixture=r"""
#include <vulkan/vulkan.h>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <chrono>
#include <thread>
#include <cstdlib>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>
#include "video_core/engines/native_ampere_semaphore.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
using GPUVAddr=u64;
using namespace Tegra::Engines;
static void Check(bool ok,const char* why) {
    if(!ok){std::fprintf(stderr,"G10 host Vulkan: %s\n",why);std::exit(1);}
}
class VulkanGuestWord {
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
    VulkanGuestWord() {
        VkApplicationInfo ai{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        ai.apiVersion=VK_API_VERSION_1_1;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo=&ai;
        VkResult instance_status = VK_ERROR_INITIALIZATION_FAILED;
        for (unsigned attempt = 0; attempt < 5; ++attempt) {
            instance_status = vkCreateInstance(&ici, nullptr, &instance);
            if (instance_status == VK_SUCCESS) break;
            std::fprintf(stderr,
                         "G10 Vulkan loader transient: vkCreateInstance=%d attempt=%u\n",
                         static_cast<int>(instance_status), attempt + 1);
            // A concurrent Vulkan host qualification may transiently exhaust
            // the runner's resources. An unsupported ICD is NOT retryable.
            if (instance_status != VK_ERROR_OUT_OF_HOST_MEMORY &&
                instance_status != VK_ERROR_INITIALIZATION_FAILED) break;
            std::this_thread::sleep_for(std::chrono::milliseconds(400 * (attempt + 1)));
        }
        Check(instance_status == VK_SUCCESS, "instance");
        u32 n{};
        Check(vkEnumeratePhysicalDevices(instance,&n,nullptr)==VK_SUCCESS&&n,"device count");
        std::vector<VkPhysicalDevice> devs(n);
        Check(vkEnumeratePhysicalDevices(instance,&n,devs.data())==VK_SUCCESS,"devices");
        u32 family=0;
        bool found=false;
        for(auto dev:devs) {
            u32 count{};
            vkGetPhysicalDeviceQueueFamilyProperties(dev,&count,nullptr);
            std::vector<VkQueueFamilyProperties> queues(count);
            vkGetPhysicalDeviceQueueFamilyProperties(dev,&count,queues.data());
            for(u32 i=0;i<count;++i)
                if(queues[i].queueCount &&
                    (queues[i].queueFlags & VK_QUEUE_TRANSFER_BIT)) {
                    physical=dev;family=i;found=true;break;
                }
            if(found)break;
        }
        Check(found,"no Vulkan transfer queue");
        float priority=1.f;
        VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qci.queueFamilyIndex=family;qci.queueCount=1;qci.pQueuePriorities=&priority;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount=1;dci.pQueueCreateInfos=&qci;
        Check(vkCreateDevice(physical,&dci,nullptr,&device)==VK_SUCCESS,"VkDevice");
        vkGetDeviceQueue(device,family,0,&queue);
        VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bi.size=4;bi.usage=VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        Check(vkCreateBuffer(device,&bi,nullptr,&buffer)==VK_SUCCESS,"buffer");
        VkMemoryRequirements req{};
        vkGetBufferMemoryRequirements(device,buffer,&req);
        VkPhysicalDeviceMemoryProperties props{};
        vkGetPhysicalDeviceMemoryProperties(physical,&props);
        u32 type=props.memoryTypeCount;
        for(u32 i=0;i<props.memoryTypeCount;++i)
            if((req.memoryTypeBits&(1U<<i)) &&
               (props.memoryTypes[i].propertyFlags &
               (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
               (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)){
                type=i;break;
            }
        Check(type<props.memoryTypeCount,"coherent guest word not supported");
        VkMemoryAllocateInfo mai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        mai.allocationSize=req.size;mai.memoryTypeIndex=type;
        Check(vkAllocateMemory(device,&mai,nullptr,&memory)==VK_SUCCESS,"allocate");
        Check(vkBindBufferMemory(device,buffer,memory,0)==VK_SUCCESS,"bind");
        void* raw{};
        Check(vkMapMemory(device,memory,0,4,0,&raw)==VK_SUCCESS,"map");
        mapped=static_cast<u32*>(raw);*mapped=2;
        VkCommandPoolCreateInfo cpci{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        cpci.queueFamilyIndex=family;
        cpci.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        Check(vkCreateCommandPool(device,&cpci,nullptr,&pool)==VK_SUCCESS,"command pool");
        VkCommandBufferAllocateInfo cbai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        cbai.commandPool=pool;cbai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        cbai.commandBufferCount=1;
        Check(vkAllocateCommandBuffers(device,&cbai,&command)==VK_SUCCESS,"command");
        VkFenceCreateInfo fi{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        Check(vkCreateFence(device,&fi,nullptr,&fence)==VK_SUCCESS,"fence");
    }
    u32 Get() const{return *mapped;}
    void FillAndRetire(u32 value) {
        Check(vkResetCommandBuffer(command,0)==VK_SUCCESS,"reset command");
        VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        Check(vkBeginCommandBuffer(command,&begin)==VK_SUCCESS,"begin");
        vkCmdFillBuffer(command,buffer,0,4,value);
        VkBufferMemoryBarrier barrier{VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER};
        barrier.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
        barrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
        barrier.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        barrier.buffer=buffer;barrier.offset=0;barrier.size=4;
        vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_TRANSFER_BIT,
                             VK_PIPELINE_STAGE_HOST_BIT,0,0,nullptr,1,&barrier,0,nullptr);
        Check(vkEndCommandBuffer(command)==VK_SUCCESS,"end");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount=1;si.pCommandBuffers=&command;
        Check(vkQueueSubmit(queue,1,&si,fence)==VK_SUCCESS,"submit");
        Check(vkWaitForFences(device,1,&fence,VK_TRUE,10000000000ULL)==VK_SUCCESS,
              "real GPU fence retirement");
        Check(vkResetFences(device,1,&fence)==VK_SUCCESS,"reset fence");
    }
    ~VulkanGuestWord() {
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
namespace VideoCommon {
enum class QueryType {Payload};
enum class QueryPropertiesFlags {IsAFence};
enum class CacheType {BufferCache};
}
struct MemoryManager {
    VulkanGuestWord& guest;
    bool mapped{true};
    bool cpu_alias{true};
    bool IsFullyMappedRange(GPUVAddr address,std::size_t bytes) const {
        return mapped && address==0x1000 && bytes==4;
    }
    std::optional<u64> GpuToCpuAddress(GPUVAddr address,std::size_t bytes) const {
        return cpu_alias && IsFullyMappedRange(address,bytes)
            ?std::optional<u64>{0x9000}:std::nullopt;
    }
    template<class T> T Read(GPUVAddr address) const {
        Check(IsFullyMappedRange(address,sizeof(T)),"guest semaphore read");
        return static_cast<T>(guest.Get());
    }
};
struct Rasterizer {
    VulkanGuestWord& guest;
    std::optional<u32> pending_value;
    bool dirty{};
    unsigned queries{},flushes{},release_fences{};
    void Query(GPUVAddr addr,VideoCommon::QueryType type,
               VideoCommon::QueryPropertiesFlags flags,u32 value,u32) {
        assert(addr==0x1000 && type==VideoCommon::QueryType::Payload &&
               flags==VideoCommon::QueryPropertiesFlags::IsAFence);
        assert(!pending_value);
        pending_value=value;++queries;
    }
    void CompleteQueuedVulkanWork() {
        assert(pending_value);
        guest.FillAndRetire(*pending_value);
        pending_value.reset();
        dirty=true;
    }
    bool MustFlushRegion(u64 addr,std::size_t size,VideoCommon::CacheType) {
        assert(addr==0x9000 && size==4);return dirty;
    }
    void FlushRegion(u64 addr,std::size_t size,VideoCommon::CacheType) {
        assert(addr==0x9000 && size==4);dirty=false;++flushes;
    }
    void ReleaseFences(){++release_fences;}
};
struct DmaPusher{
    MemoryManager& memory_manager;
    Rasterizer* rasterizer{};
};
struct Puller{
    struct Regs{std::array<u32,64> reg_array{};} regs;
    struct PendingNativeAcquire{GPUVAddr address{};u32 value{},operation{};u64 cpu_address{};};
    std::optional<PendingNativeAcquire> pending_native_acquire{};
    bool ResumeNativeAcquire(DmaPusher&);
    void ProcessNativeSemaphoreExecute(DmaPusher&,u32);
};
__REAL_OWNER__
int main() {
    VulkanGuestWord guest;
    MemoryManager memory{guest};
    Rasterizer gpu{guest};
    DmaPusher a{memory,&gpu},b{memory,&gpu};
    Puller channel_a,channel_b;
    for(auto* p:{&channel_a,&channel_b}){
        p->regs.reg_array[0x17]=0x1000;
        p->regs.reg_array[0x18]=0;
        p->regs.reg_array[0x19]=17;
    }
    channel_a.ProcessNativeSemaphoreExecute(a,0); // pending wait
    assert(channel_a.pending_native_acquire && guest.Get()==2);
    assert(!channel_a.ResumeNativeAcquire(a));
    channel_b.ProcessNativeSemaphoreExecute(b,1); // real native release owner
    assert(gpu.queries==1 && gpu.pending_value==17 && guest.Get()==2);
    assert(!channel_a.ResumeNativeAcquire(a)); // unsubmitted GPU work isn't complete
    gpu.CompleteQueuedVulkanWork(); // genuine vkCmdFillBuffer, vkQueueSubmit, VkFence
    assert(guest.Get()==17);
    assert(channel_a.ResumeNativeAcquire(a)); // same owner, guest word actually signalled
    assert(!channel_a.pending_native_acquire);
    assert(gpu.flushes==1);
    // Valid host fence never permits a stale page alias to satisfy a new
    // parked wait; this second round refuses a revoked CPU backing.
    channel_a.regs.reg_array[0x19]=19;
    channel_a.ProcessNativeSemaphoreExecute(a,2);
    assert(channel_a.pending_native_acquire);
    memory.cpu_alias=false;
    bool rejected=false;
    try{(void)channel_a.ResumeNativeAcquire(a);}
    catch(const std::runtime_error&){rejected=true;}
    assert(rejected && channel_a.pending_native_acquire);
    std::puts("G10_REAL_VULKAN_SEMAPHORE_OWNER_PASS"
              " channels=2 vkCmdFillBuffer=1 vkQueueSubmit=1"
              " VkFence_retired=1 guest_write_observed=17"
              " parked_replay=1 stale_alias_refused=1"
              " QMD3_dispatch=not_exercised PS5=not_exercised");
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in
   (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-g10-vulkan-semaphore-") as tmp:
    cpp=Path(tmp)/"owner.cpp";cpp.write_text(fixture)
    # The sharded P0-P4 job can launch several host Vulkan consumers in
    # parallel. Force Mesa's real software ICD and limit its worker threads;
    # do not fabricate a passing result if instance creation still fails.
    env=os.environ.copy()
    icd=Path("/usr/share/vulkan/icd.d/lvp_icd.x86_64.json")
    if icd.is_file():
        env["VK_ICD_FILENAMES"]=str(icd)
        env["LP_NUM_THREADS"]="2"
    for cc in compilers:
        exe=Path(tmp)/Path(cc).name.replace("+","p")
        cmd=[cc,"-std=c++20","-O1","-Wall","-Wextra","-Werror",
             "-Wno-missing-field-initializers","-pthread",
             "-I"+str(NATIVE),str(cpp),"-o",str(exe),"-lvulkan"]
        result=subprocess.run(cmd,capture_output=True,text=True,
                              timeout=80,env=env)
        assert result.returncode==0,(cc,result.stderr[-6500:])
        run=subprocess.run([str(exe)],capture_output=True,text=True,
                           timeout=45,env=env)
        assert run.returncode==0,(cc,run.stderr[-6000:])
        print(Path(cc).name,run.stdout.strip(),flush=True)
