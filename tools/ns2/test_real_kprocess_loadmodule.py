#!/usr/bin/env python3
"""N46: execute unchanged maintained KProcess::LoadModule with a host-backed
process memory/page table, using the independently cross-built public HOS NSO.

NOT a complete KProcess::LoadFromMetadata, scheduler, HLE or PS5 execution.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/sources/eden/src/core/hle/kernel/k_process.cpp"
BEGIN = "void KProcess::LoadModule("
END = "\nvoid KProcess::InitializeInterfaces("

HOST_PREFIX = r"""
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using u8 = std::uint8_t;
using u32 = std::uint32_t;
namespace Svc {
enum class MemoryPermission : std::uint8_t { ReadExecute, Read, ReadWrite };
}
namespace Kernel {
using KProcessAddress = std::uint64_t;
struct KernelCore {};
struct CodeSet {
    struct Segment {
        std::size_t offset = 0;
        KProcessAddress addr = 0;
        u32 size = 0;
    };
    std::vector<u8> memory;
    std::array<Segment, 3> segments{};
    Segment& CodeSegment() { return segments[0]; }
    const Segment& CodeSegment() const { return segments[0]; }
    Segment& RODataSegment() { return segments[1]; }
    const Segment& RODataSegment() const { return segments[1]; }
    Segment& DataSegment() { return segments[2]; }
    const Segment& DataSegment() const { return segments[2]; }
};
struct FakePageTable {
    using Record = std::tuple<KProcessAddress, u32, Svc::MemoryPermission>;
    std::vector<Record> permissions;
    void SetProcessMemoryPermission(KProcessAddress address, u32 length,
                                     Svc::MemoryPermission permissions_kind) {
        permissions.emplace_back(address, length, permissions_kind);
    }
};
struct FakeMemory {
    KProcessAddress base = 0;
    std::vector<u8> bytes;
    unsigned writes = 0;
    void WriteBlock(KProcessAddress address, const u8* data, std::size_t len) {
        if (writes != 0) throw std::runtime_error("multiple guest image copies");
        base = address;
        bytes.assign(data, data + len);
        ++writes;
    }
};
struct KProcess {
    FakePageTable m_page_table;
    FakeMemory memory;
    FakeMemory& GetMemory() { return memory; }
    void LoadModule(KernelCore& kernel, CodeSet code_set, KProcessAddress base_addr);
};
"""

HOST_TEST = r"""
} // namespace Kernel

static void Require(bool ok, const char* what) {
    if (!ok) throw std::runtime_error(what);
}
static u32 Read32(const std::vector<u8>& data, std::size_t p) {
    Require(p <= data.size() && 4 <= data.size() - p, "NSO integer out of bounds");
    return static_cast<u32>(data[p]) | (static_cast<u32>(data[p+1]) << 8) |
           (static_cast<u32>(data[p+2]) << 16) | (static_cast<u32>(data[p+3]) << 24);
}
static std::size_t AlignPage(std::size_t n) {
    constexpr std::size_t page = 0x1000;
    Require(n <= std::numeric_limits<std::size_t>::max() - page + 1, "align overflow");
    return (n + page - 1) & ~(page - 1);
}
struct Prepared {
    Kernel::CodeSet code;
    std::array<std::vector<u8>, 3> originals;
};
static Prepared Prepare(const std::vector<u8>& nso) {
    Require(nso.size() >= 0x100 && nso.size() <= 1024 * 1024 &&
            std::memcmp(nso.data(), "NSO0", 4) == 0, "invalid NSO signature/size");
    Require(Read32(nso, 0x0C) == 0, "compressed NSO unsupported in fixture");
    struct Span { u32 file, virtual_offset, length; };
    std::array<Span, 3> segments{};
    std::size_t previous_end = 0;
    for (std::size_t i = 0; i < 3; ++i) {
        const std::size_t h = 0x10 + i * 0x10;
        const Span seg{Read32(nso,h), Read32(nso,h+4), Read32(nso,h+8)};
        Require(seg.length != 0 && seg.file >= 0x100 &&
                seg.file <= nso.size() && seg.length <= nso.size() - seg.file &&
                Read32(nso, 0x60 + i * 4) == seg.length,
                "invalid NSO file segment");
        Require(seg.virtual_offset >= previous_end && seg.virtual_offset < 0x100000 &&
                seg.length <= 0x100000 - seg.virtual_offset,
                "invalid/overlapping NSO virtual segments");
        previous_end = static_cast<std::size_t>(seg.virtual_offset) + seg.length;
        segments[i] = seg;
    }
    Require(segments[0].virtual_offset == 0 &&
            segments[1].virtual_offset == 0x1000 &&
            segments[2].virtual_offset == 0x2000,
            "unexpected independently built public ExeFS virtual offsets");
    const u32 bss = Read32(nso, 0x3C);
    Require(bss == 0x1000 && previous_end <= 0x100000 - bss,
            "unexpected public fixture BSS");
    Prepared result;
    result.code.memory.resize(AlignPage(previous_end + bss), 0);
    for (std::size_t i = 0; i < segments.size(); ++i) {
        const auto& seg = segments[i];
        result.originals[i].assign(nso.begin()+seg.file,
                                   nso.begin()+seg.file+seg.length);
        std::copy(result.originals[i].begin(), result.originals[i].end(),
                  result.code.memory.begin()+seg.virtual_offset);
        result.code.segments[i].addr = seg.virtual_offset;
        result.code.segments[i].offset = seg.virtual_offset;
        result.code.segments[i].size =
            static_cast<u32>(AlignPage(seg.length + (i == 2 ? bss : 0)));
    }
    constexpr char message[] = "hello from HOS\n";
    Require(std::search(result.originals[0].begin(), result.originals[0].end(),
                        message, message + sizeof(message)-1)
            != result.originals[0].end(), "not original public guest code");
    constexpr char ro[] = "open-source-loader-test";
    constexpr char data[] = "NS2-DATA-SEGMENT";
    Require(std::search(result.originals[1].begin(), result.originals[1].end(),
                        ro, ro + sizeof(ro)-1) != result.originals[1].end(),
            "missing public RO-data marker");
    Require(std::search(result.originals[2].begin(), result.originals[2].end(),
                        data, data + sizeof(data)-1) != result.originals[2].end(),
            "missing public RW-data marker");
    return result;
}
int main(int argc, char** argv) {
    try {
        Require(argc == 2, "usage: real_kprocess_loadmodule fixture/main");
        std::ifstream stream(argv[1], std::ios::binary);
        Require(stream.is_open(), "NSO fixture not found");
        const std::vector<u8> nso{
            std::istreambuf_iterator<char>{stream},
            std::istreambuf_iterator<char>{}};
        auto prepared = Prepare(nso);
        const auto untouched = prepared.code.memory;
        const auto segments = prepared.code.segments;
        Kernel::KProcess process;
        Kernel::KernelCore kernel;
        constexpr Kernel::KProcessAddress base = 0x80000000ULL;
        process.LoadModule(kernel, std::move(prepared.code), base);
        Require(process.memory.writes == 1 &&
                process.memory.base == base &&
                process.memory.bytes == untouched,
                "genuine KProcess::LoadModule guest image copy failed");
        Require(process.m_page_table.permissions.size() == 3,
                "genuine KProcess::LoadModule did not reprotect 3 segments");
        constexpr std::array<Svc::MemoryPermission, 3> expected{
            Svc::MemoryPermission::ReadExecute,
            Svc::MemoryPermission::Read,
            Svc::MemoryPermission::ReadWrite
        };
        for (std::size_t i=0; i<3; ++i) {
            Require(process.m_page_table.permissions[i] ==
                    Kernel::FakePageTable::Record{
                        base+segments[i].addr, segments[i].size, expected[i]},
                    "genuine KProcess::LoadModule permissions mismatch");
        }
        // Independently validate the copied guest bytes at their original
        // NSO virtual positions, plus uninitialized gaps/BSS.
        for (std::size_t i=0; i<3; ++i) {
            const std::size_t address = static_cast<std::size_t>(segments[i].addr);
            Require(segments[i].size <= process.memory.bytes.size() - address,
                    "copied guest segment exceeds memory image");
            Require(std::equal(prepared.originals[i].begin(),
                               prepared.originals[i].end(),
                               process.memory.bytes.begin()+address),
                    "wrong NSO segment in guest memory");
        }
        const std::size_t bss_start = static_cast<std::size_t>(segments[2].addr) +
                                      prepared.originals[2].size();
        Require(std::all_of(process.memory.bytes.begin()+bss_start,
                            process.memory.bytes.end(), [](u8 b){return b==0;}),
                "BSS was not zero-filled");

        // Negative cases: the independent fixture decoder must not feed
        // malformed data to a production-member-function invocation.
        auto bad = nso;
        bad[0] = 'X';
        bool rejected = false;
        try { (void)Prepare(bad); } catch (const std::runtime_error&) {
            rejected = true;
        }
        Require(rejected, "bad NSO magic accepted");
        bad = nso; bad[0x0C] = 1;
        rejected = false;
        try { (void)Prepare(bad); } catch (const std::runtime_error&) {
            rejected = true;
        }
        Require(rejected, "compressed fixture improperly accepted");
        bad = nso; bad[0x24] = 0; bad[0x25] = 0;
        rejected = false;
        try { (void)Prepare(bad); } catch (const std::runtime_error&) {
            rejected = true;
        }
        Require(rejected, "overlapping NSO virtual segment accepted");
        bad = nso; bad.resize(0x100);
        rejected = false;
        try { (void)Prepare(bad); } catch (const std::runtime_error&) {
            rejected = true;
        }
        Require(rejected, "truncated NSO accepted");
        std::cout << "NS2_REAL_KPROCESS_LOADMODULE_HOST_PASS"
                  << " original_kernel_member=1 original_public_nso=1"
                  << " text_rodata_data_copied=1 bss_zero=1"
                  << " guest_permissions_r_x_r_rw=1 malformed_rejected=1"
                  << " KProcess_LoadFromMetadata_not_executed=1"
                  << " PS5_runtime_not_executed=1\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "NS2_REAL_KPROCESS_LOADMODULE_HOST_FAIL: " << e.what() << '\n';
        return 1;
    }
}
"""

def exact_kernel_owner(source: str) -> str:
    if source.count(BEGIN) != 1:
        raise AssertionError("Maintained KProcess::LoadModule owner anchor changed")
    tail = source.split(BEGIN, 1)[1]
    if END not in tail:
        raise AssertionError("Maintained KProcess next owner anchor changed")
    method = BEGIN + tail.split(END, 1)[0]
    for required in ("this->GetMemory().WriteBlock", "CodeSegment()",
                     "RODataSegment()", "DataSegment()",
                     "SetProcessMemoryPermission"):
        if required not in method:
            raise AssertionError(f"Maintained KProcess owner changed: {required}")
    if method.count("#ifdef HAS_NCE") != method.count("#endif"):
        raise AssertionError("Unexpected preprocessor boundary in method")
    return method


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--nso", required=True, type=Path)
    args = cli.parse_args()
    if not args.nso.is_file():
        raise FileNotFoundError(args.nso)
    member = exact_kernel_owner(OWNER.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="ns2-real-kprocess-loadmodule-") as temp:
        src = Path(temp) / "kprocess_loadmodule.cpp"
        src.write_text(HOST_PREFIX + "\n" + member + "\n" + HOST_TEST, encoding="utf-8")
        for compiler in ("clang++", "g++"):
            if not shutil.which(compiler):
                raise RuntimeError("Required compiler missing: " + compiler)
            exe = Path(temp) / compiler.replace("+", "p")
            subprocess.run(
                [compiler, "-std=c++20", "-O1", "-g", "-Wall", "-Wextra",
                 "-Werror", "-Wno-unused-parameter", "-fsanitize=address,undefined",
                 "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
                 str(src), "-o", str(exe)],
                check=True, timeout=120)
            subprocess.run([str(exe), str(args.nso.resolve())], check=True, timeout=30)


if __name__ == "__main__":
    main()
