// SPDX-License-Identifier: MIT
// Linux host entrypoint for authentic, user-owned DLSS-NR Original model.
// Needs a host build linked to the maintained Eden video_core Vulkan runtime.
// NEVER use a synthetic fixture as the authentic test's input or output.
// Eden's NvResult declares Success/BadValue, both global X11 macros.
// Parse that upstream enum before the Vulkan platform headers import X.h.
#include "core/hle/service/nvdrv/nvdata.h"
#include "r09_native_plans.h"
#include "nr_dll_launch_preflight.h"
#include "video_core/renderer_vulkan/nr_rdna2_frame_session.h"
#include "video_core/renderer_vulkan/nr_rdna2_frame_readback.h"
// The Linux Vulkan header includes X11/X.h, whose Success macro must not
// replace Eden's enum Service::Nvidia::NvResult::Success further below.
#ifdef Success
#undef Success
#endif
#ifdef BadValue
#undef BadValue
#endif
#include "video_core/renderer_vulkan/present/util.h"
#include "video_core/renderer_vulkan/vk_scheduler.h"
#include "video_core/renderer_vulkan/vk_state_tracker.h"
#include "video_core/vulkan_common/vulkan_device.h"
#include "video_core/vulkan_common/vulkan_instance.h"
#include "video_core/vulkan_common/vulkan_library.h"
#include "video_core/vulkan_common/vulkan_memory_allocator.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace vk = Vulkan::vk;
namespace {
constexpr std::uint32_t kWidth = 1920u;
constexpr std::uint32_t kHeight = 1080u;
constexpr VkExtent2D kExtent{kWidth, kHeight};
constexpr std::uint64_t kInputBytes = std::uint64_t(kWidth) * kHeight * 4u;

std::vector<std::uint8_t> ReadRawRgba8(const std::filesystem::path& path) {
    if (!std::filesystem::is_regular_file(path) ||
        std::filesystem::file_size(path) != kInputBytes) {
        throw std::runtime_error("R09_HOST_INPUT_NOT_REAL_RGBA8_1920X1080");
    }
    std::ifstream stream{path, std::ios::binary};
    if (!stream) throw std::runtime_error("R09_HOST_INPUT_READ_FAILED");
    std::vector<std::uint8_t> contents(kInputBytes);
    stream.read(reinterpret_cast<char*>(contents.data()),
                static_cast<std::streamsize>(contents.size()));
    if (!stream || stream.gcount() != static_cast<std::streamsize>(contents.size())) {
        throw std::runtime_error("R09_HOST_INPUT_SHORT_READ");
    }
    return contents;
}

vk::Image MakeImage(Vulkan::MemoryAllocator& allocator, VkFormat format,
                    VkImageUsageFlags usage) {
    const VkImageCreateInfo ci{
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .pNext = nullptr,
        .flags = 0u,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = format,
        .extent = {kWidth, kHeight, 1u},
        .mipLevels = 1u,
        .arrayLayers = 1u,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_OPTIMAL,
        .usage = usage,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .queueFamilyIndexCount = 0u,
        .pQueueFamilyIndices = nullptr,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    auto result = allocator.CreateImage(ci);
    if (!result) throw std::runtime_error("R09_HOST_VULKAN_IMAGE_ALLOCATION_FAILED");
    return result;
}

void Run(const std::filesystem::path& model_path,
         const std::filesystem::path& input_path,
         const std::filesystem::path& output_path) {
    if (!std::filesystem::is_regular_file(model_path)) {
        throw std::runtime_error("R09_HOST_AUTHENTIC_MODEL_MISSING");
    }
    // The shipping importer checks all 599 public learned-tensor digests.
    // Never accept a syntactically valid synthetic NRMODEL1 as Original.
    if (!Eden::Graphics::R09UsableCachedPack(
            model_path, Eden::Graphics::NeuralRDNA2::R09ModelVariant::Original)) {
        throw std::runtime_error("R09_HOST_AUTHENTIC_599_TENSOR_SHA256_REJECTED");
    }
    // Check real capture bytes before spending Vulkan memory. No generated
    // color bars or fixture mode is supported in this program.
    const auto source_pixels = ReadRawRgba8(input_path);
    auto library = Vulkan::OpenLibrary();
    vk::InstanceDispatch dispatch{};
    auto instance = Vulkan::CreateInstance(*library, dispatch, VK_API_VERSION_1_1);
    const auto physical_devices = instance.EnumeratePhysicalDevices();
    if (physical_devices.empty()) {
        throw std::runtime_error("R09_HOST_NO_VULKAN_PHYSICAL_DEVICE");
    }
    Vulkan::Device device{*instance,
                          vk::PhysicalDevice(physical_devices.front(), dispatch),
                          VK_NULL_HANDLE, dispatch};
    Vulkan::MemoryAllocator allocator{device};
    Vulkan::StateTracker state_tracker{};
    Vulkan::Scheduler scheduler{device, state_tracker};
    auto source_image = MakeImage(allocator, VK_FORMAT_R8G8B8A8_UNORM,
                                  VK_IMAGE_USAGE_TRANSFER_DST_BIT |
                                  VK_IMAGE_USAGE_SAMPLED_BIT);
    auto target_image = MakeImage(allocator, VK_FORMAT_R32G32B32A32_SFLOAT,
                                  VK_IMAGE_USAGE_STORAGE_BIT |
                                  VK_IMAGE_USAGE_SAMPLED_BIT |
                                  VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
    auto source_view = Vulkan::CreateWrappedImageView(
        device, source_image, VK_FORMAT_R8G8B8A8_UNORM);
    auto target_view = Vulkan::CreateWrappedImageView(
        device, target_image, VK_FORMAT_R32G32B32A32_SFLOAT);
    auto source_sampler = Vulkan::CreateWrappedSampler(device);
    if (!source_view || !target_view || !source_sampler) {
        throw std::runtime_error("R09_HOST_VULKAN_VIEW_OR_SAMPLER_FAILED");
    }
    // True Vulkan upload to GENERAL, followed by a completed GPU tick.
    Vulkan::UploadImage(device, allocator, scheduler, source_image,
                        kExtent, VK_FORMAT_R8G8B8A8_UNORM,
                        std::span<const std::uint8_t>{source_pixels});
    // The neural present shader expects the destination in GENERAL.
    scheduler.RequestOutsideRenderPassOperationContext();
    const VkImage target = *target_image;
    scheduler.Record([target](vk::CommandBuffer command) {
        Vulkan::TransitionImageLayout(
            command, target, VK_IMAGE_LAYOUT_GENERAL,
            VK_IMAGE_LAYOUT_UNDEFINED);
    });
    scheduler.Finish();
    Vulkan::NrRdna2FrameSession frame{device, allocator, scheduler};
    if (!frame.Initialize(
        model_path.string(), Eden::NeuralPlans::Original,
        *source_view, *source_sampler, VK_FORMAT_R8G8B8A8_UNORM, kExtent,
        *target_view, VK_FORMAT_R32G32B32A32_SFLOAT, kExtent,
        1.0f, 1.0f)) {
        throw std::runtime_error(
            std::string("R09_HOST_ORIGINAL_INIT_REJECTED phase=") +
            std::string(frame.LastInitializePhaseName()));
    }
    Vulkan::NrRdna2FrameGpuReadback evidence{};
    if (!Vulkan::ExecuteR09FrameAndReadback(
            frame, allocator, scheduler, target,
            *target_view, kExtent, evidence) ||
        !evidence.readback_completed) {
        throw std::runtime_error(
            std::string("R09_HOST_ORIGINAL_GPU_FAILED phase=") +
            evidence.record_phase);
    }
    // Output size is fixed by the true shader target. The separate
    // r09_verify_full_gpu_evidence tool must still compare an independent
    // oracle and reject incomplete per-operation GPU traces.
    constexpr std::uint64_t output_size = kInputBytes * sizeof(float);
    if (evidence.rgba32f_le.size() != output_size) {
        throw std::runtime_error("R09_HOST_RGBA32F_SIZE_MISMATCH");
    }
    std::ofstream output{output_path, std::ios::binary | std::ios::trunc};
    if (!output) throw std::runtime_error("R09_HOST_CANNOT_WRITE_OUTPUT");
    output.write(reinterpret_cast<const char*>(evidence.rgba32f_le.data()),
                 static_cast<std::streamsize>(evidence.rgba32f_le.size()));
    if (!output) throw std::runtime_error("R09_HOST_OUTPUT_WRITE_FAILED");
    std::cout << "R09_HOST_REAL_FRAME_VULKAN_READBACK "
              << evidence.rgba32f_le.size()
              << " bytes; scheduler_callbacks="
              << evidence.enqueued_callbacks << "\n"
              << "NOT_A_VERIFIED_152_OPERATION_TRACE_OR_INDEPENDENT_ORACLE\n";
}
} // namespace

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "Usage: r09_full_gpu_host ORIGINAL.nrmodel "
                  << "CAPTURE_1920x1080.rgba8 OUTPUT.rgba32f\n";
        return 64;
    }
    try {
        Run(argv[1], argv[2], argv[3]);
        return 0;
    } catch (const std::exception& failure) {
        std::cerr << "R09_FULL_GPU_HOST_REJECTED: " << failure.what() << "\n";
        return 70;
    }
}
