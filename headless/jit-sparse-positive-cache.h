// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Thread-local, positive-only hints for PS5 sparse JIT physical commitments.
// This cache never owns an RX/RW mapping; reservation/trim/release bump the
// global generation and a miss must validate ownership under sparse_jit_mutex.
#include <array>
#include <cstddef>
#include <cstdint>

namespace Eden::Jit {
class SparseCommitPositiveCache {
    struct Entry {
        void* executable{};
        std::size_t committed{};
    };
    std::array<Entry, 4> entries{};
    std::uint64_t generation{};

public:
    bool Covers(void* executable, std::size_t required, std::uint64_t current) noexcept {
        if (generation != current) return false;
        for (std::size_t i = 0; i < entries.size(); ++i) {
            if (entries[i].executable != executable || required > entries[i].committed)
                continue;
            // The usual same-core hit does not move anything; a core switch
            // promotes its entry so subsequent guest blocks cost one compare.
            const Entry hit = entries[i];
            for (std::size_t j = i; j > 0; --j) entries[j] = entries[j - 1];
            entries[0] = hit;
            return true;
        }
        return false;
    }

    void Remember(void* executable, std::size_t committed, std::uint64_t current) noexcept {
        if (generation != current) {
            entries = {};
            generation = current;
        }
        std::size_t i = 0;
        while (i < entries.size() && entries[i].executable != executable) ++i;
        if (i == entries.size()) i = entries.size() - 1;
        for (; i > 0; --i) entries[i] = entries[i - 1];
        entries[0] = {executable, committed};
    }
};
} // namespace Eden::Jit
