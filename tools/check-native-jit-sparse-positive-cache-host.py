#!/usr/bin/env python3
"""Source-linked host regression for the PS5 sparse JIT positive commit memo.

The production function remains compiled end-to-end by check-jit-sparse-host.py.
This witness compiles the exact cache header and checks interleaved arenas,
growth, MRU eviction, and generation invalidation; no console FPS claim.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "src/memory_pages.cpp").read_text()
assert '#include "jit-sparse-commit.h"' in source
assert "static thread_local ::Eden::Jit::SparseCommitPositiveCache local;" in source
assert "local.Covers(executable, required, generation)" in source
assert "local.Remember(executable, region.committed," in source
assert "sparse_jit_generation.fetch_add(1, std::memory_order_acq_rel);" in source
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
FIXTURE = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include "jit-sparse-commit.h"
int main() {
    Eden::Jit::SparseCommitPositiveCache cache;
    void* arenas[5] = {
        reinterpret_cast<void*>(0x10000000ULL),
        reinterpret_cast<void*>(0x14000000ULL),
        reinterpret_cast<void*>(0x18000000ULL),
        reinterpret_cast<void*>(0x1c000000ULL),
        reinterpret_cast<void*>(0x20000000ULL)};
    constexpr std::size_t committed = 4 * 1024 * 1024;
    for (auto* arena : arenas) assert(!cache.Covers(arena, committed, 7));
    for (unsigned i = 0; i < 4; ++i) cache.Remember(arenas[i], committed, 7);
    std::size_t misses = 0;
    for (unsigned i = 0; i < 100000; ++i)
        if (!cache.Covers(arenas[i % 4], committed, 7)) ++misses;
    assert(misses == 0);
    assert(!cache.Covers(arenas[2], committed + 1, 7));
    cache.Remember(arenas[2], committed * 2, 7);
    assert(cache.Covers(arenas[2], committed * 2, 7));
    assert(cache.Covers(arenas[0], committed, 7));
    cache.Remember(arenas[4], committed, 7);
    assert(!cache.Covers(arenas[1], committed, 7)); // LRU evicted
    assert(!cache.Covers(arenas[4], committed, 8)); // trim/release epoch
    assert(!cache.Covers(arenas[2], committed, 8));
    cache.Remember(arenas[4], committed, 8);
    assert(cache.Covers(arenas[4], committed, 8));
    assert(!cache.Covers(arenas[4], committed, 9)); // recycled VA
    std::printf("SPARSE_JIT_POSITIVE_CACHE_PASS alternating_misses=%zu epochs=1 growth=1 eviction=1\n", misses);
}
"""
with tempfile.TemporaryDirectory(prefix="eden-sparse-jit-mru-") as tmp:
    path = Path(tmp)
    (path / "test.cpp").write_text(FIXTURE)
    for opt in (0, 2):
        exe = path / f"test-O{opt}"
        subprocess.run([compiler, "-std=c++20", f"-O{opt}", "-Wall", "-Wextra",
                        "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        "-I", str(ROOT / "headless"), str(path / "test.cpp"),
                        "-o", str(exe)], check=True, timeout=90)
        subprocess.run([str(exe)], check=True, timeout=90)
print("SPARSE_JIT_POSITIVE_CACHE_HOST_PASS O0=1 O2=1 source_linked=1")
