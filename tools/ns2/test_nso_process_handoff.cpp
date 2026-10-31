// SPDX-License-Identifier: GPL-3.0-or-later
// Host-check the *same* N3u readback helper the NS2 KProcess loader calls.
// These memory callbacks are synthetic, not a real KProcess or a PS5 launch.
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>
#include "core/loader/ns2_process_handoff.h"
#include "core/loader/ns2_main_thread_admission.h"

using namespace Eden::NS2::ExeFS;
using Header = std::array<std::uint8_t, NsoHeaderBytes>;
static void Put(Header& h, std::size_t p, std::uint32_t n) {
    for (int i = 0; i < 4; ++i) h[p + i] = static_cast<std::uint8_t>(n >> (8 * i));
}
int main() {
    constexpr auto main_priority = std::uint64_t{1} << 44;
    static_assert(MainThreadPermitted(1, main_priority, 0, 44));
    static_assert(!MainThreadPermitted(0, main_priority, 0, 44));
    static_assert(!MainThreadPermitted(1, 0, 0, 44));
    static_assert(!MainThreadPermitted(2, main_priority, 0, 44));
    static_assert(!MainThreadPermitted(1, main_priority, 0, 43));
    static_assert(!MainThreadPermitted(~std::uint64_t{0},
                                       ~std::uint64_t{0}, 64, 44));
    static_assert(!MainThreadPermitted(~std::uint64_t{0},
                                       ~std::uint64_t{0}, 0, 64));
    Header h{};
    Put(h, 0x00, 0x304f534e);
    Put(h, 0x10, 0x100); Put(h, 0x14, 0); Put(h, 0x18, 16); Put(h, 0x60, 16);
    Put(h, 0x20, 0x110); Put(h, 0x24, 0x1000); Put(h, 0x28, 8); Put(h, 0x64, 8);
    Put(h, 0x30, 0x118); Put(h, 0x34, 0x2000); Put(h, 0x38, 8); Put(h, 0x68, 8);
    Put(h, 0x3c, 0x100);
    constexpr std::uint64_t base = 0x80000000;
    std::vector<std::uint8_t> file(0x120);
    for (std::size_t i = 0; i < 16; ++i)
        file[0x100 + i] = static_cast<std::uint8_t>(0xD0 + i);
    std::vector<std::uint8_t> memory(0x2108);
    std::memcpy(memory.data(), file.data() + 0x100, 16);
    auto read_file = [&](std::uint64_t off, std::uint8_t* out, std::size_t n) {
        if (off > file.size() || n > file.size() - off) return std::size_t{0};
        std::memcpy(out, file.data() + off, n);
        return n;
    };
    auto read_guest = [&](std::uint64_t addr, std::uint8_t* out, std::size_t n) {
        if (addr < base || addr - base > memory.size() ||
            n > memory.size() - (addr - base)) return false;
        std::memcpy(out, memory.data() + (addr - base), n);
        return true;
    };
    const auto check = [&](const Header& header) {
        return VerifyUncompressedTextHandoff(header, file.size(), base,
                                             read_file, read_guest);
    };
    assert(check(h) == TextHandoffStatus::Verified);
    memory[0] ^= 1;
    assert(check(h) == TextHandoffStatus::Mismatch);
    memory[0] ^= 1;
    const auto no_file = [](std::uint64_t, std::uint8_t*, std::size_t) {
        return std::size_t{0};
    };
    const auto no_guest = [](std::uint64_t, std::uint8_t*, std::size_t) {
        return false;
    };
    assert(VerifyUncompressedTextHandoff(h, file.size(), base, no_file, read_guest)
           == TextHandoffStatus::FileReadFailed);
    assert(VerifyUncompressedTextHandoff(h, file.size(), base, read_file, no_guest)
           == TextHandoffStatus::GuestReadFailed);
    auto corrupt = h;
    Put(corrupt, 0, 0);
    assert(check(corrupt) == TextHandoffStatus::InvalidHeader);
    auto compressed = h;
    Put(compressed, 0x0c, 1); Put(compressed, 0x60, 8);
    assert(check(compressed) == TextHandoffStatus::SkippedCompressed);
    auto empty = h;
    Put(empty, 0x18, 0); Put(empty, 0x60, 0);
    assert(check(empty) == TextHandoffStatus::SkippedEmptyText);
    assert(VerifyUncompressedTextHandoff(
               h, file.size(), std::numeric_limits<std::uint64_t>::max(),
               read_file, read_guest) == TextHandoffStatus::InvalidGuestAddress);
}
