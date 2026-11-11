// SPDX-License-Identifier: MIT
// Linux host entrypoint for authentic, user-owned DLSS-NR Original model.
// Needs a host build linked to the maintained Eden video_core Vulkan runtime.
// NEVER use a synthetic fixture as the authentic test's input or output.
// Eden's NvResult declares Success/BadValue, both global X11 macros.
// Parse that upstream enum before the Vulkan platform headers import X.h.
#include "core/hle/service/nvdrv/nvdata.h"
#include "r09_native_plans.h"
#include "dlss_nr_min_720_plan_emit.h"
#include "video_core/renderer_vulkan/nr_rdna2_session_preflight.h"
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
#include <cmath>
#include <algorithm>
#include <cstring>
#include <limits>
#include <span>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdlib.h> // Linux mkdtemp: private 0700 model extraction directory
#include <fcntl.h>  // O_EXCL: never overwrite the user's DLL or source capture
#include <unistd.h> // close, write, unlink
#include <stdexcept>
#include <string>
#include <vector>

namespace vk = Vulkan::vk;
namespace {
constexpr VkExtent2D kReferenceExtent{1920u,1080u};
constexpr VkExtent2D kResearch720Extent{1280u,720u};
[[nodiscard]] constexpr std::uint64_t RgbaBytes(VkExtent2D extent) noexcept {
    return std::uint64_t(extent.width)*extent.height*4u;
}

// The public runner may consume one user-supplied original model DLL directly.
// Import as DATA (never execute a Windows DLL), authenticate the 599 learned
// tensors, and delete the extracted ~141 MiB pack on every exit path.
struct PrivateModelCache {
    std::filesystem::path directory{};
    ~PrivateModelCache() {
        if (!directory.empty()) {
            std::error_code ignored;
            std::filesystem::remove_all(directory, ignored);
        }
    }
};

std::filesystem::path ResolvePrivateOriginal(
    const std::filesystem::path& input, PrivateModelCache& cache) {
    if (input.extension() != ".dll") return input;
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(input, ec);
    if (ec || !std::filesystem::is_regular_file(status) ||
        std::filesystem::is_symlink(status)) {
        throw std::runtime_error("R09_HOST_PRIVATE_DLL_NOT_REGULAR");
    }
    auto pattern = (std::filesystem::temp_directory_path() /
                    "eden-r09-original-XXXXXX").string();
    char* directory = ::mkdtemp(pattern.data());
    if (!directory) {
        throw std::runtime_error("R09_HOST_PRIVATE_MODEL_DIRECTORY_FAILED");
    }
    cache.directory = directory;
    const auto model = cache.directory / "original.nrmodel";
    const auto imported = Eden::NRDllImport::ImportOriginal(
        input, model, Eden::Graphics::NeuralRDNA2::R09OriginalManifest);
    if (!imported.imported) {
        throw std::runtime_error("R09_HOST_PRIVATE_DLL_ORIGINAL_IMPORT_REJECTED");
    }
    return model;
}

std::vector<std::uint8_t> ReadRawRgba8(
    const std::filesystem::path& path,VkExtent2D extent,bool min_720) {
    const auto bytes=RgbaBytes(extent);
    if (!std::filesystem::is_regular_file(path) ||
        std::filesystem::file_size(path) != bytes) {
        throw std::runtime_error(min_720?
            "R09_MIN_720_INPUT_NOT_REAL_RGBA8_1280X720":
            "R09_HOST_INPUT_NOT_REAL_RGBA8_1920X1080");
    }
    std::ifstream stream{path, std::ios::binary};
    if (!stream) throw std::runtime_error("R09_HOST_INPUT_READ_FAILED");
    std::vector<std::uint8_t> contents(static_cast<std::size_t>(bytes));
    stream.read(reinterpret_cast<char*>(contents.data()),
                static_cast<std::streamsize>(contents.size()));
    if (!stream || stream.gcount() != static_cast<std::streamsize>(contents.size())) {
        throw std::runtime_error("R09_HOST_INPUT_SHORT_READ");
    }
    return contents;
}

vk::Image MakeImage(Vulkan::MemoryAllocator& allocator, VkFormat format,
                    VkImageUsageFlags usage,VkExtent2D extent) {
    const VkImageCreateInfo ci{
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .pNext = nullptr,
        .flags = 0u,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = format,
        .extent = {extent.width, extent.height, 1u},
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

void Run(const std::filesystem::path& original_model_or_dll,
         const std::filesystem::path& input_path,
         const std::filesystem::path& output_path,bool min_720) {
    const VkExtent2D extent=min_720?kResearch720Extent:kReferenceExtent;
    PrivateModelCache private_cache{};
    const auto model_path = ResolvePrivateOriginal(
        original_model_or_dll, private_cache);
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
    if (!private_cache.directory.empty()) {
        std::cout << "R09_HOST_AUTHENTIC_DLL_IMPORT_AND_599_HASH_PASS\n";
    }
    std::string emitted_720{};
    std::string_view native_plan=Eden::NeuralPlans::Original;
    if(min_720) {
        Eden::Graphics::DlssNrMin::EmittedR09Min720Plan candidate{};
        if(!Eden::Graphics::DlssNrMin::EmitR09Min720NativePlan(
               Eden::NeuralPlans::Original,candidate)||
           !candidate.exact_native_round_trip||candidate.rows!=152u||
           candidate.gpu_executable)
            throw std::runtime_error("R09_MIN_720_NATIVE_PLAN_REJECTED");
        emitted_720=std::move(candidate.text);
        native_plan=emitted_720;
        Eden::Graphics::NeuralRDNA2::R09SessionCPUPlan checked{};
        if(!Eden::Graphics::NeuralRDNA2::PreflightR09Session(
               model_path.string(),native_plan,extent.width,extent.height,
               extent.width,extent.height,checked)||
           !Eden::Graphics::NeuralRDNA2::ValidateR09LearnedUpsampleInputs(
               checked))
            throw std::runtime_error(
               "R09_MIN_720_AUTHENTIC_MODEL_ADAPTER_PREFLIGHT_REJECTED");
        std::cout<<"R09_MIN_720_AUTHENTIC_152_ROW_CPU_PREFLIGHT_PASS"
                    " raster=1280x720 HOST_ONLY\\n";
    }
    const auto source_pixels=ReadRawRgba8(input_path,extent,min_720);
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
                                  VK_IMAGE_USAGE_SAMPLED_BIT,extent);
    auto target_image = MakeImage(allocator, VK_FORMAT_R32G32B32A32_SFLOAT,
                                  VK_IMAGE_USAGE_STORAGE_BIT |
                                  VK_IMAGE_USAGE_SAMPLED_BIT |
                                  VK_IMAGE_USAGE_TRANSFER_SRC_BIT,extent);
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
                        extent, VK_FORMAT_R8G8B8A8_UNORM,
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
        model_path.string(), native_plan,
        *source_view, *source_sampler, VK_FORMAT_R8G8B8A8_UNORM, extent,
        *target_view, VK_FORMAT_R32G32B32A32_SFLOAT, extent,
        1.0f, 1.0f)) {
        throw std::runtime_error(
            std::string("R09_HOST_ORIGINAL_INIT_REJECTED phase=") +
            std::string(frame.LastInitializePhaseName()));
    }
    Vulkan::NrRdna2FrameGpuReadback evidence{};
    if (!Vulkan::ExecuteR09FrameAndReadback(
            frame, allocator, scheduler, target,
            *target_view, extent, evidence) ||
        !evidence.readback_completed) {
        throw std::runtime_error(
            std::string("R09_HOST_ORIGINAL_GPU_FAILED phase=") +
            evidence.record_phase);
    }
    // Output size is fixed by the true shader target. The separate
    // r09_verify_full_gpu_evidence tool must still compare an independent
    // oracle and reject incomplete per-operation GPU traces.
    const std::uint64_t output_size=RgbaBytes(extent)*sizeof(float);
    if (evidence.rgba32f_le.size() != output_size) {
        throw std::runtime_error("R09_HOST_RGBA32F_SIZE_MISMATCH");
    }
    // A successful queue fence is not sufficient proof of a neural image.
    // Reject NaNs/infinities and a constant RGB readback before publishing
    // bytes; alpha cannot hide a completely degenerate color result.
    float min_rgb = std::numeric_limits<float>::infinity();
    float max_rgb = -std::numeric_limits<float>::infinity();
    for (std::size_t byte = 0u; byte < evidence.rgba32f_le.size();
         byte += sizeof(float)) {
        float value{};
        std::memcpy(&value, evidence.rgba32f_le.data() + byte,
                    sizeof(value));
        if (!std::isfinite(value)) {
            throw std::runtime_error("R09_HOST_RGBA32F_NONFINITE");
        }
        if ((byte / sizeof(float)) % 4u != 3u) {
            min_rgb = std::min(min_rgb, value);
            max_rgb = std::max(max_rgb, value);
        }
    }
    if (!(max_rgb - min_rgb > 0.001f)) {
        throw std::runtime_error("R09_HOST_RGBA32F_DEGENERATE_RGB");
    }
    // An accidental OUTPUT=DLL or OUTPUT=CAPTURE must never truncate the
    // only genuine model/capture. Open exclusively (0600) rather than using
    // std::ofstream(trunc), including against symlinks and existing outputs.
    const int fd = ::open(output_path.c_str(),
                          O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    if (fd < 0) throw std::runtime_error("R09_HOST_OUTPUT_EXISTS_OR_UNWRITABLE");
    struct ExclusiveOutput {
        int fd;
        std::filesystem::path path;
        bool complete{};
        ~ExclusiveOutput() {
            if (fd >= 0) ::close(fd);
            if (!complete) ::unlink(path.c_str());
        }
    } output{fd, output_path};
    std::size_t written = 0u;
    while (written < evidence.rgba32f_le.size()) {
        const auto left = evidence.rgba32f_le.size() - written;
        const auto requested = std::min(left, static_cast<std::size_t>(1u << 20));
        const auto done = ::write(output.fd, evidence.rgba32f_le.data() +
                                             written, requested);
        if (done <= 0) throw std::runtime_error("R09_HOST_OUTPUT_WRITE_FAILED");
        written += static_cast<std::size_t>(done);
    }
    if (::fsync(output.fd) != 0) {
        throw std::runtime_error("R09_HOST_OUTPUT_FLUSH_FAILED");
    }
    if (::close(output.fd) != 0) {
        output.fd = -1;
        throw std::runtime_error("R09_HOST_OUTPUT_CLOSE_FAILED");
    }
    output.fd = -1;
    output.complete = true;
    // Bind the actual bytes, not just claimed dimensions, into the host log.
    // These digests permit an offline verifier to identify the exact capture
    // and GPU readback without ever publishing proprietary model tensors.
    Eden::GlyphIntegrity::Sha256 input_hash;
    input_hash.Update(source_pixels.data(), source_pixels.size());
    Eden::GlyphIntegrity::Sha256 output_hash;
    output_hash.Update(evidence.rgba32f_le.data(),
                       evidence.rgba32f_le.size());
    std::cout << (min_720 ? "R09_MIN_720_RESEARCH_FRAME_VULKAN_READBACK " : "R09_HOST_REAL_FRAME_VULKAN_READBACK ")
              << evidence.rgba32f_le.size()
              << " bytes; scheduler_callbacks="
              << evidence.enqueued_callbacks << "\n"
              << "R09_HOST_CAPTURE_SHA256=" << input_hash.FinishHex() << "\n"
              << "R09_HOST_GPU_READBACK_SHA256=" << output_hash.FinishHex() << "\n"
              << "NOT_A_VERIFIED_152_OPERATION_TRACE_OR_INDEPENDENT_ORACLE\n";
}
} // namespace

int main(int argc, char** argv) {
    const bool min_720=argc==5&&
        std::string_view(argv[4])=="--research-720p";
    if(argc!=4&&!min_720) {
        std::cerr<<"Usage: r09_full_gpu_host ORIGINAL.nrmodel|nvngx_dlssnr.dll "
                    "CAPTURE_1920x1080.rgba8 OUTPUT.rgba32f "
                    "[--research-720p (expects 1280x720 capture)]\n";
        return 64;
    }
#if !defined(EDEN_R09_MIN_720_HOST_EXPERIMENTAL) || !EDEN_R09_MIN_720_HOST_EXPERIMENTAL
    if(min_720) {
        std::cerr<<"R09_MIN_720_HOST_EXPERIMENTAL_COMPILE_GATE_DISABLED\n";
        return 64;
    }
#endif
    try {
        Run(argv[1],argv[2],argv[3],min_720);
        return 0;
    } catch(const std::exception& failure) {
        std::cerr<<"R09_FULL_GPU_HOST_REJECTED: "<<failure.what()<<"\n";
        return 70;
    }
}
