#!/usr/bin/env python3
"""P1.4: real maintained Eden block-linear RGB swizzle and unswizzle parity.

The test keeps the real decoders.cpp implementation and drops only its unused
transitive GPU facade include in the isolated host compilation. Neither the
PS5 build nor the vendored source is altered.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vendor=root/'vendor'
if not (vendor/'sources/eden/src/video_core/textures/decoders.cpp').exists():
    vendor=root.parent/'vendor'
source_path=vendor/'sources/eden/src/video_core/textures/decoders.cpp'
source=source_path.read_text()
assert source.count('#include "video_core/gpu.h"')==1
assert 'void SwizzleTexture(' in source and 'void UnswizzleTexture(' in source
assert 'std::size_t CalculateSize(' in source
service=(vendor/'encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp').read_text()
assert 'Tegra::Texture::CalculateSize(true, BytesPerPixel' in service
assert 'Tegra::Texture::SwizzleTexture(tiled, pixels,' in service
assert service.index('Tegra::Texture::SwizzleTexture(tiled, pixels,') < service.index('pixels.swap(tiled);')
assert service.index('pixels.swap(tiled);') < service.index('if (!m_owner->WriteVideoSurface(next.id, *target, pixels))')
layout=(vendor/'encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h').read_text()
assert 'const u64 pitch = ((width + 15) & ~u64{15}) * 4;' in layout
assert 'const u64 bytes = std::max(u64{4096}, pitch * ((height + 127) & ~u64{127}));' in layout

fixture=r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <span>
#include <vector>
#include "common/assert.h"
#include "common/logging.h"
#include "video_core/textures/decoders.h"
// Stubs for the unreachable assertion/error-reporting branches; the real
// algorithm is compiled unchanged from Eden's pinned decoders.cpp source.
void AssertFailSoftImpl(){std::abort();}
namespace Common::Log {
void FmtLogMessageImpl(Class,Level,const char*,unsigned int,const char*,
                       fmt::string_view,const fmt::format_args&){std::abort();}
}
int main(){
 using namespace Tegra::Texture;
 unsigned checked{};
 for (unsigned width : {64U,96U,128U,192U,256U,720U,1280U,1920U}) {
  for (unsigned height : {64U,96U,128U,256U,720U,1080U}) {
   constexpr unsigned bpp=4, gob_height=4;
   const unsigned pitch_pixels=((width+15U)&~15U);
   const unsigned pitched_rows=(height+127U)&~127U;
   const size_t image_bytes=std::max<size_t>(4096,size_t(pitch_pixels)*4*pitched_rows);
   const size_t tiled_bytes=CalculateSize(true,bpp,pitch_pixels,height,1,gob_height,0);
   assert(tiled_bytes<=image_bytes);
   std::vector<unsigned char> linear(image_bytes),tiled(image_bytes),roundtrip(image_bytes);
   for(size_t i=0;i<linear.size();++i)linear[i]=static_cast<unsigned char>((i*197+19)%251);
   SwizzleTexture(tiled,linear,bpp,pitch_pixels,height,1,gob_height,0);
   UnswizzleTexture(roundtrip,tiled,bpp,pitch_pixels,height,1,gob_height,0);
   const size_t active_size=size_t(pitch_pixels)*4*height;
   assert(std::equal(linear.begin(),linear.begin()+active_size,roundtrip.begin()));
   ++checked;
  }
 }
 std::printf("P1_SHARED_VIDEO_REAL_SWIZZLE_PASS geometry=%u tiling=16_GOB_rows pixel_bytes=4\n",checked);
}
'''
# `video_core/gpu.h` contributes no symbols used by these algorithms, but it
# pulls unrelated emulator threads/platform types into this independent test.
slim=source.replace('#include "video_core/gpu.h"','// Test only: unused transitive video_core/gpu.h omitted')
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
# The pinned fmt dependency is mandatory in the repository's native
# source closure; the Mac fallback only supports isolated sparse checkouts.
fmt_paths = [vendor/'sources/eden-cpm/fmt/12.1.0/include',
             root/'build-ns2-a64/fmt/include',
             Path('/Users/admin/.cache/ps5-eden-headless.O3b1qV/cdeps/include')]
include_dirs=[vendor/'sources/eden/src']
fmt = next((path for path in fmt_paths if (path/'fmt/format.h').exists()),None)
assert fmt is not None, 'Pinned fmt headers are necessary for real Eden assert/logging compile'
include_dirs.append(fmt)
# On CI, the maintained dependency is exposed as a standard system header.
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-native-real-swizzle-') as tmp:
    t=Path(tmp);cpp=t/'roundtrip.cpp';cpp.write_text(fixture)
    impl=t/'decoders.cpp';impl.write_text(slim)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            exe=t/(Path(compiler).name+opt)
            cmd=[compiler,'-std=c++20',opt,'-Wall','-Wextra',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                 *[part for inc in include_dirs for part in ('-I',str(inc))],
                 str(cpp),str(impl),'-o',str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=120)
            assert built.returncode==0,(cmd,built.stderr[-3800:])
            check=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=30)
            assert check.returncode==0,(cmd,check.stderr[-3800:])
            print(Path(compiler).name,opt,check.stdout.strip(),flush=True)
print('P1_VIDEO_NATIVE_SWIZZLE_ROUNDTRIP_HOST_PASS actual_eden_decoder=1 onscreen_ps5=unverified')
