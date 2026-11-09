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
    Check(fetches == 3 && writes >= 3, "emitter omitted sampled 2D image read/write");
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
        if (!(props.bufferFeatures & VK_FORMAT_FEATURE_UNIFORM_TEXEL_BUFFER_BIT) ||
            !(props.optimalTilingFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT)) continue;
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

    std::array<VkDescriptorSetLayoutBinding, 3> bindings{};
    bindings[0].binding = 0;
    bindings[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    bindings[0].descriptorCount = 1;
    bindings[0].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    bindings[1].binding = 1;
    bindings[1].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER;
    bindings[1].descriptorCount = 2;
    bindings[1].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    bindings[2].binding = 2;
    bindings[2].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    bindings[2].descriptorCount = 1;
    bindings[2].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
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
                VK_BUFFER_USAGE_UNIFORM_TEXEL_BUFFER_BIT |
                VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
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
    // 2x2 RGBA32F sampled image staging. Pixel (1,0) has red=2.5.
    data[(1024 + 16) / 4] = Bits(2.5f);

    VkImageCreateInfo image_create{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
    image_create.imageType = VK_IMAGE_TYPE_2D;
    image_create.format = VK_FORMAT_R32G32B32A32_SFLOAT;
    image_create.extent = {2, 2, 1};
    image_create.mipLevels = 1;
    image_create.arrayLayers = 1;
    image_create.samples = VK_SAMPLE_COUNT_1_BIT;
    image_create.tiling = VK_IMAGE_TILING_OPTIMAL;
    image_create.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    image_create.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    image_create.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    VkImage sampled_image = VK_NULL_HANDLE;
    Check(vkCreateImage(device, &image_create, nullptr, &sampled_image) == VK_SUCCESS,
          "sampled TIC image");
    VkMemoryRequirements image_req{};
    vkGetImageMemoryRequirements(device, sampled_image, &image_req);
    uint32_t image_type = memory_props.memoryTypeCount;
    for (uint32_t i = 0; i < memory_props.memoryTypeCount; ++i)
        if (image_req.memoryTypeBits & (1U << i)) {
            image_type = i;
            if (memory_props.memoryTypes[i].propertyFlags &
                VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT) break;
        }
    Check(image_type < memory_props.memoryTypeCount, "sampled image memory type");
    VkMemoryAllocateInfo image_alloc{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    image_alloc.allocationSize = image_req.size;
    image_alloc.memoryTypeIndex = image_type;
    VkDeviceMemory image_memory = VK_NULL_HANDLE;
    Check(vkAllocateMemory(device, &image_alloc, nullptr, &image_memory) == VK_SUCCESS,
          "sampled image allocation");
    Check(vkBindImageMemory(device, sampled_image, image_memory, 0) == VK_SUCCESS,
          "sampled image bind");
    VkImageViewCreateInfo ivci{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
    ivci.image = sampled_image;
    ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format = VK_FORMAT_R32G32B32A32_SFLOAT;
    ivci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    ivci.subresourceRange.levelCount = 1;
    ivci.subresourceRange.layerCount = 1;
    VkImageView image_view = VK_NULL_HANDLE;
    Check(vkCreateImageView(device, &ivci, nullptr, &image_view) == VK_SUCCESS,
          "TIC sampled image view");
    VkSamplerCreateInfo sampler_ci{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
    sampler_ci.magFilter = VK_FILTER_NEAREST;
    sampler_ci.minFilter = VK_FILTER_NEAREST;
    sampler_ci.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sampler_ci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sampler_ci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sampler_ci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    VkSampler sampler = VK_NULL_HANDLE;
    Check(vkCreateSampler(device, &sampler_ci, nullptr, &sampler) == VK_SUCCESS,
          "TSC sampler");

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
    std::array<VkDescriptorPoolSize, 3> sizes{{
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1},
        {VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER, 2},
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1}
    }};
    VkDescriptorPoolCreateInfo dpci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    dpci.maxSets = 1;
    dpci.poolSizeCount = 3;
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
    std::array<VkWriteDescriptorSet, 3> writes{};
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
    VkDescriptorImageInfo sampled_info{};
    sampled_info.sampler = sampler;
    sampled_info.imageView = image_view;
    sampled_info.imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    writes[2].dstBinding = 2;
    writes[2].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    writes[2].descriptorCount = 1;
    writes[2].pImageInfo = &sampled_info;
    vkUpdateDescriptorSets(device, 3, writes.data(), 0, nullptr);

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
    VkImageMemoryBarrier image_barrier{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    image_barrier.image = sampled_image;
    image_barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    image_barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    image_barrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    image_barrier.subresourceRange.levelCount = 1;
    image_barrier.subresourceRange.layerCount = 1;
    image_barrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    image_barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    image_barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
        VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &image_barrier);
    VkBufferImageCopy image_copy{};
    image_copy.bufferOffset = 1024;
    image_copy.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    image_copy.imageSubresource.layerCount = 1;
    image_copy.imageExtent = {2,2,1};
    vkCmdCopyBufferToImage(command, buffer, sampled_image,
                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &image_copy);
    image_barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    image_barrier.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    image_barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    image_barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, 0, nullptr, 0, nullptr,
        1, &image_barrier);
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
    Check(data[0] == Bits(1.25f) && data[1] == Bits(7.5f) &&
          data[2] == Bits(2.5f),
          "wrong GPU TIC/TSC image or texel descriptor selection/SSBO writeback");
    for (uint32_t i = 3; i < 16; ++i)
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
    vkDestroySampler(device, sampler, nullptr);
    vkDestroyImageView(device, image_view, nullptr);
    vkDestroyImage(device, sampled_image, nullptr);
    vkFreeMemory(device, image_memory, nullptr);
    vkUnmapMemory(device, memory);
    vkDestroyBuffer(device, buffer, nullptr);
    vkFreeMemory(device, memory, nullptr);
    vkDestroyPipeline(device, pipeline, nullptr);
    vkDestroyShaderModule(device, module, nullptr);
    vkDestroyPipelineLayout(device, layout, nullptr);
    vkDestroyDescriptorSetLayout(device, set_layout, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);
    std::puts("G07_REAL_NATIVE_VULKAN_TIC_TSC_SSBO_PASS texel=2 sampled_2d=1 dispatch=1 fence=1 ssbo_write=3");
}
