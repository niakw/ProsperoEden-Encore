// SPDX-License-Identifier: GPL-3.0-or-later
// Real host Vulkan compute/readback for isolated R09 Min spatial shaders.
// Validates both zero residual and known synthetic RGB delta using actual GPU
// reads/writes. This is NOT a DLSS-NR network inference.
// Requires Vulkan 1.1 + storage RGBA16F/RGBA32F and linear sampling.
#include "dlss_nr_min_spatial_abi.h"
#include "dlss_nr_min_spatial_math.h"
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
void Check(VkResult r,const char* op) {
    if(r!=VK_SUCCESS)
        throw std::runtime_error(std::string(op)+" "+std::to_string(r));
}
struct Buffer {
    VkBuffer buffer{};
    VkDeviceMemory memory{};
    VkDeviceSize bytes{};
};
struct Image {
    VkImage image{};
    VkDeviceMemory memory{};
    VkImageView view{};
};
struct Host {
    VkInstance instance{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    std::uint32_t family{};
    VkCommandPool pool{};
    VkCommandBuffer cmd{};
    VkPhysicalDeviceMemoryProperties properties{};
    std::vector<Buffer> buffers{};
    std::vector<Image> images{};
    VkSampler sampler{};
    std::vector<VkDescriptorSetLayout> set_layouts{};
    VkDescriptorPool descriptor_pool{};
    std::vector<VkShaderModule> modules{};
    std::vector<VkPipelineLayout> pipeline_layouts{};
    std::vector<VkPipeline> pipelines{};

    ~Host() {
        if(device) {
            vkDeviceWaitIdle(device);
            for(auto p:pipelines)vkDestroyPipeline(device,p,nullptr);
            for(auto p:pipeline_layouts)vkDestroyPipelineLayout(device,p,nullptr);
            for(auto p:modules)vkDestroyShaderModule(device,p,nullptr);
            if(descriptor_pool)vkDestroyDescriptorPool(device,descriptor_pool,nullptr);
            for(auto s:set_layouts)vkDestroyDescriptorSetLayout(device,s,nullptr);
            if(sampler)vkDestroySampler(device,sampler,nullptr);
            for(auto i:images) {
                if(i.view)vkDestroyImageView(device,i.view,nullptr);
                if(i.image)vkDestroyImage(device,i.image,nullptr);
                if(i.memory)vkFreeMemory(device,i.memory,nullptr);
            }
            for(auto b:buffers) {
                if(b.buffer)vkDestroyBuffer(device,b.buffer,nullptr);
                if(b.memory)vkFreeMemory(device,b.memory,nullptr);
            }
            if(pool)vkDestroyCommandPool(device,pool,nullptr);
            vkDestroyDevice(device,nullptr);
        }
        if(instance)vkDestroyInstance(instance,nullptr);
    }
    std::uint32_t Memory(std::uint32_t bits,VkMemoryPropertyFlags flags) const {
        for(std::uint32_t i=0;i<properties.memoryTypeCount;++i)
            if((bits&(1u<<i)) &&
               (properties.memoryTypes[i].propertyFlags&flags)==flags)
                return i;
        throw std::runtime_error("No compatible Vulkan memory type");
    }
    void Init() {
        VkApplicationInfo app{};
        app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;
        app.pApplicationName="Eden R09 Min host GPU witness";
        app.apiVersion=VK_API_VERSION_1_1;
        VkInstanceCreateInfo ci{};
        ci.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
        ci.pApplicationInfo=&app;
        Check(vkCreateInstance(&ci,nullptr,&instance),"instance");
        std::uint32_t count{};
        Check(vkEnumeratePhysicalDevices(instance,&count,nullptr),"count");
        if(!count)throw std::runtime_error("No Vulkan physical device");
        std::vector<VkPhysicalDevice> devices(count);
        Check(vkEnumeratePhysicalDevices(instance,&count,devices.data()),"devices");
        for(const auto p:devices) {
            VkFormatProperties fp16{},fp32{};
            vkGetPhysicalDeviceFormatProperties(
                p,VK_FORMAT_R16G16B16A16_SFLOAT,&fp16);
            vkGetPhysicalDeviceFormatProperties(
                p,VK_FORMAT_R32G32B32A32_SFLOAT,&fp32);
            constexpr auto sampled=VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT |
                VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT;
            if((fp16.optimalTilingFeatures&
                (sampled|VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT)) !=
                (sampled|VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT) ||
               (fp32.optimalTilingFeatures&
                (sampled|VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT)) !=
                (sampled|VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT))
                continue;
            std::uint32_t n{};
            vkGetPhysicalDeviceQueueFamilyProperties(p,&n,nullptr);
            std::vector<VkQueueFamilyProperties> families(n);
            vkGetPhysicalDeviceQueueFamilyProperties(p,&n,families.data());
            for(std::uint32_t i=0;i<n;++i)
                if(families[i].queueFlags&VK_QUEUE_COMPUTE_BIT) {
                    physical=p;
                    family=i;
                    break;
                }
            if(physical)break;
        }
        if(!physical)
            throw std::runtime_error("No compute + FP16/FP32 image-capable ICD");
        VkPhysicalDeviceProperties gpu{};
        vkGetPhysicalDeviceProperties(physical,&gpu);
        std::cout<<"R09_MIN_HOST_GPU "<<gpu.deviceName<<"\n";
        vkGetPhysicalDeviceMemoryProperties(physical,&properties);
        float priority=1.0f;
        VkDeviceQueueCreateInfo qci{};
        qci.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
        qci.queueFamilyIndex=family;
        qci.queueCount=1u;
        qci.pQueuePriorities=&priority;
        VkDeviceCreateInfo dci{};
        dci.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
        dci.queueCreateInfoCount=1u;
        dci.pQueueCreateInfos=&qci;
        Check(vkCreateDevice(physical,&dci,nullptr,&device),"device");
        vkGetDeviceQueue(device,family,0u,&queue);
        VkCommandPoolCreateInfo pci{};
        pci.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        pci.queueFamilyIndex=family;
        Check(vkCreateCommandPool(device,&pci,nullptr,&pool),"pool");
        VkCommandBufferAllocateInfo cai{};
        cai.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        cai.commandPool=pool;
        cai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        cai.commandBufferCount=1u;
        Check(vkAllocateCommandBuffers(device,&cai,&cmd),"command");
    }
    Buffer NewBuffer(VkDeviceSize bytes,VkBufferUsageFlags usage) {
        Buffer b{};
        b.bytes=bytes;
        VkBufferCreateInfo ci{};
        ci.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        ci.size=bytes;
        ci.usage=usage;
        ci.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        Check(vkCreateBuffer(device,&ci,nullptr,&b.buffer),"buffer");
        VkMemoryRequirements req{};
        vkGetBufferMemoryRequirements(device,b.buffer,&req);
        VkMemoryAllocateInfo ai{};
        ai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize=req.size;
        ai.memoryTypeIndex=Memory(req.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
            VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        Check(vkAllocateMemory(device,&ai,nullptr,&b.memory),"buffer memory");
        Check(vkBindBufferMemory(device,b.buffer,b.memory,0u),"buffer bind");
        buffers.push_back(b);
        return b;
    }
    Image NewImage(std::uint32_t w,std::uint32_t h,VkFormat fmt,
                   VkImageUsageFlags usage) {
        Image o{};
        VkImageCreateInfo ci{};
        ci.sType=VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ci.imageType=VK_IMAGE_TYPE_2D;
        ci.format=fmt;
        ci.extent={w,h,1u};
        ci.mipLevels=1u;
        ci.arrayLayers=1u;
        ci.samples=VK_SAMPLE_COUNT_1_BIT;
        ci.tiling=VK_IMAGE_TILING_OPTIMAL;
        ci.usage=usage;
        ci.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        ci.initialLayout=VK_IMAGE_LAYOUT_UNDEFINED;
        Check(vkCreateImage(device,&ci,nullptr,&o.image),"image");
        VkMemoryRequirements req{};
        vkGetImageMemoryRequirements(device,o.image,&req);
        VkMemoryAllocateInfo ai{};
        ai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize=req.size;
        ai.memoryTypeIndex=Memory(req.memoryTypeBits,0u);
        Check(vkAllocateMemory(device,&ai,nullptr,&o.memory),"image memory");
        Check(vkBindImageMemory(device,o.image,o.memory,0u),"image bind");
        VkImageViewCreateInfo vi{};
        vi.sType=VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        vi.image=o.image;
        vi.viewType=VK_IMAGE_VIEW_TYPE_2D;
        vi.format=fmt;
        vi.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u};
        Check(vkCreateImageView(device,&vi,nullptr,&o.view),"image view");
        images.push_back(o);
        return o;
    }
    VkShaderModule Shader(const char* file) {
        std::ifstream stream(file,std::ios::binary|std::ios::ate);
        if(!stream)throw std::runtime_error("Missing SPIR-V");
        const auto size=stream.tellg();
        if(size<=0 || size%4!=0)
            throw std::runtime_error("Invalid SPIR-V byte count");
        std::vector<std::uint32_t> words(std::size_t(size)/4u);
        stream.seekg(0);
        stream.read(reinterpret_cast<char*>(words.data()),size);
        if(!stream)throw std::runtime_error("Truncated SPIR-V");
        VkShaderModuleCreateInfo ci{};
        ci.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        ci.codeSize=std::size_t(size);
        ci.pCode=words.data();
        VkShaderModule m{};
        Check(vkCreateShaderModule(device,&ci,nullptr,&m),"shader");
        modules.push_back(m);
        return m;
    }
    VkDescriptorSetLayout SetLayout(
        const VkDescriptorSetLayoutBinding* bindings,std::uint32_t count) {
        VkDescriptorSetLayoutCreateInfo ci{};
        ci.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
        ci.bindingCount=count;
        ci.pBindings=bindings;
        VkDescriptorSetLayout result{};
        Check(vkCreateDescriptorSetLayout(device,&ci,nullptr,&result),"set layout");
        set_layouts.push_back(result);
        return result;
    }
    VkPipeline Pipeline(VkShaderModule shader,VkDescriptorSetLayout set,
                        VkPipelineLayout& out_layout) {
        const VkPushConstantRange range{
            VK_SHADER_STAGE_COMPUTE_BIT,0u,
            sizeof(Eden::Graphics::DlssNrMin::SpatialShaderPush)};
        VkPipelineLayoutCreateInfo li{};
        li.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        li.setLayoutCount=1u;
        li.pSetLayouts=&set;
        li.pushConstantRangeCount=1u;
        li.pPushConstantRanges=&range;
        Check(vkCreatePipelineLayout(device,&li,nullptr,&out_layout),"pipeline layout");
        pipeline_layouts.push_back(out_layout);
        VkPipelineShaderStageCreateInfo stage{};
        stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;
        stage.module=shader;
        stage.pName="main";
        VkComputePipelineCreateInfo pi{};
        pi.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
        pi.stage=stage;
        pi.layout=out_layout;
        VkPipeline p{};
        Check(vkCreateComputePipelines(device,VK_NULL_HANDLE,1u,&pi,nullptr,&p),
              "compute pipeline");
        pipelines.push_back(p);
        return p;
    }
};
VkImageMemoryBarrier Transition(VkImage image,VkImageLayout from,
                                VkImageLayout to,VkAccessFlags src,
                                VkAccessFlags dst) {
    VkImageMemoryBarrier bar{};
    bar.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    bar.srcAccessMask=src;
    bar.dstAccessMask=dst;
    bar.oldLayout=from;
    bar.newLayout=to;
    bar.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
    bar.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
    bar.image=image;
    bar.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u};
    return bar;
}
void ImageBarrier(VkCommandBuffer cmd,VkImageMemoryBarrier bar,
                  VkPipelineStageFlags src,VkPipelineStageFlags dst) {
    vkCmdPipelineBarrier(cmd,src,dst,0u,0u,nullptr,0u,nullptr,1u,&bar);
}
void Run(Host& h,const char* pack_spv,const char* delta_spv,
         const char* transfer_spv,bool identity,bool widescreen) {
    // 160x90 -> 144x82 tests asymmetric 16:9 and a non-8-aligned
    // output edge. The 32x32 -> 28x28 canary catches the prior path.
    const std::uint32_t W=widescreen?160u:32u;
    const std::uint32_t H=widescreen?90u:32u;
    const std::uint32_t QX=widescreen?144u:28u;
    const std::uint32_t QY=widescreen?82u:28u;
    const float center=widescreen?0.8f:0.5f;
    const VkDeviceSize bytes=VkDeviceSize(W)*H*4u*sizeof(float);
    const auto staging=h.NewBuffer(bytes,VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    const auto readback=h.NewBuffer(bytes,VK_BUFFER_USAGE_TRANSFER_DST_BIT);
    const auto source=h.NewImage(W,H,VK_FORMAT_R32G32B32A32_SFLOAT,
        VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    const auto work=h.NewImage(QX,QY,VK_FORMAT_R16G16B16A16_SFLOAT,
        VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    const auto enhanced=h.NewImage(QX,QY,VK_FORMAT_R16G16B16A16_SFLOAT,
        VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    const auto target=h.NewImage(W,H,VK_FORMAT_R32G32B32A32_SFLOAT,
        VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
    std::vector<float> pixels(std::size_t(W)*H*4u);
    for(std::uint32_t y=0;y<H;++y)
        for(std::uint32_t x=0;x<W;++x) {
            const auto i=(y*W+x)*4u;
            // Real HDR (>1) and sharp UI-like checkerboard edges retain
            // their exact native pixel values when residual is zero.
            const float edge=x<W/2u?0.05f:1.65f;
            const float checker=((x/4u+y/4u)&1u)?0.2f:1.0f;
            pixels[i]=edge+0.005f*float(y);
            pixels[i+1u]=checker+0.004f*float(x);
            pixels[i+2u]=(y<H/2u?1.25f:0.15f)+0.001f*float(x);
            pixels[i+3u]=((x+y)&1u)?1.0f:0.25f;
        }
    void* ptr{};
    Check(vkMapMemory(h.device,staging.memory,0u,bytes,0u,&ptr),"map source");
    std::memcpy(ptr,pixels.data(),std::size_t(bytes));
    vkUnmapMemory(h.device,staging.memory);

    VkSamplerCreateInfo sci{};
    sci.sType=VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sci.magFilter=VK_FILTER_LINEAR;
    sci.minFilter=VK_FILTER_LINEAR;
    sci.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sci.addressModeU=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeV=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.minLod=0.0f;
    sci.maxLod=0.0f;
    Check(vkCreateSampler(h.device,&sci,nullptr,&h.sampler),"sampler");
    const VkDescriptorSetLayoutBinding pb[]{
        {0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,
            VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1u,
            VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    const VkDescriptorSetLayoutBinding ub[]{
        {0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,
            VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,
            VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {2u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,
            VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {3u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1u,
            VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
    const auto pset=h.SetLayout(pb,2u),dset=h.SetLayout(pb,2u),
               uset=h.SetLayout(ub,4u);
    const std::array<VkDescriptorPoolSize,2> sizes{{
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,5u},
        {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,3u}}};
    VkDescriptorPoolCreateInfo dpi{};
    dpi.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpi.maxSets=3u;
    dpi.poolSizeCount=std::uint32_t(sizes.size());
    dpi.pPoolSizes=sizes.data();
    Check(vkCreateDescriptorPool(h.device,&dpi,nullptr,&h.descriptor_pool),
          "descriptor pool");
    const std::array<VkDescriptorSetLayout,3> layouts{pset,dset,uset};
    std::array<VkDescriptorSet,3> sets{};
    VkDescriptorSetAllocateInfo asi{};
    asi.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    asi.descriptorPool=h.descriptor_pool;
    asi.descriptorSetCount=3u;
    asi.pSetLayouts=layouts.data();
    Check(vkAllocateDescriptorSets(h.device,&asi,sets.data()),"alloc sets");
    const VkDescriptorImageInfo original{h.sampler,source.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkDescriptorImageInfo work_read{h.sampler,work.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkDescriptorImageInfo work_write{VK_NULL_HANDLE,work.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkDescriptorImageInfo enhanced_read{h.sampler,enhanced.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkDescriptorImageInfo enhanced_write{VK_NULL_HANDLE,enhanced.view,VK_IMAGE_LAYOUT_GENERAL};
    const VkDescriptorImageInfo output{VK_NULL_HANDLE,target.view,VK_IMAGE_LAYOUT_GENERAL};
    std::array<VkWriteDescriptorSet,8> writes{};
    auto write=[&](std::size_t n,VkDescriptorSet set,std::uint32_t binding,
                   VkDescriptorType type,const VkDescriptorImageInfo* info) {
        auto& w=writes[n];
        w.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w.dstSet=set;
        w.dstBinding=binding;
        w.descriptorCount=1u;
        w.descriptorType=type;
        w.pImageInfo=info;
    };
    write(0,sets[0],0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,&original);
    write(1,sets[0],1u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,&work_write);
    write(2,sets[1],0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,&work_read);
    write(3,sets[1],1u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,&enhanced_write);
    write(4,sets[2],0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,&original);
    write(5,sets[2],1u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,&work_read);
    write(6,sets[2],2u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
          identity?&work_read:&enhanced_read);
    write(7,sets[2],3u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,&output);
    vkUpdateDescriptorSets(h.device,std::uint32_t(writes.size()),writes.data(),
                           0u,nullptr);
    VkPipelineLayout pack_layout{},delta_layout{},unpack_layout{};
    const auto pack=h.Pipeline(h.Shader(pack_spv),pset,pack_layout);
    const auto delta=h.Pipeline(h.Shader(delta_spv),dset,delta_layout);
    const auto unpack=h.Pipeline(h.Shader(transfer_spv),uset,unpack_layout);
    const Eden::Graphics::DlssNrMin::SpatialShaderPush push{
        W,H,QX,QY,center,center,float(QX)/float(W),float(QY)/float(H)};

    VkCommandBufferBeginInfo begin{};
    begin.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    Check(vkBeginCommandBuffer(h.cmd,&begin),"begin");
    ImageBarrier(h.cmd,Transition(source.image,VK_IMAGE_LAYOUT_UNDEFINED,
                 VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,0u,
                 VK_ACCESS_TRANSFER_WRITE_BIT),
                 VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkBufferImageCopy region{};
    region.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0u,0u,1u};
    region.imageExtent={W,H,1u};
    vkCmdCopyBufferToImage(h.cmd,staging.buffer,source.image,
                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1u,&region);
    ImageBarrier(h.cmd,Transition(source.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                 VK_IMAGE_LAYOUT_GENERAL,VK_ACCESS_TRANSFER_WRITE_BIT,
                 VK_ACCESS_SHADER_READ_BIT),
                 VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    ImageBarrier(h.cmd,Transition(work.image,VK_IMAGE_LAYOUT_UNDEFINED,
                 VK_IMAGE_LAYOUT_GENERAL,0u,VK_ACCESS_SHADER_WRITE_BIT),
                 VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    ImageBarrier(h.cmd,Transition(enhanced.image,VK_IMAGE_LAYOUT_UNDEFINED,
                 VK_IMAGE_LAYOUT_GENERAL,0u,VK_ACCESS_SHADER_WRITE_BIT),
                 VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    ImageBarrier(h.cmd,Transition(target.image,VK_IMAGE_LAYOUT_UNDEFINED,
                 VK_IMAGE_LAYOUT_GENERAL,0u,VK_ACCESS_SHADER_WRITE_BIT),
                 VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    vkCmdBindPipeline(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pack);
    vkCmdBindDescriptorSets(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,
                            pack_layout,0u,1u,&sets[0],0u,nullptr);
    vkCmdPushConstants(h.cmd,pack_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(push),&push);
    vkCmdDispatch(h.cmd,(QX+7u)/8u,(QY+7u)/8u,1u);
    ImageBarrier(h.cmd,Transition(work.image,VK_IMAGE_LAYOUT_GENERAL,
                 VK_IMAGE_LAYOUT_GENERAL,VK_ACCESS_SHADER_WRITE_BIT,
                 VK_ACCESS_SHADER_READ_BIT),
                 VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                 VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    if(!identity) {
        vkCmdBindPipeline(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,delta);
        vkCmdBindDescriptorSets(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,
                                delta_layout,0u,1u,&sets[1],0u,nullptr);
        vkCmdPushConstants(h.cmd,delta_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                           0u,sizeof(push),&push);
        vkCmdDispatch(h.cmd,(QX+7u)/8u,(QY+7u)/8u,1u);
        ImageBarrier(h.cmd,Transition(enhanced.image,VK_IMAGE_LAYOUT_GENERAL,
                     VK_IMAGE_LAYOUT_GENERAL,VK_ACCESS_SHADER_WRITE_BIT,
                     VK_ACCESS_SHADER_READ_BIT),
                     VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                     VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    }
    vkCmdBindPipeline(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,unpack);
    vkCmdBindDescriptorSets(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,
                            unpack_layout,0u,1u,&sets[2],0u,nullptr);
    vkCmdPushConstants(h.cmd,unpack_layout,VK_SHADER_STAGE_COMPUTE_BIT,
                       0u,sizeof(push),&push);
    vkCmdDispatch(h.cmd,(W+7u)/8u,(H+7u)/8u,1u);
    ImageBarrier(h.cmd,Transition(target.image,VK_IMAGE_LAYOUT_GENERAL,
                 VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                 VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT),
                 VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                 VK_PIPELINE_STAGE_TRANSFER_BIT);
    vkCmdCopyImageToBuffer(h.cmd,target.image,
                            VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                            readback.buffer,1u,&region);
    VkMemoryBarrier host_barrier{};
    host_barrier.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    host_barrier.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
    host_barrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(h.cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT,0u,1u,&host_barrier,
                         0u,nullptr,0u,nullptr);
    Check(vkEndCommandBuffer(h.cmd),"end");
    VkSubmitInfo submission{};
    submission.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submission.commandBufferCount=1u;
    submission.pCommandBuffers=&h.cmd;
    Check(vkQueueSubmit(h.queue,1u,&submission,VK_NULL_HANDLE),"submit");
    Check(vkQueueWaitIdle(h.queue),"wait");
    Check(vkMapMemory(h.device,readback.memory,0u,bytes,0u,&ptr),"readback");
    const auto* found=static_cast<const float*>(ptr);
    for(std::size_t i=0u;i<pixels.size();++i) {
        const auto channel=i%4u;
        // Independent host oracle for the spatially varying synthetic
        // contribution. Bilinear interpolation of a work-space linear
        // gradient equals its analytic value at the sampled coordinate
        // except at clamped texel-center boundaries.
        const std::uint32_t x=std::uint32_t(i/4u)%W;
        const std::uint32_t y=std::uint32_t(i/4u)/W;
        const Eden::Graphics::DlssNrMin::AxisWarp warp_x{
            W,QX,center,float(QX)/float(W)};
        const Eden::Graphics::DlssNrMin::AxisWarp warp_y{
            H,QY,center,float(QY)/float(H)};
        const auto px=Eden::Graphics::DlssNrMin::WarpPixel(float(x)+0.5f,warp_x);
        const auto py=Eden::Graphics::DlssNrMin::WarpPixel(float(y)+0.5f,warp_y);
        if(!std::isfinite(px)||!std::isfinite(py))
            throw std::runtime_error("Invalid reference axis mapping");
        const float ux=std::clamp(px,0.5f,float(QX)-0.5f)/float(QX);
        const float uy=std::clamp(py,0.5f,float(QY)-0.5f)/float(QY);
        const float known_delta[4]{0.125f*ux,-0.0625f*uy,
                                   0.125f*(ux+uy),0.0f};
        const float expected=pixels[i]+(identity?0.0f:known_delta[channel]);
        if(!std::isfinite(found[i]) ||
           std::fabs(found[i]-expected)>0.0035f) {
            const auto pixel=i/4u;
            const auto actual=found[i];
            vkUnmapMemory(h.device,readback.memory);
            throw std::runtime_error(
                "R09_MIN_VULKAN_RESIDUAL_GPU_MISMATCH pixel="+
                std::to_string(pixel)+" channel="+std::to_string(channel)+
                " actual="+std::to_string(actual)+
                " expected="+std::to_string(expected));
        }
    }
    vkUnmapMemory(h.device,readback.memory);
    std::cout<<(identity?"R09_MIN_VULKAN_IDENTITY_GPU_PASS ":"R09_MIN_VULKAN_SPATIALLY_VARYING_DELTA_GPU_PASS ")
             <<W<<"x"<<H<<"->"<<QX<<"x"<<QY<<"->"<<W<<"x"<<H<<"\n";
    std::cout<<"R09_MIN_HOST_VULKAN_PUBLIC_FIXTURE_NO_DLSS_INFERENCE\n";
}
} // namespace

int main(int argc,char** argv) {
    if(argc<4 || argc>6) {
        std::cerr<<"usage: r09_min_vk_spatial_smoke <pack.spv> <synthetic_delta.spv> <detail_transfer.spv> [--identity] [--widescreen]\n";
        return 2;
    }
    try {
        Host h;
        h.Init();
        bool identity=false,widescreen=false;
        for(int i=4;i<argc;++i) {
            const std::string opt{argv[i]};
            if(opt=="--identity" && !identity)identity=true;
            else if(opt=="--widescreen" && !widescreen)widescreen=true;
            else return 2;
        }
        Run(h,argv[1],argv[2],argv[3],identity,widescreen);
        return 0;
    } catch(const std::exception& e) {
        std::cerr<<"R09_MIN_VULKAN_GPU_SMOKE_FAIL: "<<e.what()<<"\n";
        return 1;
    }
}
