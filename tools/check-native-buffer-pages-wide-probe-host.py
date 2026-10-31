#!/usr/bin/env python3
"""Source-selected buffer-page bitmap guard: two-word 256 KiB guest writes."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
head = (root / "headless/buffer_pages.h").read_text()
assert "size>256*1024" in head
assert "size>64*1024" not in head
assert "const auto first_word=first/64,last_word=last/64;" in head
assert "registered[first_word].load(std::memory_order_acquire)&first_mask" in head
assert "registered[last_word].load(std::memory_order_acquire)&Bits(0,last%64)" in head
assert "coverage_unknown.load(std::memory_order_acquire)" in head
assert "if(first_word==last_word){" in head.split("inline void Mark(",1)[1].split("inline bool NeverRegistered(",1)[0]
assert "registered[first_word].fetch_or(mask,std::memory_order_release)" in head
probe = head.split("inline bool NeverRegistered(", 1)[1]
assert probe.count("coverage_unknown.load(std::memory_order_acquire)") == 2
assert "if(coverage_unknown.load(std::memory_order_acquire))" not in probe
assert probe.count("return !coverage_unknown.load(std::memory_order_acquire);") == 2

code = r"""
#include "buffer_pages.h"
#include <cassert>
#include <cstdint>
int main() {
    using namespace Eden::BufferPages;
    constexpr std::uint64_t page = 4096;
    constexpr std::uint64_t span = 256 * 1024;
    // A 256 KiB unaligned query can cross a 64-page bitmap word boundary,
    // but may only cover two words. No owner means lock elision is valid.
    constexpr std::uint64_t cross = 63 * page + 17;
    assert(NeverRegistered(cross, span));
    assert(NeverRegistered(cross, 64 * 1024 + 1));
    // The immediately preceding byte is NOT part of the query.
    Mark(cross - page, 1);
    assert(NeverRegistered(cross, span));
    // A newly registered interior page must disable lock elision.
    Mark(64 * page + 48, 1);
    assert(!NeverRegistered(cross, span));
    // Unrelated ranges must keep the fast path.
    constexpr std::uint64_t empty = 512 * page + 29;
    assert(NeverRegistered(empty, span));
    Mark(empty + span - 1, 1);
    assert(!NeverRegistered(empty, span));
    assert(NeverRegistered(empty + span + page, 64 * 1024));
    // Check a near-maximum query whose final page is across the word split.
    constexpr std::uint64_t shifted = 1023 * page + 2;
    assert(NeverRegistered(shifted, span));
    Mark(shifted + span - 1, 1);
    assert(!NeverRegistered(shifted, span));
    // The byte just beyond an unaligned query can still occupy the same
    // registered page. Only the NEXT entirely different page is unowned.
    constexpr std::uint64_t next_full_page = ((shifted + span + page - 1) / page) * page;
    assert(NeverRegistered(next_full_page, page));
    // A seven-page buffer in one bitmap word must mark its full mask.
    // The next word remains empty and eligible for skipping the cache lock.
    constexpr std::uint64_t within = 2048 * page + 9;
    Mark(within, 7 * page);
    assert(!NeverRegistered(within, 7 * page));
    assert(!NeverRegistered(within + 6 * page, 1));
    assert(NeverRegistered(within + 8 * page, 1));
    // An unaligned mark straddling the word edge remains fully registered.
    constexpr std::uint64_t edge = 3071 * page + 19;
    Mark(edge, 2 * page);
    assert(!NeverRegistered(3071 * page, 1));
    assert(!NeverRegistered(3072 * page, 1));
    assert(!NeverRegistered(3073 * page, 1));
    assert(NeverRegistered(3074 * page, 1));
    // Larger requests preserve the old conservative locking behavior.
    assert(!NeverRegistered(empty + 20 * span, span + 1));
    assert(!NeverRegistered(empty + 20 * span, 0));
    assert(!NeverRegistered(kSpace - 4096, 8192));
    assert(!NeverRegistered(kSpace, 1));
    assert(!coverage_unknown.load(std::memory_order_acquire));
    // Unknown global coverage is still a strict fail-closed fence. Both
    // one-page and 65-page unowned probes must now take the cache lock.
    Mark(kSpace + 1, 1);
    assert(coverage_unknown.load(std::memory_order_acquire));
    assert(!NeverRegistered(empty + 20 * span, 1));
    assert(!NeverRegistered(empty + 20 * span, span));
}
"""
compiler=shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-buffer-probe-") as folder:
    path=Path(folder)/"probe.cpp"
    path.write_text(code)
    for mode in ("-O0", "-O2"):
        exe=Path(folder)/("probe"+mode)
        subprocess.run([compiler,"-std=c++20",mode,"-Wall","-Wextra","-Werror",
                        "-fsanitize=undefined", "-I"+str(root/"headless"),
                        str(path),"-o",str(exe)],check=True,timeout=40)
        subprocess.run([str(exe)],check=True,timeout=20)
        print("BUFFER_PAGES_WIDE_PROBE_HOST_PASS",mode)
