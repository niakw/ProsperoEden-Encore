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
source = (root / "vendor/encore-active/eden/src/video_core/engines/maxwell_dma.cpp").read_text()
cmake = (root / "headless/CMakeLists.txt").read_text()
maintained_header = (root / "vendor/encore-active/eden/include/video_core/engines/maxwell_dma.h").read_text()
original_header = (root / "vendor/sources/eden/src/video_core/engines/maxwell_dma.h").read_text()
assert "BitField<0, 16, u32> dst_components_raw" in maintained_header
assert "BitField<0, 12, u32> dst_components_raw" in original_header
assert 'target_include_directories(video_core BEFORE PUBLIC "${EDEN_MAINTAINED_MAXWELL_DMA_INCLUDE}")' in cmake
method_start = "[[nodiscard]] Swizzle GetComponent(size_t i) const {"
assert maintained_header.count(method_start) == 1
method = maintained_header[
    maintained_header.index(method_start):
    maintained_header.index("\n        }\n    };", maintained_header.index(method_start)) + len("\n        }")
]
assert "(i * 4)" in method and "i >= 4" in method
assert "EDEN_MAINTAINED_MAXWELL_DMA" in cmake
assert 'list(REMOVE_ITEM video_sources engines/maxwell_dma.cpp)' in cmake
def extract(start, end):
    assert source.count(start) == 1, start
    begin = source.index(start)
    assert end in source[begin:], end
    return source[begin:source.index(end, begin) + 2]
coalesce = extract("constexpr bool CanCoalescePitchDma(", "\n}\n\n// Signed 2D pitch geometry")
shared_begin = "// Signed 2D pitch geometry and device-address overlap are shared by"
shared_end = "// Remapped DMA lengths are measured in pixels/blocks, NOT bytes."
assert source.count(shared_begin) == source.count(shared_end) == 1
shared = source[source.index(shared_begin):source.index(shared_end)]
remap = extract("bool CopyPitchRemap(", "\n}\n} // namespace")
for evidence in (
    "remap.GetComponent(0)", "remap.GetComponent(3)", "Swizzle::NO_WRITE",
    "Swizzle::CONST_A", "Swizzle::CONST_B", "num_src_components_minus_one",
    "num_dst_components_minus_one", "memory.ReadBlock", "memory.WriteBlock",
    "memory.CopyBlock", "std::vector<u8> snapshot", "src_row_bytes",
    "dst_row_bytes", "MAX_CPU_REMAP_BYTES", "CHUNK_BYTES",
    "PitchDmaPhysicalOverlap(", "PitchDmaRowAddress(",
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
#include <optional>
#include <utility>
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
        struct Num {
            u32 value{};
            constexpr operator u32() const { return value; }
        };
        u32 remap_consta_value{};
        u32 remap_constb_value{};
        u32 dst_components_raw{};
        Num component_size_minus_one{}, num_src_components_minus_one{},
            num_dst_components_minus_one{};
        __METHOD__
    };
};
class MemoryManager {
public:
    std::array<u8, 32768> bytes{};
    // GMMU pages 0x4000 and 0x5000 point to physical pages 0x2000
    // and 0x3000 respectively. 0x6000 is deliberately unmapped.
    std::optional<u64> GpuToCpuAddress(GPUVAddr address) const {
        if (address >= 0x4000 && address < 0x6000) return address - 0x2000;
        if (address >= 0x6000 && address < 0x7000) return std::nullopt;
        if (address < bytes.size()) return address;
        return std::nullopt;
    }
    bool IsFullyMappedRange(GPUVAddr address, std::size_t n) const {
        if (n == 0 || address > std::numeric_limits<u64>::max() - n)
            return false;
        for (std::size_t i=0; i<n; ++i) {
            if (!GpuToCpuAddress(address+i)) return false;
        }
        return true;
    }
    bool IsContinuousRange(GPUVAddr address, std::size_t n) const {
        if (!IsFullyMappedRange(address,n)) return false;
        const auto first=GpuToCpuAddress(address);
        for(std::size_t i=0;i<n;++i) {
            if (GpuToCpuAddress(address+i) !=
                std::optional<u64>{*first+i}) return false;
        }
        return true;
    }
    void ReadBlock(GPUVAddr a, void* dst, std::size_t n) {
        auto* ptr=static_cast<u8*>(dst);
        for(std::size_t i=0;i<n;++i) {
            const auto address=GpuToCpuAddress(a+i);
            assert(address && *address<bytes.size());
            ptr[i]=bytes[*address];
        }
    }
    void WriteBlock(GPUVAddr a, const void* src, std::size_t n) {
        const auto* ptr=static_cast<const u8*>(src);
        for(std::size_t i=0;i<n;++i) {
            const auto address=GpuToCpuAddress(a+i);
            assert(address && *address<bytes.size());
            bytes[*address]=ptr[i];
        }
    }
    void CopyBlock(GPUVAddr dst, GPUVAddr src, std::size_t n) {
        std::vector<u8> temporary(n);
        ReadBlock(src,temporary.data(),n);
        WriteBlock(dst,temporary.data(),n);
    }
};
__COALESCE__
__SHARED__
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
    const auto set = [](R& remap, u32 slot, S selector) {
        assert(slot < 4);
        const u32 shift = slot * 4;
        remap.dst_components_raw &= ~(0xfu << shift);
        remap.dst_components_raw |= static_cast<u32>(selector) << shift;
    };
    // The fourth destination selector lives at bit 12, not bit 9.
    {
        R check{};
        set(check, 0, S::SRC_X);
        set(check, 1, S::SRC_Z);
        set(check, 2, S::NO_WRITE);
        set(check, 3, S::CONST_B);
        assert(check.GetComponent(0) == S::SRC_X);
        assert(check.GetComponent(1) == S::SRC_Z);
        assert(check.GetComponent(2) == S::NO_WRITE);
        assert(check.GetComponent(3) == S::CONST_B);
        assert(static_cast<u32>(check.GetComponent(4)) == 7);
    }
    // Identity remap uses LINE_LENGTH_IN blocks, not raw bytes.
    auto r = cfg(1, 4, 4);
    set(r, 0, S::SRC_X);
    set(r, 1, S::SRC_Y);
    set(r, 2, S::SRC_Z);
    set(r, 3, S::SRC_W);
    for (u32 i=0;i<8;i++) mem.bytes[0x100+i] = 20+i;
    assert(apply(r, 0x100, 0x200, 8, 8, 2, 1));
    for (u32 i=0;i<8;i++) assert(mem.bytes[0x200+i]==20+i);

    // Reorder + CONST_B + NO_WRITE means preserve destination Y.
    r = cfg(1, 4, 4);
    r.remap_constb_value = 0x7b;
    set(r, 0, S::SRC_W);
    set(r, 1, S::NO_WRITE);
    set(r, 2, S::CONST_B);
    set(r, 3, S::SRC_X);
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
    set(r, 0, S::CONST_A);
    assert(apply(r, (std::numeric_limits<u64>::max)(), 0x500, 0, 0, 2, 1));
    const std::array<u8,6> expected_three{0x56,0x34,0x12,0x56,0x34,0x12};
    for (u32 i=0;i<6;i++) assert(mem.bytes[0x500+i]==expected_three[i]);

    // Multiple rows with different component counts, 16-bit little-endian.
    r=cfg(2,1,2);
    r.remap_consta_value=0x1020;
    r.remap_constb_value=0x3040;
    set(r, 0, S::CONST_A);
    set(r, 1, S::CONST_B);
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
    set(r, 0, S::SRC_X);
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

    // Two distinct virtual pages alias a later source row physically.
    // The old raw row-by-row CopyBlock would overwrite its unread row 1.
    for (u32 i=0;i<16;i++) {
        mem.bytes[0x1000+i]=static_cast<u8>(60+i);
        mem.bytes[0x2000+i]=static_cast<u8>(120+i);
    }
    assert(CopyPitchDmaPlain(mem,0x1000,0x4000,4096,4096,16,2));
    for (u32 i=0;i<16;i++) {
        assert(mem.bytes[0x2000+i]==60+i);
        assert(mem.bytes[0x3000+i]==120+i);
    }
    // Component-remapped DMA shares the same physical-VA detection.
    r=cfg(1,1,1);
    set(r,0,S::SRC_X);
    for (u32 i=0;i<16;i++) {
        mem.bytes[0x1000+i]=static_cast<u8>(30+i);
        mem.bytes[0x2000+i]=static_cast<u8>(90+i);
    }
    assert(apply(r,0x1000,0x4000,4096,4096,16,2));
    for (u32 i=0;i<16;i++) {
        assert(mem.bytes[0x2000+i]==30+i);
        assert(mem.bytes[0x3000+i]==90+i);
    }
    // Negative pitch is checked in widened arithmetic, not size_t wrap.
    for (u32 i=0;i<16;i++) {
        mem.bytes[0x1000+i]=static_cast<u8>(10+i);
        mem.bytes[0x2000+i]=static_cast<u8>(20+i);
    }
    assert(CopyPitchDmaPlain(mem,0x2000,0x5000,-4096,-4096,16,2));
    for (u32 i=0;i<16;i++) {
        assert(mem.bytes[0x3000+i]==20+i);
        assert(mem.bytes[0x2000+i]==10+i);
    }
    // When the second destination row is unmapped, fail before writing
    // the FIRST destination row, not halfway through a DMA.
    for (u32 i=0;i<16;i++) mem.bytes[0x3000+i]=static_cast<u8>(0xa0+i);
    assert(!CopyPitchDmaPlain(mem,0x1000,0x5000,4096,4096,16,2));
    for (u32 i=0;i<16;i++) assert(mem.bytes[0x3000+i]==0xa0+i);

    // An unavailable SRC_W on a one-component source is not a valid read.
    r=cfg(1,1,1);
    set(r, 0, S::SRC_W);
    mem.bytes[0xa00]=77;
    assert(!apply(r,0x900,0xa00,0,0,1,1));
    assert(mem.bytes[0xa00]==77);

    // Signed negative pitch below guest address zero is rejected.
    set(r, 0, S::SRC_X);
    mem.bytes[0xa00]=77;
    assert(!apply(r,0x900,0x5,8,-16,1,2));
    assert(mem.bytes[0xa00]==77);

    // An all-NO_WRITE command never touches an unneeded source/destination.
    set(r, 0, S::NO_WRITE);
    assert(apply(r, (std::numeric_limits<u64>::max)(),
                 (std::numeric_limits<u64>::max)(),0,0,1,1));
}
""".replace("__COALESCE__", coalesce).replace("__SHARED__", shared).replace("__REMAP__", remap).replace("__METHOD__", method)
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
