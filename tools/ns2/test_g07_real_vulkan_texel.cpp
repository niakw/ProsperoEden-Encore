// SPDX-License-Identifier: GPL-3.0-or-later
// G07: dispatch the actual native SPIR-V image-buffer/SSBO shader on host Vulkan.
// This is a real GPU-backed proof, not a PS5 guest frame or TIC/TSC binding.
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>

static void Check(bool ok, const char* message) {
    if (!ok) { std::fprintf(stderr, "G07 Vulkan: %s\n", message); std::exit(1); }
}
static std::vector<uint32_t> ReadWords(const char* filename) {
    std::ifstream f{filename, std::ios::binary | std::ios::ate};
    Check(bool(f), "missing native SPIR-V");
    const auto n = f.tellg();
    Check(n >= static_cast<std::streamoff>(20) &&
          n <= static_cast<std::streamoff>(1024 * 1024) &&
          static_cast<std::streamoff>(n) % 4 == 0, "invalid SPIR-V size");
    std::vector<uint32_t> words(static_cast<std::size_t>(n) / 4);
    f.seekg(0);
    f.read(reinterpret_cast<char*>(words.data()), n);
    Check(bool(f) && words[0] == 0x07230203U, "invalid SPIR-V magic");
    unsigned fetches{}, writes{};
    for (std::size_t i = 5; i < words.size();) {
        const auto count = words[i] >> 16;
        Check(count && count <= words.size() - i, "invalid SPIR-V instruction");
        fetches += (words[i] & 0xffffU) == 95U; // OpImageFetch
        writes += (words[i] & 0xffffU) == 62U; // OpStore
        i += count;
    }
    Check(fetches == 2 && writes >= 2, "emitter omitted real image read/write");
    return words;
}
static uint32_t Bits(float value) {
    uint32_t bits{};
    static_assert(sizeof bits == sizeof value);
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}
int main(int argc, char** argv) {
    Check(argc == 2, "expected native image-buffer SPIR-V");
    const auto spirv = ReadWords(argv[1]);
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.apiVersion = VK_API_VERSION_1_2;
    VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    ici.pApplicationInfo = &app;
    VkInstance instance = VK_NULL_HANDLE;
    Check(vkCreateInstance(&ici, nullptr, &instance) == VK_SUCCESS, "instance");
    uint32_t count{};
    Check(vkEnumeratePhysicalDevices(instance, &count, nullptr) == VK_SUCCESS && count,
          "no host Vulkan device");
    std::vector<VkPhysicalDevice> physical(count);
    Check(vkEnumeratePhysicalDevices(instance, &count, physical.data()) == VK_SUCCESS,
          "enumerate devices");
    VkPhysicalDevice gpu = VK_NULL_HANDLE;
    uint32_t family{};
    for (auto candidate : physical) {
        VkFormatProperties props{};
        vkGetPhysicalDeviceFormatProperties(candidate, VK_FORMAT_R32G32B32A32_SFLOAT, &props);
        if (!(props.bufferFeatures & VK_FORMAT_FEATURE_UNIFORM_TEXEL_BUFFER_BIT)) continue;
        uint32_t families{};
        vkGetPhysicalDeviceQueueFamilyProperties(candidate, &families, nullptr);
        std::vector<VkQueueFamilyProperties> available(families);
        vkGetPhysicalDeviceQueueFamilyProperties(candidate, &families, available.data());
        for (uint32_t i = 0; i < families; ++i) {
            if (available[i].queueCount && (available[i].queueFlags & VK_QUEUE_COMPUTE_BIT)) {
                gpu = candidate;
                family = i;
                break;
            }
        }
        if (gpu) break;
    }
    Check(gpu != VK_NULL_HANDLE, "no compute queue with float4 texel buffer support");
    const float priority = 1.f;
    VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qci.queueFamilyIndex = family;
    qci.queueCount = 1;
    qci.pQueuePriorities = &priority;
    VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    dci.queueCreateInfoCount = 1;
    dci.pQueueCreateInfos = &qci;
    VkDevice device = VK_NULL_HANDLE;
    Check(vkCreateDevice(gpu, &dci, nullptr, &device) == VK_SUCCESS, "device");
    VkQueue queue = VK_NULL_HANDLE;
    vkGetDeviceQueue(device, family, 0, &queue);

    std::array<VkDescriptorSetLayoutBinding, 2> bindings{};
    bindings[0].binding = 0;
    bindings[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    bindings[0].descriptorCount = 1;
    bindings[0].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    bindings[1].binding = 1;
    bindings[1].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER;
    bindings[1].descriptorCount = 2;
    bindings[1].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    VkDescriptorSetLayoutCreateInfo lci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    lci.bindingCount = static_cast<uint32_t>(bindings.size());
    lci.pBindings = bindings.data();
    VkDescriptorSetLayout set_layout = VK_NULL_HANDLE;
    Check(vkCreateDescriptorSetLayout(device, &lci, nullptr, &set_layout) == VK_SUCCESS,
          "set layout");
    VkPipelineLayoutCreateInfo pci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    pci.setLayoutCount = 1;
    pci.pSetLayouts = &set_layout;
    VkPipelineLayout layout = VK_NULL_HANDLE;
    Check(vkCreatePipelineLayout(device, &pci, nullptr, &layout) == VK_SUCCESS,
          "pipeline layout");
    VkShaderModuleCreateInfo sci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    sci.codeSize = spirv.size() * sizeof(uint32_t);
    sci.pCode = spirv.data();
    VkShaderModule module = VK_NULL_HANDLE;
    Check(vkCreateShaderModule(device, &sci, nullptr, &module) == VK_SUCCESS,
          "real native image shader module");
    VkComputePipelineCreateInfo cpci{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
    cpci.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    cpci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    cpci.stage.module = module;
    cpci.stage.pName = "main";
    cpci.layout = layout;
    VkPipeline pipeline = VK_NULL_HANDLE;
    Check(vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &cpci, nullptr, &pipeline)
          == VK_SUCCESS, "real native image pipeline");

    VkBufferCreateInfo bci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    bci.size = 4096;
    bci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                VK_BUFFER_USAGE_UNIFORM_TEXEL_BUFFER_BIT;
    bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkBuffer buffer = VK_NULL_HANDLE;
    Check(vkCreateBuffer(device, &bci, nullptr, &buffer) == VK_SUCCESS, "data buffer");
    VkMemoryRequirements req{};
    vkGetBufferMemoryRequirements(device, buffer, &req);
    VkPhysicalDeviceMemoryProperties memory_props{};
    vkGetPhysicalDeviceMemoryProperties(gpu, &memory_props);
    uint32_t memory_type = memory_props.memoryTypeCount;
    for (uint32_t i = 0; i < memory_props.memoryTypeCount; ++i) {
        const auto flags = memory_props.memoryTypes[i].propertyFlags;
        if ((req.memoryTypeBits & (1U << i)) &&
            (flags & (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                      VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
                (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
            memory_type = i;
            break;
        }
    }
    Check(memory_type < memory_props.memoryTypeCount, "no coherent memory");
    VkMemoryAllocateInfo allocation{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    allocation.allocationSize = req.size;
    allocation.memoryTypeIndex = memory_type;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    Check(vkAllocateMemory(device, &allocation, nullptr, &memory) == VK_SUCCESS,
          "allocate memory");
    Check(vkBindBufferMemory(device, buffer, memory, 0) == VK_SUCCESS, "bind data");
    void* mapped = nullptr;
    Check(vkMapMemory(device, memory, 0, 4096, 0, &mapped) == VK_SUCCESS,
          "map data");
    auto* data = static_cast<uint32_t*>(mapped);
    std::fill_n(data, 1024, 0U);
    data[(256 + 4 * 16) / 4] = Bits(1.25f);
    data[(512 + 8 * 16) / 4] = Bits(7.5f);

    std::array<VkBufferView, 2> views{};
    for (uint32_t i = 0; i < 2; ++i) {
        VkBufferViewCreateInfo bvi{VK_STRUCTURE_TYPE_BUFFER_VIEW_CREATE_INFO};
        bvi.buffer = buffer;
        bvi.format = VK_FORMAT_R32G32B32A32_SFLOAT;
        bvi.offset = 256 + i * 256;
        bvi.range = 256;
        Check(vkCreateBufferView(device, &bvi, nullptr, &views[i]) == VK_SUCCESS,
              "texel view");
    }
    std::array<VkDescriptorPoolSize, 2> sizes{{
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1},
        {VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER, 2}
    }};
    VkDescriptorPoolCreateInfo dpci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    dpci.maxSets = 1;
    dpci.poolSizeCount = 2;
    dpci.pPoolSizes = sizes.data();
    VkDescriptorPool pool = VK_NULL_HANDLE;
    Check(vkCreateDescriptorPool(device, &dpci, nullptr, &pool) == VK_SUCCESS,
          "descriptor pool");
    VkDescriptorSetAllocateInfo sai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    sai.descriptorPool = pool;
    sai.descriptorSetCount = 1;
    sai.pSetLayouts = &set_layout;
    VkDescriptorSet set = VK_NULL_HANDLE;
    Check(vkAllocateDescriptorSets(device, &sai, &set) == VK_SUCCESS,
          "allocate set");
    VkDescriptorBufferInfo storage{};
    storage.buffer = buffer;
    storage.offset = 0;
    storage.range = 64;
    std::array<VkWriteDescriptorSet, 2> writes{};
    for (auto& write : writes) {
        write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        write.dstSet = set;
    }
    writes[0].dstBinding = 0;
    writes[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    writes[0].descriptorCount = 1;
    writes[0].pBufferInfo = &storage;
    writes[1].dstBinding = 1;
    writes[1].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER;
    writes[1].descriptorCount = 2;
    writes[1].pTexelBufferView = views.data();
    vkUpdateDescriptorSets(device, 2, writes.data(), 0, nullptr);

    VkCommandPoolCreateInfo cmd_pool_info{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    cmd_pool_info.queueFamilyIndex = family;
    VkCommandPool command_pool = VK_NULL_HANDLE;
    Check(vkCreateCommandPool(device, &cmd_pool_info, nullptr, &command_pool)
          == VK_SUCCESS, "command pool");
    VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cai.commandPool = command_pool;
    cai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cai.commandBufferCount = 1;
    VkCommandBuffer command = VK_NULL_HANDLE;
    Check(vkAllocateCommandBuffers(device, &cai, &command) == VK_SUCCESS,
          "command buffer");
    VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    Check(vkBeginCommandBuffer(command, &begin) == VK_SUCCESS, "begin command");
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
    vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_COMPUTE, layout,
                            0, 1, &set, 0, nullptr);
    vkCmdDispatch(command, 1, 1, 1);
    VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    barrier.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
    barrier.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &barrier,
                         0, nullptr, 0, nullptr);
    Check(vkEndCommandBuffer(command) == VK_SUCCESS, "end command");
    VkFenceCreateInfo fci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VkFence fence = VK_NULL_HANDLE;
    Check(vkCreateFence(device, &fci, nullptr, &fence) == VK_SUCCESS, "fence");
    VkSubmitInfo submission{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submission.commandBufferCount = 1;
    submission.pCommandBuffers = &command;
    Check(vkQueueSubmit(queue, 1, &submission, fence) == VK_SUCCESS, "submit");
    Check(vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL)
          == VK_SUCCESS, "fence wait");
    Check(data[0] == Bits(1.25f) && data[1] == Bits(7.5f),
          "wrong GPU texel selection or missing SSBO writeback");
    for (uint32_t i = 2; i < 16; ++i)
        Check(data[i] == 0, "GPU corrupted another SSBO word");
    Check(data[(256 + 4 * 16) / 4] == Bits(1.25f) &&
          data[(512 + 8 * 16) / 4] == Bits(7.5f),
          "GPU modified read-only texel data");

    vkDeviceWaitIdle(device);
    vkDestroyFence(device, fence, nullptr);
    vkFreeCommandBuffers(device, command_pool, 1, &command);
    vkDestroyCommandPool(device, command_pool, nullptr);
    vkDestroyDescriptorPool(device, pool, nullptr);
    for (auto view : views) vkDestroyBufferView(device, view, nullptr);
    vkUnmapMemory(device, memory);
    vkDestroyBuffer(device, buffer, nullptr);
    vkFreeMemory(device, memory, nullptr);
    vkDestroyPipeline(device, pipeline, nullptr);
    vkDestroyShaderModule(device, module, nullptr);
    vkDestroyPipelineLayout(device, layout, nullptr);
    vkDestroyDescriptorSetLayout(device, set_layout, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);
    std::puts("G07_REAL_NATIVE_VULKAN_TEXEL_SSBO_PASS descriptors=2 image_fetch=2 dispatch=1 fence=1 ssbo_write=2");
}
