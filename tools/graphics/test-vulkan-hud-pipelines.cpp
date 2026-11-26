// SPDX-License-Identifier: GPL-3.0-or-later
// Host driver witness: compile the actual generated HUD and quick-menu SPIR-V,
// with distinct production-equivalent layouts. No PS5 hardware claim.
#include <vulkan/vulkan.h>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "eden_vulkan_hud_shaders.h"
#include "vulkan_menu_font_data.h"
#include "vulkan_menu_font_map.h"
namespace {
void Check(VkResult r, const char* stage) {
    if(r!=VK_SUCCESS){std::fprintf(stderr,"%s failed: %d\n",stage,int(r));std::exit(1);}
}
template<class T> T Info(VkStructureType type){T value{};value.sType=type;return value;}
template<std::size_t N> VkShaderModule Module(VkDevice d,const std::uint32_t (&words)[N]){
    static_assert(N<=32768);
    auto ci=Info<VkShaderModuleCreateInfo>(VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO);
    ci.codeSize=sizeof(words);ci.pCode=words;VkShaderModule module{};
    Check(vkCreateShaderModule(d,&ci,nullptr,&module),"create exact shader module");return module;
}
}
int main(){
    using namespace Eden::QuickOverlay;
    constexpr std::size_t slots=FontMap::kFaces.back().base+FontMap::kFaces.back().glyphs;
    constexpr std::size_t stride=112; // 4 metrics + 36 rows * 3 packed words
    static_assert(sizeof(FontAtlas::kWords)==slots*stride*sizeof(std::uint32_t));
    static_assert(FontMap::kFaces.size()==8);
    for(std::size_t i=0;i<slots;++i){
        const auto* slot=FontAtlas::kWords+i*stride;
        assert(slot[2]<=48&&slot[3]<=36);
    }
    auto ai=Info<VkApplicationInfo>(VK_STRUCTURE_TYPE_APPLICATION_INFO);
    ai.apiVersion=VK_API_VERSION_1_1;
    auto ici=Info<VkInstanceCreateInfo>(VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO);
    ici.pApplicationInfo=&ai;VkInstance instance{};
    Check(vkCreateInstance(&ici,nullptr,&instance),"instance");
    std::uint32_t count=0;Check(vkEnumeratePhysicalDevices(instance,&count,nullptr),"physical count");
    assert(count>0);std::vector<VkPhysicalDevice> physicals(count);
    Check(vkEnumeratePhysicalDevices(instance,&count,physicals.data()),"physical devices");
    const auto physical=physicals[0];
    VkPhysicalDeviceProperties props{};vkGetPhysicalDeviceProperties(physical,&props);
    assert(sizeof(FontAtlas::kWords)<=props.limits.maxStorageBufferRange);
    vkGetPhysicalDeviceQueueFamilyProperties(physical,&count,nullptr);
    std::vector<VkQueueFamilyProperties> families(count);
    vkGetPhysicalDeviceQueueFamilyProperties(physical,&count,families.data());
    std::uint32_t family=0;while(family<count&&!(families[family].queueFlags&VK_QUEUE_GRAPHICS_BIT))++family;
    assert(family<count);
    float priority=1.0f;auto qi=Info<VkDeviceQueueCreateInfo>(VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO);
    qi.queueFamilyIndex=family;qi.queueCount=1;qi.pQueuePriorities=&priority;
    auto di=Info<VkDeviceCreateInfo>(VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO);di.queueCreateInfoCount=1;di.pQueueCreateInfos=&qi;
    VkDevice device{};Check(vkCreateDevice(physical,&di,nullptr,&device),"device");
    VkAttachmentDescription attachment{};attachment.format=VK_FORMAT_R8G8B8A8_UNORM;
    attachment.samples=VK_SAMPLE_COUNT_1_BIT;attachment.loadOp=VK_ATTACHMENT_LOAD_OP_LOAD;
    attachment.storeOp=VK_ATTACHMENT_STORE_OP_STORE;attachment.initialLayout=VK_IMAGE_LAYOUT_GENERAL;
    attachment.finalLayout=VK_IMAGE_LAYOUT_GENERAL;
    VkAttachmentReference ref{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
    VkSubpassDescription sub{};sub.pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS;
    sub.colorAttachmentCount=1;sub.pColorAttachments=&ref;
    auto ri=Info<VkRenderPassCreateInfo>(VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO);
    ri.attachmentCount=1;ri.pAttachments=&attachment;ri.subpassCount=1;ri.pSubpasses=&sub;
    VkRenderPass pass{};Check(vkCreateRenderPass(device,&ri,nullptr,&pass),"render pass");
    VkDescriptorSetLayoutBinding binding{0,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr};
    auto si=Info<VkDescriptorSetLayoutCreateInfo>(VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO);
    si.bindingCount=1;si.pBindings=&binding;VkDescriptorSetLayout set{};
    Check(vkCreateDescriptorSetLayout(device,&si,nullptr,&set),"atlas layout");
    auto vertex=Module(device,EDEN_HUD_VERT_SPV);
    auto boot=Module(device,EDEN_HUD_FRAG_SPV);
    auto quick=Module(device,EDEN_QUICK_MENU_FRAG_SPV);
    VkPushConstantRange push{VK_SHADER_STAGE_FRAGMENT_BIT,0,112};
    auto loading=Module(device,EDEN_LOADING_ARTWORK_FRAG_SPV);
    for(unsigned variant:{0u,1u,2u}){
        const bool menu=variant!=0u;
        auto li=Info<VkPipelineLayoutCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO);
        li.setLayoutCount=menu?1u:0u;li.pSetLayouts=menu?&set:nullptr;
        li.pushConstantRangeCount=1;li.pPushConstantRanges=&push;
        VkPipelineLayout layout{};Check(vkCreatePipelineLayout(device,&li,nullptr,&layout),"pipeline layout");
        std::array<VkPipelineShaderStageCreateInfo,2> stages{};
        for(auto& s:stages){s.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;s.pName="main";}
        stages[0].stage=VK_SHADER_STAGE_VERTEX_BIT;stages[0].module=vertex;
        stages[1].stage=VK_SHADER_STAGE_FRAGMENT_BIT;stages[1].module=variant==2u?loading:menu?quick:boot;
        auto input=Info<VkPipelineVertexInputStateCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO);
        auto assembly=Info<VkPipelineInputAssemblyStateCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO);
        assembly.topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_STRIP;
        VkViewport viewport{0,0,64,64,0,1};VkRect2D scissor{{0,0},{64,64}};
        auto vp=Info<VkPipelineViewportStateCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO);
        vp.viewportCount=vp.scissorCount=1;vp.pViewports=&viewport;vp.pScissors=&scissor;
        auto raster=Info<VkPipelineRasterizationStateCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO);
        raster.polygonMode=VK_POLYGON_MODE_FILL;raster.cullMode=VK_CULL_MODE_NONE;raster.frontFace=VK_FRONT_FACE_COUNTER_CLOCKWISE;raster.lineWidth=1;
        auto ms=Info<VkPipelineMultisampleStateCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO);
        ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
        VkPipelineColorBlendAttachmentState dst{};dst.colorWriteMask=15;dst.blendEnable=VK_TRUE;
        dst.srcColorBlendFactor=VK_BLEND_FACTOR_SRC_ALPHA;dst.dstColorBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        dst.colorBlendOp=VK_BLEND_OP_ADD;dst.srcAlphaBlendFactor=VK_BLEND_FACTOR_ONE;dst.dstAlphaBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;dst.alphaBlendOp=VK_BLEND_OP_ADD;
        auto blend=Info<VkPipelineColorBlendStateCreateInfo>(VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO);
        blend.attachmentCount=1;blend.pAttachments=&dst;
        auto pi=Info<VkGraphicsPipelineCreateInfo>(VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO);
        pi.stageCount=2;pi.pStages=stages.data();pi.pVertexInputState=&input;pi.pInputAssemblyState=&assembly;
        pi.pViewportState=&vp;pi.pRasterizationState=&raster;pi.pMultisampleState=&ms;pi.pColorBlendState=&blend;
        pi.layout=layout;pi.renderPass=pass;pi.basePipelineIndex=-1;
        VkPipeline pipeline{};const auto begin=std::chrono::steady_clock::now();
        Check(vkCreateGraphicsPipelines(device,VK_NULL_HANDLE,1,&pi,nullptr,&pipeline),variant==2u?"loading artwork pipeline":menu?"quick menu pipeline":"boot HUD pipeline");
        const auto elapsed=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-begin).count();
        std::printf("VULKAN_HUD_REAL_PIPELINE_PASS variant=%s ms=%lld device=%s\n",variant==2u?"loading-artwork":menu?"unicode-menu":"boot",static_cast<long long>(elapsed),props.deviceName);
        vkDestroyPipeline(device,pipeline,nullptr);vkDestroyPipelineLayout(device,layout,nullptr);
    }
    for(auto m:{vertex,boot,quick,loading})vkDestroyShaderModule(device,m,nullptr);
    vkDestroyDescriptorSetLayout(device,set,nullptr);vkDestroyRenderPass(device,pass,nullptr);
    vkDestroyDevice(device,nullptr);vkDestroyInstance(instance,nullptr);
    std::printf("VULKAN_HUD_ATLAS_LAYOUT_PASS slots=%zu bytes=%zu boot_words=%zu quick_words=%zu\n",slots,sizeof(FontAtlas::kWords),std::size(EDEN_HUD_FRAG_SPV),std::size(EDEN_QUICK_MENU_FRAG_SPV));
}
