#!/usr/bin/env python3
"""Generate N54 from exact maintained owners and reject any unrelated drift."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SCRATCH=ROOT/"vendor/sources/eden/src/common/scratch_buffer.h"
TEXTURE=ROOT/"vendor/sources/eden/src/video_core/texture_cache/texture_cache.h"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
def once(src,old,new):
    assert src.count(old)==1, "maintained source owner drift: "+old[:70]
    return src.replace(old,new)
s=SCRATCH.read_text()
s=once(s,"    void swap(ScratchBuffer& other) noexcept {",
'''    // N54: discard an oversized transient scratch allocation between frames.
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
t=TEXTURE.read_text()
t=once(t,"void TextureCache<P>::TickFrame() {",
'''void TextureCache<P>::TickFrame() {
    // N54: transient ASTC/unswizzle scratch must not remain resident after
    // a huge layered image. CPU scratch is no longer in use at frame start.
    static constexpr size_t N54ScratchTrimThreshold = size_t{64} << 20;
    for (auto* const scratch : {&swizzle_data_buffer, &unswizzle_data_buffer}) {
        if (scratch->capacity() > N54ScratchTrimThreshold) {
            scratch->release();
        }
    }''')
assert 'EDEN_NS2_ASTC_SCRATCH_RELEASE_EXPERIMENTAL OR' in CMAKE
assert 'target_include_directories(common BEFORE PUBLIC "${eden_ns2_scratch_generated}")' in CMAKE
assert 'target_include_directories(video_core BEFORE PUBLIC "${eden_ns2_scratch_generated}")' in CMAKE
with tempfile.TemporaryDirectory(prefix="n54-owner-") as td:
    out=Path(td)
    subprocess.run(["cmake","-DSCRATCH_INPUT="+str(SCRATCH),"-DTEXTURE_INPUT="+str(TEXTURE),
       "-DOUTPUT_DIR="+str(out),"-P",str(ROOT/"tools/ns2/prepare_astc_scratch_owner.cmake")],check=True)
    assert (out/"common/scratch_buffer.h").read_text()==s
    assert (out/"video_core/texture_cache/texture_cache.h").read_text()==t
    marker="void TextureCache<P>::TickFrame() {"
    after=t.split(marker)[1]
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
            "-I",str(out),"-I",str(ROOT/"vendor/sources/eden/src"),
            str(out/"test.cpp"),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N54_ASTC_SCRATCH_OWNER_AND_SOURCE_EXTRACTED_LIFECYCLE_PASS")
