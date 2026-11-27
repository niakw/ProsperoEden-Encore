#!/usr/bin/env python3
"""Execute real ConvertImage layout code; decoder stubs enforce full-volume writes."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
def method(path):
    text = path.read_text()
    start = text.index('void ConvertImage(')
    return text[start:text.index('\nboost::container::small_vector<BufferImageCopy, 16> FullDownloadCopies', start)]
previous = method(ROOT / 'vendor/sources/eden/src/video_core/texture_cache/util.cpp')
current = method(ROOT / 'vendor/encore-active/eden-core/src/video_core/texture_cache/util.cpp')
decoder = (ROOT / 'vendor/sources/eden/src/video_core/texture_cache/decode_bc.cpp').read_text()
assert 'const u32 depth = copy.image_extent.depth;' in decoder
assert 'for (u32 slice = 0; slice < depth; ++slice)' in decoder
cpp = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <span>
#include <vector>
#include "common/scratch_buffer.h"
using u8=std::uint8_t; using u32=std::uint32_t; using s32=std::int32_t;
#define ASSERT(x) assert(x)
enum class PixelFormat { ASTC, BC7, A8B8G8R8_UNORM };
struct Extent2D { u32 width,height; };
struct Extent3D { u32 width,height,depth; bool operator==(const Extent3D&) const=default; };
struct Offset3D { s32 x{},y{},z{}; bool operator==(const Offset3D&) const=default; };
struct Subresource { u32 base_level{},base_layer{},num_layers{}; };
struct ImageInfo { Extent3D size; PixelFormat format; };
struct BufferImageCopy {
    std::size_t buffer_offset{},buffer_size{};
    u32 buffer_row_length{},buffer_image_height{};
    Subresource image_subresource; Offset3D image_offset; Extent3D image_extent;
};
namespace Common {
template<class A,class B> auto AlignUp(A n,B a) { return (n+a-1)/a*a; }
u32 DivideUp(u32 n,u32 d) { return (n+d-1)/d; }
}
namespace Settings {
enum class AstcRecompression { Uncompressed,Bc1,Bc3 };
unsigned reads;
struct Setting {
    AstcRecompression mode;
    AstcRecompression GetValue() const { ++reads; return mode; }
};
struct Values { Setting astc_recompression; } values;
}
Extent2D DefaultBlockSize(PixelFormat) { return {4,4}; }
Extent3D AdjustMipSize(Extent3D s,s32 l) { return {std::max(1u,s.width>>l),std::max(1u,s.height>>l),std::max(1u,s.depth>>l)}; }
bool IsPixelFormatASTC(PixelFormat f) { return f==PixelFormat::ASTC; }
u32 BytesPerBlock(PixelFormat) { return 4; }
u32 ConvertedBytesPerBlock(PixelFormat) { return 4; }
void Decode(std::span<const u8> input,u32 w,u32 h,u32 layers,std::span<u8> output) {
    const auto bytes=std::size_t(w)*h*layers*4;
    assert(!input.empty() && output.size()>=bytes);
    std::fill_n(output.begin(),bytes,input.front());
}
namespace Tegra::Texture::ASTC {
void Decompress(std::span<const u8> input,u32 w,u32 h,u32 layers,u32,u32,std::span<u8> output) { Decode(input,w,h,layers,output); }
}
namespace Tegra::Texture::BCN {
void Compress(std::span<const u8> input,u32 w,u32 h,u32 layers,std::span<u8> output,u32 divisor) {
    const auto bytes=std::size_t(Common::AlignUp(w,4))*Common::AlignUp(h,4)*layers/divisor;
    assert(!input.empty() && output.size()>=bytes);
    std::fill_n(output.begin(),bytes,input.front());
}
void CompressBC1(std::span<const u8> in,u32 w,u32 h,u32 n,std::span<u8> out) { Compress(in,w,h,n,out,2); }
void CompressBC3(std::span<const u8> in,u32 w,u32 h,u32 n,std::span<u8> out) { Compress(in,w,h,n,out,1); }
}
void DecompressBCn(std::span<const u8> in,std::span<u8> out,BufferImageCopy& c,PixelFormat) {
    Decode(in,c.image_extent.width,c.image_extent.height,c.image_extent.depth*c.image_subresource.num_layers,out);
}
namespace Before { BEFORE }
namespace After { AFTER }
using Converter=void(*)(std::span<const u8>,const ImageInfo&,std::span<u8>,std::span<BufferImageCopy>);
bool Run(Converter convert,const ImageInfo& info,u32 layers,Settings::AstcRecompression mode,unsigned& reads) {
    Settings::values.astc_recompression.mode=mode;
    std::vector<u8> input,expected;
    std::vector<BufferImageCopy> copies;
    std::vector<std::size_t> expected_offsets;
    for(u32 level=0;level<3;++level) {
        auto size=AdjustMipSize(info.size,level);
        const auto input_bytes=std::size_t(Common::DivideUp(size.width,4))*Common::DivideUp(size.height,4)*16*size.depth*layers;
        copies.push_back({input.size(),input_bytes,Common::AlignUp(size.width,4),Common::AlignUp(size.height,4),{level,0,layers},{},size});
        input.insert(input.end(),input_bytes,static_cast<u8>(0x40+level));
        expected_offsets.push_back(expected.size());
        const bool compressed=info.format==PixelFormat::ASTC && mode!=Settings::AstcRecompression::Uncompressed;
        const auto bytes=compressed ? std::size_t(Common::AlignUp(size.width,4))*Common::AlignUp(size.height,4)*size.depth*layers/(mode==Settings::AstcRecompression::Bc1?2:1)
                                    : std::size_t(size.width)*size.height*size.depth*layers*4;
        expected.insert(expected.end(),bytes,static_cast<u8>(0x40+level));
    }
    std::vector<u8> output(expected.size()+32,0xcc);
    Settings::reads=0;
    convert(input,info,std::span<u8>(output).first(expected.size()),copies);
    reads=Settings::reads;
    bool good=std::equal(expected.begin(),expected.end(),output.begin());
    for(std::size_t i=0;i<copies.size();++i) good&=copies[i].buffer_offset==expected_offsets[i];
    assert(std::all_of(output.end()-32,output.end(),[](u8 b){return b==0xcc;}));
    return good;
}
int main() {
    using R=Settings::AstcRecompression;
    unsigned old_reads{},new_reads{};
    for(auto format:{PixelFormat::ASTC,PixelFormat::BC7}) {
        ImageInfo volume{{16,16,4},format};
        assert(!Run(Before::ConvertImage,volume,1,R::Uncompressed,old_reads));
        assert(Run(After::ConvertImage,volume,1,R::Uncompressed,new_reads));
        assert(old_reads==3 && new_reads==1);
        ImageInfo array{{16,16,1},format};
        assert(Run(Before::ConvertImage,array,3,R::Uncompressed,old_reads));
        assert(Run(After::ConvertImage,array,3,R::Uncompressed,new_reads));
        assert(old_reads==3 && new_reads==1);
    }
    for(auto mode:{R::Bc1,R::Bc3})
        for(u32 depth:{1u,4u})
            assert(Run(After::ConvertImage,{{16,16,depth},PixelFormat::ASTC},2,mode,new_reads));
    Settings::reads=0;
    After::ConvertImage({},{{16,16,1},PixelFormat::ASTC},{},{});
    assert(Settings::reads==0);
    std::puts("TEXTURE_VOLUME_LAYOUT_PASS old_3D_overlap_reproduced=2 current_mip_ranges_disjoint=1 arrays=preserved BC1_BC3=preserved settings_reads=3->1 empty_reads=0");
}
'''.replace('BEFORE',previous).replace('AFTER',current)
compiler=shutil.which('clang++-18') or shutil.which('clang++') or shutil.which('g++')
assert compiler
with tempfile.TemporaryDirectory(prefix='encore-texture-volume-') as temp:
    source,binary=Path(temp)/'main.cpp',Path(temp)/'volume';source.write_text(cpp)
    subprocess.run([compiler,'-std=c++20','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-sanitize-recover=all',
                    '-I'+str(ROOT/'vendor/sources/eden/src'),str(source),'-o',str(binary)],check=True,timeout=60)
    subprocess.run([str(binary)],check=True,timeout=30)
print('TEXTURE_LAYOUT_HOST_ONLY decoded_pixel_quality_and_PS5_graphics=unverified')


# GPU-45: compile the exact generic layer splitter from the active PS5 TextureCache.
texture_owner=(ROOT/"vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
sig="inline std::vector<ImageCopy> SplitLayeredImageCopies("
start=texture_owner.index(sig)
brace=texture_owner.index("{",start)
depth=0
end=None
for i in range(brace,len(texture_owner)):
    if texture_owner[i]=="{":
        depth+=1
    elif texture_owner[i]=="}":
        depth-=1
        if depth==0:
            end=i+1
            break
assert end is not None
splitter=texture_owner[start:end]
copy_start=texture_owner.index("void TextureCache<P>::CopyImage(ImageId dst_id")
copy_end=texture_owner.index("\n}\n",copy_start)+2
copy_method=texture_owner[copy_start:copy_end]
assert "for (const ImageCopy& copy : SplitLayeredImageCopies(copies))" in copy_method
assert copy_method.count("UNIMPLEMENTED_IF(copy.dst_subresource.num_layers != 1);")==1
assert copy_method.count("UNIMPLEMENTED_IF(copy.src_subresource.num_layers != 1);")==1

layer_cpp=r"""
#include <cassert>
#include <cstdint>
#include <span>
#include <vector>
using s32=std::int32_t;
struct Subresource { s32 base_level{},base_layer{},num_layers{}; };
struct Offset3D { s32 x{},y{},z{}; bool operator==(const Offset3D&) const=default; };
struct Extent3D { std::uint32_t width{},height{},depth{}; bool operator==(const Extent3D&) const=default; };
struct ImageCopy {
    Subresource src_subresource{},dst_subresource{};
    Offset3D src_offset{},dst_offset{};
    Extent3D extent{};
};
__SPLITTER__
int main() {
    ImageCopy one{
      .src_subresource={2,4,1},.dst_subresource={3,7,1},
      .src_offset={1,2,3},.dst_offset={4,5,6},.extent={16,8,1}};
    auto a=SplitLayeredImageCopies(std::span<const ImageCopy>{&one,1});
    assert(a.size()==1);
    assert(a[0].src_subresource.base_layer==4 && a[0].dst_subresource.base_layer==7);
    assert(a[0].src_offset==one.src_offset && a[0].dst_offset==one.dst_offset &&
           a[0].extent==one.extent);

    ImageCopy three=one;
    three.src_subresource={1,10,3};
    three.dst_subresource={5,20,3};
    auto b=SplitLayeredImageCopies(std::span<const ImageCopy>{&three,1});
    assert(b.size()==3);
    for(s32 i=0;i<3;++i) {
      assert(b[i].src_subresource.base_level==1);
      assert(b[i].dst_subresource.base_level==5);
      assert(b[i].src_subresource.base_layer==10+i);
      assert(b[i].dst_subresource.base_layer==20+i);
      assert(b[i].src_subresource.num_layers==1 && b[i].dst_subresource.num_layers==1);
      assert(b[i].src_offset==three.src_offset && b[i].dst_offset==three.dst_offset &&
             b[i].extent==three.extent);
    }

    ImageCopy mismatch=three;
    mismatch.src_subresource.num_layers=2;
    auto c=SplitLayeredImageCopies(std::span<const ImageCopy>{&mismatch,1});
    assert(c.size()==1);
    assert(c[0].src_subresource.num_layers==2 && c[0].dst_subresource.num_layers==3);

    ImageCopy zero=three;
    zero.src_subresource.num_layers=0;
    zero.dst_subresource.num_layers=0;
    auto d=SplitLayeredImageCopies(std::span<const ImageCopy>{&zero,1});
    assert(d.size()==1 && d[0].src_subresource.num_layers==0 && d[0].dst_subresource.num_layers==0);

    std::vector<ImageCopy> mixed{one,three};
    auto e=SplitLayeredImageCopies(mixed);
    assert(e.size()==4);
    assert(e[0].dst_subresource.base_layer==7);
    assert(e[1].dst_subresource.base_layer==20);
    assert(e[3].dst_subresource.base_layer==22);
}
""".replace("__SPLITTER__",splitter)
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-layered-cross-format-") as tmp:
    src=Path(tmp)/"layers.cpp"
    src.write_text(layer_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(tmp)/("layers-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(src),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_LAYERED_CROSS_FORMAT_COPY_HOST_PASS active_owner=1 exact_helper=1 "
      "single_unchanged=1 three_layers=1 order=1 offsets_preserved=1 "
      "mismatch_failclosed=1 zero_failclosed=1 O0_O2=2 ASan_UBSan=1")


# GPU-48: the active format lookup is a one-hunk successor of pinned Eden.
format_original=(ROOT/"vendor/sources/eden/src/video_core/texture_cache/format_lookup_table.cpp").read_text()
format_active=(ROOT/"vendor/encore-active/eden-core/src/video_core/texture_cache/format_lookup_table.cpp").read_text()
format_old="""    case Hash(TextureFormat::X8Z24, UNORM, UINT, UINT, UINT, LINEAR):
        return PixelFormat::X8_D24_UNORM;
"""
format_new="""    case Hash(TextureFormat::X8Z24, UNORM, UINT, UINT, UINT, LINEAR):
    case Hash(TextureFormat::X8Z24, UNORM, UINT, UNORM, UNORM, LINEAR):
        return PixelFormat::X8_D24_UNORM;
"""
assert format_original.count(format_old)==1
assert format_active==format_original.replace(format_old,format_new,1)
assert format_active.count("case Hash(TextureFormat::X8Z24, UNORM, UINT, UNORM, UNORM, LINEAR):")==1
cmake=(ROOT/"headless/CMakeLists.txt").read_text()
assert 'set(EDEN_MAINTAINED_FORMAT_LOOKUP' in cmake
assert 'list(REMOVE_ITEM video_sources texture_cache/format_lookup_table.cpp)' in cmake
assert 'list(APPEND video_sources "${EDEN_MAINTAINED_FORMAT_LOOKUP}")' in cmake
assert cmake.index('list(APPEND video_sources "${EDEN_MAINTAINED_FORMAT_LOOKUP}")') < cmake.index(
    'set_property(TARGET video_core PROPERTY SOURCES "${video_sources}")')
print("NS1_X8Z24_FORMAT_LOOKUP_PASS active_owner=1 exact_delta=1 "
      "x8z24_unorm_uint_unorm_unorm=1 pinned_eden_immutable=1")
