// SPDX-License-Identifier: GPL-3.0-or-later
// Exercise the exact source-bound N3q NSO0 admission function used by ExeFS.
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>
#include "core/loader/ns2_nso_preflight.h"

using namespace Eden::NS2::ExeFS;
using Header = std::array<std::uint8_t, NsoHeaderBytes>;

static constexpr void Put(Header& h, std::size_t offset, std::uint32_t value) {
    for (std::size_t i = 0; i < 4; ++i)
        h[offset + i] = static_cast<std::uint8_t>(value >> (8 * i));
}
static constexpr Header Fixture() {
    Header h{};
    Put(h, 0x00, 0x304f534e); // 'NSO0'
    Put(h, 0x04, 0);
    Put(h, 0x0c, 0);
    // text, rodata, data; regions padded independently in guest memory.
    for (std::uint32_t i = 0; i < 3; ++i) {
        Put(h, 0x10 + 0x10 * i, 0x100 + 0x80 * i);
        Put(h, 0x14 + 0x10 * i, 0x1000 * i);
        Put(h, 0x18 + 0x10 * i, 0x80);
        Put(h, 0x60 + 0x04 * i, 0x80);
    }
    Put(h, 0x3c, 0x100);
    return h;
}
static void Reject(const Header& h, std::uint64_t length, NsoPreflightStatus expected) {
    const auto v = PreflightNso(h, length);
    if (v.status != expected) {
        std::fprintf(stderr, "Expected NSO rejection %d, got %d\n",
                     static_cast<int>(expected), static_cast<int>(v.status));
        std::abort();
    }
}
int main(int argc, char** argv) {
    static_assert(NsoHeaderBytes == 0x100);
    constexpr auto base = Fixture();
    constexpr auto valid = PreflightNso(base, 0x280);
    static_assert(valid.Ready() && valid.image_bytes == 0x2180);
    Reject(base, 0xff, NsoPreflightStatus::TruncatedHeader);
    Reject(base, 0x100, NsoPreflightStatus::InvalidFileRange);

    auto h = base;
    Put(h, 0, 0x304f534d);
    Reject(h, 0x280, NsoPreflightStatus::InvalidMagic);
    h = base; Put(h, 4, 1);
    Reject(h, 0x280, NsoPreflightStatus::UnsupportedVersion);
    h = base; Put(h, 0x0c, 0x80000000);
    Reject(h, 0x280, NsoPreflightStatus::InvalidFlags);
    h = base; Put(h, 0x0c, 0x40);
    Reject(h, 0x280, NsoPreflightStatus::InvalidFlags);
    h = base; Put(h, 0x0c, 0x80);
    Reject(h, 0x280, NsoPreflightStatus::InvalidFlags);
    h = base; Put(h, 0x0c, 0x81); Put(h, 0x60, 0x40);
    assert(PreflightNso(h, 0x280).Ready()); // ZBIC + compressed text
    h = base; Put(h, 0x18, 0x20000000);
    Reject(h, 0x280, NsoPreflightStatus::InvalidSegment);
    h = base; Put(h, 0x60, 0x10);
    Reject(h, 0x280, NsoPreflightStatus::InvalidSegment);
    h = base; Put(h, 0x10, 0xFFFFFFF0);
    Reject(h, 0x280, NsoPreflightStatus::InvalidFileRange);
    h = base; Put(h, 0x20, 0x240);
    Reject(h, 0x280, NsoPreflightStatus::InvalidFileRange);
    h = base; Put(h, 0x24, 0x10);
    Reject(h, 0x280, NsoPreflightStatus::InvalidImageLayout);
    h = base; Put(h, 0x34, 0xFFFFFFFF);
    Reject(h, 0x280, NsoPreflightStatus::InvalidImageLayout);
    h = base; Put(h, 0x3c, 0xFFFFFFFF);
    Reject(h, 0x280, NsoPreflightStatus::InvalidImageLayout);
    // An empty data segment is a valid homebrew case; do not silently
    // reject legitimate NSO modules that contain only executable code.
    h = base; Put(h, 0x38, 0); Put(h, 0x68, 0);
    assert(PreflightNso(h, 0x200).Ready());
    h = base; Put(h, 0x0c, 1); Put(h, 0x60, 0x40);
    assert(PreflightNso(h, 0x280).Ready()); // compact LZ4 bytes; decode is later
    h = base; Put(h, 0x0c, 1); Put(h, 0x60, 0);
    Reject(h, 0x280, NsoPreflightStatus::InvalidSegment);
    h = base; Put(h, 0x18, 0); Put(h, 0x60, 4);
    Reject(h, 0x280, NsoPreflightStatus::InvalidSegment);
    std::puts("NS2 ExeFS NSO0 bounds preflight: PASS (valid, empty, compressed, malformed)");
    if (argc == 2) {
        std::ifstream file(argv[1], std::ios::binary);
        assert(file);
        Header bytes{};
        file.read(reinterpret_cast<char*>(bytes.data()), bytes.size());
        assert(file.gcount() == static_cast<std::streamsize>(bytes.size()));
        file.seekg(0, std::ios::end);
        const auto size = file.tellg();
        assert(size >= 0);
        const auto result = PreflightNso(bytes, static_cast<std::uint64_t>(size));
        assert(result.Ready());
        assert(NsoWord(bytes, 0) == 0x304f534e);
        std::printf("NS2 independent cross-built HOS NSO0: PASS (file=%lld, image=%llu)\n",
                    static_cast<long long>(size),
                    static_cast<unsigned long long>(result.image_bytes));
    } else assert(argc == 1);
}
