#!/usr/bin/env python3
"""Compile the exact selected R4 physical-span admission lambda with host doubles.

This is source-backed GMMU mapping/alias preflight, NOT a PS5 GPU timeline or
real guest page-table concurrency test. The exact vendor header SHA is pinned.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h"
EXPECTED_SHA = "b48a544156be57b0dfe21bdf3972399a4349941c"

def run():
    actual = subprocess.check_output(
        ["git", "hash-object", str(OWNER)], text=True
    ).strip()
    assert actual == EXPECTED_SHA, ("R4 active N60 owner changed", actual)
    original = OWNER.read_text()
    start = original.index("        struct PhysicalSpan {", original.index("const auto copy_native_volume_slice"))
    end = original.index("        const auto src_physical = capture_physical", start)
    block = original[start:end]
    assert "gpu_memory->IsContinuousRange" in block
    assert "image.guest_size_bytes" in block
    assert "const auto overlaps" in block
    assert "src_physical_after->address != src_physical->address" in original
    assert "dst_physical_after->address != dst_physical->address" in original
    test = r"""
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstddef>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>

using u64 = std::uint64_t;
using ImageId = std::size_t;

struct Image {
    u64 gpu_addr{};
    u64 cpu_addr{};
    u64 guest_size_bytes{};
};

struct MockGpuMemory {
    struct Span {u64 gpu, physical, length;};
    std::vector<Span> spans;
    std::optional<u64> GpuToCpuAddress(u64 gpu) const {
        for (const auto& item : spans) {
            if (gpu >= item.gpu && gpu - item.gpu < item.length)
                return item.physical + gpu - item.gpu;
        }
        return std::nullopt;
    }
    bool IsContinuousRange(u64 address, std::size_t bytes) const {
        if (!bytes || address > std::numeric_limits<u64>::max() - (bytes - 1))
            return false;
        const auto begin = GpuToCpuAddress(address);
        if (!begin || *begin > std::numeric_limits<u64>::max() - (bytes - 1))
            return false;
        for (u64 offset = 0; offset < bytes; offset += 4096) {
            const auto mapped = GpuToCpuAddress(address + offset);
            if (!mapped || *mapped != *begin + offset)
                return false;
        }
        const auto end = GpuToCpuAddress(address + bytes - 1);
        return end && *end == *begin + bytes - 1;
    }
};

int main() {
    std::array<Image, 2> slot_images{{
        {0x1000, 0x100000, 8192},
        {0x4000, 0x200000, 8192},
    }};
    MockGpuMemory manager{{{0x1000,0x100000,8192},{0x4000,0x200000,8192}}};
    MockGpuMemory* gpu_memory = &manager;
    auto capture = [&]() {
@@EXACT_LAMBDA@@
        auto src = capture_physical(0);
        auto dst = capture_physical(1);
        const bool alias = src && dst && overlaps(*src, *dst);
        return std::pair{std::pair{src, dst}, alias};
    };
    unsigned checks{};
    const auto check = [&](bool pass) {
        ++checks;
        if (!pass) throw std::runtime_error("R4 physical-host assertion " +
                                            std::to_string(checks));
    };
    auto base = capture();
    check(base.first.first.has_value() && base.first.second.has_value());
    check(!base.second);
    check(base.first.first->address == 0x100000);
    check(base.first.second->address == 0x200000);

    // Different GPU VAs, *same* physical memory: must never enter fast path.
    manager.spans[1].physical = slot_images[1].cpu_addr = 0x100000;
    check(capture().second);
    manager.spans[1].physical = slot_images[1].cpu_addr = 0x101000;
    check(capture().second); // only partial overlap
    manager.spans[1].physical = slot_images[1].cpu_addr = 0x200000;
    check(!capture().second);

    // Gap and physical discontinuity: even two valid endpoints are not enough.
    manager.spans[0].length = 4096;
    check(!capture().first.first);
    manager.spans.push_back({0x2000,0x900000,4096});
    check(!capture().first.first);
    manager.spans.pop_back();
    manager.spans[0].length = 8192;
    check(capture().first.first.has_value());

    // A stale cached physical base cannot be trusted across a guest remap.
    slot_images[0].cpu_addr = 0xdead000;
    check(!capture().first.first);
    slot_images[0].cpu_addr = 0x100000;
    check(capture().first.first.has_value());

    // Huge or wrapping guest ranges are rejected before querying mapping.
    slot_images[0].guest_size_bytes = (256ULL << 20) + 1;
    check(!capture().first.first);
    slot_images[0].guest_size_bytes = 0;
    check(!capture().first.first);
    slot_images[0] = {std::numeric_limits<u64>::max()-16, 0x100000, 8192};
    check(!capture().first.first);
    slot_images[0] = {0x1000,0x100000,8192};

    // The real caller captures again after PrepareImage. A rebinding within
    // that window must not be treated as the same physical image.
    const auto before = capture().first;
    manager.spans[0].physical = slot_images[0].cpu_addr = 0x300000;
    const auto after = capture().first;
    check(before.first && after.first &&
          before.first->address != after.first->address);
    manager.spans[0].physical = slot_images[0].cpu_addr = 0x100000;
    const auto restored = capture().first;
    check(restored.first && restored.second &&
          restored.first->address == before.first->address &&
          restored.second->address == before.second->address);
    std::cout << "R4_ACTIVE_PHYSICAL_ALIAS_SOURCE_PASS checks=" << checks << "\n";
}
""".replace("@@EXACT_LAMBDA@@", block)
    with tempfile.TemporaryDirectory(prefix="r4-real-physical-alias-") as d:
        src = Path(d) / "source.cpp"
        src.write_text(test)
        for compiler in ("clang++", "g++"):
            for opt in ("0", "2"):
                output = Path(d) / (compiler.replace("+","p") + "-O" + opt)
                flags = [
                    compiler, "-std=c++20", "-O"+opt, "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-fsanitize=address,undefined",
                    "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
                    str(src), "-o", str(output),
                ]
                built = subprocess.run(flags, capture_output=True, text=True)
                if built.returncode:
                    raise RuntimeError("R4 exact lambda compilation failed\n" + built.stderr[-7000:])
                ran = subprocess.run([str(output)], capture_output=True, text=True)
                if ran.returncode:
                    raise RuntimeError("R4 exact lambda tests failed\n" + ran.stdout + ran.stderr[-7000:])
                print(compiler, "O"+opt, ran.stdout.strip(), flush=True)

if __name__ == "__main__":
    run()
