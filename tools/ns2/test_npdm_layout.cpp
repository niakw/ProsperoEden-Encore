// SPDX-License-Identifier: GPL-3.0-or-later
// Standalone host test of the exact helper included by the experimental NPDM reader.
#include <cassert>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>
#include "npdm_layout.h"

int main() {
    using Eden::NS2::ContainsRange;
    using Eden::NS2::FindAcidBody;
    constexpr std::uint64_t max = std::numeric_limits<std::uint64_t>::max();
    static_assert(ContainsRange(0, 0, 0));
    static_assert(ContainsRange(10, 5, 15));
    static_assert(!ContainsRange(11, 5, 15));
    static_assert(!ContainsRange(max, 2, max));
    static_assert(!ContainsRange(max - 1, 4, max));

    std::vector<char> blob(0x900, 0);
    const auto put_magic = [&](std::size_t offset) {
        std::memcpy(blob.data() + offset, "ACID", 4);
    };
    const auto valid = [&](std::uint64_t position) {
        return ContainsRange(position, 0x40, blob.size()) &&
               std::memcmp(blob.data() + position, "ACID", 4) == 0;
    };
    const auto locate = [&](std::uint64_t offset, std::uint64_t length) {
        return FindAcidBody(offset, length, blob.size(), 0x40, valid);
    };

    assert(!locate(0x80, 0x400)); // no magic: never claim Switch 2
    put_magic(0x100 + 0x200);
    auto legacy = locate(0x100, 0x400);
    assert(legacy && legacy->absolute_offset == 0x300 && !legacy->extended);
    put_magic(0x100 + 0x300);
    legacy = locate(0x100, 0x400);
    assert(legacy && !legacy->extended); // ambiguity: preserve Switch 1
    std::memset(blob.data() + 0x300, 0, 4);
    auto extended = locate(0x100, 0x400);
    assert(extended && extended->absolute_offset == 0x400 && extended->extended);
    assert(!locate(0x100, 0x33F)); // truncated extended body
    assert(!locate(0x100, 0x300)); // no complete extended header
    assert(!locate(0x80, max)); // overflow-safe range rejection
    assert(!locate(max, 0x400)); // overflow-safe base rejection
    assert(!locate(0x7F, 0x401)); // NPDM header overlap
    assert(!locate(0x800, 0x400)); // end past file
    assert(!FindAcidBody(0x100, 0x400, blob.size(), 0x40,
                         [](std::uint64_t) { return false; }));
}
