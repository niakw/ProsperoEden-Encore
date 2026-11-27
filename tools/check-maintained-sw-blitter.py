#!/usr/bin/env python3
"""Exact selected Fermi2D blitter provenance and host UBSan/ASan geometry witness.

Only the maintained vendor C++ is compiled by the native PS5 CMake path.
The upstream/backport blobs remain historical baselines, not runtime fallbacks.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
backport = (root / "vendor/encore-active/eden/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
upstream = (root / "vendor/sources/eden/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
maintained = (root / "vendor/encore-active/eden-core/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
decoder = (root / "vendor/encore-active/eden-core/src/video_core/textures/decoders.cpp").read_text()
module = (root / "headless/gpu_native_observability.cmake").read_text()

def git_blob(data: str) -> str:
    payload = data.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()

assert upstream != backport
assert git_blob(backport) == "f014de1b85eb1667024a7b5a7162d7c6307d80f6"
assert "floor/ceil yield ordinary pixel coordinates" in backport
assert git_blob(maintained) == "d5a5436cdc2414c53834a886cdaa4578b4dc8a94", (
    "Unreviewed shipping PS5 Fermi2D software blitter; historical predecessor was "
    "2c5aaf8fe19835dc72eee40f3c9eebc17f17350b")
assert "#include <optional>" in maintained
begin = "    const auto checked_surface_size = "
end = "    const u32 src_extent_x = "
assert maintained.count(begin) == maintained.count(end) == 1
getter = maintained[maintained.index(begin):maintained.index(end, maintained.index(begin))]
for required in (
    "surface.block_height > 5 || surface.block_depth > 5",
    "static_cast<u64>(surface.width) * bytes_per_pixel",
    "(width_bytes + 63) & ~u64{63}",
    "const u64 padded_height",
    "const u64 padded_depth",
    "padded_width > MAX_BYTES / padded_height",
    "slice_bytes > MAX_BYTES / padded_depth",
    "CalculateSize(true, bytes_per_pixel",
    "!=\n            checked_bytes",
):
    assert required in getter, ("Missing checked GOB backing guard", required)
assert maintained.count("const auto src_size = checked_surface_size(src, src_bytes_per_pixel);") == 1
assert maintained.count("const auto dst_size = checked_surface_size(dst, dst_bytes_per_pixel);") == 1
assert maintained.count("if (!src_size || !dst_size)") == 1
assert maintained.count("src.Address() > ~u64{0} - *src_size") == 1
assert maintained.count("dst.Address() > ~u64{0} - *dst_size") == 1
assert "src.Address(), *src_size" in maintained
assert "dst.Address(), *dst_size" in maintained
assert "memory_manager.UsesNativeTiling(), dst.layer" in maintained
assert "src.linear == Fermi2D::MemoryLayout::BlockLinear && src.layer != 0" in maintained
assert decoder.count("u32 origin_z") >= 3
assert "depth - origin_z" in decoder
assert "return aligned_width * aligned_height * aligned_depth;" in decoder
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_NATIVE_BLITTER}")' in module
assert 'list(FILTER sw_blitter_sources EXCLUDE REGEX "engines/sw_blitter/blitter[.]cpp$")' in module

# Exercise the EXACT size-admission C++ lambda extracted from the versioned
# production TU; the stub reproduces CalculateSize's existing u32 arithmetic.
# A 256 MiB linear 2D surface with GOB depth=32 used to return ZERO backing
# bytes after 8 GiB of padded geometry wrapped modulo 2^32.
cpp = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <optional>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
struct Fermi2D {
    enum class MemoryLayout { Pitch, BlockLinear };
    struct Surface {
        MemoryLayout linear;
        u32 width, height, depth, block_height, block_depth, pitch;
    };
};
std::size_t CalculateSize(bool tiled, u32 bpp, u32 width, u32 height,
                          u32 depth, u32 bh, u32 bd) {
    if (!tiled) return width * height * depth * bpp;
    const u32 aw = ((width * bpp + 63) / 64) * 64;
    const u32 ah = ((height + (u32{8} << bh) - 1) / (u32{8} << bh)) * (u32{8} << bh);
    const u32 ad = ((depth + (u32{1} << bd) - 1) / (u32{1} << bd)) * (u32{1} << bd);
    return aw * ah * ad;
}
int main() {
__GETTER__
    using Layout = Fermi2D::MemoryLayout;
    Fermi2D::Surface valid{Layout::BlockLinear, 1920, 1080, 1, 4, 0, 0};
    assert(checked_surface_size(valid, 4) == 8847360);
    Fermi2D::Surface pitch{Layout::Pitch, 1920, 1080, 1, 0, 0, 7680};
    assert(checked_surface_size(pitch, 4) == 8294400);
    Fermi2D::Surface volume{Layout::BlockLinear, 64, 64, 32, 0, 5, 0};
    assert(checked_surface_size(volume, 4) == 524288);
    Fermi2D::Surface wrapped{Layout::BlockLinear, 8192, 8192, 1, 0, 5, 0};
    assert(CalculateSize(true, 4, 8192, 8192, 1, 0, 5) == 0);
    assert(!checked_surface_size(wrapped, 4));
    wrapped.block_depth = 6;
    assert(!checked_surface_size(wrapped, 4));
    wrapped.block_depth = 0;
    wrapped.block_height = 6;
    assert(!checked_surface_size(wrapped, 4));
    wrapped.block_height = 0;
    wrapped.width = 0;
    assert(!checked_surface_size(wrapped, 4));
    wrapped.width = 0xffffffffU;
    assert(!checked_surface_size(wrapped, 16));
    pitch.pitch = 0xffffffffU;
    assert(!checked_surface_size(pitch, 4));
}
""".replace("__GETTER__", getter)
clang = shutil.which("clang++-18") or shutil.which("clang++")
assert clang, "Host Clang required"
with tempfile.TemporaryDirectory(prefix="encore-ns1-sw-blitter-") as tmp:
    source = Path(tmp) / "blitter-gob.cpp"
    executable = Path(tmp) / "blitter-gob"
    source.write_text(cpp)
    subprocess.run([clang, "-std=c++20", "-O1", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    str(source), "-o", str(executable)], check=True, timeout=45)
    subprocess.run([str(executable)], check=True, timeout=20)
print("VENDOR_MAINTAINED_SW_BLITTER_PARITY_PASS padded_GOB_64bit=1 "
      "u32_wrap_rejected=1 pitch_valid=1 volume_valid=1 "
      "unsupported_geometry_rejected=1 native_tiling_unchanged=1 asan_ubsan=1")

# Exercise both exact nearest-neighbor paths against an integer-coordinate oracle.
nearest = maintained[maintained.index("template <typename T>\nvoid NearestNeighborRows("):maintained.index("void Bilinear(")]
nearest_cpp = r"""
#include <cassert>
#include <cstdint>
#include <cstring>
#include <span>
#include <vector>
using u8=std::uint8_t; using u32=std::uint32_t; using u64=std::uint64_t; using f32=float;
constexpr size_t ir_components=4;
""" + nearest + r"""
int main() {
    for(u32 sh=1;sh<=12;++sh) for(u32 sw=1;sw<=12;++sw)
    for(u32 dh=1;dh<=12;++dh) for(u32 dw=1;dw<=12;++dw) {
        std::vector<u8> a(sw*sh*4), b(dw*dh*4);
        std::vector<f32> f(sw*sh*4), g(dw*dh*4);
        for(size_t i=0;i<a.size();++i) {a[i]=static_cast<u8>((i*31+i/256)%251); f[i]=static_cast<f32>(i);}
        NearestNeighbor(a,b,sw,sh,dw,dh,4);
        NearestNeighborFast(f,g,sw,sh,dw,dh);
        for(u32 y=0;y<dh;++y) for(u32 x=0;x<dw;++x) for(size_t c=0;c<4;++c) {
            const size_t s=((static_cast<u64>(y)*sh/dh)*sw+static_cast<u64>(x)*sw/dw)*4+c;
            const size_t d=(y*dw+x)*4+c;
            assert(a[s]==b[d] && f[s]==g[d]);
        }
    }
}
"""
with tempfile.TemporaryDirectory(prefix="encore-blitter-nearest-") as tmp:
    source = Path(tmp) / "nearest.cpp"
    executable = Path(tmp) / "nearest"
    source.write_text(nearest_cpp)
    for opt in ("-O0", "-O2"):
        subprocess.run([clang, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        str(source), "-o", str(executable)], check=True, timeout=45)
        subprocess.run([str(executable)], check=True, timeout=20)
print("VENDOR_NEAREST_NEIGHBOR_PASS geometries=20736 packed_and_float=1 asan_ubsan=1")
