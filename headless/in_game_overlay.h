// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// PS5 quick menu: the input worker publishes a bounded immutable menu frame.
// Vulkan reads it only while visible; closed gameplay takes one atomic branch.
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <mutex>
#include <string_view>
#include <utility>
#include "hud.h"
#include "in_game_overlay_style.h"

namespace Eden::QuickOverlay {
enum Action : std::uint32_t {
    none = 0, up = 1u << 0, down = 1u << 1,
    left = 1u << 2, right = 1u << 3,
    select = 1u << 4, back = 1u << 5,
    previous_tab = 1u << 6, next_tab = 1u << 7,
};
inline constexpr std::size_t kMaxRows = 14;
// The native quick-menu input model must retain text independently of the
// legacy 3x5 HUD transport. Fixed storage keeps publication bounded and
// allocation-free. Labels are valid UTF-8 from menu/translation sources;
// if a future label exceeds the capacity, do not split a codepoint.
struct MenuText {
    static constexpr std::size_t kCapacity = 96;
    std::array<char, kCapacity> bytes{};
    std::uint8_t length{};
    bool truncated{};

    void Assign(std::string_view value) noexcept {
        std::size_t n = std::min(value.size(), bytes.size());
        if (n < value.size()) {
            while (n > 0 && (static_cast<unsigned char>(value[n]) & 0xc0u) == 0x80u)
                --n;
        }
        if (n != 0) std::copy_n(value.data(), n, bytes.data());
        length = static_cast<std::uint8_t>(n);
        truncated = n != value.size();
    }
    std::string_view View() const noexcept { return {bytes.data(), length}; }
};

struct Frame {
    std::array<HudSnapshot, kMaxRows> rows{};
    // Same row index and publication lifetime as the existing HUD fallback.
    std::array<MenuText, kMaxRows> text{};
    std::uint32_t count{};
    bool visible{};
    std::uint32_t style{}; // immutable frame appearance; no GPU preferences I/O
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
