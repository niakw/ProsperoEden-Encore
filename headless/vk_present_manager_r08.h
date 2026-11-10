// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// SPDX-FileCopyrightText: Copyright 2023 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <atomic>
#include <condition_variable>
#include <mutex>
#include <exception>
#include <boost/container/deque.hpp>

#include "common/common_types.h"
#include "common/polyfill_thread.h"
#include "video_core/vulkan_common/vulkan_memory_allocator.h"
#include "video_core/vulkan_common/vulkan_wrapper.h"

namespace Core::Frontend {
class EmuWindow;
} // namespace Core::Frontend

namespace Vulkan {

class Device;
class Scheduler;
class Swapchain;

struct Frame {
    u32 width;
    u32 height;
    u32 index;
    vk::Image image;
    vk::ImageView image_view;
    vk::ImageView storage_view;
    vk::Framebuffer framebuffer;
    vk::CommandBuffer cmdbuf;
    vk::Semaphore render_ready;
    vk::Fence present_done;
};

class PresentManager {
public:
    PresentManager(const vk::Instance& instance,
                   Core::Frontend::EmuWindow& render_window,
                   const Device& device,
                   MemoryAllocator& memory_allocator,
                   Scheduler& scheduler,
                   Swapchain& swapchain,
                   vk::SurfaceKHR& surface);
    ~PresentManager();

    /// Returns the last used presentation frame
    Frame* GetRenderFrame();

    // Synthetic frames must never stall real game presentation. A reserved
    // frame is NOT fence-reset until ConfirmReservedRenderFrame. If generation
    // is ineligible, CancelReservedRenderFrame returns it untouched to FIFO.
    Frame* TryReserveRenderFrame() {
        std::scoped_lock lock{free_mutex};
        if (present_failure || free_queue.empty()) return nullptr;
        // The oldest recycled buffer may still have its GPU fence pending
        // while a later buffer is already ready. Scan at most 8 slots
        // instead of stalling the real game or missing a usable resource.
        for (auto it = free_queue.begin(); it != free_queue.end(); ++it) {
            Frame* frame = *it;
            if (frame->present_done.GetStatus() != VK_SUCCESS) continue;
            free_queue.erase(it);
            return frame;
        }
        return nullptr;
    }

    void CancelReservedRenderFrame(Frame* frame) {
        if (!frame) return;
        {
            std::scoped_lock lock{free_mutex};
            free_queue.push_front(frame);
        }
        free_cv.notify_one();
    }

    void ConfirmReservedRenderFrame(Frame* frame) {
        if (frame) frame->present_done.Reset();
    }

    /// Pushes a frame for presentation
    void Present(Frame* frame);

    /// Recreates the present frame to match the provided parameters
    void RecreateFrame(Frame* frame, u32 width, u32 height, VkFormat image_view_format,
                       VkRenderPass rd);

    /// Waits for the present thread to finish presenting all queued frames.
    void WaitPresent();

    /// How many additional frames can be queued without stalling the render thread
    [[nodiscard]] size_t MaxExtraFrames() const;
    [[nodiscard]] std::size_t SwapchainImageCount() const { return swapchain_image_count.load(); }
    [[nodiscard]] VkFormat SwapchainImageFormat() const { return swapchain_image_format.load(); }
    [[nodiscard]] VkFormat SwapchainImageViewFormat() const { return swapchain_image_view_format.load(); }

private:
    void PresentThread(std::stop_token token);

    void CopyToSwapchain(Frame* frame);

    void CopyToSwapchainImpl(Frame* frame);

    void RecreateSwapchain(Frame* frame);

    void DiscardFrame(Frame* frame);

    void SetImageCount();

private:
    const vk::Instance& instance;
    Core::Frontend::EmuWindow& render_window;
    const Device& device;
    MemoryAllocator& memory_allocator;
    Scheduler& scheduler;
    Swapchain& swapchain;
    vk::SurfaceKHR& surface;
    vk::CommandPool cmdpool;
    std::vector<Frame> frames;
    boost::container::deque<Frame*> present_queue;
    boost::container::deque<Frame*> free_queue;
    // Independent wakeups for the worker and WaitPresent consumers.
    // Keep the complete maintained synchronization owner layout.
    std::condition_variable_any frame_cv;
    std::condition_variable_any present_ready_cv;
    std::condition_variable free_cv;
    std::mutex swapchain_mutex;
    std::mutex queue_mutex;
    std::mutex free_mutex;
    std::size_t free_waiters{}; // guarded by free_mutex
    bool present_in_flight{}; // guarded by queue_mutex
    std::size_t present_waiters{}; // drain waiters, guarded by queue_mutex
    std::exception_ptr present_failure;
    std::jthread present_thread;
    bool blit_supported;
    bool storage_supported;
    bool use_present_thread;
    std::atomic<std::size_t> image_count{};
    std::atomic<std::size_t> swapchain_image_count{};
    std::atomic<VkFormat> swapchain_image_format{};
    std::atomic<VkFormat> swapchain_image_view_format{};
};

} // namespace Vulkan
