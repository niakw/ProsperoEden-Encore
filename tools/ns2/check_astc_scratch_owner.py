#!/usr/bin/env python3
"""N54 exact maintained vendor scratch and source-extracted frame trim."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/"vendor/encore-active/ns2-astc/include"
SCRATCH=OWNER/"common/scratch_buffer.h"
TEXTURE=OWNER/"video_core/texture_cache/texture_cache.h"
BASE_SCRATCH=ROOT/"vendor/sources/eden/src/common/scratch_buffer.h"
BASE_TEXTURE=ROOT/"vendor/encore-active/eden-backports/src/video_core/texture_cache/texture_cache.h"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
def once(src,old,new):
    assert src.count(old)==1, "maintained source owner drift: "+old[:70]
    return src.replace(old,new)
s=BASE_SCRATCH.read_text()
s=once(s,"    void swap(ScratchBuffer& other) noexcept {",
'''    // Drop oversized transient CPU staging storage without retaining capacity.
    void release() noexcept {
        buffer.reset();
        buffer_capacity = 0;
        last_requested_size = 0;
    }

    void swap(ScratchBuffer& other) noexcept {''')
s=once(s,"            std::memcpy(new_buffer.get(), buffer.get(), buffer_capacity * sizeof(T));",
'''            if (buffer_capacity != 0) {
                std::memcpy(new_buffer.get(), buffer.get(), buffer_capacity * sizeof(T));
            }''')
t=BASE_TEXTURE.read_text()
t=once(t,"void TextureCache<P>::TickFrame() {",
'''void TextureCache<P>::TickFrame() {
    // Release only oversized transient CPU scratch at the next frame boundary.
    // The normal <= 64 MiB cached working set and GPU residency are unchanged.
    static constexpr size_t N54ScratchTrimThreshold = size_t{64} << 20;
    for (auto* const scratch : {&swizzle_data_buffer, &unswizzle_data_buffer}) {
        if (scratch->capacity() > N54ScratchTrimThreshold) {
            scratch->release();
        }
    }''')
assert 'EDEN_NS2_ASTC_SCRATCH_RELEASE_EXPERIMENTAL OR' in CMAKE
assert 'target_include_directories(common BEFORE PUBLIC "${EDEN_NS2_ASTC_OWNER_ROOT}")' in CMAKE
assert 'target_include_directories(video_core BEFORE PUBLIC "${EDEN_NS2_ASTC_OWNER_ROOT}")' in CMAKE
assert 'prepare_astc_scratch_owner.cmake' not in CMAKE
assert 'eden_ns2_scratch_generated' not in CMAKE
assert SCRATCH.read_text()==s, 'N54 scratch differs from pinned base + exact fix'
# N60 extends the same vendor texture header under a strict opt-in macro.
# N60's companion checker pins the full source bytes and fallback ownership.
assert 'N54ScratchTrimThreshold' in TEXTURE.read_text()
assert '#ifdef EDEN_NS2_ASTC_SCRATCH_TRIM' in TEXTURE.read_text()
assert 'EDEN_NS2_ASTC_SCRATCH_TRIM=1' in CMAKE
with tempfile.TemporaryDirectory(prefix="n54-vendor-owner-") as td:
    out=Path(td)
    marker="void TextureCache<P>::TickFrame() {"
    after=TEXTURE.read_text().split(marker)[1]
    extraction=after[:after.index("    // If we can obtain the memory info")]
    assert extraction.count("scratch->release();")==1
    cpp=('''#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "common/scratch_buffer.h"
using u8=std::uint8_t;
struct Cache {
    Common::ScratchBuffer<u8> swizzle_data_buffer;
    Common::ScratchBuffer<u8> unswizzle_data_buffer;
    void TickFrame() {
'''+extraction+'''
    }
};
int main() {
    Cache cache;
    cache.swizzle_data_buffer.resize_destructive((64u<<20)+4096);
    cache.unswizzle_data_buffer.resize_destructive(4096);
    assert(cache.swizzle_data_buffer.capacity()>(64u<<20));
    cache.TickFrame();
    assert(cache.swizzle_data_buffer.capacity()==0);
    assert(cache.swizzle_data_buffer.size()==0);
    assert(cache.unswizzle_data_buffer.capacity()==4096);
    cache.swizzle_data_buffer.resize_destructive(2048);
    cache.swizzle_data_buffer[0]=123;
    cache.swizzle_data_buffer.resize(4096);
    assert(cache.swizzle_data_buffer[0]==123);
    cache.swizzle_data_buffer.release();
    cache.swizzle_data_buffer.resize(8);
    cache.swizzle_data_buffer[0]=42;
    assert(cache.swizzle_data_buffer[0]==42);
    Cache small;
    small.swizzle_data_buffer.resize_destructive(64u<<20);
    small.TickFrame();
    assert(small.swizzle_data_buffer.capacity()==(64u<<20));
}
''')
    (out/"test.cpp").write_text(cpp)
    for cxx in ("clang++","g++"):
        exe=out/("n54-"+cxx.replace("+","p"))
        subprocess.run([cxx,"-std=c++20","-O1","-Wall","-Wextra","-Werror",
            "-fsanitize=address,undefined","-fno-sanitize-recover=all",
            "-DEDEN_NS2_ASTC_SCRATCH_TRIM=1",
            "-I",str(OWNER),"-I",str(ROOT/"vendor/sources/eden/src"),
            str(out/"test.cpp"),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N54_VENDOR_SOURCE_EXTRACTED_LIFECYCLE_PASS")
