#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile the active Maxwell B0B5 pitch-remap C++ with a mocked GPU memory.

This tests hardware component selectors, row-unit widths, overlap snapshots,
NO_WRITE and rejected invalid spans. No game-specific behavior or console claim.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "vendor/encore-active/eden-core/src/video_core/engines/maxwell_dma.cpp").read_text()
cmake = (root / "headless/CMakeLists.txt").read_text()
assert "EDEN_MAINTAINED_MAXWELL_DMA" in cmake
assert 'list(REMOVE_ITEM video_sources engines/maxwell_dma.cpp)' in cmake
def extract(start, end):
    assert source.count(start) == 1, start
    begin = source.index(start)
    assert end in source[begin:], end
    return source[begin:source.index(end, begin) + 2]
coalesce = extract("constexpr bool CanCoalescePitchDma(", "\n}\n\n// Remapped DMA lengths")
remap = extract("bool CopyPitchRemap(", "\n}\n} // namespace")
for evidence in (
    "remap.dst_x.Value()", "remap.dst_w.Value()", "Swizzle::NO_WRITE",
    "Swizzle::CONST_A", "Swizzle::CONST_B", "num_src_components_minus_one",
    "num_dst_components_minus_one", "memory.ReadBlock", "memory.WriteBlock",
    "memory.CopyBlock", "std::vector<u8> snapshot", "src_row_bytes",
    "dst_row_bytes", "MAX_CPU_REMAP_BYTES", "CHUNK_BYTES",
):
    assert evidence in remap, evidence
assert source.count("if (launch.remap_enable != 0 &&") == 1
assert source.count("CopyPitchRemap(memory_manager, regs.remap_const") == 1

cpp = r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>
using u8 = std::uint8_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s32 = std::int32_t;
using s64 = std::int64_t;
using GPUVAddr = u64;
namespace Common {
template <typename T> class ScratchBuffer {
    std::vector<T> buffer;
public:
    void resize_destructive(std::size_t n) { buffer.resize(n); }
    T* data() { return buffer.data(); }
};
}
struct MaxwellDMA {
    struct RemapConst {
        enum class Swizzle : u32 {
            SRC_X=0, SRC_Y=1, SRC_Z=2, SRC_W=3,
            CONST_A=4, CONST_B=5, NO_WRITE=6
        };
        struct Selector {
            Swizzle selected{Swizzle::NO_WRITE};
            constexpr Swizzle Value() const { return selected; }
        };
        struct Num {
            u32 value{};
            constexpr operator u32() const { return value; }
        };
        u32 remap_consta_value{};
        u32 remap_constb_value{};
        Selector dst_x{}, dst_y{}, dst_z{}, dst_w{};
        Num component_size_minus_one{}, num_src_components_minus_one{},
            num_dst_components_minus_one{};
    };
};
class MemoryManager {
public:
    std::array<u8, 8192> bytes{};
    void ReadBlock(GPUVAddr a, void* dst, std::size_t n) {
        assert(a <= bytes.size() && n <= bytes.size() - a);
        std::memcpy(dst, bytes.data() + a, n);
    }
    void WriteBlock(GPUVAddr a, const void* src, std::size_t n) {
        assert(a <= bytes.size() && n <= bytes.size() - a);
        std::memcpy(bytes.data() + a, src, n);
    }
    void CopyBlock(GPUVAddr dst, GPUVAddr src, std::size_t n) {
        assert(src <= bytes.size() && n <= bytes.size() - src);
        assert(dst <= bytes.size() && n <= bytes.size() - dst);
        std::memmove(bytes.data() + dst, bytes.data() + src, n);
    }
};
__COALESCE__
__REMAP__
int main() {
    using R = MaxwellDMA::RemapConst;
    using S = R::Swizzle;
    MemoryManager mem;
    Common::ScratchBuffer<u8> source_scratch, destination_scratch;
    const auto apply = [&](const R& r, GPUVAddr from, GPUVAddr to, s32 ip, s32 op,
                           u32 blocks, u32 rows) {
        return CopyPitchRemap(mem, r, from, to, ip, op, blocks, rows,
                              source_scratch, destination_scratch);
    };
    const auto cfg = [](u32 bytes, u32 src_count, u32 dst_count) {
        R r{};
        r.component_size_minus_one.value = bytes - 1;
        r.num_src_components_minus_one.value = src_count - 1;
        r.num_dst_components_minus_one.value = dst_count - 1;
        return r;
    };
    // Identity remap uses LINE_LENGTH_IN blocks, not raw bytes.
    auto r = cfg(1, 4, 4);
    r.dst_x.selected = S::SRC_X;
    r.dst_y.selected = S::SRC_Y;
    r.dst_z.selected = S::SRC_Z;
    r.dst_w.selected = S::SRC_W;
    for (u32 i=0;i<8;i++) mem.bytes[0x100+i] = 20+i;
    assert(apply(r, 0x100, 0x200, 8, 8, 2, 1));
    for (u32 i=0;i<8;i++) assert(mem.bytes[0x200+i]==20+i);

    // Reorder + CONST_B + NO_WRITE means preserve destination Y.
    r = cfg(1, 4, 4);
    r.remap_constb_value = 0x7b;
    r.dst_x.selected = S::SRC_W;
    r.dst_y.selected = S::NO_WRITE;
    r.dst_z.selected = S::CONST_B;
    r.dst_w.selected = S::SRC_X;
    for (u32 i=0;i<8;i++) {
        mem.bytes[0x300+i] = 10+i;
        mem.bytes[0x400+i] = 80+i;
    }
    assert(apply(r, 0x300, 0x400, 8, 8, 2, 1));
    const std::array<u8,8> expected{13,81,0x7b,10,17,85,0x7b,14};
    for (u32 i=0;i<8;i++) assert(mem.bytes[0x400+i]==expected[i]);

    // A three-byte CONST_A should not read the unused (even invalid) source.
    r = cfg(3, 1, 1);
    r.remap_consta_value=0x123456;
    r.dst_x.selected=S::CONST_A;
    assert(apply(r, (std::numeric_limits<u64>::max)(), 0x500, 0, 0, 2, 1));
    const std::array<u8,6> expected_three{0x56,0x34,0x12,0x56,0x34,0x12};
    for (u32 i=0;i<6;i++) assert(mem.bytes[0x500+i]==expected_three[i]);

    // Multiple rows with different component counts, 16-bit little-endian.
    r=cfg(2,1,2);
    r.remap_consta_value=0x1020;
    r.remap_constb_value=0x3040;
    r.dst_x.selected=S::CONST_A;
    r.dst_y.selected=S::CONST_B;
    assert(apply(r, 0, 0x600, 4, 10, 2, 2));
    for(u32 row=0;row<2;row++) {
        const u32 a=0x600+10*row;
        for(u32 i=0;i<2;i++) {
            assert(mem.bytes[a+4*i]==0x20 && mem.bytes[a+4*i+1]==0x10);
            assert(mem.bytes[a+4*i+2]==0x40 && mem.bytes[a+4*i+3]==0x30);
        }
    }

    // Negative input pitch maps row 1 before row 0, without unsigned wrap.
    r=cfg(1,1,1);
    r.dst_x.selected=S::SRC_X;
    for(u32 i=0;i<3;i++) {mem.bytes[0x70c+i]=11+i;mem.bytes[0x708+i]=21+i;}
    assert(apply(r,0x70c,0x800,-4,4,3,2));
    for(u32 i=0;i<3;i++) {
        assert(mem.bytes[0x800+i]==11+i);
        assert(mem.bytes[0x804+i]==21+i);
    }

    // Overlapping ranges are snapshotted; no read-after-overwrite corruption.
    for(u32 i=0;i<8;i++)mem.bytes[0x900+i]=40+i;
    assert(apply(r,0x900,0x902,8,8,8,1));
    for(u32 i=0;i<8;i++)assert(mem.bytes[0x902+i]==40+i);

    // An unavailable SRC_W on a one-component source is not a valid read.
    r=cfg(1,1,1);
    r.dst_x.selected=S::SRC_W;
    mem.bytes[0xa00]=77;
    assert(!apply(r,0x900,0xa00,0,0,1,1));
    assert(mem.bytes[0xa00]==77);

    // Signed negative pitch below guest address zero is rejected.
    r.dst_x.selected=S::SRC_X;
    mem.bytes[0xa00]=77;
    assert(!apply(r,0x900,0x5,8,-16,1,2));
    assert(mem.bytes[0xa00]==77);

    // An all-NO_WRITE command never touches an unneeded source/destination.
    r.dst_x.selected=S::NO_WRITE;
    assert(apply(r, (std::numeric_limits<u64>::max)(),
                 (std::numeric_limits<u64>::max)(),0,0,1,1));
}
""".replace("__COALESCE__", coalesce).replace("__REMAP__", remap)
compilers = [c for c in ("clang++", "g++") if shutil.which(c)]
assert compilers, "No C++ compiler available for the native remap contract"
with tempfile.TemporaryDirectory(prefix="eden-b0b5-remap-") as temp:
    root_tmp = Path(temp)
    source_file = root_tmp / "remap.cpp"
    source_file.write_text(cpp)
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            binary = root_tmp / (compiler.replace("+", "x") + opt)
            subprocess.run(
                [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                 "-fsanitize=undefined", "-fno-sanitize-recover=all",
                 str(source_file), "-o", str(binary)],
                check=True, timeout=90)
            subprocess.run([str(binary)], check=True, timeout=90)
print("B0B5_PITCH_REMAP_HOST_PASS compilers=", ",".join(compilers),
      "cases=identity,swizzle,no_write,const_a,const_b,24bit,16bit,negative_pitch,overlap,invalid")
