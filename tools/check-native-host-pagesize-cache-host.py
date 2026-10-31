#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Source-extracted process-page-size cache, host-only; not PS5 FPS evidence."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "src/memory_pages.cpp").read_text()
start = "long CachedHostPageSize() noexcept {"
assert source.count(start) == 1
begin = source.index(start)
end = source.index("\n}\n", begin) + len("\n}")
helper = source[begin:end]
assert source.count("sysconf(_SC_PAGESIZE)") == 1
assert source.count("const long page = CachedHostPageSize();") == 8
assert "positive_page.load(std::memory_order_relaxed)" in helper
assert "if (current > 0)" in helper
assert "positive_page.store(current, std::memory_order_relaxed);" in helper
assert "return current;" in helper
for workflow in ("encore-core-fast-gate.yml", "encore-core-preflight.yml"):
    steps = (root / ".github/workflows" / workflow).read_text()
    assert "python3 -B tools/check-native-host-pagesize-cache-host.py" in steps

cpp = r"""
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdio>
#include <thread>
#include <vector>
constexpr int _SC_PAGESIZE = 30;
std::atomic<unsigned> queries{};
long host_sysconf(int name) {
    assert(name == _SC_PAGESIZE);
    return queries.fetch_add(1, std::memory_order_relaxed) == 0 ? -1 : 16384;
}
#define sysconf host_sysconf
namespace Common {
HELPER
}
#undef sysconf
int main() {
    assert(Common::CachedHostPageSize() == -1); // failure not cached
    assert(queries.load(std::memory_order_relaxed) == 1);
    assert(Common::CachedHostPageSize() == 16384);
    assert(queries.load(std::memory_order_relaxed) == 2);
    std::vector<std::thread> workers;
    for (unsigned i = 0; i < 8; ++i) {
        workers.emplace_back([] {
            for (unsigned n = 0; n < 20000; ++n)
                assert(Common::CachedHostPageSize() == 16384);
        });
    }
    for (auto& worker : workers) worker.join();
    assert(queries.load(std::memory_order_relaxed) == 2);
    std::puts("NATIVE_PAGE_SIZE_CACHE_PASS initial_error_retry=1 positive_reuse=160000 queries=2 concurrency=8");
}
""".replace("HELPER", helper)
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-native-page-size-") as temp:
    path = Path(temp) / "page.cpp"
    path.write_text(cpp)
    for opt in ("0", "2", "3"):
        exe = Path(temp) / ("page-O" + opt)
        subprocess.run([compiler, "-std=c++20", "-O" + opt,
                        "-Wall", "-Wextra", "-Werror", "-pthread",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        str(path), "-o", str(exe)], check=True, timeout=60)
        subprocess.run([str(exe)], check=True, timeout=30)
print("NATIVE_PAGE_SIZE_SOURCE_LINKED_PASS O0=1 O2=1 O3=1 native_PS5=unverified")
