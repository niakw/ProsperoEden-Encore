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
cache_header = (ROOT / "headless/jit-sparse-commit.h").read_text()
assert "if (!entries[i].executable) return false;" in cache_header
assert "if (entries[0].executable == executable) {" in cache_header
assert "return required <= entries[0].committed;" in cache_header
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
FIXTURE = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <new>
#include <sys/mman.h>
#include <unistd.h>
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
    // The most frequent single-core hit is strictly read-only. Catch a
    // redundant self-promotion store even at -O0 by protecting the page.
    const long page_size = sysconf(_SC_PAGESIZE);
    assert(page_size > 0 && static_cast<std::size_t>(page_size) >= sizeof(cache));
    void* page = mmap(nullptr, static_cast<std::size_t>(page_size),
                      PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    assert(page != MAP_FAILED);
    auto* readonly = new (page) Eden::Jit::SparseCommitPositiveCache{};
    readonly->Remember(arenas[0], committed, 7);
    assert(mprotect(page, static_cast<std::size_t>(page_size), PROT_READ) == 0);
    for (unsigned i = 0; i < 1000; ++i) {
        assert(readonly->Covers(arenas[0], committed, 7));
        // A cold/missing arena must short-circuit at the vacant second slot
        // without modifying a partially populated read-only cache.
        assert(!readonly->Covers(arenas[1], committed, 7));
        assert(!readonly->Covers(arenas[0], committed + 1, 7));
    }
    assert(mprotect(page, static_cast<std::size_t>(page_size), PROT_READ | PROT_WRITE) == 0);
    readonly->~SparseCommitPositiveCache();
    assert(munmap(page, static_cast<std::size_t>(page_size)) == 0);
    assert(!cache.Covers(arenas[2], committed + 1, 7));
    cache.Remember(arenas[2], committed * 2, 7);
    assert(cache.Covers(arenas[2], committed * 2, 7));
    assert(!cache.Covers(arenas[2], committed * 2 + 1, 7));
    // A later physical commit refreshes the same arena in-place.
    cache.Remember(arenas[2], committed * 4, 7);
    assert(cache.Covers(arenas[2], committed * 4, 7));
    assert(cache.Covers(arenas[0], committed, 7));
    cache.Remember(arenas[4], committed, 7);
    assert(!cache.Covers(arenas[1], committed, 7)); // LRU evicted
    assert(!cache.Covers(arenas[4], committed, 8)); // trim/release epoch
    assert(!cache.Covers(arenas[2], committed, 8));
    cache.Remember(arenas[4], committed, 8);
    assert(cache.Covers(arenas[4], committed, 8));
    assert(!cache.Covers(arenas[4], committed, 9)); // recycled VA
    // Two active slots after an epoch reset retain MRU order while all
    // negative lookups exit on the first never-populated entry.
    Eden::Jit::SparseCommitPositiveCache partial;
    partial.Remember(arenas[0], committed, 20);
    partial.Remember(arenas[1], committed, 20);
    assert(!partial.Covers(arenas[4], committed, 20));
    assert(partial.Covers(arenas[0], committed, 20));
    assert(partial.Covers(arenas[1], committed, 20));
    assert(!partial.Covers(arenas[2], committed, 21));
    std::printf("SPARSE_JIT_POSITIVE_CACHE_PASS alternating_misses=%zu epochs=1 growth=1 eviction=1 readonly_hit=1 cold_miss=1\n", misses);
}
"""
with tempfile.TemporaryDirectory(prefix="eden-sparse-jit-mru-") as tmp:
    path = Path(tmp)
    (path / "test.cpp").write_text(FIXTURE)
    for opt in (0, 2, 3):
        exe = path / f"test-O{opt}"
        subprocess.run([compiler, "-std=c++20", f"-O{opt}", "-Wall", "-Wextra",
                        "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        "-I", str(ROOT / "headless"), str(path / "test.cpp"),
                        "-o", str(exe)], check=True, timeout=90)
        subprocess.run([str(exe)], check=True, timeout=90)
print("SPARSE_JIT_POSITIVE_CACHE_HOST_PASS O0=1 O2=1 O3=1 source_linked=1")
