// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// One temporary, title-scoped frame linking the native OpenGL jacket
// animation to the PS5 Vulkan warm-up. No disk I/O and no guest GPU state.
#include "loading_case.hpp"
#include <atomic>
#include <chrono>
#include <cstdint>
#include <limits>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

namespace Eden::LaunchHandoff {

struct Frame {
    std::uint32_t width{};
    std::uint32_t height{};
    // Top-to-bottom, tightly packed RGBA8; Vulkan converts to output format.
    std::vector<std::uint8_t> rgba;
};

// One-shot destination; never starts guest-thread networking or another compositor.
inline std::atomic<bool> multiplayer_requested{false};
inline void QueueMultiplayer() { multiplayer_requested.store(true, std::memory_order_release); }
inline bool TakeMultiplayerRequest() { return multiplayer_requested.exchange(false, std::memory_order_acq_rel); }
inline std::mutex frame_mutex;
inline std::shared_ptr<const Frame> pending_frame;
// The second frame is the flat paper atlas, not a projected jacket.
inline std::shared_ptr<const Frame> alternate_frame;
inline std::shared_ptr<const LoadingCase::Scene> case_scene;
inline void PublishCase(LoadingCase::Scene&& scene) {
    if(!LoadingCase::Valid(scene))return;
    auto stored=std::make_shared<LoadingCase::Scene>(std::move(scene));
    const std::lock_guard lock{frame_mutex};
    case_scene=std::move(stored);
}
inline std::shared_ptr<const LoadingCase::Scene> PeekCase() {
    const std::lock_guard lock{frame_mutex};
    return case_scene;
}

// One monotonic loading epoch spans launcher GL, the retained GL presenter and
// Vulkan. Each backend asks for the current shader time instead of resetting
// to t=1 when ownership changes.
inline std::atomic<std::int64_t> loading_started_ns{0};
inline std::int64_t MonotonicNs() noexcept {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline void BeginLoading() noexcept {
    loading_started_ns.store(MonotonicNs(), std::memory_order_release);
}
inline void EndLoading() noexcept {
    loading_started_ns.store(0, std::memory_order_release);
}
inline double LoadingSeconds(double calm_offset = 0.0) noexcept {
    const auto started = loading_started_ns.load(std::memory_order_acquire);
    const auto now = MonotonicNs();
    const double elapsed = started > 0 && now > started
        ? static_cast<double>(now - started) / 1'000'000'000.0
        : 0.0;
    return 1.0 + calm_offset + elapsed;
}

// Bounded by the largest normal 4K console output. Reject anything that
// could overflow the byte count or require an unbounded image allocation.
inline bool Valid(const Frame& frame) {
    constexpr std::uint32_t max_width = 4096;
    constexpr std::uint32_t max_height = 2160;
    return frame.width > 0 && frame.height > 0 &&
           frame.width <= max_width && frame.height <= max_height &&
           frame.rgba.size() == static_cast<std::size_t>(frame.width) *
                                    static_cast<std::size_t>(frame.height) * 4;
}
inline void Publish(Frame&& frame, bool alternate = false) {
    if (!Valid(frame)) return;
    auto stored = std::make_shared<Frame>(std::move(frame));
    const std::lock_guard lock{frame_mutex};
    if (alternate)
        alternate_frame = std::move(stored);
    else
        pending_frame = std::move(stored);
}
// Renderer may inspect pending pixels while the swapchain has zero extent
// or while a transient staging allocation fails. The owner stays available
// until successful Vulkan upload; a failed warm-up must never eat the jacket.
inline std::shared_ptr<const Frame> Peek() {
    const std::lock_guard lock{frame_mutex};
    return pending_frame;
}
inline std::shared_ptr<const Frame> PeekAlternate() {
    const std::lock_guard lock{frame_mutex};
    return alternate_frame;
}
inline void ClearAlternate() {
    const std::lock_guard lock{frame_mutex};
    alternate_frame.reset();
    case_scene.reset();
}
inline std::shared_ptr<const Frame> Take() {
    const std::lock_guard lock{frame_mutex};
    alternate_frame.reset();
    case_scene.reset();
    return std::exchange(pending_frame, {});
}
inline void Clear() {
    const std::lock_guard lock{frame_mutex};
    pending_frame.reset();
    alternate_frame.reset();
    case_scene.reset();
}
} // namespace Eden::LaunchHandoff
