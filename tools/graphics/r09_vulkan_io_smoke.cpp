// SPDX-License-Identifier: MIT
// Run the R09 texture->native proxy->sampleable Vulkan image path on a
// genuine Vulkan compute queue, including barriers and pixel readback.
// This intentionally does NOT execute a neural network or an emulator.
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
        const VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT,0u,16u};
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
void Smoke(Context& c,const char* input_spv,const char* compose_spv,const char* output_spv){
    // A non-square 4x3 image catches incorrect native 3x4 transpose.
    constexpr std::uint32_t screen_width=4u,screen_height=3u;
    constexpr std::uint32_t native_width=screen_height,native_height=screen_width;
    constexpr std::uint32_t pixels=screen_width*screen_height;
    constexpr VkDeviceSize rgba8_bytes=pixels*4u;
    constexpr VkDeviceSize rgba32_bytes=pixels*16u;
    const Buffer staging=c.MakeBuffer(rgba8_bytes,VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    const Buffer native=c.MakeBuffer(rgba32_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer features=c.MakeBuffer(pixels*32u,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer composed=c.MakeBuffer(rgba32_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer readback=c.MakeBuffer(rgba32_bytes,VK_BUFFER_USAGE_TRANSFER_DST_BIT);
    const Image scene=c.MakeImage(screen_width,screen_height,VK_FORMAT_R8G8B8A8_UNORM,
                                  VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT);
    const Image output=c.MakeImage(screen_width,screen_height,VK_FORMAT_R32G32B32A32_SFLOAT,
                                   VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|
                                   VK_IMAGE_USAGE_SAMPLED_BIT);
    std::array<std::uint8_t,rgba8_bytes> expected{};
    for(std::uint32_t y=0;y<screen_height;++y)
        for(std::uint32_t x=0;x<screen_width;++x){
            const std::size_t i=(y*screen_width+x)*4u;
            expected[i+0u]=std::uint8_t(17u+32u*x+9u*y);
            expected[i+1u]=std::uint8_t(22u+11u*x+25u*y);
            expected[i+2u]=std::uint8_t(33u+7u*x+40u*y);
            expected[i+3u]=std::uint8_t(252u-x-y);
        }
    void* mapped{};
    Check(vkMapMemory(c.device,staging.memory,0u,rgba8_bytes,0u,&mapped),"map staging");
    std::memcpy(mapped,expected.data(),expected.size());
    vkUnmapMemory(c.device,staging.memory);
    Check(vkMapMemory(c.device,features.memory,0u,pixels*32u,0u,&mapped),
          "map learned head fixture");
    // Model head's live FP16 lanes: (+0.125,-0.125,+0.25,logit 0).
    // The remaining 12 padded lanes are zero, never claimed as RGB.
    auto* head=static_cast<std::uint32_t*>(mapped);
    for(std::uint32_t p=0u;p<pixels;++p){
        head[p*8u+0u]=0xb0003000u;
        head[p*8u+1u]=0x00003400u;
        for(std::uint32_t lane=2u;lane<8u;++lane)
            head[p*8u+lane]=0u;
    }
    vkUnmapMemory(c.device,features.memory);
    const VkSamplerCreateInfo sample{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,nullptr,0u,
        VK_FILTER_NEAREST,VK_FILTER_NEAREST,VK_SAMPLER_MIPMAP_MODE_NEAREST,
        VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,0.0f,VK_FALSE,1.0f,VK_FALSE,
        VK_COMPARE_OP_ALWAYS,0.0f,0.0f,VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK,VK_FALSE};
    Check(vkCreateSampler(c.device,&sample,nullptr,&c.sampler),"create sampler");
    const VkDescriptorSetLayoutBinding input_bindings[]{
        {0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    const VkDescriptorSetLayoutBinding compose_bindings[]{
        {0u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {2u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    const VkDescriptorSetLayoutBinding output_bindings[]{
        {0u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    auto make_set=[&](const VkDescriptorSetLayoutBinding* bs,std::uint32_t count){
        VkDescriptorSetLayoutCreateInfo ci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
            nullptr,0u,count,bs};
        VkDescriptorSetLayout l{};
        Check(vkCreateDescriptorSetLayout(c.device,&ci,nullptr,&l),"create set layout");
        c.sets.push_back(l);
        return l;
    };
    const auto input_set=make_set(input_bindings,2u);
    const auto compose_set=make_set(compose_bindings,3u);
    const auto output_set=make_set(output_bindings,2u);
    const VkDescriptorPoolSize pools[]{
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u},
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,5u},
        {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1u}};
    const VkDescriptorPoolCreateInfo pool_ci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        nullptr,0u,3u,3u,pools};
    Check(vkCreateDescriptorPool(c.device,&pool_ci,nullptr,&c.descriptors),"descriptor pool");
    const VkDescriptorSetLayout layouts[]{input_set,compose_set,output_set};
    const VkDescriptorSetAllocateInfo allocate{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        nullptr,c.descriptors,3u,layouts};
    VkDescriptorSet sets[3]{};
    Check(vkAllocateDescriptorSets(c.device,&allocate,sets),"allocate sets");
    const VkDescriptorBufferInfo proxy_info{native.handle,0u,rgba32_bytes};
    const VkDescriptorBufferInfo head_info{features.handle,0u,pixels*32u};
    const VkDescriptorBufferInfo color_info{composed.handle,0u,rgba32_bytes};
    const VkDescriptorImageInfo scene_info{c.sampler,scene.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkDescriptorImageInfo output_info{VK_NULL_HANDLE,output.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkWriteDescriptorSet writes[]{
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[0],0u,0u,1u,
         VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,&scene_info,nullptr,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[0],1u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&proxy_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[1],0u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&proxy_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[1],1u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&head_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[1],2u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&color_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[2],0u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&color_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[2],1u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,&output_info,nullptr,nullptr}};
    vkUpdateDescriptorSets(c.device,7u,writes,0u,nullptr);
    VkPipelineLayout input_layout{},compose_layout{},output_layout{};
    const VkPipeline in_pipeline=c.Pipeline(c.Shader(input_spv),input_set,input_layout);
    const VkPipeline compose_pipeline=c.Pipeline(
        c.Shader(compose_spv),compose_set,compose_layout);
    const VkPipeline out_pipeline=c.Pipeline(c.Shader(output_spv),output_set,output_layout);
    const VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,nullptr,
                                         VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,nullptr};
    Check(vkBeginCommandBuffer(c.command,&begin),"begin command buffer");
    auto src_to_copy=ImageBarrier(scene.handle,0u,VK_ACCESS_TRANSFER_WRITE_BIT,
                                  VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    auto dst_to_write=ImageBarrier(output.handle,0u,VK_ACCESS_SHADER_WRITE_BIT,
                                   VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_GENERAL);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT|VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         0u,0u,nullptr,0u,nullptr,1u,&src_to_copy);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         0u,nullptr,0u,nullptr,1u,&dst_to_write);
    const VkBufferImageCopy copy{0u,0u,0u,{VK_IMAGE_ASPECT_COLOR_BIT,0u,0u,1u},
                                 {0,0,0},{screen_width,screen_height,1u}};
    vkCmdCopyBufferToImage(c.command,staging.handle,scene.handle,
                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1u,&copy);
    auto src_to_compute=ImageBarrier(scene.handle,VK_ACCESS_TRANSFER_WRITE_BIT,
                                     VK_ACCESS_SHADER_READ_BIT,
                                     VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         0u,nullptr,0u,nullptr,1u,&src_to_compute);
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,in_pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            input_layout,0u,1u,&sets[0],0u,nullptr);
    const InputPush ip{native_width,native_height,1.f,0u};
    vkCmdPushConstants(c.command,input_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(ip),&ip);
    vkCmdDispatch(c.command,1u,1u,1u);
    const VkMemoryBarrier compute_between{VK_STRUCTURE_TYPE_MEMORY_BARRIER,
        nullptr,VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT};
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         1u,&compute_between,0u,nullptr,0u,nullptr);
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,compose_pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            compose_layout,0u,1u,&sets[1],0u,nullptr);
    const InputPush cp{native_width,native_height,1.f,0u};
    vkCmdPushConstants(c.command,compose_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(cp),&cp);
    vkCmdDispatch(c.command,1u,1u,1u);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         1u,&compute_between,0u,nullptr,0u,nullptr);
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,out_pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            output_layout,0u,1u,&sets[2],0u,nullptr);
    const OutputPush op{native_width,native_height,0u,0u};
    vkCmdPushConstants(c.command,output_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(op),&op);
    vkCmdDispatch(c.command,1u,1u,1u);
    auto out_to_copy=ImageBarrier(output.handle,VK_ACCESS_SHADER_WRITE_BIT,
                                  VK_ACCESS_TRANSFER_READ_BIT,
                                  VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,0u,
                         0u,nullptr,0u,nullptr,1u,&out_to_copy);
    vkCmdCopyImageToBuffer(c.command,output.handle,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                           readback.handle,1u,&copy);
    const VkBufferMemoryBarrier to_host{VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,
        nullptr,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
        VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
        readback.handle,0u,rgba32_bytes};
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT,0u,0u,nullptr,1u,&to_host,0u,nullptr);
    Check(vkEndCommandBuffer(c.command),"end command buffer");
    const VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO,nullptr,
        0u,nullptr,nullptr,1u,&c.command,0u,nullptr};
    Check(vkQueueSubmit(c.queue,1u,&submit,VK_NULL_HANDLE),"submit");
    Check(vkQueueWaitIdle(c.queue),"wait result");
    Check(vkMapMemory(c.device,readback.memory,0u,rgba32_bytes,0u,&mapped),"map readback");
    const auto* rgba=static_cast<const float*>(mapped);
    for(std::uint32_t y=0;y<screen_height;++y)
        for(std::uint32_t x=0;x<screen_width;++x)
            for(std::uint32_t ch=0;ch<4u;++ch){
                const std::size_t i=(y*screen_width+x)*4u+ch;
                const float correction[4]{0.03125f,-0.03125f,0.0625f,0.0f};
                const float wanted=std::clamp(
                    float(expected[i])/255.f+correction[ch],0.0f,1.0f);
                if(!std::isfinite(rgba[i])||std::fabs(rgba[i]-wanted)>0.00005f){
                    const float actual=rgba[i];
                    vkUnmapMemory(c.device,readback.memory);
                    throw std::runtime_error("GPU sampled image/raster roundtrip mismatch at "+
                        std::to_string(x)+","+std::to_string(y)+" channel "+
                        std::to_string(ch)+": "+std::to_string(actual)+
                        " != "+std::to_string(wanted));
                }
            }
    vkUnmapMemory(c.device,readback.memory);
    std::cout<<"R09_VULKAN_REAL_GPU_IO_AND_COMPOSITE_PASS "
             <<screen_width<<"x"<<screen_height<<"\n";
}
} // namespace
int main(int argc,char**argv){
    if(argc!=4){
        std::cerr<<"usage: r09_vulkan_io_smoke <texture_proxy.spv> <compose.spv> <nohistory_present.spv>\n";
        return 2;
    }
    try{
        Context context;
        context.Initialize();
        Smoke(context,argv[1],argv[2],argv[3]);
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"R09_VULKAN_REAL_GPU_IO_FAIL: "<<e.what()<<"\n";
        return 1;
    }
}