// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// SPDX-FileCopyrightText: Copyright 2018 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include <algorithm>
#include <array>
#include <cstring>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <fmt/ranges.h>
#include <algorithm>
#include <chrono>
#include <limits>

#include "common/logging.h"
#include <ranges>
#include "common/scope_exit.h"
#include "common/settings.h"
#include "core/core_timing.h"
#include "core/frontend/graphics_context.h"
#include "video_core/capture.h"
#include "video_core/gpu.h"
#include "video_core/present.h"
#include "video_core/renderer_vulkan/present/util.h"
#include "video_core/renderer_vulkan/renderer_vulkan.h"
#include "prosperoeden/pe/platform/display_egl.hpp"
#include "display_refresh.h"
#include "frame_metrics.h"
#include "fsr3_optical_session.h"
#include "hud.h"
#include "mihawk_native_session.h"
#include "mihawk_session_resize.h"
#include "storage_paths.h"
#include "video_core/renderer_vulkan/vk_blit_screen.h"
#include "video_core/renderer_vulkan/vk_rasterizer.h"
#include "video_core/renderer_vulkan/vk_scheduler.h"
#include "video_core/renderer_vulkan/vk_state_tracker.h"
#include "video_core/renderer_vulkan/vk_swapchain.h"
#include "video_core/textures/decoders.h"
#include "video_core/vulkan_common/vulkan_debug_callback.h"
#include "video_core/vulkan_common/vulkan_device.h"
#include "video_core/vulkan_common/vulkan_instance.h"
#include "video_core/vulkan_common/vulkan_library.h"
#include "video_core/vulkan_common/vulkan_memory_allocator.h"
#include "video_core/vulkan_common/vulkan_surface.h"
#include "video_core/vulkan_common/vulkan_wrapper.h"
#ifdef __ANDROID__
#include <jni.h>
#endif
namespace Vulkan {
namespace {

constexpr VkExtent2D CaptureImageSize{
    .width = VideoCore::Capture::LinearWidth,
    .height = VideoCore::Capture::LinearHeight,
};

#ifdef HAS_LSFG
[[nodiscard]] VkExtent2D GuestExtent(std::span<const Tegra::FramebufferConfig> framebuffers) {
    if (framebuffers.empty()) {
        return VkExtent2D{};
    }

    const auto& framebuffer = framebuffers.front();
    if (framebuffer.crop_rect.IsEmpty()) {
        return VkExtent2D{.width = framebuffer.width, .height = framebuffer.height};
    }
    return VkExtent2D{
        .width = static_cast<u32>(framebuffer.crop_rect.GetWidth()),
        .height = static_cast<u32>(framebuffer.crop_rect.GetHeight()),
    };
}
#endif

constexpr VkExtent3D CaptureImageExtent{
    .width = VideoCore::Capture::LinearWidth,
    .height = VideoCore::Capture::LinearHeight,
    .depth = VideoCore::Capture::LinearDepth,
};

constexpr VkFormat CaptureFormat = VK_FORMAT_A8B8G8R8_UNORM_PACK32;

std::string GetReadableVersion(u32 version) {
    return fmt::format("{}.{}.{}", VK_VERSION_MAJOR(version), VK_VERSION_MINOR(version),
                       VK_VERSION_PATCH(version));
}

std::string GetDriverVersion(const Device& device) {
    // Extracted from
    // https://github.com/SaschaWillems/vulkan.gpuinfo.org/blob/5dddea46ea1120b0df14eef8f15ff8e318e35462/functions.php#L308-L314
    const u32 version = device.GetDriverVersion();

    if (device.GetDriverID() == VK_DRIVER_ID_NVIDIA_PROPRIETARY) {
        const u32 major = (version >> 22) & 0x3ff;
        const u32 minor = (version >> 14) & 0x0ff;
        const u32 secondary = (version >> 6) & 0x0ff;
        const u32 tertiary = version & 0x003f;
        return fmt::format("{}.{}.{}.{}", major, minor, secondary, tertiary);
    }
    if (device.GetDriverID() == VK_DRIVER_ID_INTEL_PROPRIETARY_WINDOWS) {
        const u32 major = version >> 14;
        const u32 minor = version & 0x3fff;
        return fmt::format("{}.{}", major, minor);
    }
    return GetReadableVersion(version);
}

std::string BuildCommaSeparatedExtensions(
    const std::set<std::string, std::less<>>& available_extensions) {
    return fmt::format("{}", fmt::join(available_extensions, ","));
}

vk::SurfaceKHR CreateHandoffSurface(
    const vk::Instance& instance,
    const Core::Frontend::EmuWindow::WindowSystemInfo& window_info) {
#ifdef PS5_NATIVE
    if (pe::ps5::Display::has_deferred_scanout()) {
        // Keep the final OpenGL loading frame visible through System::Load
        // and Vulkan instance creation. Release VideoOut only at the exact
        // WSI takeover boundary; never run two scanout owners concurrently.
        if (!pe::ps5::Display::close_deferred_scanout())
            throw std::runtime_error{"Could not release launcher VideoOut before Vulkan surface creation"};
        std::fprintf(stderr, "EDEN_GL_VK_SCANOUT_HANDOFF release=1 boundary=create_surface\n");
    }
#endif
    return CreateSurface(instance, window_info);
}

} // Anonymous namespace

Device CreateDevice(const vk::Instance& instance, const vk::InstanceDispatch& dld, VkSurfaceKHR surface) {
    const std::vector<VkPhysicalDevice> devices = instance.EnumeratePhysicalDevices();
    const u32 device_index = Settings::values.vulkan_device.GetValue();
    if (device_index >= u32(devices.size())) {
        LOG_ERROR(Render_Vulkan, "Invalid device index {}!", device_index);
        throw vk::Exception(VK_ERROR_INITIALIZATION_FAILED);
    }
    const vk::PhysicalDevice physical_device(devices[device_index], dld);
    return Device(*instance, physical_device, surface, dld);
}

RendererVulkan::RendererVulkan(Core::Frontend::EmuWindow& emu_window,
                               Tegra::MaxwellDeviceMemoryManager& device_memory_,
                               Tegra::GPU& gpu_,
                               std::unique_ptr<Core::Frontend::GraphicsContext> context_)
try
    : RendererBase(emu_window, std::move(context_))
    , device_memory(device_memory_)
    , gpu(gpu_)
    , library(OpenLibrary(context.get()))
    , dld()
    // Create raw Vulkan instance first
    , instance(CreateInstance(*library,
                            dld,
                            VK_API_VERSION_1_1,
                            render_window.GetWindowInfo().type,
                            Settings::values.renderer_debug.GetValue()))
    // Create debug messenger if debug is enabled
    , debug_messenger(Settings::values.renderer_debug ? CreateDebugUtilsCallback(instance)
                                                    : vk::DebugUtilsMessenger{})
    // Create surface
    , surface(CreateHandoffSurface(instance, render_window.GetWindowInfo()))
    , device(CreateDevice(instance, dld, *surface))
    , memory_allocator(device)
    , state_tracker()
    , scheduler(device, state_tracker)
    , swapchain(*surface,
                device,
                scheduler,
               render_window.GetFramebufferLayout().width,
               render_window.GetFramebufferLayout().height)
    , present_manager(instance,
                      render_window,
                      device,
                      memory_allocator,
                      scheduler,
                      swapchain,
                      surface)
    , blit_swapchain(device_memory,
                   device,
                   memory_allocator,
                   present_manager,
                   scheduler,
                   PresentFiltersForDisplay)
    , blit_capture(device_memory,
                   device,
                   memory_allocator,
                   present_manager,
                   scheduler,
                   PresentFiltersForDisplay)
    , blit_applet(device_memory,
                  device,
                  memory_allocator,
                  present_manager,
                  scheduler,
                  PresentFiltersForAppletCapture)
    , rasterizer(render_window, gpu, device_memory, device, memory_allocator, state_tracker, scheduler)
#ifdef HAS_LSFG
    , frame_gen(memory_allocator, scheduler)
#endif
{

    if (Settings::values.renderer_force_max_clock.GetValue() && device.ShouldBoostClocks()) {
        turbo_mode.emplace(instance, dld);
        scheduler.RegisterOnSubmit([this] { turbo_mode->QueueSubmitted(); });
    }

    PresentLoading();
    Report();
} catch (const vk::Exception& exception) {
    LOG_ERROR(Render_Vulkan, "Vulkan initialization failed with error: {}", exception.what());
    throw std::runtime_error{fmt::format("Vulkan initialization error {}", exception.what())};
}

RendererVulkan::~RendererVulkan() {
    scheduler.RegisterOnSubmit([] {});
    // Drain the scheduler's deferred recording worker BEFORE retiring
    // the private images, then wait for Vulkan completion in Destroy().
    // This runs only at renderer shutdown, never in the frame loop.
    scheduler.Finish();
    mihawk_native.reset();
    fsr3_optical.reset();
    void(device.GetLogical().WaitIdle());
}

void RendererVulkan::Composite(std::span<const Tegra::FramebufferConfig> framebuffers) {
    SCOPE_EXIT {
        render_window.OnFrameDisplayed();
    };

    RenderAppletCaptureLayer(framebuffers);

    if (!render_window.IsShown()) {
        return;
    }

    RenderScreenshot(framebuffers);
    // An observed source/composite callback is not an emulated guest FPS
    // measurement. Loading/splash work is accounted separately below.
    ::Eden::FrameMetrics::OnSourceComposite();
    if (::Eden::Display::SkipFrame()) {
        ::Eden::FrameMetrics::OnSourceSkipped();
        gpu.RendererFrameEndNotify();
        rasterizer.TickFrame();
        return;
    }
    Frame* frame = present_manager.GetRenderFrame();

    // Keep Encore's own overlay out of BOTH interpolation backends, not only
    // MihawkGen. Draw once AFTER generating on each image; guest HUD pixels
    // remain inseparable without per-game hooks.
    const int native_fg_method =
        Eden::Display::frame_generation_method.load(std::memory_order_relaxed);
    const bool mihawk_selected = native_fg_method == 1 && !framebuffers.empty();
    const bool postprocess_hud_required =
        (native_fg_method >= 1 && native_fg_method <= 3) && !framebuffers.empty();
    const Eden::HudSnapshot postprocess_hud =
        postprocess_hud_required ? Eden::GetVulkanHud() : Eden::HudSnapshot{};
    scheduler.RequestOutsideRenderPassOperationContext();
    blit_swapchain.DrawToFrame(device, rasterizer, frame, framebuffers,
                               render_window.GetFramebufferLayout(), present_manager.SwapchainImageCount(),
                               present_manager.SwapchainImageViewFormat(), !postprocess_hud_required);

#ifdef HAS_LSFG
    // User-selected LSFG only. Do not mix a legacy generator with MihawkGen
    // or turn frame generation on merely because HAS_LSFG was compiled in.
    if (Eden::Display::frame_generation_method.load(std::memory_order_relaxed) == 3) {
    void(frame_gen.WantedGenerations(present_manager.MaxExtraFrames()));

    frame_gen.Process(device, frame, present_manager.SwapchainImageFormat(), GuestExtent(framebuffers));

    const size_t generated_frames = frame_gen.GeneratedFrameCount();
    for (size_t generation = 0; generation < generated_frames; ++generation) {
        Frame* generated = present_manager.GetRenderFrame();
        blit_swapchain.PrepareFrame(device, generated, render_window.GetFramebufferLayout());
        frame_gen.GenerateInto(device, generated, generation);
        // LSFG's shader output is in GENERAL. Native UI is post-composited
        // like MihawkGen, so it never enters optical-flow calculations.
        blit_swapchain.DrawHudOverlay(device, generated, postprocess_hud);
        scheduler.Flush(*generated->render_ready);
        present_manager.Present(generated);
        ::Eden::FrameMetrics::OnGeneratedQueued();
    }
    }
#endif

    // The AMD FSR3-derived optical-flow interpolator consumes only the real
    // game frame pair. Its private resources must be fenced before reuse;
    // the real frame is always presented even if generation drops out.
    Frame* fsr3_synthetic = nullptr;
    bool fsr3_generated = false;
    bool fsr3_captured = false;
    if (native_fg_method == 2 && !framebuffers.empty()) {
        ++fsr3_source_sequence;
        const u64 source_ns = static_cast<u64>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count());
        const u64 delta_ns = source_ns > fsr3_previous_source_ns
            ? source_ns - fsr3_previous_source_ns : 0;
        fsr3_previous_source_ns = source_ns;
        if (!fsr3_optical)
            fsr3_optical = std::make_unique<Eden::FeatureLab::Fsr3OpticalSession>();
        const auto resize = Eden::FeatureLab::ChooseMihawkSessionAction(
            fsr3_optical->Ready(), fsr3_optical->Width(), fsr3_optical->Height(),
            fsr3_optical->Format(), frame->width, frame->height,
            present_manager.SwapchainImageFormat());
        if (resize == Eden::FeatureLab::MihawkSessionAction::RecreateAfterGpuIdle) {
            scheduler.Finish();
            present_manager.WaitPresent();
            fsr3_optical->Destroy();
            fsr3_init_attempted = false;
            fsr3_present_gate.Reset();
            fsr3_last_capture_tick = 0;
            fsr3_last_capture_id = 0;
        }
        if (resize != Eden::FeatureLab::MihawkSessionAction::InvalidTarget &&
            !fsr3_init_attempted) {
            fsr3_init_attempted = true;
            if (fsr3_optical->Create(
                    dld.vkGetInstanceProcAddr, *instance,
                    device.GetPhysical(), *device.GetLogical(),
                    frame->width, frame->height,
                    present_manager.SwapchainImageFormat()))
                fsr3_present_gate.Reset();
        }
        if (fsr3_optical->Ready()) {
            // The engine keeps TWO source images and one reusable output.
            // Do not touch them while the previous GPU submission is live.
            const bool previous_completed = fsr3_last_capture_tick &&
                scheduler.IsFree(fsr3_last_capture_tick);
            const bool consecutive = fsr3_last_capture_id &&
                fsr3_source_sequence == fsr3_last_capture_id + 1;
            if (!previous_completed || !consecutive)
                fsr3_present_gate.Reset();
            if (fsr3_last_capture_tick == 0 || previous_completed) {
                const int output_mhz =
                    Eden::Display::output_millihertz.load(std::memory_order_relaxed);
                const unsigned output_hz = output_mhz > 0
                    ? static_cast<unsigned>((output_mhz + 500) / 1000) : 0U;
                const unsigned source_fps =
                    delta_ns >= 8'000'000 && delta_ns <= 100'000'000
                    ? static_cast<unsigned>(1'000'000'000ULL / delta_ns) : 0U;
                const Eden::FeatureLab::GraphicsCapabilities caps{
                    .native_vulkan = true,
                    .fsr3_optical_flow = true,
                    .game_fps = source_fps
                };
                const Eden::FeatureLab::PresentGateInput input{
                    .real_frame_id = fsr3_source_sequence,
                    .timestamp_ns = source_ns,
                    .width = frame->width,
                    .height = frame->height,
                    .output_hz = output_hz,
                    .display_mode_verified =
                        output_mhz > 0 && (output_hz == 60 || output_hz == 120)
                };
                const auto decision = fsr3_present_gate.OnRealFrame(
                    Eden::FeatureLab::FrameGeneration::Fsr3Vulkan, caps, input);
                if (decision.eligible() && previous_completed && consecutive) {
                    fsr3_synthetic = present_manager.TryReserveRenderFrame();
                    if (fsr3_synthetic &&
                        (fsr3_synthetic->width != frame->width ||
                         fsr3_synthetic->height != frame->height)) {
                        present_manager.CancelReservedRenderFrame(fsr3_synthetic);
                        fsr3_synthetic = nullptr;
                    }
                    fsr3_generated = fsr3_synthetic != nullptr;
                }
                // Always record the real source when the private GPU images
                // are free. The first copy only primes the optical history.
                scheduler.RequestOutsideRenderPassOperationContext();
                auto* session = fsr3_optical.get();
                const VkImage real_image = *frame->image;
                const VkImage extra_image =
                    fsr3_generated ? *fsr3_synthetic->image : VK_NULL_HANDLE;
                const bool synth = fsr3_generated;
                scheduler.Record([session, real_image, extra_image, synth](
                    vk::CommandBuffer cmd) {
                    (void)session->Record(*cmd, real_image, extra_image, synth);
                });
                fsr3_captured = true;
            }
        }
    } else {
        fsr3_present_gate.Reset();
        fsr3_previous_source_ns = 0;
    }

    // R08 native interpolation. The true guest composite is ALWAYS presented,
    // even when synthesis, GPU pacing, model load or extra FIFO slots fail.
    // The synthetic midpoint must precede the newest real frame in FIFO.
    Eden::FeatureLab::MihawkCapturePermit r08_capture{};
    Frame* r08_synthetic = nullptr;
    bool r08_generated = false;
    if (mihawk_selected) {
        // Zero steady-clock reads or interpolation allocations for the
        // default OFF path. Source IDs count actual compositor callbacks,
        // not generated frames or the game's requested VI cadence.
        ++mihawk_source_sequence;
        const u64 r08_source_ns = static_cast<u64>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count());
        const u64 r08_delta_ns = r08_source_ns > mihawk_previous_source_ns
            ? r08_source_ns - mihawk_previous_source_ns : 0;
        mihawk_previous_source_ns = r08_source_ns;
        if (!mihawk_native)
            mihawk_native = std::make_unique<Eden::FeatureLab::MihawkNativeSession>();
        const auto session_action = Eden::FeatureLab::ChooseMihawkSessionAction(
            mihawk_native->Ready(),
            mihawk_native->Images().Width(), mihawk_native->Images().Height(),
            mihawk_native->Images().SourceFormat(),
            frame->width, frame->height, present_manager.SwapchainImageFormat());
        if (session_action == Eden::FeatureLab::MihawkSessionAction::RecreateAfterGpuIdle) {
            // Genuine extent / format change: drain queued commands FIRST.
            // Device-idle and neural network recreation are one-time work
            // per resize, not a hidden VkDeviceWaitIdle in the frame loop.
            scheduler.Finish();
            present_manager.WaitPresent();
            mihawk_native->Destroy();
            mihawk_capture_fences.ResetAfterDeviceIdle();
            mihawk_present_gate.Reset();
            mihawk_previous_source_ns = 0;
            mihawk_init_attempted = false;
        }
        if (session_action != Eden::FeatureLab::MihawkSessionAction::InvalidTarget &&
            !mihawk_init_attempted) {
            mihawk_init_attempted = true;
            const auto model = Eden::AppResourceFile("mihawkgen/network.fgw");
            if (mihawk_native->Create({
                .instance_proc = dld.vkGetInstanceProcAddr,
                .instance = *instance,
                .physical = device.GetPhysical(),
                .device = *device.GetLogical(),
                .compositor_format = present_manager.SwapchainImageFormat(),
                .width = frame->width,
                .height = frame->height,
                .model_path = model
            })) {
                mihawk_capture_fences.ResetAfterDeviceIdle();
                mihawk_present_gate.Reset();
            }
        }
        if (mihawk_native->Ready() &&
            mihawk_native->Images().Width() == frame->width &&
            mihawk_native->Images().Height() == frame->height &&
            mihawk_native->Images().SourceFormat() == present_manager.SwapchainImageFormat()) {
            r08_capture = mihawk_capture_fences.Acquire(
                [this](u64 tick) { return scheduler.IsFree(tick); });
            if (r08_capture.valid) {
                const auto& owned = mihawk_native->Images();
                const auto& private_history = owned.History(r08_capture.slot);
                const Eden::FeatureLab::MihawkSourceRecord source{
                    .source_real = *frame->image,
                    .history_owned = private_history.image,
                    .history_initialized = owned.Initialized(r08_capture.slot),
                    .width = frame->width,
                    .height = frame->height
                };

                if (Eden::FeatureLab::ValidateOwnedSnapshotInput(source)
                    == Eden::FeatureLab::MihawkRecordResult::Recorded) {
                    const int actual_output_mhz =
                        Eden::Display::output_millihertz.load(std::memory_order_relaxed);
                    const unsigned actual_hz = actual_output_mhz > 0
                        ? static_cast<unsigned>((actual_output_mhz + 500) / 1000) : 0U;
                    // Observed compositor interval, NEVER the guest's requested VI
                    // clock or the synthetic display-frame counter.
                    const unsigned observed_fps = r08_delta_ns >= 8'000'000 &&
                        r08_delta_ns <= 100'000'000
                        ? static_cast<unsigned>(1'000'000'000ULL / r08_delta_ns) : 0U;
                    const Eden::FeatureLab::GraphicsCapabilities graphics{
                        .native_vulkan = true,
                        .mihawk_compute = mihawk_native->Ready(),
                        .model_weights_verified_and_loaded = mihawk_native->Ready(),
                        .game_fps = observed_fps
                    };
                    const Eden::FeatureLab::PresentGateInput input{
                        .real_frame_id = mihawk_source_sequence,
                        .timestamp_ns = r08_source_ns,
                        .width = frame->width,
                        .height = frame->height,
                        .output_hz = actual_hz,
                        .display_mode_verified =
                            actual_output_mhz > 0 && (actual_hz == 60 || actual_hz == 120),
                        .overlay_changed = false // Native overlay is applied after FG
                    };
                    const auto decision = mihawk_present_gate.OnRealFrame(
                        Eden::FeatureLab::FrameGeneration::MihawkGen, graphics, input);
                    const bool prior_snapshot_fenced =
                        mihawk_capture_fences.CanGenerate(
                            r08_capture, mihawk_source_sequence,
                            [this](u64 tick) { return scheduler.IsFree(tick); });

                    Eden::FeatureLab::MihawkGenerateRecord neural{};
                    if (decision.eligible() && prior_snapshot_fenced) {
                        // TryReserve never waits and never resets a fence until
                        // the synthetic image is fully prepared for submission.
                        r08_synthetic = present_manager.TryReserveRenderFrame();
                        if (r08_synthetic &&
                            r08_synthetic->width == frame->width &&
                            r08_synthetic->height == frame->height) {
                            const auto format = present_manager.SwapchainImageFormat();
                            const auto& previous = owned.History(r08_capture.slot ^ 1U);
                            neural = {
                                .context = mihawk_native->Context(),
                                .previous_owned = previous.image,
                                .current_owned = private_history.image,
                                .previous_view = previous.view,
                                .current_view = private_history.view,
                                .private_rgba_output = owned.RgbaOutput().image,
                                .private_rgba_view = owned.RgbaOutput().view,
                                .synthetic_present = *r08_synthetic->image,
                                .width = frame->width,
                                .height = frame->height,
                                .descriptor_slot = 0,
                                .context_slot_count = mihawk_native->DescriptorSlots(),
                                .output_was_blitted = mihawk_native->OutputWasBlitted(),
                                .capabilities = {
                                    .enabled = true,
                                    .native_vulkan = true,
                                    .compute_and_storage = mihawk_native->Ready(),
                                    .model_verified_and_loaded = mihawk_native->Ready(),
                                    .blit_rgba_to_present = true,  // probed by allocator
                                    .owned_history_pair = previous.image != private_history.image,
                                    .history_matches_source_format = owned.SourceFormat() == format,
                                    .private_output_rgba8_storage = owned.RgbaOutput().image != VK_NULL_HANDLE,
                                    .present_image_transfer_dst = true, // RecreateFrame usage
                                    .history_descriptor_slots_fenced = prior_snapshot_fenced,
                                    .present_queue_ordered = true, // same scheduler/queue
                                    .native_hud_absent = true, // absent from input snapshot
                                    .available_present_frames =
                                        static_cast<std::uint8_t>(
                                            std::min<std::size_t>(
                                                present_manager.MaxExtraFrames() + 1, 255)),
                                    .width = frame->width,
                                    .height = frame->height,
                                    .compositor_format =
                                        format == VK_FORMAT_R8G8B8A8_UNORM
                                            ? Eden::FeatureLab::ColorFormat::Rgba8Unorm
                                            : format == VK_FORMAT_B8G8R8A8_UNORM
                                                ? Eden::FeatureLab::ColorFormat::Bgra8Unorm
                                                : Eden::FeatureLab::ColorFormat::Other
                                }
                            };
                            r08_generated =
                                Eden::FeatureLab::ValidateNativeMihawkPairInput(neural) ==
                                Eden::FeatureLab::MihawkRecordResult::Recorded;
                        }
                        if (!r08_generated && r08_synthetic) {
                            // No fence reset, no GPU commands: return the slot as-is.
                            present_manager.CancelReservedRenderFrame(r08_synthetic);
                            r08_synthetic = nullptr;
                        }
                    }

                    scheduler.RequestOutsideRenderPassOperationContext();
                    // Scheduler::Record may invoke the callback through a
                    // const wrapper. Keep captured descriptors immutable and
                    // update local copies with the command buffer handle.
                    scheduler.Record([source, neural, r08_generated](vk::CommandBuffer cmd) {
                        auto recorded_source = source;
                        recorded_source.cmd = *cmd;
                        (void)Eden::FeatureLab::RecordOwnedSnapshot(recorded_source);
                        if (r08_generated) {
                            // Source and generated image remain in the same
                            // recorded command buffer and ordered submission.
                            auto recorded_neural = neural;
                            recorded_neural.cmd = *cmd;
                            (void)Eden::FeatureLab::RecordNativeMihawkPair(recorded_neural);
                        }
                    });
                } else {
                    mihawk_capture_fences.AbortUnsubmitted();
                    r08_capture = {};
                }
            }
        }
    } else {
        // Game/menu/renderer switch cannot reuse an old source pair.
        mihawk_present_gate.Reset();
        mihawk_previous_source_ns = 0;
    }

    // If generated, submit and queue the midpoint FIRST. The original real
    // frame is flushed and queued next. Both use existing PresentManager FIFO.
    if (r08_generated) {
        // Preserve interpolated pixels with a LOAD render pass, then add
        // Encore's native HUD. Framebuffer remains valid, no image copy.
        blit_swapchain.DrawHudOverlay(device, r08_synthetic, postprocess_hud);
        present_manager.ConfirmReservedRenderFrame(r08_synthetic);
        const u64 generated_tick = scheduler.Flush(*r08_synthetic->render_ready);
        if (r08_capture.valid) {
            if (mihawk_capture_fences.Commit(
                    r08_capture, generated_tick, mihawk_source_sequence, true)) {
                mihawk_native->Images().MarkInitialized(r08_capture.slot);
                mihawk_native->MarkOutputBlitted();
            } else {
                // The GPU command was submitted but its tick could not be
                // attested. Preserve quarantine: never reuse private images
                // or claim the output can be overwritten by the next frame.
                mihawk_present_gate.Reset();
            }
        }
        present_manager.Present(r08_synthetic);
        ::Eden::FrameMetrics::OnGeneratedQueued();
    }

    // Exactly one method can own synthetic presentation. The original
    // composite always follows any generated frame in PresentManager FIFO.
    if (fsr3_generated) {
        blit_swapchain.DrawHudOverlay(device, fsr3_synthetic, postprocess_hud);
        present_manager.ConfirmReservedRenderFrame(fsr3_synthetic);
        const u64 synthetic_tick = scheduler.Flush(*fsr3_synthetic->render_ready);
        present_manager.Present(fsr3_synthetic);
        ::Eden::FrameMetrics::OnGeneratedQueued();
        // The real frame flush below fences the full command sequence.
        (void)synthetic_tick;
    }

    // HUD is always restored on the true frame, including when no midpoint
    // could be generated; do not deprive the user of diagnostic overlay.
    if (postprocess_hud_required)
        blit_swapchain.DrawHudOverlay(device, frame, postprocess_hud);
    const u64 real_tick = scheduler.Flush(*frame->render_ready);
    if (fsr3_captured) {
        if (real_tick != 0 && real_tick > fsr3_last_capture_tick) {
            fsr3_last_capture_tick = real_tick;
            fsr3_last_capture_id = fsr3_source_sequence;
        } else {
            // The command was submitted but its GPU lifetime is unproven.
            // Quarantine the private history rather than reuse it.
            fsr3_last_capture_tick = std::numeric_limits<u64>::max();
            fsr3_last_capture_id = 0;
            fsr3_present_gate.Reset();
        }
    }
    if (r08_capture.valid && !r08_generated &&
        mihawk_capture_fences.Commit(
            r08_capture, real_tick, mihawk_source_sequence, false)) {
        mihawk_native->Images().MarkInitialized(r08_capture.slot);
    }
    present_manager.Present(frame);
    ::Eden::FrameMetrics::OnRealQueued();
    scheduler.DispatchWork();

    gpu.RendererFrameEndNotify();
    rasterizer.TickFrame();
}

// Runs on the existing GPU worker, before the first guest Composite. Reuse its
// swapchain and composition pass without guest captures or FPS notifications.
void RendererVulkan::PresentLoading() {
    Frame* frame = present_manager.GetRenderFrame();
    scheduler.RequestOutsideRenderPassOperationContext();
    // The OpenGL launcher already showed this same loading_scene.glsl frame.
    // Vulkan starts with its normal output image and draws that shared scene
    // fullscreen; there is no jacket screenshot, bottom-band overlay or
    // second branded loader.
    blit_swapchain.DrawToFrame(device, rasterizer, frame, {},
                              render_window.GetFramebufferLayout(),
                              present_manager.SwapchainImageCount(),
                              present_manager.SwapchainImageViewFormat(), true);
#ifdef PS5_NATIVE
    const Eden::HudSnapshot live_loading = Eden::GetVulkanHud();
    if (live_loading.loading != 0u && live_loading.width != 0u)
        blit_swapchain.DrawHudOverlay(device, frame, live_loading);
#endif
    scheduler.Flush(*frame->render_ready);
    present_manager.Present(frame);
    ::Eden::FrameMetrics::OnLoadingQueued();
}

void RendererVulkan::Report() const {
    using namespace Common::Literals;
    const std::string vendor_name{device.GetVendorName()};
    const std::string model_name{device.GetModelName()};
    const std::string driver_version = GetDriverVersion(device);
    const std::string driver_name = fmt::format("{} {}", vendor_name, driver_version);

    const std::string api_version = GetReadableVersion(device.ApiVersion());

    const std::string extensions = BuildCommaSeparatedExtensions(device.GetAvailableExtensions());

    const auto available_vram = static_cast<f64>(device.GetDeviceLocalMemory()) / f64{1_GiB};

    LOG_INFO(Render_Vulkan, "Driver: {}", driver_name);
    LOG_INFO(Render_Vulkan, "Device: {}", model_name);
    LOG_INFO(Render_Vulkan, "Vulkan: {}", api_version);
    LOG_INFO(Render_Vulkan, "Available VRAM: {:.2f} GiB", available_vram);
}

vk::Buffer RendererVulkan::RenderToBuffer(std::span<const Tegra::FramebufferConfig> framebuffers,
                                          const Layout::FramebufferLayout& layout, VkFormat format,
                                          VkDeviceSize buffer_size) {
    auto frame = [&]() {
        Frame f{};
        f.image =
            CreateWrappedImage(memory_allocator, VkExtent2D{layout.width, layout.height}, format);
        f.image_view = CreateWrappedImageView(device, f.image, format);
        f.framebuffer = blit_capture.CreateFramebuffer(device, layout, *f.image_view, format);
        return f;
    }();

    auto dst_buffer = CreateWrappedBuffer(memory_allocator, buffer_size, MemoryUsage::Download);
    blit_capture.DrawToFrame(device, rasterizer, &frame, framebuffers, layout, 1, format, true);

    scheduler.RequestOutsideRenderPassOperationContext();
    scheduler.Record([&](vk::CommandBuffer cmdbuf) {
        DownloadColorImage(cmdbuf, *frame.image, *dst_buffer,
                           VkExtent3D{layout.width, layout.height, 1});
    });

    // Ensure the copy is fully completed before saving the capture
    scheduler.Finish();

    // Copy backing image data to the capture buffer
    dst_buffer.Invalidate();
    return dst_buffer;
}

void RendererVulkan::RenderScreenshot(std::span<const Tegra::FramebufferConfig> framebuffers) {
    if (!renderer_settings.screenshot_requested) {
        return;
    }

    const auto screenshot_layers = Tegra::FilterLayerStack(
        framebuffers, renderer_settings.screenshot_layer_stack, screenshot_layer_scratch);

    const auto& layout{renderer_settings.screenshot_framebuffer_layout};
    const auto dst_buffer = RenderToBuffer(screenshot_layers, layout, VK_FORMAT_B8G8R8A8_UNORM,
                                           layout.width * layout.height * 4);

    std::memcpy(renderer_settings.screenshot_bits, dst_buffer.Mapped().data(),
                dst_buffer.Mapped().size());
    renderer_settings.screenshot_complete_callback(false);
    renderer_settings.screenshot_requested = false;
}

std::vector<u8> RendererVulkan::GetAppletCaptureBuffer() {
    using namespace VideoCore::Capture;

    std::vector<u8> out(VideoCore::Capture::TiledSize);

    if (!applet_frame.image) {
        return out;
    }

    const auto dst_buffer =
        CreateWrappedBuffer(memory_allocator, VideoCore::Capture::TiledSize, MemoryUsage::Download);

    scheduler.RequestOutsideRenderPassOperationContext();
    scheduler.Record([&](vk::CommandBuffer cmdbuf) {
        DownloadColorImage(cmdbuf, *applet_frame.image, *dst_buffer, CaptureImageExtent);
    });

    // Ensure the copy is fully completed before writing the capture
    scheduler.Finish();

    // Swizzle image data to the capture buffer
    dst_buffer.Invalidate();
    Tegra::Texture::SwizzleTexture(out, dst_buffer.Mapped(), BytesPerPixel, LinearWidth,
                                   LinearHeight, LinearDepth, BlockHeight, BlockDepth);

    return out;
}

void RendererVulkan::RenderAppletCaptureLayer(
    std::span<const Tegra::FramebufferConfig> framebuffers) {
    const auto capture_layers = Tegra::FilterLayerStack(
        framebuffers, Service::Nvnflinger::LayerStackId::LastFrame, applet_capture_layers);

    if (capture_layers.empty())
        return;

    if (!applet_frame.image) {
        applet_frame.image = CreateWrappedImage(memory_allocator, CaptureImageSize, CaptureFormat);
        applet_frame.image_view = CreateWrappedImageView(device, applet_frame.image, CaptureFormat);
        applet_frame.framebuffer = blit_applet.CreateFramebuffer(device,
            VideoCore::Capture::Layout, *applet_frame.image_view, CaptureFormat);
    }

    scheduler.RequestOutsideRenderPassOperationContext();
    blit_applet.DrawToFrame(device, rasterizer, &applet_frame, capture_layers, VideoCore::Capture::Layout, 1,
                            CaptureFormat);
}

} // namespace Vulkan
namespace Eden {
void PresentVulkanLoading(VideoCore::RendererBase& renderer) {
    static_cast<Vulkan::RendererVulkan&>(renderer).PresentLoading();
}
}
