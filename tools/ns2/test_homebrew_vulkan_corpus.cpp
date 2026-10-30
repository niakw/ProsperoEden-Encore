// SPDX-License-Identifier: GPL-3.0-or-later
// External independently published HBLauncher GPU-app corpus.
// Proves actual host Vulkan graphics/compute pipeline creation and one
// compute dispatch, NOT the Switch 2 SM86 ISA, PS5 RADV, or an NSO boot.
#include <vulkan/vulkan.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

static void Check(VkResult rc, const char* what) {
    if (rc != VK_SUCCESS) {
        std::fprintf(stderr, "%s failed (VkResult %d)\n", what, static_cast<int>(rc));
        std::exit(1);
    }
}
static void Require(bool ok, const char* what) {
    if (!ok) { std::fprintf(stderr, "%s\n", what); std::exit(1); }
}
static std::vector<uint32_t> ReadWords(const char* path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    Require(bool(file), "SPIR-V input missing");
    const std::streamsize size = static_cast<std::streamsize>(file.tellg());
    Require(size >= 20 && size <= 1024 * 1024 && size % 4 == 0,
            "SPIR-V input has invalid size");
    std::vector<uint32_t> words(static_cast<std::size_t>(size) / 4);
    file.seekg(0);
    file.read(reinterpret_cast<char*>(words.data()), size);
    Require(bool(file) && words[0] == 0x07230203u, "SPIR-V magic or read invalid");
    return words;
}
static uint32_t FindHostMemoryType(VkPhysicalDevice gpu, uint32_t bits) {
    VkPhysicalDeviceMemoryProperties props{};
    vkGetPhysicalDeviceMemoryProperties(gpu, &props);
    for (uint32_t i = 0; i < props.memoryTypeCount; ++i) {
        const auto flags = props.memoryTypes[i].propertyFlags;
        if ((bits & (1u << i)) &&
            (flags & (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                      VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
                     (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                      VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))
            return i;
    }
    throw std::runtime_error("No host-visible coherent Vulkan memory type");
}
int main(int argc, char** argv) {
    Require(argc == 4, "usage: binary vertex.spv fragment.spv compute.spv");
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName = "Encore external homebrew research";
    app.apiVersion = VK_API_VERSION_1_1;
    VkInstanceCreateInfo instance_ci{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    instance_ci.pApplicationInfo = &app;
    VkInstance instance{};
    Check(vkCreateInstance(&instance_ci, nullptr, &instance), "vkCreateInstance");

    uint32_t physical_count{};
    Check(vkEnumeratePhysicalDevices(instance, &physical_count, nullptr), "enumerate GPU count");
    Require(physical_count > 0, "No Vulkan physical device");
    std::vector<VkPhysicalDevice> physical(physical_count);
    Check(vkEnumeratePhysicalDevices(instance, &physical_count, physical.data()), "enumerate GPUs");
    VkPhysicalDevice gpu{};
    uint32_t family{};
    for (auto candidate : physical) {
        uint32_t count{};
        vkGetPhysicalDeviceQueueFamilyProperties(candidate, &count, nullptr);
        std::vector<VkQueueFamilyProperties> props(count);
        vkGetPhysicalDeviceQueueFamilyProperties(candidate, &count, props.data());
        for (uint32_t i = 0; i < count; ++i) {
            if ((props[i].queueFlags & (VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_COMPUTE_BIT)) ==
                (VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_COMPUTE_BIT)) {
                gpu = candidate;
                family = i;
                break;
            }
        }
        if (gpu) break;
    }
    Require(gpu != VK_NULL_HANDLE, "No graphics+compute Vulkan queue");
    VkPhysicalDeviceProperties props{};
    vkGetPhysicalDeviceProperties(gpu, &props);
    std::printf("Homebrew corpus Vulkan device: %s\n", props.deviceName);
    const float priority = 1.0f;
    VkDeviceQueueCreateInfo queue_ci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    queue_ci.queueFamilyIndex = family;
    queue_ci.queueCount = 1;
    queue_ci.pQueuePriorities = &priority;
    VkDeviceCreateInfo device_ci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    device_ci.queueCreateInfoCount = 1;
    device_ci.pQueueCreateInfos = &queue_ci;
    VkDevice device{};
    Check(vkCreateDevice(gpu, &device_ci, nullptr, &device), "vkCreateDevice");
    VkQueue queue{};
    vkGetDeviceQueue(device, family, 0, &queue);
    auto make_module = [&](const char* file) {
        const auto words = ReadWords(file);
        VkShaderModuleCreateInfo ci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
        ci.codeSize = words.size() * sizeof(uint32_t);
        ci.pCode = words.data();
        VkShaderModule out{};
        Check(vkCreateShaderModule(device, &ci, nullptr, &out), "vkCreateShaderModule");
        return out;
    };
    const VkShaderModule vert = make_module(argv[1]);
    const VkShaderModule frag = make_module(argv[2]);
    const VkShaderModule comp = make_module(argv[3]);

    VkDescriptorSetLayoutBinding binding{};
    binding.binding = 0;
    binding.descriptorCount = 1;
    binding.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    binding.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT | VK_SHADER_STAGE_COMPUTE_BIT;
    VkDescriptorSetLayoutCreateInfo set_ci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    set_ci.bindingCount = 1;
    set_ci.pBindings = &binding;
    VkDescriptorSetLayout set_layout{};
    Check(vkCreateDescriptorSetLayout(device, &set_ci, nullptr, &set_layout), "set layout");
    VkPipelineLayoutCreateInfo layout_ci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    layout_ci.setLayoutCount = 1;
    layout_ci.pSetLayouts = &set_layout;
    VkPipelineLayout layout{};
    Check(vkCreatePipelineLayout(device, &layout_ci, nullptr, &layout), "pipeline layout");

    VkAttachmentDescription color{};
    color.format = VK_FORMAT_R8G8B8A8_UNORM;
    color.samples = VK_SAMPLE_COUNT_1_BIT;
    color.loadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    color.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    color.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    color.finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    VkAttachmentReference color_ref{};
    color_ref.attachment = 0;
    color_ref.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &color_ref;
    VkRenderPassCreateInfo renderpass_ci{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
    renderpass_ci.attachmentCount = 1;
    renderpass_ci.pAttachments = &color;
    renderpass_ci.subpassCount = 1;
    renderpass_ci.pSubpasses = &subpass;
    VkRenderPass renderpass{};
    Check(vkCreateRenderPass(device, &renderpass_ci, nullptr, &renderpass), "renderpass");

    VkPipelineShaderStageCreateInfo stages[2]{};
    for (uint32_t i = 0; i < 2; ++i) {
        stages[i].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stages[i].stage = i ? VK_SHADER_STAGE_FRAGMENT_BIT : VK_SHADER_STAGE_VERTEX_BIT;
        stages[i].module = i ? frag : vert;
        stages[i].pName = "main";
    }
    VkPipelineVertexInputStateCreateInfo input{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo assembly{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    assembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkViewport viewport{0.f, 0.f, 64.f, 64.f, 0.f, 1.f};
    VkRect2D scissor{{0, 0}, {64, 64}};
    VkPipelineViewportStateCreateInfo viewport_ci{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    viewport_ci.viewportCount = 1;
    viewport_ci.pViewports = &viewport;
    viewport_ci.scissorCount = 1;
    viewport_ci.pScissors = &scissor;
    VkPipelineRasterizationStateCreateInfo raster{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    raster.polygonMode = VK_POLYGON_MODE_FILL;
    raster.cullMode = VK_CULL_MODE_NONE;
    raster.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    raster.lineWidth = 1.f;
    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState colorblend{};
    colorblend.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                                VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    blend.attachmentCount = 1;
    blend.pAttachments = &colorblend;
    VkGraphicsPipelineCreateInfo graphics_ci{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
    graphics_ci.stageCount = 2;
    graphics_ci.pStages = stages;
    graphics_ci.pVertexInputState = &input;
    graphics_ci.pInputAssemblyState = &assembly;
    graphics_ci.pViewportState = &viewport_ci;
    graphics_ci.pRasterizationState = &raster;
    graphics_ci.pMultisampleState = &ms;
    graphics_ci.pColorBlendState = &blend;
    graphics_ci.layout = layout;
    graphics_ci.renderPass = renderpass;
    VkPipeline graphics{};
    Check(vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &graphics_ci,
                                    nullptr, &graphics), "Blockfall graphics pipeline");
    std::puts("Blockfall: real vertex + fragment graphics pipeline PASS");

    VkComputePipelineCreateInfo compute_ci{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
    compute_ci.layout = layout;
    compute_ci.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    compute_ci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    compute_ci.stage.module = comp;
    compute_ci.stage.pName = "main";
    VkPipeline compute{};
    Check(vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &compute_ci,
                                   nullptr, &compute), "Blockfall compute pipeline");

    // HBLauncher ABI 1's extended data resides near byte 0x7f0000.
    // Match the demo's >=8-MiB shared storage buffer; do not pretend
    // this is a Nintendo GMMU or a PS5 driver buffer.
    constexpr VkDeviceSize buffer_size = 8u * 1024u * 1024u;
    VkBufferCreateInfo buffer_ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    buffer_ci.size = buffer_size;
    buffer_ci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
    buffer_ci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkBuffer buffer{};
    Check(vkCreateBuffer(device, &buffer_ci, nullptr, &buffer), "shared state buffer");
    VkMemoryRequirements req{};
    vkGetBufferMemoryRequirements(device, buffer, &req);
    VkMemoryAllocateInfo alloc_ci{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    alloc_ci.allocationSize = req.size;
    alloc_ci.memoryTypeIndex = FindHostMemoryType(gpu, req.memoryTypeBits);
    VkDeviceMemory memory{};
    Check(vkAllocateMemory(device, &alloc_ci, nullptr, &memory), "shared buffer memory");
    Check(vkBindBufferMemory(device, buffer, memory, 0), "bind shared buffer");
    void* mapped{};
    Check(vkMapMemory(device, memory, 0, buffer_size, 0, &mapped), "map state");
    std::memset(mapped, 0, static_cast<size_t>(buffer_size));
    // Initial state.bin places a float=1 at byte offset 960.
    const float transition = 1.f;
    std::memcpy(static_cast<char*>(mapped) + 960, &transition, sizeof(transition));

    VkDescriptorPoolSize pool_size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1};
    VkDescriptorPoolCreateInfo pool_ci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    pool_ci.maxSets = 1;
    pool_ci.poolSizeCount = 1;
    pool_ci.pPoolSizes = &pool_size;
    VkDescriptorPool pool{};
    Check(vkCreateDescriptorPool(device, &pool_ci, nullptr, &pool), "descriptor pool");
    VkDescriptorSetAllocateInfo ds_ci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    ds_ci.descriptorPool = pool;
    ds_ci.descriptorSetCount = 1;
    ds_ci.pSetLayouts = &set_layout;
    VkDescriptorSet ds{};
    Check(vkAllocateDescriptorSets(device, &ds_ci, &ds), "descriptor set");
    VkDescriptorBufferInfo descriptor{buffer, 0, buffer_size};
    VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
    write.dstSet = ds;
    write.dstBinding = 0;
    write.descriptorCount = 1;
    write.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    write.pBufferInfo = &descriptor;
    vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);

    VkCommandPoolCreateInfo cmd_pool_ci{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    cmd_pool_ci.queueFamilyIndex = family;
    VkCommandPool cmd_pool{};
    Check(vkCreateCommandPool(device, &cmd_pool_ci, nullptr, &cmd_pool), "command pool");
    VkCommandBufferAllocateInfo cmd_ci{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cmd_ci.commandPool = cmd_pool;
    cmd_ci.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cmd_ci.commandBufferCount = 1;
    VkCommandBuffer cmd{};
    Check(vkAllocateCommandBuffers(device, &cmd_ci, &cmd), "command buffer");
    VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    Check(vkBeginCommandBuffer(cmd, &begin), "command begin");
    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, compute);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, layout,
                            0, 1, &ds, 0, nullptr);
    vkCmdDispatch(cmd, 1, 1, 1);
    VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    barrier.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
    barrier.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &barrier,
                         0, nullptr, 0, nullptr);
    Check(vkEndCommandBuffer(cmd), "command end");
    VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submit.commandBufferCount = 1;
    submit.pCommandBuffers = &cmd;
    VkFenceCreateInfo fence_ci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VkFence fence{};
    Check(vkCreateFence(device, &fence_ci, nullptr, &fence), "create fence");
    Check(vkQueueSubmit(queue, 1, &submit, fence), "submit compute");
    Check(vkWaitForFences(device, 1, &fence, VK_TRUE, 10'000'000'000ull),
          "compute completion timeout");
    uint32_t initialized{};
    std::memcpy(&initialized, static_cast<char*>(mapped) + 788, sizeof(initialized));
    Require((initialized & 1u) == 1u, "Blockfall compute did not initialize ABI-1 game state");
    std::printf("Blockfall: real Vulkan compute dispatch + host readback PASS (game flags=%u)\n",
                initialized);

    vkDestroyFence(device, fence, nullptr);
    vkDestroyCommandPool(device, cmd_pool, nullptr);
    vkDestroyDescriptorPool(device, pool, nullptr);
    vkUnmapMemory(device, memory);
    vkDestroyBuffer(device, buffer, nullptr);
    vkFreeMemory(device, memory, nullptr);
    vkDestroyPipeline(device, compute, nullptr);
    vkDestroyPipeline(device, graphics, nullptr);
    vkDestroyRenderPass(device, renderpass, nullptr);
    vkDestroyPipelineLayout(device, layout, nullptr);
    vkDestroyDescriptorSetLayout(device, set_layout, nullptr);
    vkDestroyShaderModule(device, comp, nullptr);
    vkDestroyShaderModule(device, frag, nullptr);
    vkDestroyShaderModule(device, vert, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);
    std::puts("NS2 external homebrew Vulkan corpus PASS (host only; no console/NS2 loader proof)");
}
