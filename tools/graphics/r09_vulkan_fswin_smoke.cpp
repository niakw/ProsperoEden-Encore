// SPDX-License-Identifier: MIT
// Run the R09 texture->native proxy->sampleable Vulkan image path on a
// genuine Vulkan compute queue, including barriers and pixel readback.
// This intentionally does NOT execute a neural network or an emulator.
#include <vulkan/vulkan.h>
#include "video_core/renderer_vulkan/nr_rdna2_model_file.h"
#include "nr_dll_launch_preflight.h"
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


// Exact production shader layout: 8 unsigned 32-bit push constants.
struct DensePush {
    std::uint32_t input_bytes,weight_bytes,residual_bytes,scale_floats;
    std::uint32_t output_bytes,windows,channels,stage;
};
static_assert(sizeof(DensePush)==32u);
void SmokeFSwinDense(Context& c,const char* spirv,const char* private_model=nullptr){
    constexpr std::uint32_t channels=32u,tokens=64u,half=2u;
    constexpr VkDeviceSize fp8_bytes=tokens*channels;
    constexpr VkDeviceSize raw_bytes=fp8_bytes*half;
    const Buffer input=c.MakeBuffer(fp8_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer weights=c.MakeBuffer(channels*channels,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer residual=c.MakeBuffer(fp8_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer scales=c.MakeBuffer(channels*sizeof(float),VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer quant=c.MakeBuffer(fp8_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    const Buffer raw=c.MakeBuffer(raw_bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    constexpr std::array<std::uint8_t,4> e4{
        0x28u,0x30u,0x38u,0xb0u}; // 0.25,0.5,1.0,-0.5
    constexpr std::array<std::uint16_t,4> f16{
        0x3400u,0x3800u,0x3c00u,0xb800u};
    const auto write=[&](const Buffer& b,const void* data,VkDeviceSize bytes){
        void* mapped=nullptr;
        Check(vkMapMemory(c.device,b.memory,0u,bytes,0u,&mapped),"map upload");
        std::memcpy(mapped,data,std::size_t(bytes));
        vkUnmapMemory(c.device,b.memory);
    };
    std::array<std::uint8_t,fp8_bytes> input_data{};
    for(std::uint32_t t=0u;t<tokens;++t)
        for(std::uint32_t ch=0u;ch<channels;++ch)
            input_data[t*channels+ch]=e4[(t+ch)%e4.size()];
    write(input,input_data.data(),fp8_bytes);
    std::array<std::uint8_t,channels*channels> matrix{};
    if(private_model){
        // A file with the right tensor name and dimensions is not proof
        // of learned weights. Authenticate ALL 599 public tensor SHA-256
        // values before labeling this a genuine Original GPU test.
        if(!Eden::Graphics::R09UsableCachedPack(
               private_model,
               Eden::Graphics::NeuralRDNA2::R09ModelVariant::Original))
            throw std::runtime_error(
                "R09 private Original pack failed 599/599 SHA-256 proofs");
        Eden::Graphics::NeuralRDNA2::NeuralModelFile model;
        std::vector<std::uint8_t> actual;
        if(!model.Open(private_model)||
           !model.LoadRaw(
               "unpacked-postblock/block70.layer0.layer.attn_out_proj.bin",
               actual)||actual.size()!=matrix.size())
            throw std::runtime_error(
                "R09 authentic postblock projection tensor not available");
        std::copy(actual.begin(),actual.end(),matrix.begin());
    }else{
        for(std::uint32_t ch=0u;ch<channels;++ch)
            matrix[ch*channels+ch]=0x38u; // E4M3FN +1 fixture
    }
    write(weights,matrix.data(),matrix.size());
    std::array<std::uint8_t,fp8_bytes> zeros{};
    write(residual,zeros.data(),zeros.size());
    std::array<float,channels> scale_values{};
    scale_values.fill(1.0f);
    write(scales,scale_values.data(),scale_values.size()*sizeof(float));
    std::array<VkDescriptorSetLayoutBinding,5> bindings{};
    for(std::uint32_t i=0u;i<bindings.size();++i)
        bindings[i]={i,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1u,
                     VK_SHADER_STAGE_COMPUTE_BIT,nullptr};
    const VkDescriptorSetLayoutCreateInfo layout_ci{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
        nullptr,0u,static_cast<std::uint32_t>(bindings.size()),bindings.data()};
    VkDescriptorSetLayout layout{};
    Check(vkCreateDescriptorSetLayout(c.device,&layout_ci,nullptr,&layout),
          "create FSwin set layout");
    c.sets.push_back(layout);
    const VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,10u};
    const VkDescriptorPoolCreateInfo pool_ci{
        VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,nullptr,0u,2u,1u,&size};
    Check(vkCreateDescriptorPool(c.device,&pool_ci,nullptr,&c.descriptors),
          "create FSwin pool");
    const std::array<VkDescriptorSetLayout,2> layouts{layout,layout};
    const VkDescriptorSetAllocateInfo allocate{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        nullptr,c.descriptors,2u,layouts.data()};
    VkDescriptorSet sets[2]{};
    Check(vkAllocateDescriptorSets(c.device,&allocate,sets),
          "allocate FSwin sets");
    const std::array<VkDescriptorBufferInfo,6> infos{{
        {input.handle,0u,fp8_bytes},
        {weights.handle,0u,channels*channels},
        {residual.handle,0u,fp8_bytes},
        {scales.handle,0u,channels*sizeof(float)},
        {quant.handle,0u,fp8_bytes},
        {raw.handle,0u,raw_bytes}}};
    std::array<VkWriteDescriptorSet,10> updates{};
    for(std::uint32_t set=0u;set<2u;++set)
        for(std::uint32_t i=0u;i<5u;++i)
            updates[set*5u+i]={
                VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,nullptr,
                sets[set],i,0u,1u,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                nullptr,&infos[i==4u?4u+set:i],nullptr};
    vkUpdateDescriptorSets(c.device,
        static_cast<std::uint32_t>(updates.size()),updates.data(),0u,nullptr);
    VkPipelineLayout pipeline_layout{};
    const VkPipeline pipeline=c.Pipeline(c.Shader(spirv),
        layout,pipeline_layout,sizeof(DensePush));
    const VkCommandBufferBeginInfo begin{
        VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,nullptr,
        VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,nullptr};
    Check(vkBeginCommandBuffer(c.command,&begin),"begin FSwin GPU command");
    for(std::uint32_t direction : {3u,4u}){
        const DensePush pc{0u,0u,0u,0u,0u,1u,channels,direction};
        vkCmdBindPipeline(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
        vkCmdBindDescriptorSets(c.command,VK_PIPELINE_BIND_POINT_COMPUTE,
            pipeline_layout,0u,1u,&sets[direction-3u],0u,nullptr);
        vkCmdPushConstants(c.command,pipeline_layout,
            VK_SHADER_STAGE_COMPUTE_BIT,0u,sizeof(pc),&pc);
        // 32 channels -> 8 local invocations; 64 tokens, one window.
        vkCmdDispatch(c.command,1u,tokens,1u);
    }
    const std::array<VkBufferMemoryBarrier,2> host{{
        {VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,nullptr,
            VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
            VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
            quant.handle,0u,fp8_bytes},
        {VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,nullptr,
            VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT,
            VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,
            raw.handle,0u,raw_bytes}
    }};
    vkCmdPipelineBarrier(c.command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
        VK_PIPELINE_STAGE_HOST_BIT,0u,0u,nullptr,
        static_cast<std::uint32_t>(host.size()),host.data(),0u,nullptr);
    Check(vkEndCommandBuffer(c.command),"end FSwin GPU command");
    const VkSubmitInfo submit{
        VK_STRUCTURE_TYPE_SUBMIT_INFO,nullptr,0u,nullptr,nullptr,
        1u,&c.command,0u,nullptr};
    Check(vkQueueSubmit(c.queue,1u,&submit,VK_NULL_HANDLE),
          "submit FSwin GPU");
    Check(vkQueueWaitIdle(c.queue),"wait FSwin GPU");
    void* mapped=nullptr;
    Check(vkMapMemory(c.device,quant.memory,0u,fp8_bytes,0u,&mapped),
          "map FSwin E4M3FN output");
    const auto* e4_result=static_cast<const std::uint8_t*>(mapped);
    // Independent scalar CPU reference: actual row-major E4M3FN learned
    // weights, exact fma accumulation and FP16-round before re-quantization.
    // This path takes the user's PRIVATE NRMODEL1 pack; CI requires none.
    std::array<std::uint8_t,fp8_bytes> expected_fp8{};
    std::array<std::uint16_t,fp8_bytes> expected_fp16{};
    if(private_model){
        const auto decode=[](std::uint8_t raw){
            const int exponent=(raw>>3u)&15, mantissa=raw&7;
            if(exponent==15&&mantissa==7)
                throw std::runtime_error("non-finite authentic E4M3FN");
            const float sign=(raw&128u)?-1.0f:1.0f;
            return exponent==0?sign*std::ldexp(float(mantissa),-9):
                sign*std::ldexp(float(8+mantissa),exponent-10);
        };
        const auto encode=[](float x){
            const unsigned sign=std::signbit(x)?128u:0u;
            const float a=std::min(std::abs(x),448.0f);
            if(a<0.015625f){
                const unsigned m=unsigned(std::nearbyint(a*512.0f));
                return std::uint8_t(sign|(m>=8u?8u:m));
            }
            int e=int(std::floor(std::log2(a)));
            unsigned m=unsigned(std::nearbyint(
                (a/std::ldexp(1.0f,e)-1.0f)*8.0f));
            if(m==8u){++e;m=0u;}
            const unsigned exp=unsigned(e+7);
            if(exp>15u||(exp==15u&&m>6u))
                return std::uint8_t(sign|126u);
            return std::uint8_t(sign|(exp<<3u)|m);
        };
        for(std::uint32_t t=0u;t<tokens;++t)
            for(std::uint32_t ch=0u;ch<channels;++ch){
                float acc=0.0f;
                for(std::uint32_t k=0u;k<channels;++k)
                    acc=std::fma(
                        decode(input_data[t*channels+k]),
                        decode(matrix[ch*channels+k]),acc);
                const _Float16 rounded=static_cast<_Float16>(acc);
                std::uint16_t bits{};
                std::memcpy(&bits,&rounded,sizeof(bits));
                expected_fp16[t*channels+ch]=bits;
                expected_fp8[t*channels+ch]=encode(float(rounded));
            }
    }
    for(std::uint32_t t=0u;t<tokens;++t)
        for(std::uint32_t ch=0u;ch<channels;++ch)
            if(e4_result[t*channels+ch]!=(private_model?
                   expected_fp8[t*channels+ch]:e4[(t+ch)%e4.size()]))
                throw std::runtime_error(
                    "FSwin E4M3FN numeric mismatch at token "+
                    std::to_string(t)+" channel "+std::to_string(ch));
    vkUnmapMemory(c.device,quant.memory);
    Check(vkMapMemory(c.device,raw.memory,0u,raw_bytes,0u,&mapped),
          "map FSwin RAW FP16 output");
    const auto* raw_result=static_cast<const std::uint16_t*>(mapped);
    for(std::uint32_t t=0u;t<tokens;++t)
        for(std::uint32_t ch=0u;ch<channels;++ch)
            if(raw_result[t*channels+ch]!=(private_model?
                   expected_fp16[t*channels+ch]:f16[(t+ch)%f16.size()]))
                throw std::runtime_error(
                    "FSwin FP16 numeric mismatch at token "+
                    std::to_string(t)+" channel "+std::to_string(ch));
    vkUnmapMemory(c.device,raw.memory);
    std::cout<<(private_model?
             "R09_AUTHENTIC_ORIGINAL_FSWIN_GPU_CPU_FP8_FP16_PASS ":
             "R09_VULKAN_REAL_FSWIN_DENSE3_FP8_AND_RAW_FP16_PASS ")
             <<tokens<<" tokens x "<<channels<<" channels\n";
}
} // namespace
int main(int argc,char**argv) {
    if(argc!=2&&argc!=3){
        std::cerr<<"usage: r09_vulkan_fswin_smoke <fswin_dense.spv> "
                    "[private_original.nrmodel]\n";
        return 2;
    }
    try{
        Context context;
        context.Initialize();
        SmokeFSwinDense(context,argv[1],argc==3?argv[2]:nullptr);
        return 0;
    }catch(const std::exception& error){
        std::cerr<<"R09_VULKAN_REAL_FSWIN_DENSE3_FAIL "
                 <<error.what()<<"\n";
        return 1;
    }
}
