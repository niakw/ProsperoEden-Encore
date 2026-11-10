// SPDX-License-Identifier: GPL-3.0-or-later
// Standalone host Vulkan witness: 8 synthetic blocks, 9 VkBuffers, 7 barriers.
// NOT neural inference, NOT an R09 renderer integration, NOT PS5 qualified.
#include "dlss_nr_min_vit_reuse_plan.h"
#include "r09_native_plans.h"
#include <vulkan/vulkan.h>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr std::uint32_t N=64u,Blocks=8u,Slots=9u;
constexpr VkDeviceSize Bytes=N*sizeof(std::uint32_t);
void Check(VkResult r,const char* name){
 if(r!=VK_SUCCESS)throw std::runtime_error(std::string(name)+": "+std::to_string(r));
}
struct Buf{VkBuffer buffer{};VkDeviceMemory memory{};};
VKAPI_ATTR VkBool32 VKAPI_CALL ValidationCallback(
    VkDebugUtilsMessageSeverityFlagBitsEXT severity,
    VkDebugUtilsMessageTypeFlagsEXT,
    const VkDebugUtilsMessengerCallbackDataEXT* details,
    void* user) {
    if(severity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT) {
        static_cast<std::atomic<unsigned>*>(user)->fetch_add(1u);
        std::cerr<<"R09_MIN_VIT_KHRONOS_VALIDATION_ERROR: "
                 <<(details&&details->pMessage?details->pMessage:"unknown")<<"\n";
    }
    return VK_FALSE;
}
struct Host{
 VkInstance instance{};VkPhysicalDevice physical{};VkDevice device{};VkQueue queue{};
 std::uint32_t family{};VkPhysicalDeviceMemoryProperties properties{};
 std::array<Buf,Slots> buffers{};
 VkDescriptorSetLayout set_layout{};VkDescriptorPool descriptor_pool{};
 std::array<VkDescriptorSet,Blocks> sets{};
 VkShaderModule shader{};VkPipelineLayout pipeline_layout{};VkPipeline pipeline{};
 VkCommandPool pool{};VkCommandBuffer cmd{};VkFence fence{};
 VkDebugUtilsMessengerEXT debug_messenger{};
 std::atomic<unsigned> validation_errors{0u};
 bool validation_enabled{};
 ~Host(){
  if(device){
   vkDeviceWaitIdle(device);
   if(fence)vkDestroyFence(device,fence,nullptr);
   if(pipeline)vkDestroyPipeline(device,pipeline,nullptr);
   if(pipeline_layout)vkDestroyPipelineLayout(device,pipeline_layout,nullptr);
   if(shader)vkDestroyShaderModule(device,shader,nullptr);
   if(descriptor_pool)vkDestroyDescriptorPool(device,descriptor_pool,nullptr);
   if(set_layout)vkDestroyDescriptorSetLayout(device,set_layout,nullptr);
   for(auto b:buffers){
    if(b.buffer)vkDestroyBuffer(device,b.buffer,nullptr);
    if(b.memory)vkFreeMemory(device,b.memory,nullptr);
   }
   if(pool)vkDestroyCommandPool(device,pool,nullptr);
   vkDestroyDevice(device,nullptr);
  }
  if(instance) {
   if(debug_messenger){
    auto destroy=reinterpret_cast<PFN_vkDestroyDebugUtilsMessengerEXT>(
        vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT"));
    if(destroy)destroy(instance,debug_messenger,nullptr);
   }
   vkDestroyInstance(instance,nullptr);
  }
 }
 std::uint32_t Mem(std::uint32_t bits,VkMemoryPropertyFlags flags)const{
  for(std::uint32_t i=0;i<properties.memoryTypeCount;++i)
   if((bits&(1u<<i))&&(properties.memoryTypes[i].propertyFlags&flags)==flags)return i;
  throw std::runtime_error("Vulkan host-coherent memory unavailable");
 }
 void Init(){
  VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app.apiVersion=VK_API_VERSION_1_1;
  app.pApplicationName="Encore R09 Min synthetic ViT reuse";
  VkInstanceCreateInfo ici{};ici.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  ici.pApplicationInfo=&app;
  validation_enabled=std::getenv("R09_MIN_VALIDATE_SYNC")!=nullptr;
  const char* layer="VK_LAYER_KHRONOS_validation";
  const std::array<const char*,2> extensions{
      VK_EXT_DEBUG_UTILS_EXTENSION_NAME,
      VK_EXT_VALIDATION_FEATURES_EXTENSION_NAME};
  VkValidationFeatureEnableEXT enabled_feature=
      VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT;
  VkValidationFeaturesEXT features{};
  features.sType=VK_STRUCTURE_TYPE_VALIDATION_FEATURES_EXT;
  features.enabledValidationFeatureCount=1u;
  features.pEnabledValidationFeatures=&enabled_feature;
  VkDebugUtilsMessengerCreateInfoEXT debug_info{};
  debug_info.sType=VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT;
  debug_info.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;
  debug_info.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT|
                         VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT;
  debug_info.pfnUserCallback=ValidationCallback;
  debug_info.pUserData=&validation_errors;
  if(validation_enabled){
   features.pNext=&debug_info;
   ici.pNext=&features;
   ici.enabledLayerCount=1u;
   ici.ppEnabledLayerNames=&layer;
   ici.enabledExtensionCount=std::uint32_t(extensions.size());
   ici.ppEnabledExtensionNames=extensions.data();
  }
  Check(vkCreateInstance(&ici,nullptr,&instance),"create instance");
  if(validation_enabled){
   auto create=reinterpret_cast<PFN_vkCreateDebugUtilsMessengerEXT>(
       vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT"));
   if(!create)throw std::runtime_error("Khronos debug messenger unavailable");
   Check(create(instance,&debug_info,nullptr,&debug_messenger),
         "create Khronos debug messenger");
   std::cout<<"R09_MIN_VIT_KHRONOS_SYNC_VALIDATION_ENABLED\n";
  }
  std::uint32_t count{};
  Check(vkEnumeratePhysicalDevices(instance,&count,nullptr),"device count");
  if(!count)throw std::runtime_error("No Vulkan device");
  std::vector<VkPhysicalDevice> devices(count);
  Check(vkEnumeratePhysicalDevices(instance,&count,devices.data()),"enumerate");
  for(auto p:devices){
   VkPhysicalDeviceProperties caps{};
   vkGetPhysicalDeviceProperties(p,&caps);
   if(caps.limits.maxPerStageDescriptorStorageBuffers<Slots ||
      caps.limits.maxStorageBufferRange<Bytes)continue;
   std::uint32_t n{};
   vkGetPhysicalDeviceQueueFamilyProperties(p,&n,nullptr);
   std::vector<VkQueueFamilyProperties> families(n);
   vkGetPhysicalDeviceQueueFamilyProperties(p,&n,families.data());
   for(std::uint32_t i=0;i<n;++i)
    if(families[i].queueFlags&VK_QUEUE_COMPUTE_BIT){
     physical=p;family=i;break;
    }
   if(physical){std::cout<<"R09_MIN_VIT_GPU_DEVICE "<<caps.deviceName<<"\n";break;}
  }
  if(!physical)throw std::runtime_error("No compute device with 9 SSBO bindings");
  vkGetPhysicalDeviceMemoryProperties(physical,&properties);
  float priority=1.0f;
  VkDeviceQueueCreateInfo qci{};qci.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
  qci.queueFamilyIndex=family;qci.queueCount=1u;qci.pQueuePriorities=&priority;
  VkDeviceCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  ci.queueCreateInfoCount=1u;ci.pQueueCreateInfos=&qci;
  Check(vkCreateDevice(physical,&ci,nullptr,&device),"create device");
  vkGetDeviceQueue(device,family,0u,&queue);
  for(auto& b:buffers){
   VkBufferCreateInfo bc{};bc.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
   bc.size=Bytes;bc.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
   bc.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
   Check(vkCreateBuffer(device,&bc,nullptr,&b.buffer),"create buffer");
   VkMemoryRequirements mr{};
   vkGetBufferMemoryRequirements(device,b.buffer,&mr);
   VkMemoryAllocateInfo ai{};ai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
   ai.allocationSize=mr.size;
   ai.memoryTypeIndex=Mem(mr.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|
                                        VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
   Check(vkAllocateMemory(device,&ai,nullptr,&b.memory),"allocate");
   Check(vkBindBufferMemory(device,b.buffer,b.memory,0u),"bind buffer");
  }
  std::array<VkDescriptorSetLayoutBinding,Slots> bindings{};
  for(std::uint32_t i=0;i<Slots;++i)
   bindings[i]={i,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,
                VK_SHADER_STAGE_COMPUTE_BIT,nullptr};
  VkDescriptorSetLayoutCreateInfo li{};li.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
  li.bindingCount=Slots;li.pBindings=bindings.data();
  Check(vkCreateDescriptorSetLayout(device,&li,nullptr,&set_layout),"set layout");
  VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,Slots*Blocks};
  VkDescriptorPoolCreateInfo pc{};pc.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
  pc.maxSets=Blocks;pc.poolSizeCount=1u;pc.pPoolSizes=&size;
  Check(vkCreateDescriptorPool(device,&pc,nullptr,&descriptor_pool),"descriptor pool");
  std::array<VkDescriptorSetLayout,Blocks> layouts{};layouts.fill(set_layout);
  VkDescriptorSetAllocateInfo da{};da.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
  da.descriptorPool=descriptor_pool;da.descriptorSetCount=Blocks;
  da.pSetLayouts=layouts.data();
  Check(vkAllocateDescriptorSets(device,&da,sets.data()),"allocate sets");
  // The GPU descriptors are driven by the SAME candidate maps derived
  // from both authentic R09 model plans, at both candidate raster sizes.
  using namespace Eden::Graphics::DlssNrMin;
  static_assert(kVitFieldCount==Slots);
  VitReuseCandidate reference{};
  bool found=false;
  for(const auto native : {Eden::NeuralPlans::Original,
                           Eden::NeuralPlans::Compact}) {
   for(const auto raster : {kCurrentR09Graph,kCandidateMinRaster}) {
    VitReuseCandidate candidate{};
    if(!BuildVitCrossBlockReuseCandidate(native,raster,candidate) ||
       candidate.blocks.size()!=Blocks ||
       candidate.pool_slots.size()!=Slots ||
       candidate.runnable || candidate.gpu_barriers_proven ||
       candidate.gpu_fences_proven)
     throw std::runtime_error("Authentic R09 ViT reuse plan invalid");
    if(!found){reference=candidate;found=true;}
    else for(std::uint32_t j=0u;j<Blocks;++j)
     if(candidate.blocks[j].slots!=reference.blocks[j].slots)
      throw std::runtime_error("Original/Compact/720p mapping divergence");
   }
  }
  if(!found)throw std::runtime_error("No candidate ViT plan");
  if(CheckVitReuseAdmission(reference,{})!=VitReuseGate::ConcurrentGpuUse)
   throw std::runtime_error("ViT reuse safety gate unexpectedly open");
  for(std::uint32_t j=0;j<Blocks;++j){
   const auto& map=reference.blocks[j].slots;
   for(std::uint32_t a=0;a<Slots;++a)
    for(std::uint32_t b=0;b<a;++b)
     if(map[a]==map[b])throw std::runtime_error("Unsafe intra-block alias");
   std::array<VkDescriptorBufferInfo,Slots> infos{};
   std::array<VkWriteDescriptorSet,Slots> writes{};
   for(std::uint32_t i=0;i<Slots;++i){
    infos[i]={buffers[map[i]].buffer,0u,Bytes};
    VkWriteDescriptorSet w{};w.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    w.dstSet=sets[j];w.dstBinding=i;w.descriptorCount=1u;
    w.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;w.pBufferInfo=&infos[i];
    writes[i]=w;
   }
   vkUpdateDescriptorSets(device,Slots,writes.data(),0u,nullptr);
  }
  VkCommandPoolCreateInfo pool_info{};pool_info.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
  pool_info.queueFamilyIndex=family;
  Check(vkCreateCommandPool(device,&pool_info,nullptr,&pool),"pool");
  VkCommandBufferAllocateInfo cb{};cb.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
  cb.commandPool=pool;cb.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;cb.commandBufferCount=1u;
  Check(vkAllocateCommandBuffers(device,&cb,&cmd),"allocate command");
 }
 void Pipeline(const char* file){
  std::ifstream in(file,std::ios::binary|std::ios::ate);
  if(!in)throw std::runtime_error("Missing synthetic SPIR-V");
  const auto length=in.tellg();
  if(length<=0||length%4!=0)throw std::runtime_error("Bad SPIR-V size");
  std::vector<std::uint32_t> words(std::size_t(length)/4u);
  in.seekg(0);in.read(reinterpret_cast<char*>(words.data()),length);
  if(!in)throw std::runtime_error("Incomplete SPIR-V");
  VkShaderModuleCreateInfo sm{};sm.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
  sm.codeSize=std::size_t(length);sm.pCode=words.data();
  Check(vkCreateShaderModule(device,&sm,nullptr,&shader),"module");
  VkPushConstantRange push{VK_SHADER_STAGE_COMPUTE_BIT,0u,4u};
  VkPipelineLayoutCreateInfo pl{};pl.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
  pl.setLayoutCount=1u;pl.pSetLayouts=&set_layout;
  pl.pushConstantRangeCount=1u;pl.pPushConstantRanges=&push;
  Check(vkCreatePipelineLayout(device,&pl,nullptr,&pipeline_layout),"pipeline layout");
  VkPipelineShaderStageCreateInfo stage{};
  stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
  stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;stage.module=shader;stage.pName="main";
  VkComputePipelineCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
  ci.stage=stage;ci.layout=pipeline_layout;
  Check(vkCreateComputePipelines(device,VK_NULL_HANDLE,1u,&ci,nullptr,&pipeline),"pipeline");
 }
 void Run(bool omit_one_interblock_barrier=false){
  for(std::uint32_t s=0;s<Slots;++s){
   void* mapped{};
   Check(vkMapMemory(device,buffers[s].memory,0u,Bytes,0u,&mapped),"map initialize");
   auto* u=static_cast<std::uint32_t*>(mapped);
   for(std::uint32_t t=0;t<N;++t)u[t]=s==0u?t+3u:0xfade0000u+s;
   vkUnmapMemory(device,buffers[s].memory);
  }
  VkCommandBufferBeginInfo begin{};begin.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
  begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
  Check(vkBeginCommandBuffer(cmd,&begin),"begin");
  VkMemoryBarrier from_host{};from_host.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
  from_host.srcAccessMask=VK_ACCESS_HOST_WRITE_BIT;
  from_host.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;
  vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_HOST_BIT,
    VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,1u,&from_host,0u,nullptr,0u,nullptr);
  for(std::uint32_t j=0;j<Blocks;++j){
   vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
   vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,
     pipeline_layout,0u,1u,&sets[j],0u,nullptr);
   vkCmdPushConstants(cmd,pipeline_layout,VK_SHADER_STAGE_COMPUTE_BIT,
     0u,sizeof(j),&j);
   vkCmdDispatch(cmd,1u,1u,1u);
   if(j+1u<Blocks && !(omit_one_interblock_barrier && j==3u)){
    VkMemoryBarrier barrier{};barrier.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    barrier.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
    barrier.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
      VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,1u,&barrier,0u,nullptr,0u,nullptr);
   }
  }
  VkMemoryBarrier host{};host.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
  host.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;host.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
  vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
     VK_PIPELINE_STAGE_HOST_BIT,0u,1u,&host,0u,nullptr,0u,nullptr);
  Check(vkEndCommandBuffer(cmd),"end");
  VkFenceCreateInfo fc{};fc.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
  Check(vkCreateFence(device,&fc,nullptr,&fence),"fence");
  VkSubmitInfo si{};si.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
  si.commandBufferCount=1u;si.pCommandBuffers=&cmd;
  Check(vkQueueSubmit(queue,1u,&si,fence),"submit");
  Check(vkWaitForFences(device,1u,&fence,VK_TRUE,10000000000ull),"fence wait");
 }
 void Verify()const{
  std::array<std::array<std::uint32_t,N>,8> expected{};
  for(std::uint32_t t=0;t<N;++t){
   std::uint32_t input=t+3u;
   for(std::uint32_t j=0;j<Blocks;++j){
    const auto hidden=input+j,ffwd=hidden*2u,attention=ffwd+1u;
    const auto scratch=attention+3u,query=scratch+5u,key=query+7u;
    const auto value=key+11u;
    if(j+1u==Blocks){
     expected[1][t]=hidden;expected[2][t]=ffwd;expected[3][t]=attention;
     expected[4][t]=scratch;expected[5][t]=query;
     expected[6][t]=key;expected[7][t]=value;
    }
    input=value+13u;
   }
   expected[0][t]=input;
  }
  for(std::uint32_t s=0;s<Slots;++s){
   if(s==1u)continue;
   void* raw{};
   Check(vkMapMemory(device,buffers[s].memory,0u,Bytes,0u,&raw),"readback");
   const auto* u=static_cast<const std::uint32_t*>(raw);
   const auto index=s==0u?0u:s-1u;
   for(std::uint32_t t=0;t<N;++t)
    if(u[t]!=expected[index][t]){
     const auto seen=u[t],want=expected[index][t];
     vkUnmapMemory(device,buffers[s].memory);
     throw std::runtime_error("ViT reuse GPU mismatch slot="+std::to_string(s)+
       " token="+std::to_string(t)+" actual="+std::to_string(seen)+
       " expected="+std::to_string(want));
    }
   vkUnmapMemory(device,buffers[s].memory);
  }
  std::cout<<"R09_MIN_VIT_REUSE_8_BLOCKS_9_BUFFERS_7_BARRIERS_VULKAN_PASS\n";
  std::cout<<"R09_MIN_VIT_SYNTHETIC_ONLY_NO_PS5_OR_NEURAL_INFERENCE\n";
 }
};
} // namespace
int main(int argc,char** argv){
 if(argc!=2 && argc!=3){
  std::cerr<<"usage: r09_min_vk_vit_reuse_smoke <shader.spv> [--negative-missing-barrier]\n";
  return 2;
 }
 const bool negative=argc==3 && std::string(argv[2])=="--negative-missing-barrier";
 if(argc==3 && !negative)return 2;
 try{
  Host h;h.Init();h.Pipeline(argv[1]);
  if(negative && !h.validation_enabled)
   throw std::runtime_error("Negative barrier fixture requires Khronos sync validation");
  h.Run(negative);
  if(negative){
   // Expected-only negative control: no readback or assertion on the
   // undefined data produced by dispatches lacking a memory dependency.
   if(h.validation_errors.load()==0u)
    throw std::runtime_error("Missing barrier was NOT detected by Khronos");
   std::cout<<"R09_MIN_VIT_KHRONOS_SYNC_NEGATIVE_MISSING_BARRIER_DETECTED\n";
   return 0;
  }
  h.Verify();
  if(h.validation_enabled){
   if(h.validation_errors.load()!=0u)
    throw std::runtime_error("Khronos detected Vulkan validation errors");
   std::cout<<"R09_MIN_VIT_KHRONOS_SYNC_VALIDATION_ZERO_ERRORS\n";
  }
  return 0;
 }
 catch(const std::exception& e){
  std::cerr<<"R09_MIN_VIT_REUSE_GPU_SMOKE_FAIL: "<<e.what()<<"\n";return 1;
 }
}
