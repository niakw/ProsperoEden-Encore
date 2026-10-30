// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R433: monotonic page occupancy for PS5 Vulkan texture-cache lock elision.
// A positive bit only means an image has EVER occupied this CPU address; no
// unregister clears it. This is conservative, including between game launches.
#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
namespace Eden::ImagePages {
inline constexpr unsigned kPageBits = 12; // Core::DEVICE_PAGEBITS
inline constexpr std::uint64_t kSpace = std::uint64_t{1} << 34;
inline constexpr std::size_t kWords = static_cast<std::size_t>(kSpace >> kPageBits) / 64;
inline std::array<std::atomic<std::uint64_t>, kWords> held{};
constexpr std::uint64_t Bits(unsigned first, unsigned last) noexcept {
    return (~std::uint64_t{0} >> (63 - last)) & (~std::uint64_t{0} << first);
}
// Publish the page BEFORE it is inserted into the registered image slot map.
inline void Mark(std::uint64_t address, std::uint64_t size) noexcept {
    if (size == 0 || address >= kSpace) return;
    // Registering a single 4 KiB page is common for small texture
    // views. Avoid general range masks and the per-word loop, while keeping
    // release publication for concurrent reader lock-elision probes.
    constexpr std::uint64_t page_mask = (std::uint64_t{1} << kPageBits) - 1;
    if (size <= (std::uint64_t{1} << kPageBits) - (address & page_mask)) {
        const auto page = address >> kPageBits;
        const auto word = page / 64;
        const auto bit = std::uint64_t{1} << (page % 64);
        if (!(held[word].load(std::memory_order_relaxed) & bit))
            held[word].fetch_or(bit, std::memory_order_release);
        return;
    }
    const auto first = address >> kPageBits;
    const auto last = ((std::min)(size, kSpace - address) + address - 1) >> kPageBits;
    for (auto word = first / 64; word <= last / 64; ++word) {
        const auto bits = Bits(word == first / 64 ? first % 64 : 0,
                               word == last / 64 ? last % 64 : 63);
        if ((held[word].load(std::memory_order_relaxed) & bits) != bits)
            held[word].fetch_or(bits, std::memory_order_release);
    }
}
// Return true ONLY when it is safe to skip the cache lock. Large and invalid
// queries use the unchanged blocking path; cap bitmap scanning on guest calls.
inline bool NeverHeld(std::uint64_t address, std::uint64_t size) noexcept {
    if (size == 0) size = 1;
    if (address >= kSpace || size > kSpace - address) return false;
    if (size > 256 * 1024) return false;
    // Most CPU writes are contained in a single 4 KiB page. One acquire
    // load and a single bit test replace construction of a two-endpoint
    // word mask. The larger/unaligned cross-page path stays unchanged.
    constexpr std::uint64_t page_mask = (std::uint64_t{1} << kPageBits) - 1;
    if (size <= (std::uint64_t{1} << kPageBits) - (address & page_mask)) {
        const auto page = address >> kPageBits;
        return !(held[page / 64].load(std::memory_order_acquire) &
                 (std::uint64_t{1} << (page % 64)));
    }
    const auto first = address >> kPageBits;
    const auto last = (address + size - 1) >> kPageBits;
    // The 256 KiB cap covers at most 65 pages and two bitmap words.
    const auto first_word = first / 64;
    const auto last_word = last / 64;
    const auto first_bits = Bits(first % 64, first_word == last_word ? last % 64 : 63);
    if (held[first_word].load(std::memory_order_acquire) & first_bits) return false;
    return first_word == last_word ||
           !(held[last_word].load(std::memory_order_acquire) & Bits(0, last % 64));
}
} // namespace Eden::ImagePages
