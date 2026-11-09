// SPDX-License-Identifier: GPL-3.0-or-later
// G09: actual Vulkan graphics pipeline creation from the reviewed native
// Task/Mesh SPIR-V compiler. A missing host extension is NOT a pass.
#include <vulkan/vulkan.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
#include <cstring>
static void Require(bool condition, const char* what) {
    if (!condition) { std::fprintf(stderr, "G09 mesh Vulkan: %s\n", what); std::exit(1); }
}
static std::vector<uint32_t> ReadModule(const char* path) {
    std::ifstream f{path, std::ios::binary | std::ios::ate};
    Require(bool(f), "native SPIR-V output missing");
    const auto n = f.tellg();
    Require(n >= static_cast<std::streamoff>(20) &&
            n <= static_cast<std::streamoff>(1024*1024) &&
            static_cast<std::streamoff>(n) % 4 == 0, "invalid module size");
    std::vector<uint32_t> words(static_cast<size_t>(n)/4);
    f.seekg(0);
    f.read(reinterpret_cast<char*>(words.data()), n);
    Require(bool(f) && words[0] == 0x07230203U, "invalid SPIR-V payload");
    return words;
}
int main(int argc, char** argv) {
    Require(argc==3, "expected authentic Task and Mesh SPIR-V");
    const auto task_words=ReadModule(argv[1]);
    const auto mesh_words=ReadModule(argv[2]);
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.apiVersion=VK_API_VERSION_1_2;
    VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    ici.pApplicationInfo=&app;
    VkInstance instance=VK_NULL_HANDLE;
    Require(vkCreateInstance(&ici,nullptr,&instance)==VK_SUCCESS,"instance");
    uint32_t count{};
    Require(vkEnumeratePhysicalDevices(instance,&count,nullptr)==VK_SUCCESS && count,
            "physical devices");
    std::vector<VkPhysicalDevice> devices(count);
    Require(vkEnumeratePhysicalDevices(instance,&count,devices.data())==VK_SUCCESS,
            "device enumeration");
    VkPhysicalDevice selected=VK_NULL_HANDLE;
    uint32_t family{};
    for (const auto device:devices) {
        VkPhysicalDeviceProperties props{};
        vkGetPhysicalDeviceProperties(device,&props);
        if(props.apiVersion<VK_API_VERSION_1_2)continue;
        uint32_t extensions{};
        if(vkEnumerateDeviceExtensionProperties(device,nullptr,&extensions,nullptr)!=VK_SUCCESS)
            continue;
        std::vector<VkExtensionProperties> list(extensions);
        if(vkEnumerateDeviceExtensionProperties(device,nullptr,&extensions,list.data())!=VK_SUCCESS)
            continue;
        if(std::none_of(list.begin(),list.end(),[](const auto& e) {
            return std::strcmp(e.extensionName,VK_EXT_MESH_SHADER_EXTENSION_NAME)==0;
        }))continue;
        VkPhysicalDeviceMeshShaderFeaturesEXT mesh_features{
            VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_FEATURES_EXT};
        VkPhysicalDeviceFeatures2 features{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
        features.pNext=&mesh_features;
        vkGetPhysicalDeviceFeatures2(device,&features);
        if(!mesh_features.meshShader || !mesh_features.taskShader)continue;
        uint32_t queues{};
        vkGetPhysicalDeviceQueueFamilyProperties(device,&queues,nullptr);
        std::vector<VkQueueFamilyProperties> families(queues);
        vkGetPhysicalDeviceQueueFamilyProperties(device,&queues,families.data());
        for(uint32_t i=0;i<queues;++i) {
            if(families[i].queueCount && (families[i].queueFlags&VK_QUEUE_GRAPHICS_BIT)) {
                selected=device;family=i;break;
            }
        }
        if(selected)break;
    }
    if(!selected) {
        std::puts("G09_HOST_MESH_UNAVAILABLE real_pipeline=NOT_VALIDATED extension=VK_EXT_mesh_shader");
        vkDestroyInstance(instance,nullptr);
        return 0;
    }
    VkPhysicalDeviceProperties props{};
    vkGetPhysicalDeviceProperties(selected,&props);
    std::printf("G09_VULKAN_MESH_DEVICE %s\n",props.deviceName);
    float priority=1.0f;
    VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qci.queueFamilyIndex=family;
    qci.queueCount=1;
    qci.pQueuePriorities=&priority;
    VkPhysicalDeviceMeshShaderFeaturesEXT enabled{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_FEATURES_EXT};
    enabled.meshShader=VK_TRUE;
    enabled.taskShader=VK_TRUE;
    const char* extensions[]={VK_EXT_MESH_SHADER_EXTENSION_NAME};
    VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    dci.pNext=&enabled;
    dci.queueCreateInfoCount=1;
    dci.pQueueCreateInfos=&qci;
    dci.enabledExtensionCount=1;
    dci.ppEnabledExtensionNames=extensions;
    VkDevice device=VK_NULL_HANDLE;
    Require(vkCreateDevice(selected,&dci,nullptr,&device)==VK_SUCCESS,
            "task/mesh device creation");
    auto shader=[&](const std::vector<uint32_t>& words) {
        VkShaderModuleCreateInfo sci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
        sci.codeSize=words.size()*sizeof(uint32_t);
        sci.pCode=words.data();
        VkShaderModule module=VK_NULL_HANDLE;
        Require(vkCreateShaderModule(device,&sci,nullptr,&module)==VK_SUCCESS,
                "native Task/Mesh shader module");
        return module;
    };
    const VkShaderModule task=shader(task_words);
    const VkShaderModule mesh=shader(mesh_words);
    VkPipelineLayoutCreateInfo lci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    VkPipelineLayout layout=VK_NULL_HANDLE;
    Require(vkCreatePipelineLayout(device,&lci,nullptr,&layout)==VK_SUCCESS,
            "mesh pipeline layout");
    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS;
    VkRenderPassCreateInfo rpci{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
    rpci.subpassCount=1;
    rpci.pSubpasses=&subpass;
    VkRenderPass pass=VK_NULL_HANDLE;
    Require(vkCreateRenderPass(device,&rpci,nullptr,&pass)==VK_SUCCESS,
            "mesh render pass");
    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0].sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage=VK_SHADER_STAGE_TASK_BIT_EXT;
    stages[0].module=task;
    stages[0].pName="main";
    stages[1].sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage=VK_SHADER_STAGE_MESH_BIT_EXT;
    stages[1].module=mesh;
    stages[1].pName="main";
    VkViewport viewport{};
    viewport.width=1.0f;viewport.height=1.0f;viewport.maxDepth=1.0f;
    VkRect2D scissor{};
    scissor.extent.width=1;scissor.extent.height=1;
    VkPipelineViewportStateCreateInfo vp{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    vp.viewportCount=1;vp.pViewports=&viewport;
    vp.scissorCount=1;vp.pScissors=&scissor;
    VkPipelineRasterizationStateCreateInfo raster{
        VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    raster.rasterizerDiscardEnable=VK_TRUE;
    raster.polygonMode=VK_POLYGON_MODE_FILL;
    raster.cullMode=VK_CULL_MODE_NONE;
    raster.frontFace=VK_FRONT_FACE_COUNTER_CLOCKWISE;
    raster.lineWidth=1.0f;
    VkPipelineMultisampleStateCreateInfo ms{
        VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendStateCreateInfo blend{
        VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    for (unsigned variant=0;variant<2;++variant) {
        VkGraphicsPipelineCreateInfo gpci{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
        gpci.stageCount=variant==0?1:2;
        gpci.pStages=variant==0?&stages[1]:stages;
        gpci.pViewportState=&vp;
        gpci.pRasterizationState=&raster;
        gpci.pMultisampleState=&ms;
        gpci.pColorBlendState=&blend;
        gpci.layout=layout;
        gpci.renderPass=pass;
        VkPipeline pipeline=VK_NULL_HANDLE;
        const auto result=vkCreateGraphicsPipelines(
            device,VK_NULL_HANDLE,1,&gpci,nullptr,&pipeline);
        if(result!=VK_SUCCESS)std::fprintf(stderr,
            "G09 real pipeline variant=%u VkResult=%d\n",variant,int(result));
        Require(result==VK_SUCCESS && pipeline!=VK_NULL_HANDLE,
                "host rejected native Mesh/Task pipeline");
        vkDestroyPipeline(device,pipeline,nullptr);
    }
    vkDestroyRenderPass(device,pass,nullptr);
    vkDestroyPipelineLayout(device,layout,nullptr);
    vkDestroyShaderModule(device,mesh,nullptr);
    vkDestroyShaderModule(device,task,nullptr);
    vkDestroyDevice(device,nullptr);
    vkDestroyInstance(instance,nullptr);
    std::puts("G09_REAL_NATIVE_VULKAN_MESH_PIPELINES_PASS mesh_only=1 task_mesh=1");
}
