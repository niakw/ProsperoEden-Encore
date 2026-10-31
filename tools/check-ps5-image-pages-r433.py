#!/usr/bin/env python3
"""R433: host-sanitized proof of monotonic texture-page lock-elision boundaries."""
import ast
from pathlib import Path
import shutil
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
header = (root / "headless/image_pages.h").read_text()
raster = (root / "vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
cache = (root / "vendor/encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h").read_text()
generator = (root / "tools/prepare-vulkan-port.py").read_text()
ast.parse(generator)
assert raster.count("::Eden::ImagePages::NeverHeld(addr, size)") == 9
write_start = raster.index("bool RasterizerVulkan::OnCPUWrite")
write_end = raster.index("void RasterizerVulkan::OnCacheInvalidation", write_start)
write_method = raster[write_start:write_end]
assert write_method.count("::Eden::ImagePages::NeverHeld(addr, size)") == 1
assert write_method.index("::Eden::BufferPages::NeverRegistered") < write_method.index(
    "::Eden::ImagePages::NeverHeld")
assert write_method.index("::Eden::ImagePages::NeverHeld") < write_method.index(
    "::Eden::Performance::GuestCacheLock(texture_cache.mutex, true)")
assert write_method.index("texture_cache.WriteMemory(addr, size)") < write_method.index(
    "pipeline_cache.InvalidateRegion(addr, size)")
assert write_method.count("pipeline_cache.InvalidateRegion(addr, size)") == 1
assert raster.index("::Eden::ImagePages::NeverHeld(addr, size)") < raster.index(
    "::Eden::Performance::GuestCacheLock(texture_cache.mutex, true)",
    raster.index("RasterizerVulkan::GetFlushArea"))
assert cache.count("::Eden::ImagePages::Mark(image.cpu_addr, image.guest_size_bytes);") == 1
assert cache.count("::Eden::ImagePages::Mark(cpu_addr, size);") == 1
assert cache.index("::Eden::ImagePages::Mark(image.cpu_addr") < cache.index(
    "slot_map_views.insert(image.gpu_addr")
assert cache.index("::Eden::ImagePages::Mark(cpu_addr, size);") < cache.index(
    "slot_map_views.insert(gpu_addr, cpu_addr")
assert "ImagePages::NeverHeld" in generator and generator.count("ImagePages::Mark(") == 2
assert "memory_order_acquire" in header and "memory_order_release" in header
assert 'const auto word = page / 64;' in header
assert 'const auto bit = std::uint64_t{1} << (page % 64);' in header
assert 'held[word].fetch_or(bit, std::memory_order_release);' in header
mark_body = header.split('inline void Mark(',1)[1].split('inline bool NeverHeld(',1)[0]
assert 'if (first_word == last_word) {' in mark_body
assert 'held[first_word].fetch_or(bits, std::memory_order_release);' in mark_body
assert 'const auto last = ((std::min)(size, kSpace - address) + address - 1) >> kPageBits;' in header
assert "size > 256 * 1024" in header
assert 'if (size <= (std::uint64_t{1} << kPageBits) - (address & page_mask)) {' in header
assert 'const auto page = address >> kPageBits;' in header
assert 'held[page / 64].load(std::memory_order_acquire)' in header
never_held = header[header.index('inline bool NeverHeld('):]
assert never_held.index('if (size > 256 * 1024) return false;') < never_held.index(
    'const auto page = address >> kPageBits;')
cxx = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
assert cxx
fixture = r"""
#include "image_pages.h"
#include <cassert>
#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>
using namespace Eden::ImagePages;
int main() {
  constexpr std::uint64_t p=4096;
  assert(NeverHeld(0,1) && NeverHeld(kSpace-1,1) && NeverHeld(123456789,64*p));
  assert(!NeverHeld(kSpace,1) && !NeverHeld(kSpace-1,2));
  assert(!NeverHeld(0,256*1024+1));
  Mark(p,1);
  assert(NeverHeld(p-1,1) && !NeverHeld(p,1) && !NeverHeld(2*p-1,1));
  assert(NeverHeld(2*p,1) && !NeverHeld(p-1,2));
  Mark(63*p+5,2*p);
  assert(!NeverHeld(63*p,1) && !NeverHeld(64*p,1) && !NeverHeld(65*p,1));
  assert(NeverHeld(66*p,p));
  Mark(1000*p,9000*p);
  assert(!NeverHeld(1000*p,1) && !NeverHeld(5000*p,1));
  assert(NeverHeld(10000*p,p));
  Mark(kSpace-1,1<<20);
  assert(!NeverHeld(kSpace-1,1) && !NeverHeld(kSpace-1,2));
  // Single-page fast publication, crossing a 64-bit word, and unaligned
  // two-page fallthrough must agree with the complete monotonic bitmap.
  Mark(14000*p+17,1);
  assert(!NeverHeld(14000*p,1) && NeverHeld(14001*p,1));
  Mark(14079*p+4095,2);
  assert(!NeverHeld(14079*p,1) && !NeverHeld(14080*p,1));
  // A seven-page unaligned image registration fits in one bitmap word,
  // whereas a similar one at the boundary takes the existing two-word path.
  Mark(18000*p+4000,6*p);
  assert(!NeverHeld(18000*p,1) && !NeverHeld(18006*p,1));
  assert(NeverHeld(18007*p,1));
  Mark(18047*p+4095,2*p);
  assert(!NeverHeld(18047*p,1) && !NeverHeld(18048*p,1));
  assert(!NeverHeld(18049*p,1) && NeverHeld(18050*p,1));
  // Simultaneous insertions of distinct bits in one word cannot be lost
  // by the load-before-fetch_or optimization.
  std::vector<std::thread> overlapped;
  for(unsigned t=0;t<8;++t) overlapped.emplace_back([t]{
    for(unsigned n=0;n<500;++n) {
      Mark((16000+t)*p,1);
      Mark(16000*p,8*p);
    }
  });
  for(auto& thread:overlapped) thread.join();
  for(unsigned t=0;t<8;++t) assert(!NeverHeld((16000+t)*p,1));
  assert(NeverHeld(16008*p,1));
  // Independent page-by-page baseline across all byte offsets, word
  // boundaries, empty spans, oversized ranges and partial ownership.
  // A false "never held" could suppress texture invalidation and leave
  // the guest HUD permanently stale.
  auto baseline = [](std::uint64_t address, std::uint64_t size) {
    if (!size) size = 1;
    if (address >= kSpace || size > kSpace-address || size > 256*1024) return false;
    const auto first = address >> kPageBits;
    const auto last = (address+size-1) >> kPageBits;
    for (auto page = first; page <= last; ++page)
      if ((held[page/64].load(std::memory_order_acquire) >> (page%64)) & 1u)
        return false;
    return true;
  };
  std::uint64_t rng = 0xa1c2b3d4f0012283ull;
  constexpr std::uint64_t lengths[]{0,1,2,17,4095,4096,4097,8193,65536,262144,262145};
  for (int i = 0; i < 12000; ++i) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    const auto address = i%3 == 0 ? rng % (4096ull*12000) :
                         i%3 == 1 ? kSpace - 1 - rng % 10000 : rng % kSpace;
    const auto size = lengths[i%11];
    assert(NeverHeld(address,size) == baseline(address,size));
  }
  assert(NeverHeld(4095,2) == baseline(4095,2));
  assert(NeverHeld(63*p+4095,2) == baseline(63*p+4095,2));
  std::vector<std::thread> threads;
  std::atomic<unsigned> misses{0};
  for(unsigned i=0;i<8;++i) threads.emplace_back([i,&misses] {
    auto base=(1000000u+i*1000u)*4096ull;
    for(unsigned n=0;n<800;++n) {
      Mark(base+n*4096,p);
      if(NeverHeld(base+n*4096,1)) ++misses;
    }
  });
  for(auto& thread:threads) thread.join();
  assert(misses.load()==0);
  for(unsigned i=0;i<8;++i) {
    auto base=(1000000u+i*1000u)*4096ull;
    assert(!NeverHeld(base+799*p,1) && NeverHeld(base+800*p,1));
  }
}
"""
with tempfile.TemporaryDirectory(prefix="eden-r433-image-pages-") as tmp:
    source = Path(tmp) / "test.cpp"
    exe = Path(tmp) / "test"
    source.write_text(fixture)
    subprocess.run([cxx, "-std=c++20", "-O1", "-pthread",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                    "-Wall", "-Wextra", "-Werror", "-I" + str(root / "headless"),
                    str(source), "-o", str(exe)], check=True, timeout=90)
    subprocess.run([str(exe)], check=True, timeout=90)
print("PASS R433: registered pages never fast-skipped; bounded scanning, concurrent marking, source replay guards")
