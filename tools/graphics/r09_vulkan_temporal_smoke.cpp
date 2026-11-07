// SPDX-License-Identifier: MIT
// R09 GPU-compute temporal learned-head smoke; synthetic inputs are test
// fixtures, never inferred model results or a full DLSS-NR demonstration.
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
void Check(VkResult r, const char* op) {
    if (r != VK_SUCCESS) throw std::runtime_error(std::string(op)+": "+std::to_string(r));
}
struct Buffer {
    VkBuffer handle{};
    VkDeviceMemory memory{};
    VkDeviceSize size{};
};
struct Image {
    VkImage handle{};
    VkDeviceMemory memory{};
    VkImageView view{};
};
struct Context {
    VkInstance instance{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    std::uint32_t family{};
    VkCommandPool command_pool{};
    VkCommandBuffer command{};
    VkPhysicalDeviceMemoryProperties memory_types{};
    std::vector<Buffer> buffers;
    std::vector<Image> images;
    std::vector<VkDescriptorSetLayout> sets;
    std::vector<VkPipelineLayout> layouts;
    std::vector<VkShaderModule> modules;
    std::vector<VkPipeline> pipelines;
    VkDescriptorPool descriptors{};
    VkSampler sampler{};
    ~Context(){
        if (!device) { if(instance)vkDestroyInstance(instance,nullptr); return; }
        vkDeviceWaitIdle(device);
        for(auto p:pipelines)vkDestroyPipeline(device,p,nullptr);
        for(auto p:modules)vkDestroyShaderModule(device,p,nullptr);
        for(auto p:layouts)vkDestroyPipelineLayout(device,p,nullptr);
        for(auto p:sets)vkDestroyDescriptorSetLayout(device,p,nullptr);
        if(descriptors)vkDestroyDescriptorPool(device,descriptors,nullptr);
        if(sampler)vkDestroySampler(device,sampler,nullptr);
        for(auto& x:images){
            if(x.view)vkDestroyImageView(device,x.view,nullptr);
            if(x.handle)vkDestroyImage(device,x.handle,nullptr);
            if(x.memory)vkFreeMemory(device,x.memory,nullptr);
        }
        for(auto& x:buffers){
            if(x.handle)vkDestroyBuffer(device,x.handle,nullptr);
            if(x.memory)vkFreeMemory(device,x.memory,nullptr);
        }
        if(command_pool)vkDestroyCommandPool(device,command_pool,nullptr);
        vkDestroyDevice(device,nullptr);
        vkDestroyInstance(instance,nullptr);
    }
    std::uint32_t FindMemory(std::uint32_t bits, VkMemoryPropertyFlags flags) {
        for(std::uint32_t i=0;i<memory_types.memoryTypeCount;++i)
            if((bits&(1u<<i)) &&
               (memory_types.memoryTypes[i].propertyFlags&flags)==flags)return i;
        throw std::runtime_error("No compatible Vulkan memory type");
    }
    void Initialize(){
        const VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO,nullptr,
            "R09 Vulkan I/O proof",1u,"Eden Encore",1u,VK_API_VERSION_1_1};
        const VkInstanceCreateInfo ci{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
            nullptr,0u,&app,0u,nullptr,0u,nullptr};
        Check(vkCreateInstance(&ci,nullptr,&instance),"vkCreateInstance");
        std::uint32_t count=0;
        Check(vkEnumeratePhysicalDevices(instance,&count,nullptr),"enumerate count");
        if(!count)throw std::runtime_error("No Vulkan physical device: lavapipe must be installed");
        std::vector<VkPhysicalDevice> available(count);
        Check(vkEnumeratePhysicalDevices(instance,&count,available.data()),"enumerate devices");
        for(auto p:available){
            VkFormatProperties ldr{},rgba{};
            vkGetPhysicalDeviceFormatProperties(p,VK_FORMAT_R8G8B8A8_UNORM,&ldr);
            vkGetPhysicalDeviceFormatProperties(p,VK_FORMAT_R32G32B32A32_SFLOAT,&rgba);
            if(!(ldr.optimalTilingFeatures&VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT)||
               (rgba.optimalTilingFeatures&(VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT|
                  VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT))!=
                 (VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT))continue;
            std::uint32_t queues=0;
            vkGetPhysicalDeviceQueueFamilyProperties(p,&queues,nullptr);
            std::vector<VkQueueFamilyProperties> families(queues);
            vkGetPhysicalDeviceQueueFamilyProperties(p,&queues,families.data());
            for(std::uint32_t i=0;i<queues;++i)
                if(families[i].queueFlags&VK_QUEUE_COMPUTE_BIT){physical=p;family=i;break;}
            if(physical)break;
        }
        if(!physical)throw std::runtime_error("No Vulkan compute queue with R8 sampling + RGBA32F storage");
        VkPhysicalDeviceProperties info{};
        vkGetPhysicalDeviceProperties(physical,&info);
        std::cout<<"R09_VULKAN_IO_DEVICE "<<info.deviceName<<"\n";
        vkGetPhysicalDeviceMemoryProperties(physical,&memory_types);
        const float priority=1.f;
        const VkDeviceQueueCreateInfo queue_ci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
            nullptr,0u,family,1u,&priority};
        const VkDeviceCreateInfo device_ci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
            nullptr,0u,1u,&queue_ci,0u,nullptr,0u,nullptr,nullptr};
        Check(vkCreateDevice(physical,&device_ci,nullptr,&device),"vkCreateDevice");
        vkGetDeviceQueue(device,family,0u,&queue);
        const VkCommandPoolCreateInfo pool{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
            nullptr,0u,family};
        Check(vkCreateCommandPool(device,&pool,nullptr,&command_pool),"create pool");
        const VkCommandBufferAllocateInfo alloc{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
            nullptr,command_pool,VK_COMMAND_BUFFER_LEVEL_PRIMARY,1u};
        Check(vkAllocateCommandBuffers(device,&alloc,&command),"allocate cmd");
    }
    Buffer MakeBuffer(VkDeviceSize bytes,VkBufferUsageFlags usage){
        Buffer b{};
        b.size=bytes;
        const VkBufferCreateInfo ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
            nullptr,0u,bytes,usage,VK_SHARING_MODE_EXCLUSIVE,0u,nullptr};
        Check(vkCreateBuffer(device,&ci,nullptr,&b.handle),"create buffer");
        VkMemoryRequirements req{};
        vkGetBufferMemoryRequirements(device,b.handle,&req);
        const VkMemoryAllocateInfo mem{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            nullptr,req.size,FindMemory(req.memoryTypeBits,
                VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)};
        Check(vkAllocateMemory(device,&mem,nullptr,&b.memory),"allocate buffer memory");
        Check(vkBindBufferMemory(device,b.handle,b.memory,0u),"bind buffer");
        buffers.push_back(b);
        return b;
    }
    Image MakeImage(std::uint32_t w,std::uint32_t h,VkFormat format,
                    VkImageUsageFlags usage){
        Image image{};
        const VkImageCreateInfo ci{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
            nullptr,0u,VK_IMAGE_TYPE_2D,format,{w,h,1u},1u,1u,
            VK_SAMPLE_COUNT_1_BIT,VK_IMAGE_TILING_OPTIMAL,usage,
            VK_SHARING_MODE_EXCLUSIVE,0u,nullptr,VK_IMAGE_LAYOUT_UNDEFINED};
        Check(vkCreateImage(device,&ci,nullptr,&image.handle),"create image");
        VkMemoryRequirements req{};
        vkGetImageMemoryRequirements(device,image.handle,&req);
        const VkMemoryAllocateInfo mem{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            nullptr,req.size,FindMemory(req.memoryTypeBits,0u)};
        Check(vkAllocateMemory(device,&mem,nullptr,&image.memory),"allocate image memory");
        Check(vkBindImageMemory(device,image.handle,image.memory,0u),"bind image");
        const VkImageViewCreateInfo view{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
            nullptr,0u,image.handle,VK_IMAGE_VIEW_TYPE_2D,format,
            {VK_COMPONENT_SWIZZLE_IDENTITY,VK_COMPONENT_SWIZZLE_IDENTITY,
             VK_COMPONENT_SWIZZLE_IDENTITY,VK_COMPONENT_SWIZZLE_IDENTITY},
            {VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u}};
        Check(vkCreateImageView(device,&view,nullptr,&image.view),"create image view");
        images.push_back(image);
        return image;
    }
    VkShaderModule Shader(const char* path){
        std::ifstream stream(path,std::ios::binary|std::ios::ate);
        if(!stream)throw std::runtime_error(std::string("Missing SPIR-V: ")+path);
        const auto length=stream.tellg();
        if(length<=0||length%4!=0)throw std::runtime_error("Bad SPIR-V size");
        std::vector<std::uint32_t> words(std::size_t(length)/4u);
        stream.seekg(0);
        stream.read(reinterpret_cast<char*>(words.data()),length);
        const VkShaderModuleCreateInfo ci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
            nullptr,0u,std::size_t(length),words.data()};
        VkShaderModule shader{};
        Check(vkCreateShaderModule(device,&ci,nullptr,&shader),"create shader");
        modules.push_back(shader);
        return shader;
    }
    VkPipeline Pipeline(VkShaderModule shader,VkDescriptorSetLayout set,
                        VkPipelineLayout& pl){
        const VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT,0u,32u};
        const VkPipelineLayoutCreateInfo ci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
            nullptr,0u,1u,&set,1u,&pc};
        Check(vkCreatePipelineLayout(device,&ci,nullptr,&pl),"create pipeline layout");
        layouts.push_back(pl);
        const VkPipelineShaderStageCreateInfo stage{VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
            nullptr,0u,VK_SHADER_STAGE_COMPUTE_BIT,shader,"main",nullptr};
        const VkComputePipelineCreateInfo pipeline{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
            nullptr,0u,stage,pl,VK_NULL_HANDLE,-1};
        VkPipeline result{};
        Check(vkCreateComputePipelines(device,VK_NULL_HANDLE,1u,&pipeline,nullptr,&result),
              "create compute pipeline");
        pipelines.push_back(result);
        return result;
    }
};
VkImageMemoryBarrier ImageBarrier(VkImage image,VkAccessFlags from,VkAccessFlags to,
                                  VkImageLayout old_layout,VkImageLayout new_layout){
    VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,nullptr,
        from,to,old_layout,new_layout,VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
        image,{VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u}};
    return b;
}
struct InputPush{std::uint32_t native_width,native_height;float paper_white;std::uint32_t color_mode;};
struct OutputPush{std::uint32_t native_width,native_height,zero0,zero1;};
static_assert(sizeof(InputPush)==16u&&sizeof(OutputPush)==16u);

struct TemporalPush {
    std::uint32_t width,height;
    float intensity,blend_scale;
    std::uint32_t history_valid,z0,z1,z2;
};
static_assert(sizeof(TemporalPush)==32u);
float TruncateHalf(float value){
    const float clipped=std::clamp(value,0.f,1.f);
    std::uint32_t bits=0;
    std::memcpy(&bits,&clipped,sizeof(bits));
    const std::uint32_t exponent=(bits>>23u)&255u;
    const std::uint32_t mantissa=bits&0x7fffffu;
    const int h=static_cast<int>(exponent)-112;
    std::uint32_t raw=0u;
    if(h>0)raw=(std::uint32_t(h)<<10u)|(mantissa>>13u);
    else if(h>=-10)raw=(mantissa|0x800000u)>>std::uint32_t(14-h);
    const auto e=(raw>>10u)&31u,m=raw&1023u;
    return e?std::ldexp(1.0f+float(m)/1024.0f,int(e)-15):
             float(m)*0x1p-24f;
}
void Smoke(Context& c,const char* shader_path,std::uint32_t valid){
    // Use non-square native raster dimensions; all storage is pixel-major.
    constexpr std::uint32_t width=3u,height=4u,pixels=width*height;
    constexpr VkDeviceSize rgba_bytes=pixels*16u;
    constexpr VkDeviceSize head_bytes=pixels*32u;
    const auto proxy=c.MakeBuffer(rgba_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const auto head=c.MakeBuffer(head_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const auto motion=c.MakeBuffer(rgba_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const auto previous=c.MakeBuffer(rgba_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const auto result=c.MakeBuffer(rgba_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const auto next=c.MakeBuffer(rgba_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    void* data{};
    Check(vkMapMemory(c.device,proxy.memory,0,rgba_bytes,0,&data),"map proxy");
    auto* rgba=static_cast<float*>(data);
    for(std::uint32_t p=0;p<pixels;++p){
        rgba[p*4+0]=0.1f+float(p)*0.025f;
        rgba[p*4+1]=0.4f+float(p)*0.017f;
        rgba[p*4+2]=0.2f+float(p)*0.021f;
        rgba[p*4+3]=0.8f;
    }
    vkUnmapMemory(c.device,proxy.memory);
    Check(vkMapMemory(c.device,head.memory,0,head_bytes,0,&data),"map head");
    auto* lanes=static_cast<std::uint32_t*>(data);
    for(std::uint32_t p=0;p<pixels;++p){
        lanes[p*8u+0u]=0xb0003000u; // FP16 +.125, -.125
        lanes[p*8u+1u]=0x00003400u; // FP16 +.25, logit=0
        for(std::uint32_t k=2;k<8;++k)lanes[p*8u+k]=0u;
    }
    vkUnmapMemory(c.device,head.memory);
    Check(vkMapMemory(c.device,motion.memory,0,rgba_bytes,0,&data),"map motion");
    rgba=static_cast<float*>(data);
    for(std::uint32_t p=0;p<pixels;++p){
        rgba[p*4u+0u]=0.f; rgba[p*4u+1u]=0.f;
        rgba[p*4u+2u]=1.f; rgba[p*4u+3u]=0.f;
    }
    vkUnmapMemory(c.device,motion.memory);
    Check(vkMapMemory(c.device,previous.memory,0,rgba_bytes,0,&data),"map prior");
    rgba=static_cast<float*>(data);
    for(std::uint32_t p=0;p<pixels;++p){
        rgba[p*4u+0u]=0.5f; rgba[p*4u+1u]=0.5f;
        rgba[p*4u+2u]=0.5f; rgba[p*4u+3u]=1.f;
    }
    vkUnmapMemory(c.device,previous.memory);
    const std::array<VkDescriptorSetLayoutBinding,6> bindings{{
        {0u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {2u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {3u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {4u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {5u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}
    }};
    const VkDescriptorSetLayoutCreateInfo dsl{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,nullptr,0u,
        std::uint32_t(bindings.size()),bindings.data()};
    VkDescriptorSetLayout set_layout{};
    Check(vkCreateDescriptorSetLayout(c.device,&dsl,nullptr,&set_layout),"create temporal set");
    c.sets.push_back(set_layout);
    const VkDescriptorPoolSize pool_sizes{
        VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,6u};
    const VkDescriptorPoolCreateInfo pool{
        VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,nullptr,0u,1u,1u,&pool_sizes};
    Check(vkCreateDescriptorPool(c.device,&pool,nullptr,&c.descriptors),"temporal pool");
    const VkDescriptorSetAllocateInfo allocate{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,nullptr,
        c.descriptors,1u,&set_layout};
    VkDescriptorSet ds{};
    Check(vkAllocateDescriptorSets(c.device,&allocate,&ds),"temporal descriptors");
    const std::array<VkDescriptorBufferInfo,6> info{{
        {proxy.handle,0,rgba_bytes},{head.handle,0,head_bytes},
        {motion.handle,0,rgba_bytes},{previous.handle,0,rgba_bytes},
        {result.handle,0,rgba_bytes},{next.handle,0,rgba_bytes}
    }};
    std::array<VkWriteDescriptorSet,6> writes{};
    for(std::uint32_t i=0;i<writes.size();++i)
        writes[i]=VkWriteDescriptorSet{
            VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,ds,i,0u,1u,
            VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&info[i],nullptr};
    vkUpdateDescriptorSets(c.device,std::uint32_t(writes.size()),
                           writes.data(),0u,nullptr);
    VkPipelineLayout pipeline_layout{};
    const auto pipeline=c.Pipeline(c.Shader(shader_path),set_layout,pipeline_layout);
    const VkCommandBufferBeginInfo begin{
        VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,nullptr,
        VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,nullptr};
    Check(vkBeginCommandBuffer(c.command,&begin),"begin temporal commands");
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            pipeline_layout,0u,1u,&ds,0u,nullptr);
    const TemporalPush push{width,height,1.0f,0.75f,valid,0u,0u,0u};
    vkCmdPushConstants(c.command,pipeline_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(push),&push);
    vkCmdDispatch(c.command,1u,1u,1u);
    const std::array<VkBufferMemoryBarrier,2> to_host{{
        {VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,nullptr,
         VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
         VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
         result.handle,0u,rgba_bytes},
        {VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,nullptr,
         VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
         VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
         next.handle,0u,rgba_bytes}
    }};
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT,0u,0u,nullptr,
                         std::uint32_t(to_host.size()),to_host.data(),0u,nullptr);
    Check(vkEndCommandBuffer(c.command),"end temporal commands");
    const VkSubmitInfo submit{
        VK_STRUCTURE_TYPE_SUBMIT_INFO,nullptr,0u,nullptr,nullptr,
        1u,&c.command,0u,nullptr};
    Check(vkQueueSubmit(c.queue,1u,&submit,VK_NULL_HANDLE),"submit temporal");
    Check(vkQueueWaitIdle(c.queue),"wait temporal GPU");
    void* result_map{};
    void* history_map{};
    Check(vkMapMemory(c.device,result.memory,0u,rgba_bytes,0u,
                      &result_map),"map temporal result");
    Check(vkMapMemory(c.device,next.memory,0u,rgba_bytes,0u,
                      &history_map),"map next history");
    const auto* actual=static_cast<const float*>(result_map);
    const auto* actual_next=static_cast<const float*>(history_map);
    const std::array<float,3> delta{0.125f,-0.125f,0.25f};
    const float history_weight=valid?0.375f:0.f;
    for(std::uint32_t p=0u;p<pixels;++p){
        const std::array<float,3> base{
            0.1f+float(p)*0.025f,
            0.4f+float(p)*0.017f,
            0.2f+float(p)*0.021f};
        for(std::uint32_t ch=0u;ch<4u;++ch){
            const auto index=p*4u+ch;
            const float full=ch<3u?TruncateHalf(
                std::clamp(base[ch]+delta[ch]*0.25f,0.f,1.f)*
                    (1.0f-history_weight)+0.5f*history_weight):1.f;
            const float wanted=ch<3u?full:0.8f;
            if(!std::isfinite(actual[index])||
               !std::isfinite(actual_next[index])||
               std::fabs(actual[index]-wanted)>0.00005f||
               std::fabs(actual_next[index]-full)>0.00005f){
                const float seen=actual[index],next_seen=actual_next[index];
                vkUnmapMemory(c.device,next.memory);
                vkUnmapMemory(c.device,result.memory);
                throw std::runtime_error("R09 temporal GPU pixel mismatch at "+
                    std::to_string(p)+" channel "+std::to_string(ch)+
                    ": "+std::to_string(seen)+"/"+std::to_string(next_seen)+
                    " expected "+std::to_string(wanted)+"/"+std::to_string(full));
            }
        }
    }
    vkUnmapMemory(c.device,next.memory);
    vkUnmapMemory(c.device,result.memory);
    std::cout<<"R09_VULKAN_TEMPORAL_REAL_GPU_PASS history_valid="
             <<valid<<" shape="<<width<<"x"<<height<<"\n";
}
} // namespace
int main(int argc,char** argv){
    if(argc!=2){
        std::cerr<<"usage: r09_vulkan_temporal_smoke <temporal_compose.spv>\n";
        return 2;
    }
    try{
        for(std::uint32_t valid: {0u,1u}){
            Context context;
            context.Initialize();
            Smoke(context,argv[1],valid);
        }
        return 0;
    }catch(const std::exception& error){
        std::cerr<<"R09_VULKAN_TEMPORAL_GPU_FAIL "<<error.what()<<"\n";
        return 1;
    }
}
