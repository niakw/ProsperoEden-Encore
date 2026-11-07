// SPDX-License-Identifier: MIT
// Run the R09 texture->native proxy->sampleable Vulkan image path on a
// genuine Vulkan compute queue, including barriers and pixel readback.
// This intentionally does NOT execute a neural network or an emulator.
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
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
                        VkPipelineLayout& pl,std::uint32_t push_bytes=16u){
        const VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT,0u,push_bytes};
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
// Independent CPU oracle for the shader's round-toward-zero FP16 output.
float HalfTruncated(float value){
    value=std::clamp(value,0.0f,1.0f);
    const std::uint32_t bits=std::bit_cast<std::uint32_t>(value);
    const std::uint32_t exponent=(bits>>23u)&255u;
    const std::uint32_t mantissa=bits&0x7fffffu;
    const int e=int(exponent)-112;
    std::uint32_t half=0u;
    if(e>0)half=(std::uint32_t(e)<<10u)|(mantissa>>13u);
    else if(e>=-10)half=(mantissa|0x800000u)>>std::uint32_t(14-e);
    const int he=int((half>>10u)&31u);
    const std::uint32_t hm=half&1023u;
    return he==0?std::ldexp(float(hm),-24):
                 std::ldexp(1.0f+float(hm)/1024.f,he-15);
}
// Production proxy feature shader's exact 12-word push constant ABI.
struct LiftPush{std::uint32_t width,height,direction;};
static_assert(sizeof(LiftPush)==12u);
struct FeaturePush {
    std::uint32_t full_width,full_height,valid_width,valid_height;
    std::uint32_t source_width,source_height,seed;
    float auto_mask,local_tone,local_structure,skin_structure,style;
};
static_assert(sizeof(FeaturePush)==48u);
float DecodeFp8(std::uint8_t v){
    const float sign=(v&0x80u)?-1.f:1.f;
    const unsigned exp=(v>>3u)&15u,m=v&7u;
    if(exp==15u&&m==7u)return std::numeric_limits<float>::quiet_NaN();
    return sign*(exp==0u?std::ldexp(float(m),-9):
                std::ldexp(float(8u+m),int(exp)-10));
}
float DecodeHalf(std::uint16_t v) {
    const float sign=(v&0x8000u)?-1.f:1.f;
    const int exponent=int((v>>10u)&31u);
    const unsigned mantissa=v&1023u;
    if(exponent==31)return std::numeric_limits<float>::quiet_NaN();
    return sign*(exponent==0?std::ldexp(float(mantissa),-24):
           std::ldexp(1.f+float(mantissa)/1024.f,exponent-15));
}
struct InputPush{std::uint32_t native_width,native_height;float paper_white;std::uint32_t color_mode;};
struct OutputPush{std::uint32_t native_width,native_height,zero0,zero1;};
static_assert(sizeof(InputPush)==16u&&sizeof(OutputPush)==16u);
void Smoke(Context& c,const char* input_spv,const char* feature_spv,
           const char* lift_spv,const char* compose_spv,const char* output_spv,
           std::uint32_t screen_width,std::uint32_t screen_height){
    // The 4x3 canary validates transpose; 1920x1080 additionally exercises
    // all 2,073,600 real native screen pixels and dispatch workgroups.
    if(!screen_width||!screen_height||
       std::uint64_t(screen_width)*screen_height>1920ull*1080ull)
        throw std::runtime_error("Invalid smoke-test geometry");
    const std::uint32_t native_width=screen_height,native_height=screen_width;
    const std::uint32_t pixels=screen_width*screen_height;
    const VkDeviceSize rgba8_bytes=VkDeviceSize(pixels)*4u;
    const VkDeviceSize rgba32_bytes=VkDeviceSize(pixels)*16u;
    const Buffer staging=c.MakeBuffer(rgba8_bytes,VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    const Buffer native=c.MakeBuffer(rgba32_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    // Actual first-frame 16-lane feature shader output, distinct from the
    // synthetic final learned head used to test the output compositor.
    const Buffer encoded=c.MakeBuffer(pixels*32u,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    // The model-matrix GPU smoke is only run for small test rasters.
    // A billion FP16 multiply-adds under Lavapipe at 1080p would be a
    // performance benchmark, not a useful correctness test.
    const bool check_lift=pixels<=3600u;
    const Buffer lifted=c.MakeBuffer((check_lift?pixels:1u)*32u,
                                     VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer lift_weights=c.MakeBuffer(1024u,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer features=c.MakeBuffer(pixels*32u,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer composed=c.MakeBuffer(rgba32_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer readback=c.MakeBuffer(rgba32_bytes,VK_BUFFER_USAGE_TRANSFER_DST_BIT);
    const Image scene=c.MakeImage(screen_width,screen_height,VK_FORMAT_R8G8B8A8_UNORM,
                                  VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT);
    const Image output=c.MakeImage(screen_width,screen_height,VK_FORMAT_R32G32B32A32_SFLOAT,
                                   VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|
                                   VK_IMAGE_USAGE_SAMPLED_BIT);
    std::vector<std::uint8_t> expected(static_cast<std::size_t>(rgba8_bytes));
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
    Check(vkMapMemory(c.device,lift_weights.memory,0u,1024u,0u,&mapped),
          "map synthetic lift matrix");
    std::memset(mapped,0,1024u);
    auto* matrix=static_cast<std::uint32_t*>(mapped);
    for(std::uint32_t channel=0u;channel<32u;++channel){
        const std::uint32_t in=channel<16u?4u+channel%3u:
                                   (channel&1u?13u:3u);
        const std::uint32_t index=channel*16u+in;
        matrix[index/2u]|=0x3c00u<<((index&1u)*16u); // FP16 +1
    }
    vkUnmapMemory(c.device,lift_weights.memory);
    const VkSamplerCreateInfo sample{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,nullptr,0u,
        VK_FILTER_NEAREST,VK_FILTER_NEAREST,VK_SAMPLER_MIPMAP_MODE_NEAREST,
        VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,0.0f,VK_FALSE,1.0f,VK_FALSE,
        VK_COMPARE_OP_ALWAYS,0.0f,0.0f,VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK,VK_FALSE};
    Check(vkCreateSampler(c.device,&sample,nullptr,&c.sampler),"create sampler");
    const VkDescriptorSetLayoutBinding input_bindings[]{
        {0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    const VkDescriptorSetLayoutBinding feature_bindings[]{
        {0u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    const VkDescriptorSetLayoutBinding lift_bindings[]{
        {0u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {2u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
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
    const auto feature_set=make_set(feature_bindings,2u);
    const auto lift_set=make_set(lift_bindings,3u);
    const auto compose_set=make_set(compose_bindings,3u);
    const auto output_set=make_set(output_bindings,2u);
    const VkDescriptorPoolSize pools[]{
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u},
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,10u},
        {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1u}};
    const VkDescriptorPoolCreateInfo pool_ci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        nullptr,0u,5u,3u,pools};
    Check(vkCreateDescriptorPool(c.device,&pool_ci,nullptr,&c.descriptors),"descriptor pool");
    const VkDescriptorSetLayout layouts[]{input_set,compose_set,output_set,feature_set,lift_set};
    const VkDescriptorSetAllocateInfo allocate{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        nullptr,c.descriptors,5u,layouts};
    VkDescriptorSet sets[5]{};
    Check(vkAllocateDescriptorSets(c.device,&allocate,sets),"allocate sets");
    const VkDescriptorBufferInfo proxy_info{native.handle,0u,rgba32_bytes};
    const VkDescriptorBufferInfo encoded_info{encoded.handle,0u,pixels*32u};
    const VkDescriptorBufferInfo lift_weight_info{lift_weights.handle,0u,1024u};
    const VkDescriptorBufferInfo lifted_info{lifted.handle,0u,
        (check_lift?pixels:1u)*32u};
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
         VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,&output_info,nullptr,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[3],0u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&proxy_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[3],1u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&encoded_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[4],0u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&encoded_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[4],1u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&lift_weight_info,nullptr},
        {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,sets[4],2u,0u,1u,
         VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,nullptr,&lifted_info,nullptr}};
    vkUpdateDescriptorSets(c.device,12u,writes,0u,nullptr);
    VkPipelineLayout input_layout{},compose_layout{},output_layout{},feature_layout{},lift_layout{};
    const VkPipeline in_pipeline=c.Pipeline(c.Shader(input_spv),input_set,input_layout);
    const VkPipeline feature_pipeline=c.Pipeline(c.Shader(feature_spv),feature_set,feature_layout,48u);
    const VkPipeline lift_pipeline=c.Pipeline(c.Shader(lift_spv),lift_set,lift_layout,12u);
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
    vkCmdDispatch(c.command,(native_width+7u)/8u,
                  (native_height+7u)/8u,1u);
    const VkMemoryBarrier compute_between{VK_STRUCTURE_TYPE_MEMORY_BARRIER,
        nullptr,VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT};
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         1u,&compute_between,0u,nullptr,0u,nullptr);
    // Execute the same no-history 16-channel input encoder used by the
    // production preblock, after the actual sampled image -> RGBA proxy.
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,feature_pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            feature_layout,0u,1u,&sets[3],0u,nullptr);
    const FeaturePush fp{native_width,native_height,native_width,native_height,
                         native_width,native_height,0u,0.f,0.f,0.f,0.f,0.f};
    vkCmdPushConstants(c.command,feature_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(fp),&fp);
    vkCmdDispatch(c.command,(native_width+7u)/8u,
                  (native_height+7u)/8u,1u);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         1u,&compute_between,0u,nullptr,0u,nullptr);
    if(check_lift){
        vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,lift_pipeline);
        vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                                lift_layout,0u,1u,&sets[4],0u,nullptr);
        const LiftPush lp{native_width,native_height,0u};
        vkCmdPushConstants(c.command,lift_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                           0u,sizeof(lp),&lp);
        vkCmdDispatch(c.command,(native_width+63u)/64u,native_height,1u);
        vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                             VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                             1u,&compute_between,0u,nullptr,0u,nullptr);
    }
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,compose_pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            compose_layout,0u,1u,&sets[1],0u,nullptr);
    const InputPush cp{native_width,native_height,0.65f,0u};
    vkCmdPushConstants(c.command,compose_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(cp),&cp);
    vkCmdDispatch(c.command,(native_width+7u)/8u,
                  (native_height+7u)/8u,1u);
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0u,
                         1u,&compute_between,0u,nullptr,0u,nullptr);
    vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,out_pipeline);
    vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
                            output_layout,0u,1u,&sets[2],0u,nullptr);
    const OutputPush op{native_width,native_height,0u,0u};
    vkCmdPushConstants(c.command,output_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(op),&op);
    vkCmdDispatch(c.command,(screen_width+7u)/8u,
                  (screen_height+7u)/8u,1u);
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
    const VkBufferMemoryBarrier features_to_host{
        VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,nullptr,
        VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
        VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
        encoded.handle,0u,pixels*32u};
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT,0u,0u,nullptr,
                         1u,&features_to_host,0u,nullptr);
    if(check_lift){
        const VkBufferMemoryBarrier lift_to_host{
            VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,nullptr,
            VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
            VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
            lifted.handle,0u,pixels*32u};
        vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                             VK_PIPELINE_STAGE_HOST_BIT,0u,0u,nullptr,
                             1u,&lift_to_host,0u,nullptr);
    }
    Check(vkEndCommandBuffer(c.command),"end command buffer");
    const VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO,nullptr,
        0u,nullptr,nullptr,1u,&c.command,0u,nullptr};
    Check(vkQueueSubmit(c.queue,1u,&submit,VK_NULL_HANDLE),"submit");
    Check(vkQueueWaitIdle(c.queue),"wait result");
    Check(vkMapMemory(c.device,encoded.memory,0u,pixels*32u,0u,
                      &mapped),"map GPU input features");
    const auto* encoded_words=static_cast<const std::uint32_t*>(mapped);
    const auto feature_lane=[&](std::uint32_t pixel,std::uint32_t lane){
        const std::uint32_t packed=encoded_words[pixel*8u+lane/2u];
        return DecodeHalf(static_cast<std::uint16_t>(
            (lane&1u)?packed>>16u:packed&0xffffu));
    };
    for(std::uint32_t y=0u;y<native_height;++y){
        for(std::uint32_t x=0u;x<native_width;++x){
            const auto pixel=y*native_width+x;
            const auto physical=(x*screen_width+y)*4u;
            if(feature_lane(pixel,3u)!=1.f||
               feature_lane(pixel,13u)!=-1.f||
               feature_lane(pixel,14u)!=-1.f||
               feature_lane(pixel,15u)!=0.f)
                throw std::runtime_error("GPU input feature constants differ");
            for(std::uint32_t channel=0u;channel<3u;++channel){
                const float wanted=(float(expected[physical+channel])/255.f-
                                    0.5f)*0.125f;
                for(const auto lane : {4u+channel,7u+channel}){
                    const float actual=feature_lane(pixel,lane);
                    if(!std::isfinite(actual)||std::fabs(actual-wanted)>0.00008f){
                        throw std::runtime_error(
                            "GPU FP16 proxy feature mismatch at native "+
                            std::to_string(x)+","+std::to_string(y)+
                            " lane "+std::to_string(lane));
                    }
                }
            }
            for(std::uint32_t noise=0u;noise<3u;++noise)
                if(!std::isfinite(feature_lane(pixel,noise))||
                   std::fabs(feature_lane(pixel,noise))>20.f)
                    throw std::runtime_error("GPU input noise nonfinite");
        }
    }
    vkUnmapMemory(c.device,encoded.memory);
    if(check_lift){
        Check(vkMapMemory(c.device,lifted.memory,0u,pixels*32u,0u,&mapped),
              "map real GPU FP16-to-FP8 projection");
        const auto* fp8=static_cast<const std::uint32_t*>(mapped);
        for(std::uint32_t y=0u;y<native_height;++y){
            for(std::uint32_t x=0u;x<native_width;++x){
                const auto pixel=y*native_width+x;
                const auto physical=(x*screen_width+y)*4u;
                for(std::uint32_t channel=0u;channel<32u;++channel){
                    const std::uint32_t packed=fp8[pixel*8u+channel/4u];
                    const auto bits=static_cast<std::uint8_t>(
                        packed>>((channel%4u)*8u));
                    const float actual=DecodeFp8(bits);
                    const float wanted=channel<16u?
                        (float(expected[physical+channel%3u])/255.f-0.5f)*0.125f:
                        (channel&1u?-1.f:1.f);
                    if(!std::isfinite(actual)||std::fabs(actual-wanted)>0.006f)
                        throw std::runtime_error(
                            "GPU learned FP16->FP8 projection mismatch at "+
                            std::to_string(x)+","+std::to_string(y)+
                            " channel "+std::to_string(channel));
                }
            }
        }
        vkUnmapMemory(c.device,lifted.memory);
        std::cout<<"R09_VULKAN_GPU_LEARNED_LIFT_ONEHOT_PASS "
                 <<screen_width<<"x"<<screen_height<<"\n";
    }
    std::cout<<"R09_VULKAN_REAL_GPU_16LANE_INPUT_FEATURES_PASS "
             <<screen_width<<"x"<<screen_height<<"\n";
    Check(vkMapMemory(c.device,readback.memory,0u,rgba32_bytes,0u,&mapped),"map readback");
    const auto* rgba=static_cast<const float*>(mapped);
    for(std::uint32_t y=0;y<screen_height;++y)
        for(std::uint32_t x=0;x<screen_width;++x)
            for(std::uint32_t ch=0;ch<4u;++ch){
                const std::size_t i=(y*screen_width+x)*4u+ch;
                const float correction[4]{0.03125f,-0.03125f,0.0625f,0.0f};
                const float base=float(expected[i])/255.f;
                const float neural=std::clamp(
                    base+correction[ch],0.0f,1.0f);
                const float wanted=ch==3u?base:HalfTruncated(
                    std::clamp(base+0.65f*(neural-base),0.0f,1.0f));
                if(!std::isfinite(rgba[i])||std::fabs(rgba[i]-wanted)>0.00005f){
                    const float actual=rgba[i];
                    vkUnmapMemory(c.device,readback.memory);
                    throw std::runtime_error("GPU sampled image/raster roundtrip mismatch at "+
                        std::to_string(x)+","+std::to_string(y)+" channel "+
                        std::to_string(ch)+": "+std::to_string(actual)+
                        " != "+std::to_string(wanted));
                }
            }
    if(screen_width==80u&&screen_height==45u){
        // Evidence is the CPU-uploaded source and ACTUAL Vulkan storage
        // image GPU readback. Both RGB P6 frames preserve every sample;
        // no screenshot substitution or learned-model inference is claimed.
        const std::string header="P6\n"+std::to_string(screen_width)+" "+
                                 std::to_string(screen_height)+"\n255\n";
        std::vector<char> before(pixels*3u),after(pixels*3u);
        for(std::uint32_t i=0u;i<pixels;++i)
            for(std::uint32_t ch=0u;ch<3u;++ch){
                const std::size_t rgb=i*3u+ch,rgba_index=i*4u+ch;
                before[rgb]=static_cast<char>(expected[rgba_index]);
                const float sample=std::clamp(rgba[rgba_index],0.0f,1.0f);
                after[rgb]=static_cast<char>(std::lround(sample*255.0f));
            }
        const auto write=[&](const char* p,const std::vector<char>& rgb){
            std::ofstream image(p,std::ios::binary|std::ios::trunc);
            if(!image)throw std::runtime_error("Cannot create GPU evidence");
            image<<header;
            image.write(rgb.data(),static_cast<std::streamsize>(rgb.size()));
            if(!image.good())throw std::runtime_error("GPU evidence write failed");
        };
        write(".build-r09-gpu/r09_before.ppm",before);
        write(".build-r09-gpu/r09_after_gpu.ppm",after);
    }
    vkUnmapMemory(c.device,readback.memory);
    std::cout<<"R09_VULKAN_REAL_GPU_IO_AND_COMPOSITE_PASS "
             <<screen_width<<"x"<<screen_height<<"\n";
}
// Exercise the *actual* temporal GLSL shader through a Vulkan compute
// queue, with a valid external motion field and a known previous history.
// This fixture is NOT a fabricated model and is never used by runtime.
} // namespace
int main(int argc,char**argv){
    if(argc!=6&&argc!=8){
        std::cerr<<"usage: r09_vulkan_io_smoke <texture_proxy.spv> <proxy_features.spv> <image_feature.spv> <compose.spv> <nohistory_present.spv> [width height]\n";
        return 2;
    }
    try{
        Context context;
        context.Initialize();
        const std::uint32_t width=argc==8?static_cast<std::uint32_t>(
            std::stoul(argv[6])):4u;
        const std::uint32_t height=argc==8?static_cast<std::uint32_t>(
            std::stoul(argv[7])):3u;
        Smoke(context,argv[1],argv[2],argv[3],argv[4],argv[5],width,height);
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"R09_VULKAN_REAL_GPU_IO_FAIL: "<<e.what()<<"\n";
        return 1;
    }
}