#!/usr/bin/env python3
"""Compile the native B0B5 tiled remap with pinned Eden GOB swizzle code."""
from pathlib import Path
import shutil
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
core=root/"vendor"
source=(core/"encore-active/eden-core/src/video_core/engines/maxwell_dma.cpp").read_text()
header=(core/"encore-active/eden-core/include/video_core/engines/maxwell_dma.h").read_text()
decoder=(core/"sources/eden/src/video_core/textures/decoders.cpp").read_text()
cmake=(root/"headless/CMakeLists.txt").read_text()
assert "EDEN_MAINTAINED_MAXWELL_DMA_INCLUDE" in cmake
def cut(s,a,z):
    assert s.count(a)==1,a
    n=s.index(a)
    return s[n:s.index(z,n)]
live=cut(source,"bool MaxwellDMA::CopyBlockLinearRemap() {","void MaxwellDMA::CopyBlockLinearToPitch() {")
method=cut(header,"[[nodiscard]] Swizzle GetComponent(size_t i) const {",
           "\n    };\n    static_assert(sizeof(RemapConst)")
method=method[:method.rindex("        }")+len("        }")]
pdep=cut(decoder,"template <u32 mask>\nconstexpr u32 pdep(",
         "template <bool TO_LINEAR, u32 BYTES_PER_PIXEL>\nvoid SwizzleImpl(")
gob=cut(decoder,"template <bool TO_LINEAR, u32 BYTES_PER_PIXEL>\nvoid SwizzleSubrectImpl(",
        "template <bool TO_LINEAR>\nvoid Swizzle(")
api=cut(decoder,"void SwizzleSubrect(","std::size_t CalculateSize(")
# This historical GOB implementation models NS1 only; real NS2 bytes
# and the native tiling switch are independently tested by vendor R3.
assert api.count("u32 pitch_linear) {") == 2
api=api.replace("u32 pitch_linear) {",
                "u32 pitch_linear, bool native_tiling = false) {\n    assert(!native_tiling);")
assert "i * 4" in method
assert all(s in live for s in ["UnswizzleSubrect(", "SwizzleSubrect(",
                              "needs_destination", "MAX_BYTES", "IsFullyMappedRange",
                              "padded_width > MAX_BYTES / padded_height"])
assert "UnswizzleSubrect(linear_src, tiled_src, 1," in live
assert "UnswizzleSubrect(linear_dst, tiled_dst, 1," in live
assert "SwizzleSubrect(tiled_dst, linear_dst, 1," in live
# Historical host mock embeds Eden's unchanged NS1-only GOB decoder. The
# selected native decoder has an independently tested origin-Z overload.
# Authenticate the exact new 3D remap source, then remove its three
# origin-Z arguments only in the 2D compatibility fixture below.
live_host = live
if "memory_manager.UsesNativeTiling(),\n                             regs.src_params.layer" in live:
    import hashlib
    raw = source.encode("utf-8")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert blob == "d083d3298b3fb11373d7a7fc164a42ba92bdb2b5"
    assert "const bool is_volume = image.layer != 0 || image.depth != 1" in live
    assert "const u64 padded_depth =" in live
    assert "padded_width * padded_height * padded_depth" in live
    for path in (
        "                             regs.src_params.layer);",
        "                             regs.dst_params.layer);",
        "                       regs.dst_params.layer);",
    ):
        old = "memory_manager.UsesNativeTiling(),\\n" + path
        old = old.replace("\\n", "\n")
        assert live_host.count(old) == 1, ("3D remap Z owner drift", path)
        live_host = live_host.replace(old, "memory_manager.UsesNativeTiling());", 1)
cpp=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <span>
#include <vector>
// The real GOB decoder uses common/assert.h; the isolated host witness
// supplies the same failing-contract behavior without including its engine.
#define ASSERT_MSG(condition, ...) assert(condition)
using u8=std::uint8_t;using u32=std::uint32_t;using u64=std::uint64_t;
using s32=std::int32_t;using s64=std::int64_t;using GPUVAddr=u64;
namespace Common {
constexpr u32 DivCeilLog2(u32 n,u32 k) {return static_cast<u32>((static_cast<u64>(n)+((u64{1}<<k)-1))>>k);}
constexpr u32 AlignUpLog2(u32 n,u32 k) {return DivCeilLog2(n,k)<<k;}
}
namespace Tegra {
namespace Texture {
constexpr u32 GOB_SIZE_X_SHIFT=6,GOB_SIZE_Y_SHIFT=3,GOB_SIZE_SHIFT=9;
constexpr u32 SWIZZLE_X_BITS=0b100101111,SWIZZLE_Y_BITS=0b011010000;
__PDEP__
__GOB__
__API__
}
namespace DMA {
struct F{u32 v{};constexpr u32 Value()const{return v;}constexpr operator u32()const{return v;}};
struct Parameters{
 struct Block{F width{},height{},depth{};}block_size{};
 u32 width{},height{},depth{1},layer{};
 struct Origin{F x{},y{};}origin{};
};
}
struct MemoryManager{
 bool UsesNativeTiling() const noexcept{return false;}
 std::array<u8,65536> mem{};
 u32 writes{};
 bool IsFullyMappedRange(GPUVAddr a,size_t n)const{return a<=mem.size()&&n<=mem.size()-a;}
 void ReadBlock(GPUVAddr a,void* out,size_t n){assert(IsFullyMappedRange(a,n));std::memcpy(out,mem.data()+a,n);}
 void WriteBlock(GPUVAddr a,const void* in,size_t n){assert(IsFullyMappedRange(a,n));std::memcpy(mem.data()+a,in,n);++writes;}
};
namespace Engines {
struct MaxwellDMA {
 struct RemapConst{
  enum class Swizzle:u32{SRC_X=0,SRC_Y=1,SRC_Z=2,SRC_W=3,CONST_A=4,CONST_B=5,NO_WRITE=6};
  DMA::F component_size_minus_one{},num_src_components_minus_one{},num_dst_components_minus_one{};
  u32 remap_consta_value{},remap_constb_value{},dst_components_raw{};
  __METHOD__
 };
 struct LaunchDMA {
  enum class MemoryLayout{BLOCKLINEAR=0,PITCH=1};
  MemoryLayout src_memory_layout{MemoryLayout::BLOCKLINEAR};
  MemoryLayout dst_memory_layout{MemoryLayout::BLOCKLINEAR};
 };
 struct Regs {
  RemapConst remap_const{};LaunchDMA launch_dma{};
  DMA::Parameters src_params{},dst_params{};
  GPUVAddr offset_in{},offset_out{};
  s32 pitch_in{},pitch_out{};u32 line_length_in{},line_count{};
 }regs{};
 MemoryManager memory_manager;
 bool CopyBlockLinearRemap();
};
using namespace Texture;
__LIVE__
}
}
int main(){
 using Tegra::Engines::MaxwellDMA;
 using S=MaxwellDMA::RemapConst::Swizzle;
 using L=MaxwellDMA::LaunchDMA::MemoryLayout;
 using namespace Tegra::Texture;
 MaxwellDMA d{};
 auto set=[&](u32 i,S s){
   d.regs.remap_const.dst_components_raw &= ~(0xfu<<(i*4));
   d.regs.remap_const.dst_components_raw |= static_cast<u32>(s)<<(i*4);
 };
 auto reset=[&](u32 comp,u32 ns,u32 nd){
   d.regs={};
   d.regs.src_params.width=d.regs.dst_params.width=4;
   d.regs.src_params.height=d.regs.dst_params.height=4;
   d.regs.offset_in=0x1000;d.regs.offset_out=0x3000;
   d.regs.line_length_in=2;d.regs.line_count=2;
   d.regs.remap_const.component_size_minus_one.v=comp-1;
   d.regs.remap_const.num_src_components_minus_one.v=ns-1;
   d.regs.remap_const.num_dst_components_minus_one.v=nd-1;
   set(0,S::SRC_X);
 };
 auto encode=[&](u32 base,u32 bpp,const std::vector<u8>& x){
   std::span<u8> raw(d.memory_manager.mem.data()+base,512);
   SwizzleSubrect(raw,x,1,4*bpp,4,1,0,0,4*bpp,4,0,0,4*bpp);
 };
 auto decode=[&](u32 base,u32 bpp){
   std::span<const u8> raw(d.memory_manager.mem.data()+base,512);
   std::vector<u8> x(16*bpp);
   UnswizzleSubrect(x,raw,1,4*bpp,4,1,0,0,4*bpp,4,0,0,4*bpp);
   return x;
 };
 reset(1,1,1);
 d.regs.launch_dma.src_memory_layout=L::PITCH;
 d.regs.pitch_in=2;
 d.regs.dst_params.origin.x.v=d.regs.dst_params.origin.y.v=1;
 for(u32 i=0;i<4;i++)d.memory_manager.mem[0x1000+i]=i+1;
 std::fill_n(d.memory_manager.mem.data()+0x3000,512,0xee);
 assert(d.CopyBlockLinearRemap());
 auto output=decode(0x3000,1);
 for(u32 y=0;y<4;y++)for(u32 x=0;x<4;x++){
   const bool inside=x>=1&&x<3&&y>=1&&y<3;
   assert(output[y*4+x]==(inside?static_cast<u8>(1+(y-1)*2+x-1):0xee));
 }
 reset(1,2,2);
 d.regs.launch_dma.dst_memory_layout=L::PITCH;
 d.regs.pitch_out=4;
 d.regs.src_params.origin.x.v=d.regs.src_params.origin.y.v=1;
 set(0,S::SRC_Y);set(1,S::CONST_B);
 d.regs.remap_const.remap_constb_value=0x7b;
 std::vector<u8> src(32);
 for(u32 i=0;i<16;i++){src[2*i]=10+i;src[2*i+1]=50+i;}
 encode(0x1000,2,src);
 assert(d.CopyBlockLinearRemap());
 assert(d.memory_manager.mem[0x3000]==55);
 assert(d.memory_manager.mem[0x3001]==0x7b);
 reset(1,1,2);
 d.regs.src_params.origin.x.v=d.regs.dst_params.origin.x.v=1;
 d.regs.src_params.origin.y.v=d.regs.dst_params.origin.y.v=1;
 set(1,S::NO_WRITE);
 std::vector<u8> xs(16),xd(32);
 for(u32 i=0;i<16;i++){xs[i]=i+1;xd[i*2]=0xee;xd[i*2+1]=0xcd;}
 encode(0x1000,1,xs);encode(0x3000,2,xd);
 assert(d.CopyBlockLinearRemap());
 output=decode(0x3000,2);
 for(u32 y=0;y<4;y++)for(u32 x=0;x<4;x++){
   const bool inside=x>=1&&x<3&&y>=1&&y<3;
   assert(output[(y*4+x)*2]==(inside?xs[y*4+x]:0xee));
   assert(output[(y*4+x)*2+1]==0xcd);
 }
 // 9->12 B/px: three-byte components must cross GOB microtiles
 // without confusing the next row. Source Z, source X, CONST_A, NO_WRITE.
 reset(3,3,4);
 d.regs.src_params.origin.x.v=d.regs.dst_params.origin.x.v=1;
 d.regs.src_params.origin.y.v=d.regs.dst_params.origin.y.v=1;
 set(0,S::SRC_Z);
 set(1,S::SRC_X);
 set(2,S::CONST_A);
 set(3,S::NO_WRITE);
 d.regs.remap_const.remap_consta_value=0x00a1b2c3;
 std::vector<u8> src9(16*9),dst12(16*12);
 for(u32 pix=0;pix<16;pix++){
   for(u32 byte=0;byte<9;byte++)src9[pix*9+byte]=static_cast<u8>(pix*9+byte);
   for(u32 byte=0;byte<12;byte++)dst12[pix*12+byte]=static_cast<u8>(0x80+byte);
 }
 encode(0x1000,9,src9);encode(0x3000,12,dst12);
 assert(d.CopyBlockLinearRemap());
 output=decode(0x3000,12);
 for(u32 y=0;y<4;y++)for(u32 x=0;x<4;x++){
   const u32 pix=y*4+x;
   const bool hit=x>=1&&x<3&&y>=1&&y<3;
   for(u32 byte=0;byte<12;byte++){
     u8 value=dst12[pix*12+byte];
     if(hit && byte<3)value=src9[pix*9+6+byte];
     else if(hit && byte<6)value=src9[pix*9+byte-3];
     else if(hit && byte<9)value=(byte==6?0xc3:(byte==7?0xb2:0xa1));
     assert(output[pix*12+byte]==value);
   }
 }
 const auto writes=d.memory_manager.writes;
 d.regs.dst_params.depth=2;
 assert(!d.CopyBlockLinearRemap()&&d.memory_manager.writes==writes);
 d.regs.dst_params.depth=1;
 d.regs.dst_params.origin.x.v=4;
 assert(!d.CopyBlockLinearRemap()&&d.memory_manager.writes==writes);
 // Even a malformed host-produced register view must fail before indexing
 // beyond the four NVIDIA destination selectors or shifting past 32 bits.
 reset(1,1,5);
 assert(!d.CopyBlockLinearRemap()&&d.memory_manager.writes==writes);
 reset(5,1,1);
 assert(!d.CopyBlockLinearRemap()&&d.memory_manager.writes==writes);
 reset(1,1,1);
 d.regs.offset_in=(std::numeric_limits<u64>::max)();
 set(0,S::CONST_A);
 d.regs.remap_const.remap_consta_value=0xa5;
 assert(d.CopyBlockLinearRemap());
 output=decode(0x3000,1);
 assert(output[0]==0xa5&&output[1]==0xa5);
}
"""
for k,v in [("__PDEP__",pdep),("__GOB__",gob),("__API__",api),
            ("__METHOD__",method),("__LIVE__",live_host)]:
    assert cpp.count(k)==1,k
    cpp=cpp.replace(k,v)
compilers=[x for x in ("clang++","g++") if shutil.which(x)]
assert compilers
with tempfile.TemporaryDirectory(prefix="b0b5-gob-") as folder:
    f=Path(folder)/"gob.cpp"
    f.write_text(cpp)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(folder)/(compiler.replace("+","x")+opt)
            subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                            "-fsanitize=undefined","-fno-sanitize-recover=all",
                            str(f),"-o",str(exe)],check=True,timeout=120)
            subprocess.run([str(exe)],check=True,timeout=120)
print("B0B5_TILED_GOB_HOST_PASS: pitch_to_tiled,tiled_to_pitch,tiled_to_tiled,NO_WRITE,bounds")
