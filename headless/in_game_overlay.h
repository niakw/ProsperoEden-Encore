// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// PS5 quick menu: the input worker publishes a small immutable glyph frame.
// Vulkan reads it only while visible; closed gameplay takes one atomic branch.
#include <array>
#include <atomic>
#include <cstdint>
#include <mutex>
#include <utility>
#include "hud.h"

namespace Eden::QuickOverlay {
enum Action : std::uint32_t {
    none = 0, up = 1u << 0, down = 1u << 1,
    left = 1u << 2, right = 1u << 3,
    select = 1u << 4, back = 1u << 5,
    previous_tab = 1u << 6, next_tab = 1u << 7,
};
inline constexpr std::uint32_t kBackdrop = 0xfffffff1u;
inline constexpr std::uint32_t kRow = 0xfffffff2u;
inline constexpr std::uint32_t kSelectedRow = 0xfffffff3u;
inline constexpr std::uint32_t kWarningRow = 0xfffffff4u;
inline constexpr std::size_t kMaxRows = 14;
struct Frame {
    std::array<HudSnapshot, kMaxRows> rows{};
    std::uint32_t count{};
    bool visible{};
};
inline std::mutex frame_mutex;
inline Frame published_frame{};
inline std::atomic<bool> frame_visible{false};

inline void Publish(const Frame& next) {
    std::lock_guard lock(frame_mutex);
    published_frame = next;
    frame_visible.store(next.visible, std::memory_order_release);
}
inline Frame Snapshot() {
    if (!frame_visible.load(std::memory_order_acquire)) return {};
    std::lock_guard lock(frame_mutex);
    return published_frame;
}
inline void Reset() {
    Publish(Frame{});
}
} // namespace Eden::QuickOverlay
