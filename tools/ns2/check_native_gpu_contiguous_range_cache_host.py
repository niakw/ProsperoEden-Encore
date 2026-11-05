#!/usr/bin/env python3
"""P1.2/P2 native GPU range cache: compile actual shared mapper scan under remaps.

Host-only proof. The real MaxContinuousRange implementation is extracted from
the pinned vendor owner and built unchanged against deterministic 4 KiB PTEs.
This does NOT infer GPU-driver performance or console correctness.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/encore-active/eden-core/src/video_core/memory_manager.cpp"
source = OWNER.read_text()
start = "size_t MemoryManager::MaxContinuousRange(GPUVAddr gpu_addr, size_t size) const {"
end = "\nsize_t MemoryManager::GetMemoryLayoutSize("
assert source.count(start) == source.count(end) == 1
actual_range_function = source.split(start, 1)[1].split(end, 1)[0]
assert source.count("gpu_page_table_revision.fetch_add(1, std::memory_order_release)") == 4
assert "thread_local std::array<Entry, 64> cache{};" in actual_range_function
assert "entry.owner == this && entry.owner_id == unique_identifier" in actual_range_function
assert actual_range_function.count("gpu_page_table_revision.load(std::memory_order_acquire)") >= 3
assert "MemoryOperation(gpu_addr, size, true, big_check, fail, check_short_pages)" in actual_range_function

fixture = r"""
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <optional>
using u64 = std::uint64_t;
using u32 = std::uint32_t;
using GPUVAddr = std::uint64_t;
using DAddr = std::uint64_t;
namespace Tegra {
namespace {
std::atomic<u64> gpu_page_table_revision{1};
}
class MemoryManager {
public:
    explicit MemoryManager(std::size_t id) : unique_identifier(id) {}
    std::size_t unique_identifier;
    mutable std::size_t page_walks = 0;
    u64 big_page_bits = 12;
    u64 cpu_page_bits = 12;
    std::array<u32, 16> page_table{};
    std::array<u32, 16> big_page_table_dev{};
    std::array<bool, 16> mapped{};

    template <typename Map, typename Reserve, typename Unmap>
    void MemoryOperation(GPUVAddr address, std::size_t bytes, bool is_big,
                         Map&& on_map, Reserve&& on_reserved, Unmap&& on_unmap) const {
        ++page_walks;
        (void)is_big;
        for (std::size_t visited = 0; visited < bytes;) {
            const u64 pos = address + visited;
            const auto page = static_cast<std::size_t>(pos >> 12);
            const auto offset = static_cast<std::size_t>(pos & 4095);
            const auto chunk = std::min<std::size_t>(bytes - visited, 4096 - offset);
            if (page >= mapped.size()) {
                if (on_reserved(page, offset, chunk)) break;
            } else if (!mapped[page]) {
                if (on_unmap(page, offset, chunk)) break;
            } else if (on_map(page, offset, chunk)) {
                break;
            }
            visited += chunk;
        }
    }
    std::size_t MaxContinuousRange(GPUVAddr address, std::size_t bytes) const;
};
__EXTRACTED_RANGE__
} // namespace Tegra
int main() {
    using Tegra::MemoryManager;
    MemoryManager a{4};
    a.mapped[0] = a.mapped[1] = true;
    a.big_page_table_dev[0] = 0x30;
    a.big_page_table_dev[1] = 0x31;
    assert(a.MaxContinuousRange(0, 8192) == 8192);
    assert(a.page_walks == 1);
    // The second native SSBO bind must not rewalk 2 x 4 KiB PTEs.
    assert(a.MaxContinuousRange(0, 8192) == 8192 && a.page_walks == 1);
    // A device backing remap must invalidate the old contiguous answer.
    a.big_page_table_dev[1] = 0x91;
    Tegra::gpu_page_table_revision.fetch_add(1, std::memory_order_release);
    assert(a.MaxContinuousRange(0, 8192) == 4096 && a.page_walks == 2);
    assert(a.MaxContinuousRange(0, 8192) == 4096 && a.page_walks == 2);
    a.big_page_table_dev[1] = 0x31;
    Tegra::gpu_page_table_revision.fetch_add(1, std::memory_order_release);
    assert(a.MaxContinuousRange(0, 8192) == 8192 && a.page_walks == 3);

    // Two guests with equal GPU addresses cannot share physical backing.
    MemoryManager b{5};
    b.mapped[0] = b.mapped[1] = true;
    b.big_page_table_dev[0] = 0x20;
    b.big_page_table_dev[1] = 0x91;
    assert(b.MaxContinuousRange(0, 8192) == 4096 && b.page_walks == 1);
    assert(b.MaxContinuousRange(0, 8192) == 4096 && b.page_walks == 1);
    assert(a.MaxContinuousRange(0, 8192) == 8192 && a.page_walks == 4);

    // A freed GPU page must produce zero contiguous backing, never stale bytes.
    a.mapped[0] = false;
    Tegra::gpu_page_table_revision.fetch_add(1, std::memory_order_release);
    const auto before_unmap = a.page_walks;
    assert(a.MaxContinuousRange(0, 8192) == 0 && a.page_walks > before_unmap);
    // The unmap path itself walks both big and short PTE tiers; its exact
    // number of nested operations is irrelevant to cache correctness.
    const auto after_unmap = a.page_walks;
    assert(a.MaxContinuousRange(0, 8192) == 0 && a.page_walks == after_unmap);
    a.mapped[0] = true;
    a.big_page_table_dev[0] = 0x30;
    Tegra::gpu_page_table_revision.fetch_add(1, std::memory_order_release);
    assert(a.MaxContinuousRange(0, 8192) == 8192 &&
           a.page_walks == after_unmap + 1);
    // A map mutation in a different guest also invalidates cache entries.
    b.big_page_table_dev[1] = 0x21;
    Tegra::gpu_page_table_revision.fetch_add(1, std::memory_order_release);
    assert(a.MaxContinuousRange(0, 8192) == 8192 &&
           a.page_walks == after_unmap + 2);
    assert(b.MaxContinuousRange(0, 8192) == 8192);
    std::puts("P1_2_SHARED_GPU_CONTIGUOUS_RANGE_CACHE_PASS");
}
"""
fixture = fixture.replace("__EXTRACTED_RANGE__", start + actual_range_function)
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
env = os.environ.copy()
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
compilers = list(dict.fromkeys(filter(None,
    (shutil.which("clang++"), shutil.which("g++")))))
assert compilers, "No real host C++20 compiler"
with tempfile.TemporaryDirectory(prefix="eden-contiguous-range-") as temp:
    cpp = Path(temp) / "range.cpp"
    cpp.write_text(fixture)
    for compiler in compilers:
        for optimization in ("-O0", "-O2"):
            binary = Path(temp) / (Path(compiler).name.replace("+", "p") + optimization)
            built = subprocess.run(
                [compiler, "-std=c++20", optimization, "-Wall", "-Wextra",
                 "-Werror", "-Wno-unused-parameter", "-fsanitize=undefined",
                 "-fno-sanitize-recover=all",
                 str(cpp), "-o", str(binary)],
                text=True, capture_output=True, timeout=60, env=env)
            assert built.returncode == 0, (compiler, built.stderr[-3200:])
            ran = subprocess.run([str(binary)], text=True, capture_output=True,
                                 timeout=15, env=env)
            assert ran.returncode == 0, (compiler, ran.stderr[-3200:])
            assert "P1_2_SHARED_GPU_CONTIGUOUS_RANGE_CACHE_PASS" in ran.stdout
            print("P1_2_GPU_RANGE_CACHE_SOURCE_PASS", Path(compiler).name,
                  optimization, "NS1+NS2=unchanged VA mapping", flush=True)
