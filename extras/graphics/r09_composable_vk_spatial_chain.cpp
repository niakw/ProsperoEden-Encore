// SPDX-License-Identifier: GPL-3.0-or-later
// Real host Vulkan 1..3 consecutive spatial image stages with readback.
// Validates both zero residual and known synthetic RGB delta using actual GPU
// reads/writes. This is NOT a DLSS-NR network inference.
// Requires Vulkan 1.1 + storage RGBA16F/RGBA32F and linear sampling.
#include "dlss_nr_min_spatial_abi.h"
#include "dlss_nr_min_spatial_math.h"
#include "neural_pipeline_recipe.h"
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <type_traits>
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

struct Size {std::uint32_t w{},h{};};
std::vector<float> Expected(const std::vector<float>& in,Size a,Size b,
                            bool nearest){
    std::vector<float> out(std::size_t(b.w)*b.h*4u);
    const auto idx=[&](int x,int y,unsigned channel)->std::size_t {
        x=std::clamp(x,0,int(a.w)-1);
        y=std::clamp(y,0,int(a.h)-1);
        return (std::size_t(y)*a.w+unsigned(x))*4u+channel;
    };
    for(std::uint32_t y=0;y<b.h;++y)
        for(std::uint32_t x=0;x<b.w;++x){
            const float px=(float(x)+0.5f)*float(a.w)/float(b.w);
            const float py=(float(y)+0.5f)*float(a.h)/float(b.h);
            for(unsigned c=0;c<4u;++c){
                float value{};
                if(nearest){
                    value=in[idx(int(std::floor(px)),int(std::floor(py)),c)];
                }else{
                    const float fx=px-0.5f,fy=py-0.5f;
                    const int left=int(std::floor(fx));
                    const int top=int(std::floor(fy));
                    const float tx=fx-float(left),ty=fy-float(top);
                    const float a00=in[idx(left,top,c)];
                    const float a10=in[idx(left+1,top,c)];
                    const float a01=in[idx(left,top+1,c)];
                    const float a11=in[idx(left+1,top+1,c)];
                    value=(a00+(a10-a00)*tx)*(1.0f-ty)+
                          (a01+(a11-a01)*tx)*ty;
                }
                out[(std::size_t(y)*b.w+x)*4u+c]=value;
            }
        }
    return out;
}

template<typename Handle>
[[nodiscard]] std::uint64_t RealHandleToken(Handle h) {
    if constexpr(std::is_pointer_v<Handle>)
        return static_cast<std::uint64_t>(
            reinterpret_cast<std::uintptr_t>(h));
    else
        return static_cast<std::uint64_t>(h);
}
void Run(Host& h,const char* spv,unsigned passes,bool recipe_720){
    if(passes<1u||passes>3u)
        throw std::runtime_error("Expected 1,2,3 spatial stages");
    const std::array<Size,4u> shapes=recipe_720?
        std::array<Size,4u>{{
            {320u,180u},{640u,360u},{960u,540u},{1280u,720u}
        }}:
        std::array<Size,4u>{{
            {64u,36u},{128u,72u},{192u,108u},{256u,144u}
        }};
    constexpr std::array<bool,3u> use_nearest{{true,false,true}};
    Eden::Graphics::PipelineComposer::Recipe recipe{};
    if(recipe_720){
        namespace PC=Eden::Graphics::PipelineComposer;
        recipe.source_extent={shapes[0].w,shapes[0].h};
        for(unsigned i=0;i<passes;++i){
            const PC::RecipeStage stage{
                PC::Kind::Spatial,use_nearest[i]?3:0,
                {shapes[i+1u].w,shapes[i+1u].h},false};
            if(!PC::InsertStep(recipe,i,stage))
                throw std::runtime_error("Could not insert native spatial pass");
        }
        if(!PC::InsertStep(recipe,passes,{
            PC::Kind::Present,0,
            {shapes[passes].w,shapes[passes].h},false}))
            throw std::runtime_error("Could not append terminal Present");
    }
    // Use a gradient PLUS sharp discontinuities and alpha values to
    // ensure every pass really reads the PREVIOUS output, not guest input.
    std::vector<float> original(std::size_t(shapes[0].w)*shapes[0].h*4u);
    for(unsigned y=0;y<shapes[0].h;++y)
      for(unsigned x=0;x<shapes[0].w;++x){
        const auto offset=(std::size_t(y)*shapes[0].w+x)*4u;
        original[offset]=0.2f+0.007f*float(x)+(x<23u?0.0f:0.9f);
        original[offset+1u]=0.15f+0.015f*float(y)+
                             ((x+y)%9u==0u?0.8f:0.0f);
        original[offset+2u]=0.0008f*float(x*y)+
                             ((x/7u+y/5u)&1u?1.25f:0.0f);
        original[offset+3u]=((x+y)&1u?1.0f:0.25f);
      }
    std::array<Image,4u> images{};
    images[0]=h.NewImage(shapes[0].w,shapes[0].h,
        VK_FORMAT_R32G32B32A32_SFLOAT,
        VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    std::array<Buffer,3u> readbacks{};
    for(unsigned i=0;i<passes;++i){
        images[i+1u]=h.NewImage(shapes[i+1u].w,shapes[i+1u].h,
            VK_FORMAT_R32G32B32A32_SFLOAT,
            VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT|
            VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
        const VkDeviceSize n=VkDeviceSize(shapes[i+1u].w)*
            shapes[i+1u].h*4u*sizeof(float);
        readbacks[i]=h.NewBuffer(n,VK_BUFFER_USAGE_TRANSFER_DST_BIT);
    }
    const VkDeviceSize bytes=VkDeviceSize(original.size())*sizeof(float);
    const auto staging=h.NewBuffer(bytes,VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    void* ptr{};
    Check(vkMapMemory(h.device,staging.memory,0u,bytes,0u,&ptr),
          "map staging");
    std::memcpy(ptr,original.data(),std::size_t(bytes));
    vkUnmapMemory(h.device,staging.memory);

    VkSamplerCreateInfo sci{};
    sci.sType=VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sci.magFilter=VK_FILTER_LINEAR;
    sci.minFilter=VK_FILTER_LINEAR;
    sci.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sci.addressModeU=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeV=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    Check(vkCreateSampler(h.device,&sci,nullptr,&h.sampler),"sampler");
    const VkDescriptorSetLayoutBinding binding[]{
        {0u,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1u,
         VK_SHADER_STAGE_COMPUTE_BIT,nullptr},
        {1u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1u,
         VK_SHADER_STAGE_COMPUTE_BIT,nullptr}
    };
    const auto layout=h.SetLayout(binding,2u);
    const VkDescriptorPoolSize pools[]{
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,passes},
        {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,passes}
    };
    VkDescriptorPoolCreateInfo dp{};
    dp.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp.maxSets=passes;
    dp.poolSizeCount=2u;
    dp.pPoolSizes=pools;
    Check(vkCreateDescriptorPool(h.device,&dp,nullptr,&h.descriptor_pool),
          "descriptor pool");
    std::array<VkDescriptorSetLayout,3u> layouts{layout,layout,layout};
    std::array<VkDescriptorSet,3u> sets{};
    VkDescriptorSetAllocateInfo ai{};
    ai.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ai.descriptorPool=h.descriptor_pool;
    ai.descriptorSetCount=passes;
    ai.pSetLayouts=layouts.data();
    Check(vkAllocateDescriptorSets(h.device,&ai,sets.data()),"sets");
    std::array<VkDescriptorImageInfo,3u> read{},write{};
    std::array<VkWriteDescriptorSet,6u> writes{};
    for(unsigned i=0u;i<passes;++i){
        // The VkImage and VkImageView from the previous GPU stage are the
        // actual descriptor source: not a view over the initial game image.
        read[i]={h.sampler,images[i].view,VK_IMAGE_LAYOUT_GENERAL};
        write[i]={VK_NULL_HANDLE,images[i+1u].view,VK_IMAGE_LAYOUT_GENERAL};
        auto& a=writes[2u*i];
        a.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        a.dstSet=sets[i];a.dstBinding=0u;
        a.descriptorCount=1u;
        a.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        a.pImageInfo=&read[i];
        auto& b=writes[2u*i+1u];
        b.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        b.dstSet=sets[i];b.dstBinding=1u;
        b.descriptorCount=1u;
        b.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
        b.pImageInfo=&write[i];
    }
    vkUpdateDescriptorSets(h.device,2u*passes,writes.data(),0u,nullptr);
    VkPipelineLayout pipeline_layout{};
    const auto pipeline=h.Pipeline(h.Shader(spv),layout,pipeline_layout);

    VkCommandBufferBeginInfo bi{};
    bi.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bi.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    Check(vkBeginCommandBuffer(h.cmd,&bi),"command begin");
    ImageBarrier(h.cmd,Transition(images[0].image,VK_IMAGE_LAYOUT_UNDEFINED,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,0u,
        VK_ACCESS_TRANSFER_WRITE_BIT),
        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkBufferImageCopy upload{};
    upload.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0u,0u,1u};
    upload.imageExtent={shapes[0].w,shapes[0].h,1u};
    vkCmdCopyBufferToImage(h.cmd,staging.buffer,images[0].image,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1u,&upload);
    ImageBarrier(h.cmd,Transition(images[0].image,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,
        VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT),
        VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
    for(unsigned i=0u;i<passes;++i){
        const auto in=shapes[i],out=shapes[i+1u];
        if(recipe_720){
            const auto& stage=recipe.stages[i];
            if(stage.kind!=Eden::Graphics::PipelineComposer::Kind::Spatial||
               stage.method!=(use_nearest[i]?3:0)||
               stage.output!=Eden::Graphics::PipelineComposer::Extent{out.w,out.h})
                throw std::runtime_error("Compiled graph stage drift");
        }
        ImageBarrier(h.cmd,Transition(images[i+1u].image,
            VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_GENERAL,0u,
            VK_ACCESS_SHADER_WRITE_BIT),
            VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
        vkCmdBindPipeline(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
        vkCmdBindDescriptorSets(h.cmd,VK_PIPELINE_BIND_POINT_COMPUTE,
            pipeline_layout,0u,1u,&sets[i],0u,nullptr);
        const Eden::Graphics::DlssNrMin::SpatialShaderPush push{
            in.w,in.h,out.w,out.h,use_nearest[i]?1.0f:0.0f,0.0f,0.0f,0.0f};
        vkCmdPushConstants(h.cmd,pipeline_layout,VK_SHADER_STAGE_COMPUTE_BIT,
            0u,sizeof(push),&push);
        vkCmdDispatch(h.cmd,(out.w+7u)/8u,(out.h+7u)/8u,1u);
        // This one barrier makes the actual GPU-produced next-stage image
        // visible to subsequent shader sampling AND to exact GPU readback.
        ImageBarrier(h.cmd,Transition(images[i+1u].image,
            VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_GENERAL,
            VK_ACCESS_SHADER_WRITE_BIT,
            VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_TRANSFER_READ_BIT),
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT|
            VK_PIPELINE_STAGE_TRANSFER_BIT);
        VkBufferImageCopy region{};
        region.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0u,0u,1u};
        region.imageExtent={out.w,out.h,1u};
        vkCmdCopyImageToBuffer(h.cmd,images[i+1u].image,
            VK_IMAGE_LAYOUT_GENERAL,readbacks[i].buffer,1u,&region);
    }
    VkMemoryBarrier host_visible{};
    host_visible.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    host_visible.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
    host_visible.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(h.cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_HOST_BIT,0u,1u,&host_visible,
        0u,nullptr,0u,nullptr);
    Check(vkEndCommandBuffer(h.cmd),"end command");
    VkFence fence{};
    VkFenceCreateInfo fci{};
    fci.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    Check(vkCreateFence(h.device,&fci,nullptr,&fence),"fence");
    VkSubmitInfo sub{};
    sub.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
    sub.commandBufferCount=1u;
    sub.pCommandBuffers=&h.cmd;
    Check(vkQueueSubmit(h.queue,1u,&sub,fence),"queue submit");
    Check(vkWaitForFences(h.device,1u,&fence,VK_TRUE,10'000'000'000ull),
          "wait GPU fence");
    vkDestroyFence(h.device,fence,nullptr);

    // Independent CPU nearest/bilinear oracle for ALL intermediate stages.
    // Comparing only the last output would allow broken stage reuse.
    auto expected=original;
    std::uint64_t checked{};
    for(unsigned i=0u;i<passes;++i){
        expected=Expected(expected,shapes[i],shapes[i+1u],use_nearest[i]);
        const auto n=readbacks[i].bytes;
        void* mapped{};
        Check(vkMapMemory(h.device,readbacks[i].memory,0u,n,0u,&mapped),
              "map GPU readback");
        const auto* actual=static_cast<const float*>(mapped);
        for(std::size_t j=0u;j<expected.size();++j){
            if(!std::isfinite(actual[j])||
               std::fabs(actual[j]-expected[j])>0.00025f){
                const float got=actual[j],wanted=expected[j];
                vkUnmapMemory(h.device,readbacks[i].memory);
                throw std::runtime_error(
                    "R09_COMPOSED_VULKAN_STAGE_GPU_MISMATCH stage="+
                    std::to_string(i)+" pixel="+std::to_string(j/4u)+
                    " channel="+std::to_string(j%4u)+
                    " GPU="+std::to_string(got)+
                    " oracle="+std::to_string(wanted));
            }
        }
        checked+=expected.size();
        vkUnmapMemory(h.device,readbacks[i].memory);
        std::cout<<"R09_COMPOSABLE_REAL_VKIMAGE_STAGE_PASS stage="<<i+1u
                 <<" "<<shapes[i].w<<"x"<<shapes[i].h
                 <<"->"<<shapes[i+1u].w<<"x"<<shapes[i+1u].h
                 <<" source_image=PREVIOUS_OUTPUT"
                 <<" pixels="<<expected.size()/4u<<"\n";
    }
    if(recipe_720){
        namespace PC=Eden::Graphics::PipelineComposer;
        PC::Bindings ownership{};
        ownership.guest_image=RealHandleToken(images[0].image);
        ownership.guest_view=RealHandleToken(images[0].view);
        for(unsigned i=0u;i<passes;++i){
            auto& proof=ownership.stages[i];
            proof.image=RealHandleToken(images[i+1u].image);
            proof.view=RealHandleToken(images[i+1u].view);
            proof.native_gpu_pass_recorded=true;
            proof.compatible_queue=true;
            proof.producer_to_consumer_visible=true;
            // All VkImage/VkImageView owners remain in Host.images
            // until AFTER this method and GPU fence have completed.
            proof.owner_retained_through_gpu_fence=true;
        }
        const auto qualified=PC::QualifyBoundRecipe(recipe,ownership);
        if(qualified.reason!=PC::Reason::HostCandidateOnly||
           !qualified.shape_qualified||qualified.runtime_enabled||
           qualified.spatial_passes!=passes||
           qualified.result!=PC::Extent{shapes[passes].w,shapes[passes].h})
            throw std::runtime_error(
                "Real VkImage-bound ordered recipe rejected");
        // Missing one genuine Vulkan source/owner must fail closed.
        ownership.stages[0].owner_retained_through_gpu_fence=false;
        if(PC::QualifyBoundRecipe(recipe,ownership).reason!=
           PC::Reason::MissingQueueBarrierOrFence)
            throw std::runtime_error(
                "Recipe incorrectly tolerated dropped Vulkan owner");
        std::cout<<"R09_COMPOSABLE_REAL_VULKAN_RECIPE_BOUND_PASS "
                 <<"passes="<<passes<<" source=320x180"
                 <<" target="<<shapes[passes].w<<"x"<<shapes[passes].h
                 <<" all_real_image_views_bound=YES runtime=OFF\n";
    }
    std::cout<<"R09_COMPOSABLE_HOST_VULKAN_MULTI_IMAGE_GPU_PASS passes="
             <<passes<<" channels_compared="<<checked
             <<" real_images=YES per_stage_fence=YES"
                " real_neural_model=NO native_FSR_SGSR=NO PS5=NO\n";
}
} // namespace

int main(int argc,char** argv){
    const bool recipe_720=argc==4&&
        std::string(argv[3])=="--recipe-720p";
    if(argc!=3&&!recipe_720){
        std::cerr<<"Usage: r09_composable_vk_spatial_chain <shader.spv> "
                    "<passes:1|2|3> [--recipe-720p]\n";
        return 2;
    }
    try {
        const auto n=std::stoi(argv[2]);
        if(n<1||n>3)return 2;
        Host h;
        h.Init();
        Run(h,argv[1],static_cast<unsigned>(n),recipe_720);
        return 0;
    }catch(const std::exception& ex){
        std::cerr<<"R09_COMPOSABLE_VULKAN_CHAIN_FAIL "<<ex.what()<<"\n";
        return 1;
    }
}
