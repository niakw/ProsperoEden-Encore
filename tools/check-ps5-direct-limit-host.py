#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile source-extracted PS5 direct extent cache against concurrent host mocks.

NOT a firmware test: exercises the real C++ helper and its positive-only
atomic cache on a Linux runner during the explicit next-build source gates.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
s = (root / "src/memory_pages.cpp").read_text()
begin = s.index("namespace {\n// This is the fixed addressable direct-memory EXTENT")
# The original anonymous namespace also contains the independent CPU VA
# reservation wrapper, which needs native mapping mocks from another harness.
# Extract only the direct-extent cache and allocator exercised here.
reservation_begin = s.index("void* ReserveCpuVirtualRange(", begin)
# The native fault receipt's C ABI now follows the anonymous namespace.
# Extract its real implementation too: the old "} // namespace\\n#endif"
# adjacency disappeared when the durable error snapshot was added.
namespace_end = s.index("} // namespace\n", reservation_begin)
receipt_begin = s.index('extern "C" std::uint64_t eden_ps5_direct_failure_snapshot(', namespace_end)
native_guard_end = s.index("\n#endif", receipt_begin)
assert reservation_begin < namespace_end < receipt_begin < native_guard_end
helper = (s[begin:reservation_begin] + "} // namespace\n" +
          s[receipt_begin:native_guard_end] + "\n")
assert helper.count("sceKernelGetDirectMemorySize()") == 1
assert "cached_direct_memory_extent.store(current, std::memory_order_release)" in helper
assert "return extent > 0 ? sceKernelAllocateDirectMemory(" in helper
compiler = next((x for x in ("clang++-18", "clang++", "g++") if shutil.which(x)), None)
if not compiler:
    raise SystemExit("C++20 compiler required for direct-memory extent host gate")

head = r"""
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <thread>
#include <vector>

static std::atomic<unsigned> extent_queries{};
static std::atomic<unsigned> issued_allocations{};
static std::atomic<bool> fail_first{true};
static std::int64_t sceKernelGetDirectMemorySize() {
    extent_queries.fetch_add(1);
    return fail_first.exchange(false) ? -1 : (std::int64_t{12} << 30);
}
static std::int32_t sceKernelAllocateDirectMemory(
    std::int64_t begin, std::int64_t limit, std::size_t bytes,
    std::size_t alignment, int type, std::int64_t* physical) {
    assert(begin == 0 && limit == (std::int64_t{12} << 30));
    assert(bytes == 2u * 1024 * 1024 && alignment == bytes && type == 12);
    assert(physical);
    *physical = 0x12000;
    issued_allocations.fetch_add(1);
    return 0;
}
"""
tail = r"""
int main() {
    std::int64_t physical = -1;
    // An unknown/negative kernel response must not call the physical alloc.
    assert(AllocateDirectOwned(2u << 20, 2u << 20, &physical) != 0);
    assert(extent_queries.load() == 1 && issued_allocations.load() == 0);
    assert(AllocateDirectOwned(2u << 20, 2u << 20, &physical) == 0);
    assert(extent_queries.load() == 2 && issued_allocations.load() == 1);
    // The actual native fault snapshot remains available after the extra
    // C ABI definition; otherwise this host gate would miss receipt drift.
    std::uint64_t failed_bytes = 0, failed_extent = 0;
    std::uint32_t failed_result = 0, failed_stage = 0;
    assert(eden_ps5_direct_failure_snapshot(
        &failed_bytes, &failed_extent, &failed_result, &failed_stage) == 0);
    NoteDirectAllocationFailure(1, 0x80020023u, 4u << 20, std::uint64_t{12} << 30);
    assert(eden_ps5_direct_failure_snapshot(
        &failed_bytes, &failed_extent, &failed_result, &failed_stage) == 1);
    assert(failed_stage == 1 && failed_result == 0x80020023u);
    assert(failed_bytes == (4u << 20) && failed_extent == (std::uint64_t{12} << 30));
    NoteDirectAllocationFailure(2, 0x80020024u, 8u << 20, std::uint64_t{12} << 30);
    assert(eden_ps5_direct_failure_snapshot(
        &failed_bytes, &failed_extent, &failed_result, &failed_stage) == 2);
    assert(failed_stage == 2 && failed_result == 0x80020024u);
    assert(failed_bytes == (8u << 20) && failed_extent == (std::uint64_t{12} << 30));
    std::vector<std::thread> threads;
    for (unsigned i = 0; i < 8; ++i)
        threads.emplace_back([] {
            for (unsigned j = 0; j < 20000; ++j) {
                std::int64_t owned = -1;
                assert(AllocateDirectOwned(2u << 20, 2u << 20, &owned) == 0);
                assert(owned == 0x12000);
            }
        });
    for (auto& thread : threads) thread.join();
    assert(extent_queries.load() == 2);
    assert(issued_allocations.load() == 1 + 8 * 20000u);
}
"""
with tempfile.TemporaryDirectory(prefix="eden-dmem-extent-") as tmp:
    folder = Path(tmp)
    src, exe = folder / "extent.cpp", folder / "extent"
    src.write_text(head + helper + tail)
    subprocess.run([compiler, "-std=c++20", "-O2", "-pthread", "-Wall", "-Wextra",
                    "-Werror", str(src), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print("PASS: real direct-memory extent cache retries initial error and reuses one positive result across 8 threads")
print("Firmware native direct-memory allocation and frame-time effect remain UNTESTED")
