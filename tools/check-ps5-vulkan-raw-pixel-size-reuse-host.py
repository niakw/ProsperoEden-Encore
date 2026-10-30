#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prove exact native raw-frame pitch arithmetic reuses already decoded BPP.

The desktop code retains the pinned GetSizeInBytes call. Tests source-extracted
PS5/desktop C++ under sanitizers, both 2/4 BPP and large/empty framebuffers.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
source=(root/"vendor/encore-active/eden-vulkan/vulkan_present_layer.cpp").read_text()
generator=(root/"tools/prepare-vulkan-port.py").read_text()
start="    const u32 bytes_per_pixel = GetBytesPerPixel(framebuffer);"
end="#ifdef PS5_NATIVE\n    // An unmapped guest framebuffer has no tiled source to measure."
assert source.count(start)==1 and source.count(end)==1
fragment=source[source.index(start):source.index(end,source.index(start))].rstrip()
assert fragment.count("GetBytesPerPixel(framebuffer)")==1
assert fragment.count("GetSizeInBytes(framebuffer)")==1
assert fragment.count("static_cast<std::size_t>(framebuffer.stride)")==1
assert fragment.count("static_cast<std::size_t>(framebuffer.height)")==1
assert fragment.count("#ifdef PS5_NATIVE")==1 and fragment.count("#else")==1
assert "This raw upload already resolved the guest pixel format above." in generator

cpp=r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <utility>
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Framebuffer { u32 width{}, height{}, stride{}, bpp{}; };
unsigned bpp_lookups{}, byte_length_calls{};
u32 GetBytesPerPixel(const Framebuffer& f) {
    ++bpp_lookups;
    assert(f.bpp==2 || f.bpp==4);
    return f.bpp;
}
std::size_t GetSizeInBytes(const Framebuffer& f) {
    ++byte_length_calls;
    return static_cast<std::size_t>(f.stride) *
        static_cast<std::size_t>(f.height) * GetBytesPerPixel(f);
}
std::pair<u64,u32> Compute(const Framebuffer& framebuffer) {
__EXACT_SOURCE__
    return {linear_size,bytes_per_pixel};
}
int main() {
    for (u32 bpp : {2u,4u}) {
        for (const auto& [stride,height] : {
            std::pair<u32,u32>{0,200},
            {1,0}, {16,16}, {2048,1080},
            {65537,4096}, {8192,8192}}) {
            bpp_lookups=byte_length_calls=0;
            auto [bytes,linear_bpp]=Compute({1280,height,stride,bpp});
            assert(linear_bpp==bpp);
            const u64 expected=static_cast<std::size_t>(stride) *
                               static_cast<std::size_t>(height) * bpp;
            assert(bytes==expected);
#ifdef PS5_NATIVE
            assert(bpp_lookups==1 && byte_length_calls==0);
#else
            assert(bpp_lookups==2 && byte_length_calls==1);
#endif
        }
    }
}
""".replace("__EXACT_SOURCE__",fragment)
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-raw-pixel-size-") as temp:
    path=Path(temp)/"raw.cpp";path.write_text(cpp)
    for profile,flags in (("PS5",["-DPS5_NATIVE=1"]),("desktop",[])):
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(profile+opt[1:])
            subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                            "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                            *flags,str(path),"-o",str(exe)],check=True,timeout=50)
            subprocess.run([str(exe)],check=True,timeout=18)
            print(f"VULKAN_RAW_BPP_REUSE_PASS profile={profile} opt={opt}")
print("No claimed FC27 latency improvement before PS5 measurement")
