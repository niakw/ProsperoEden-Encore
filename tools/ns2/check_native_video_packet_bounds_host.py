#!/usr/bin/env python3
"""H05: execute real native FFmpeg packet admission before host narrowing.

FFmpeg::Packet in the pinned core writes a std::span length into signed s32.
Nx2VideoDecoder stores FFmpeg timestamps in signed s64 and adds input
padding. The genuine maintained bound guard must run before all three.
Test exact limits and adversarial +1 values with GCC/Clang UBSan O0/O2.
This does not claim a Vulkan/guest IPC EOS completion witness.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/"vendor/encore-active/ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.cpp"
PACKET=ROOT/"vendor/sources/eden/src/video_core/host1x/ffmpeg.cpp"
source=OWNER.read_text()
ffmpeg=PACKET.read_text()
assert "m_packet->size = static_cast<s32>(data.size());" in ffmpeg
begin="[[nodiscard]] constexpr bool IsSafeNativeVideoPacketInput("
tail="\n}\n\n} // namespace"
assert source.count(begin)==1 and tail in source.split(begin,1)[1]
method=begin+source.split(begin,1)[1].split(tail,1)[0]+"\n}"
assert "std::numeric_limits<s32>::max()" in method
assert "std::numeric_limits<s64>::max()" in method
decode=source.split("bool Nx2VideoDecoder::Decode(",1)[1].split(
    "bool Nx2VideoDecoder::Drain(",1)[0]
assert decode.index("IsSafeNativeVideoPacketInput(data.size(), pts)") < decode.index(
    "impl->packet.assign(data.size() + AV_INPUT_BUFFER_PADDING_SIZE")
assert decode.index("IsSafeNativeVideoPacketInput(data.size(), pts)") < decode.index(
    "FFmpeg::Packet packet{")
assert "packet.GetPacket()->pts = static_cast<s64>(pts);" in decode

cpp=r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <limits>
using u64=std::uint64_t;
using s32=std::int32_t;
using s64=std::int64_t;
__ACTUAL_OWNER__
int main(){
    constexpr std::size_t packet_max=static_cast<std::size_t>(
        std::numeric_limits<s32>::max());
    constexpr u64 pts_max=static_cast<u64>(std::numeric_limits<s64>::max());
    static_assert(IsSafeNativeVideoPacketInput(0,0));
    static_assert(IsSafeNativeVideoPacketInput(1,0));
    static_assert(IsSafeNativeVideoPacketInput(packet_max,pts_max));
    static_assert(!IsSafeNativeVideoPacketInput(packet_max+1,pts_max));
    static_assert(!IsSafeNativeVideoPacketInput(packet_max+64,pts_max));
    static_assert(!IsSafeNativeVideoPacketInput(packet_max,pts_max+1));
    static_assert(!IsSafeNativeVideoPacketInput(packet_max,~u64{0}));
    static_assert(IsSafeNativeVideoPacketInput(4096,pts_max));
    assert(IsSafeNativeVideoPacketInput(2048,12345));
    assert(!IsSafeNativeVideoPacketInput(packet_max+1,0));
    assert(!IsSafeNativeVideoPacketInput(20,pts_max+1));
}
""".replace("__ACTUAL_OWNER__",method)
compilers=list(dict.fromkeys(c for c in
    (shutil.which("clang++"),shutil.which("g++")) if c))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h05-packet-bound-") as tmp:
    file=Path(tmp)/"actual.cpp";file.write_text(cpp)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            executable=Path(tmp)/(Path(compiler).name+opt)
            command=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     str(file),"-o",str(executable)]
            b=subprocess.run(command,capture_output=True,text=True,timeout=60,
                             env=os.environ.copy())
            assert b.returncode==0,(compiler,b.stderr[-4500:])
            r=subprocess.run([str(executable)],capture_output=True,
                             text=True,timeout=20,env=os.environ.copy())
            assert r.returncode==0,(compiler,r.stderr[-4500:])
            print("H05_REAL_FFMPEG_INPUT_BOUNDS_PASS",Path(compiler).name,
                  opt,"INT32_MAX=allowed +1=refused INT64_MAX_PTS=allowed"
                  " +1_PTS=refused guest_Vulkan_IPC=not_exercised",flush=True)
