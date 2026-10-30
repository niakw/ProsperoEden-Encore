// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Eight-way thread-local positive alias memo: no mutex on an existing RX/RW
// pair, even when the PS5 virtual arenas share the same low address bits.
// This is only a lookup hint; the allocator owns and validates every mapping.
#include <array>
#include <cstddef>
#include <cstdint>

namespace Eden::Jit {
class AliasPositiveCache {
    struct Entry {
        std::uint8_t* executable{};
        std::uint8_t* writable{};
    };
    std::array<Entry, 8> entries{};
    std::uint64_t generation{};
    std::size_t next_slot{};
public:
    std::uint8_t* Find(std::uint8_t* executable,
                       std::uint64_t current_generation) const noexcept {
        if (generation != current_generation) return nullptr;
        for (const Entry& entry : entries) {
            if (entry.executable == executable) return entry.writable;
        }
        return nullptr;
    }

    void Remember(std::uint8_t* executable, std::uint8_t* writable,
                  std::uint64_t current_generation) noexcept {
        if (generation != current_generation) {
            entries = {};
            generation = current_generation;
            next_slot = 0;
        }
        entries[next_slot] = {executable, writable};
        next_slot = (next_slot + 1) % entries.size();
    }
};
} // namespace Eden::Jit
