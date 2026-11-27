#!/usr/bin/env python3
"""C++ sanitizer witness from the actual two maintained Fermi2D address blocks.

The pre-widening source stays immutable as a historical regression witness.
A successful host test does not prove PS5 execution or close GitHub CodeQL.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
engines = root / "vendor/encore-active/eden-core/src/video_core/engines"
pinned = (root / "vendor/sources/eden/src/video_core/engines/fermi_2d.cpp").read_text()
old = "auto address = src.Address() + config.src_x0 * bytes_per_pixel;"
assert pinned.count(old) == 1
blocks = []
for name in ("fermi_2d_observed.cpp", "fermi_2d_experimental.cpp"):
    data = (engines / name).read_text()
    assert old not in data, ("unwidened CodeQL product", name)
    start = data.index("    const auto need_align_to_pitch =")
    stop = data.index("\n    memory_manager.FlushCaching();", start)
    snippet = data[start:stop]
    assert "bytes_per_pixel != 0 &&" in snippet
    assert "static_cast<u64>(config.src_x0) *" in snippet
    assert "static_cast<u64>(bytes_per_pixel)" in snippet
    assert "x_offset > ~u64{0} - base_address" in snippet
    blocks.append(snippet)
assert blocks[0] == blocks[1], "default and optional Fermi protections diverged"
workflow = (root / ".github/workflows/encore-core-preflight.yml").read_text()
assert "python3 -B tools/check-fermi2d-address-widening-host.py" in workflow

fermi_layer_source = (engines / "fermi_2d_observed.cpp").read_text()
# The active Fermi2D owner now distinguishes pitch-array layers from a
# hardware-defined destination-only block-linear volume slice. Keep the
# original 64-bit pitched-layer lambdas intact and verify the new gates.
assert "const bool has_layer = regs.src.layer != 0 || regs.dst.layer != 0;" in fermi_layer_source
assert "has_layer && regs.src.linear == MemoryLayout::Pitch &&" in fermi_layer_source
assert "regs.dst.linear == MemoryLayout::Pitch;" in fermi_layer_source
assert "const bool dst_volume_layer_copy =" in fermi_layer_source
assert "regs.src.layer == 0 && regs.dst.layer != 0 &&" in fermi_layer_source
assert "regs.dst.linear == MemoryLayout::BlockLinear && regs.dst.block_depth > 0" in fermi_layer_source
assert "regs.dst.depth > 1 && regs.dst.layer < regs.dst.depth" in fermi_layer_source
assert "else if (has_layer && !dst_volume_layer_copy)" in fermi_layer_source
assert 'UNIMPLEMENTED_MSG("Rejected Fermi2D destination volume slice")' in fermi_layer_source
assert "regs.src.format != regs.dst.format || regs.clip_enable != 0" in fermi_layer_source
assert fermi_layer_source.count("memory_manager.IsFullyMappedRange(base + offset,") == 1
assert "sw_blitter->Blit(src, dst, config);" in fermi_layer_source
layer_validation = fermi_layer_source[
    fermi_layer_source.index("        const auto valid_pitch_layers = "):
    fermi_layer_source.index("        if (!valid_pitch_layers", fermi_layer_source.index("        const auto valid_pitch_layers = "))
]
layer_selector = fermi_layer_source[
    fermi_layer_source.index("        const auto select_pitch_layer = "):
    fermi_layer_source.index("        if (!select_pitch_layer", fermi_layer_source.index("        const auto select_pitch_layer = "))
]

cpp = r"""
#include <cassert>
#include <cstdint>
#include <limits>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s32 = std::int32_t;
namespace Tegra::Engines {
struct Fermi2D { enum class MemoryLayout { Pitch, Block }; };
}
struct Surface {
    Tegra::Engines::Fermi2D::MemoryLayout linear;
    u32 width, pitch;
    u64 address;
    u32 addr_upper{}, addr_lower{};
    u64 Address() const { return (static_cast<u64>(addr_upper) << 32) | addr_lower; }
    explicit Surface(Tegra::Engines::Fermi2D::MemoryLayout layout, u32 w,
                     u32 p, u64 a) : linear(layout), width(w), pitch(p),
                                       address(a), addr_upper(u32(a >> 32)),
                                       addr_lower(u32(a)) {}
};
struct Config { s32 src_x0, src_x1; };
static unsigned rejected = 0;
void AssertFailSoftImpl() { ++rejected; }
void Apply(Surface& src, Config& config, u32 bytes_per_pixel) {
__SOURCE__
}
int main() {
    using Layout = Tegra::Engines::Fermi2D::MemoryLayout;
    {
        Surface src{Layout::Pitch, 1024, 32, 0xffffffffULL};
        Config c{16, 1024};
        Apply(src, c, 4);
        assert(rejected == 0);
        assert(src.Address() == 0x10000003fULL && src.width == 1008);
        assert(c.src_x0 == 0 && c.src_x1 == 1008);
    }
    {
        // Prior implicit 32-bit multiplication would wrap and lose upper bits.
        Surface src{Layout::Pitch, 2147483647u, 8, 0x1000};
        Config c{2147483646, 2147483647};
        Apply(src, c, 16);
        assert(rejected == 0);
        assert(src.Address() == 0x1000ULL +
               static_cast<u64>(2147483646ULL) * 16ULL);
        assert(src.width == 1u && c.src_x0 == 0 && c.src_x1 == 1);
    }
    {
        Surface src{Layout::Pitch, 1024, 32, std::numeric_limits<u64>::max()-20};
        Config c{16, 1024};
        const u64 original = src.Address();
        Apply(src, c, 4);
        assert(rejected == 1);
        assert(src.Address() == original && src.width == 1024);
        assert(c.src_x0 == 16 && c.src_x1 == 1024);
    }
    {
        // Zero block size cannot reach pitch division, even on a pitch surface.
        Surface src{Layout::Pitch, 1024, 32, 0x1000};
        Config c{16, 1024};
        Apply(src, c, 0);
        assert(rejected == 1 && src.Address() == 0x1000);
    }
    {
        Surface src{Layout::Pitch, 1024, 32, 0x1000};
        Config c{-1, 1024};
        Apply(src, c, 4);
        assert(rejected == 1 && src.Address() == 0x1000);
    }
    {
        Surface src{Layout::Block, 1024, 32, 0x1000};
        Config c{16, 1024};
        Apply(src, c, 4);
        assert(rejected == 1 && src.Address() == 0x1000);
    }
}
""".replace("__SOURCE__", blocks[0])
clang = shutil.which("clang++-18") or shutil.which("clang++")
assert clang, "Clang required for the sanitizer witness"
with tempfile.TemporaryDirectory(prefix="encore-fermi2d-widening-") as tmp:
    source = Path(tmp) / "fermi2d-widening.cpp"
    output = Path(tmp) / "witness"
    source.write_text(cpp)
    subprocess.run(
        [clang, "-std=c++20", "-O1", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
         str(source), "-o", str(output)], check=True, timeout=45)
    subprocess.run([str(output)], check=True, timeout=20)
print("FERMI2D_ADDRESS_WIDENING_HOST_PASS variants=2 offset64=1 carry=1 "
      "large_product=1 address_wrap_rejected=1 zero_bpp=1 guards=2 sanitizer=1")

# GPU-31: compile and run the exact two source lambdas on synthetic GPU
# address-space and pitched-layer descriptors. This is an executable
# semantics witness, not a full native TU or a PS5 game validation.
layer_cpp = r"""
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using GPUVAddr = u64;
enum class MemoryLayout { Pitch, BlockLinear };
struct Surface {
    MemoryLayout linear{MemoryLayout::Pitch};
    u32 depth{1},layer{0},width{32},height{8},pitch{256},format{4};
    u32 addr_upper{},addr_lower{};
    GPUVAddr Address() const {
        return (GPUVAddr{addr_upper} << 32) | addr_lower;
    }
    void SetAddress(u64 value) {
        addr_upper = u32(value >> 32);
        addr_lower = u32(value);
    }
};
u32 PixelFormatFromRenderTargetFormat(u32 f) {return f;}
u32 BytesPerBlock(u32 f) {return f == 4 ? 4 : 0;}
struct MemoryManager {
    bool mapped=true;
    unsigned checks{};
    bool IsFullyMappedRange(u64 a,std::size_t n) {
        ++checks;
        return mapped && n>0 && a<0x100000000ULL &&
               n<=0x100000000ULL-a;
    }
};
struct NativeFermi {
    MemoryManager& memory_manager;
    bool Run(Surface src,Surface dst,Surface& resolved_src,Surface& resolved_dst) {
__VALIDATOR__
        if (!valid_pitch_layers(src) || !valid_pitch_layers(dst) ||
            src.format != dst.format) return false;
__SELECTOR__
        if (!select_pitch_layer(src) || !select_pitch_layer(dst)) return false;
        resolved_src=src;
        resolved_dst=dst;
        return true;
    }
};
int main() {
    MemoryManager memory{};
    NativeFermi f{memory};
    Surface src{},dst{},a{},b{};
    src.depth=3;src.layer=1;src.SetAddress(0x10000);
    dst.depth=4;dst.layer=2;dst.SetAddress(0x30000);
    assert(f.Run(src,dst,a,b));
    assert(a.Address()==0x10800 && b.Address()==0x31000);
    assert(a.layer==0 && b.layer==0 && a.depth==1 && b.depth==1);
    assert(src.Address()==0x10000 && dst.Address()==0x30000);
    assert(src.layer==1 && dst.layer==2);
    assert(memory.checks==2);
    memory.mapped=false;
    assert(!f.Run(src,dst,a,b));
    memory.mapped=true;
    src.layer=3;
    assert(!f.Run(src,dst,a,b));
    src.layer=1;src.linear=MemoryLayout::BlockLinear;
    assert(!f.Run(src,dst,a,b));
    src.linear=MemoryLayout::Pitch;
    src.pitch=100; // 32 pixels * 4 bytes cannot fit in a row.
    assert(!f.Run(src,dst,a,b));
    src.pitch=256;src.format=999;
    assert(!f.Run(src,dst,a,b));
    src.format=4;
    src.SetAddress(std::numeric_limits<u64>::max()-100);
    assert(!f.Run(src,dst,a,b));
    src.SetAddress(0x10000);
    dst.depth=0;
    assert(!f.Run(src,dst,a,b));
    dst.depth=4;
    src.pitch=std::numeric_limits<u32>::max();
    assert(!f.Run(src,dst,a,b));
    src.pitch=256;
    // A valid base layer to a selected nonzero destination is supported.
    src.depth=1;src.layer=0;
    assert(f.Run(src,dst,a,b) && a.Address()==0x10000 && b.Address()==0x31000);
}
""".replace("__VALIDATOR__", layer_validation).replace("__SELECTOR__",layer_selector)
with tempfile.TemporaryDirectory(prefix="encore-fermi2d-layered-") as tmp:
    source = Path(tmp) / "pitch-layer.cpp"
    source.write_text(layer_cpp)
    for opt in ("-O0", "-O2"):
        exe = Path(tmp) / ("pitch-layer"+opt[1:])
        subprocess.run([clang, "-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("FERMI2D_PITCH_LAYER_HOST_PASS source_lambdas=2 complete_layers=1 "
      "mapping_guard=1 bad_stride=1 bad_depth=1 overflow=1 blocklinear_rejected=1 "
      "O0_O2=2 asan_ubsan=1")


# GPU-44: Lichii #853 volume-slice semantics adapted to the active NS1
# Maxwell owner. A depth>1 copy may try TextureCache, but it must never fall
# through to SoftwareBlitEngine, whose subrect decoder is single-slice here.
fermi_volume_source=(engines/"fermi_2d_observed.cpp").read_text()
assert "Source depth is not one" not in fermi_volume_source
assert 'UNIMPLEMENTED_MSG("Invalid zero-depth Fermi2D surface")' in fermi_volume_source
assert 'UNIMPLEMENTED_MSG("Unresolved Fermi2D volume-slice copy")' in fermi_volume_source
fallback_start=fermi_volume_source.index(
    "    if (!rasterizer->AccelerateSurfaceCopy(src, regs.dst, config)) {")
fallback_end=fermi_volume_source.index("\n    }\n}",fallback_start)+6
volume_fallback=fermi_volume_source[fallback_start:fallback_end]
assert "if (src.depth != 1 || regs.dst.depth != 1)" in volume_fallback
assert volume_fallback.index("src.depth != 1") < volume_fallback.index("sw_blitter->Blit")

texture_volume=(root/"vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
assert texture_volume.count("const auto copy_ns1_volume_slice = [&]() -> bool {") == 1
ns1_start=texture_volume.index("const auto copy_ns1_volume_slice = [&]() -> bool {")
ns1_end=texture_volume.index("\n        };",ns1_start)+11
ns1_volume=texture_volume[ns1_start:ns1_end]
for token in (
    "gpu_memory->UsesNativeTiling()",
    "surface.depth > 1",
    "surface.linear == Fermi2D::MemoryLayout::BlockLinear",
    "surface.layer == 0",
    "image.slice_offsets.size() != image.slice_subresources.size()",
    "std::ranges::find(image.slice_offsets",
    "image.aliased_images.empty()",
    "image.overlapping_images.empty()",
    "gpu_memory->IsContinuousRange",
    "PrepareImage(src_slice->id, false, false);",
    "PrepareImage(dst_slice->id, false, false);",
    "const auto src_after = find_slice(src);",
    "const auto dst_after = find_slice(dst);",
    "MarkModification(slot_images[dst_slice->id]);",
    "runtime.CopyImage(slot_images[dst_slice->id], slot_images[src_slice->id]",
):
    assert token in ns1_volume, token
# Native-tiling (authenticated NS2) channels must not enter this NS1 path.
assert ns1_volume.index("gpu_memory->UsesNativeTiling()") < ns1_volume.index("find_slice")

fallback_fixture=r"""
#include <cassert>
#include <cstdint>
using u32=std::uint32_t;
static unsigned unimplemented{}, software_calls{}, accelerated_calls{};
#define UNIMPLEMENTED_MSG(...) (++unimplemented)
struct Surface { u32 depth{1}; u32 layer{}; };
struct Config {};
struct Rasterizer {
 bool result{};
 bool AccelerateSurfaceCopy(const Surface&,const Surface&,const Config&) {
   ++accelerated_calls; return result;
 }
};
struct Blitter {
 void Blit(Surface&,Surface&,Config&) { ++software_calls; }
};
struct Regs { Surface dst{}; u32 clip_enable{}; };
struct Test {
 Rasterizer* rasterizer{};
 Blitter* sw_blitter{};
 Regs regs{};
 void Run(Surface src, Config config) {
__FALLBACK__
 }
};
int main() {
 Rasterizer r{}; Blitter b{}; Test t{&r,&b,{}};
 Surface s{}; Config c{};
 r.result=false; s.depth=1; t.regs.dst.depth=1; t.Run(s,c);
 assert(accelerated_calls==1 && software_calls==1 && unimplemented==0);
 // Base z=0 of a 3D surface is now a verified software fallback after
 // TextureCache declines acceleration; it must not be reported unsupported.
 r.result=false; s.depth=4; s.layer=0; t.regs.dst.depth=4; t.regs.dst.layer=0; t.Run(s,c);
 assert(accelerated_calls==2 && software_calls==2 && unimplemented==0);
 // A 2D source targeting the destination's base z=0 slice is equally safe.
 r.result=false; s.depth=1; t.regs.dst.depth=4; t.Run(s,c);
 assert(accelerated_calls==3 && software_calls==3 && unimplemented==0);
 // A non-zero volume slice remains unresolved and must fail closed.
 s.depth=4; s.layer=1; t.regs.dst.depth=4; t.regs.dst.layer=0; t.Run(s,c);
 assert(accelerated_calls==4 && software_calls==3 && unimplemented==1);
 // Successful TextureCache acceleration still bypasses software fallback.
 s.layer=0; r.result=true; t.Run(s,c);
 assert(accelerated_calls==5 && software_calls==3 && unimplemented==1);
}
""".replace("__FALLBACK__",volume_fallback)

slice_fixture=r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <optional>
#include <vector>
using u32=std::uint32_t; using u64=std::uint64_t; using s32=std::int32_t;
struct Base { s32 level{},layer{}; };
struct Image {
 u64 gpu_addr{},guest_size_bytes{};
 u32 width{},height{},depth{};
 bool bad{};
 std::vector<u32> slice_offsets{};
 std::vector<Base> slice_subresources{};
};
struct Slice { u32 id{}; s32 depth{}; };
std::optional<Slice> Find(const std::vector<Image>& images,u64 address,u32 w,u32 h,u32 d) {
 std::optional<Slice> found; bool ambiguous=false;
 for(u32 id=0;id<images.size();++id) {
  const auto& image=images[id];
  if(image.bad || image.width!=w || image.height!=h || image.depth!=d ||
     address<image.gpu_addr) continue;
  const u64 relative=address-image.gpu_addr;
  if(relative>=image.guest_size_bytes || relative>0xffffffffULL ||
     image.slice_offsets.size()!=image.slice_subresources.size()) continue;
  const auto it=std::find(image.slice_offsets.begin(),image.slice_offsets.end(),(u32)relative);
  if(it==image.slice_offsets.end()) continue;
  const auto index=(size_t)std::distance(image.slice_offsets.begin(),it);
  const Base base=image.slice_subresources[index];
  if(base.level!=0 || base.layer<0 || (u32)base.layer>=image.depth) continue;
  if(found) { ambiguous=true; continue; }
  found=Slice{id,base.layer};
 }
 return ambiguous?std::nullopt:found;
}
int main() {
 std::vector<Image> images(2);
 images[0]={0x1000,0x3000,16,16,3,false,{0,0x1000,0x2000},{{0,0},{0,1},{0,2}}};
 auto s=Find(images,0x2000,16,16,3);
 assert(s && s->id==0 && s->depth==1);
 assert(!Find(images,0x2001,16,16,3));
 images[1]=images[0];
 assert(!Find(images,0x2000,16,16,3)); // ambiguous cache match fails closed
 images[1].bad=true;
 s=Find(images,0x3000,16,16,3);
 assert(s && s->depth==2);
 assert(!Find(images,0x3000,8,16,3));
}
"""
with tempfile.TemporaryDirectory(prefix="encore-fermi2d-volume-") as tmp:
    base=Path(tmp)
    for name,code in (("fallback",fallback_fixture),("slice",slice_fixture)):
        source=base/(name+".cpp"); source.write_text(code)
        for opt in ("-O0","-O2"):
            exe=base/(name+opt[1:])
            subprocess.run([clang,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                            "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                            str(source),"-o",str(exe)],check=True,timeout=45)
            subprocess.run([str(exe)],check=True,timeout=20)
print("FERMI2D_NS1_VOLUME_SLICE_HOST_PASS upstream_853=1 active_owner=1 "
      "ns2_native_tiling_excluded=1 exact_fallback=1 depth1_software=1 "
      "base_layer_software_fallback=1 nonzero_slice_failclosed=1 cached_slice=1 ambiguous_rejected=1 "
      "O0_O2=2 ASan_UBSan=1")
