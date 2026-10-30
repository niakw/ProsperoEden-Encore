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
constexpr int count_ldapr(std::uint32_t instruction) {
    int count = 0;
    for (const auto& entry : table)
        if (entry.mnemonic=="LDAPR" && match(instruction, entry.bits))
            ++count;
    return count;
}

constexpr std::uint32_t base_of(std::string_view name) {
    for (auto entry : table) {
        if (entry.mnemonic != name) continue;
        std::uint32_t code = 0;
        for (char b : entry.bits) code = (code << 1) | (b == '1' ? 1u : 0u);
        return code;
    }
    return 0;
}
constexpr int count_named(std::uint32_t instruction, std::string_view name) {
    int count = 0;
    for (const auto& entry : table)
        if (entry.mnemonic==name && match(instruction, entry.bits))
            ++count;
    return count;
}
static_assert(count_named(base_of("CAS"), "CAS") == 1);
static_assert(count_named(base_of("LDADD"), "LDADD") == 1);
static_assert(count_named(base_of("LDCLR"), "LDCLR") == 1);
static_assert(count_named(base_of("LDEOR"), "LDEOR") == 1);
static_assert(count_named(base_of("LDSET"), "LDSET") == 1);
static_assert(count_named(base_of("SWP"), "SWP") == 1);
static_assert(count_named(base_of("SWPB"), "SWPB") == 1);
static_assert(count_named(base_of("SWPH"), "SWPH") == 1);
static_assert(count_named(0xD65F0BFF, "CAS") == 0);
static_assert(count_ldapr(0xB8BFC000) == 1); // LDAPR W0,[X0]
static_assert(count_ldapr(0xF8BFC000) == 1); // LDAPR X0,[X0]
static_assert(count_ldapr(0x38BFC000) == 1); // LDAPRB W0,[X0]
static_assert(count_ldapr(0xD65F0BFF) == 0); // RETAA is not LDAPR
static_assert(count_ldapr(0xFFFFFFFF) == 0);
static_assert(count_reta(0xD65F0BFF) == 1); // RETAA
static_assert(count_reta(0xD65F0FFF) == 1); // RETAB
static_assert(count_reta(0xD65F03C0) == 0); // RET X30
static_assert(is_regular_ret(0xD65F03C0));
static_assert(!is_regular_ret(0xD65F0BFF));
static_assert(!is_regular_ret(0xD65F0FFF));
static_assert(count_reta(0xFFFFFFFF) == 0);
int main() {
    assert(count_ldapr(0xB8BFC000) == 1);
    assert(count_ldapr(0xF8BFC000) == 1);
    assert(count_reta(0xD65F0BFF) == 1);
    assert(count_reta(0xD65F0FFF) == 1);
    assert(is_regular_ret(0xD65F03C0));
}
