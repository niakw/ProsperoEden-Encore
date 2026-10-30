// SPDX-License-Identifier: GPL-3.0-or-later
// Decode the actual research a64.inc table; no mocked instruction patterns.
#include <array>
#include <cassert>
#include <cstdint>
#include <string_view>

struct Entry { std::string_view mnemonic; std::string_view bits; };
constexpr Entry table[]{
#define INST(method, description, pattern) Entry{#method, pattern},
#include "dynarmic/frontend/A64/decoder/a64.inc"
#undef INST
};

constexpr bool match(std::uint32_t instruction, std::string_view pattern) {
    if (pattern.size() != 32) return false;
    for (unsigned i=0; i<32; ++i) {
        const char bit=pattern[i];
        if ((bit=='0'||bit=='1') && ((instruction >> (31-i)) & 1U) != (bit-'0'))
            return false;
    }
    return true;
}

constexpr int count_reta(std::uint32_t instruction) {
    int count = 0;
    for (const auto& entry : table)
        if (entry.mnemonic=="RETA" && match(instruction, entry.bits))
            ++count;
    return count;
}
constexpr bool is_regular_ret(std::uint32_t instruction) {
    for (const auto& entry : table)
        if (entry.mnemonic=="RET" && match(instruction, entry.bits))
            return true;
    return false;
}
static_assert(count_reta(0xD65F0BFF) == 1); // RETAA
static_assert(count_reta(0xD65F0FFF) == 1); // RETAB
static_assert(count_reta(0xD65F03C0) == 0); // RET X30
static_assert(is_regular_ret(0xD65F03C0));
static_assert(!is_regular_ret(0xD65F0BFF));
static_assert(!is_regular_ret(0xD65F0FFF));
static_assert(count_reta(0xFFFFFFFF) == 0);
int main() {
    assert(count_reta(0xD65F0BFF) == 1);
    assert(count_reta(0xD65F0FFF) == 1);
    assert(is_regular_ret(0xD65F03C0));
}
