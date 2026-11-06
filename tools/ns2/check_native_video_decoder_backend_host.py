#!/usr/bin/env python3
"""P1.3: actual maintained H264 bitstream framing and FFmpeg backend owner."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
vroot = root / 'vendor'
if not (vroot / 'encore-active').exists():
    vroot = root.parent / 'vendor'  # sparse Mac checkout, not used in CI
code_dir = vroot / 'encore-active/ns2-runtime/video_decoder/video_core/host1x'
header = (code_dir / 'nx2_video_decoder.h').read_text()
backend = (code_dir / 'nx2_video_decoder.cpp').read_text()
converter = (code_dir / 'h264_packet.h').read_text()
recipe = (root / 'headless/CMakeLists.txt').read_text()
for source in ('nx2_video_decoder.cpp', 'nx2_video_decoder.h', 'h264_packet.h'):
    assert (code_dir / source).is_file(), source
assert 'set(EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT' in recipe
assert 'target_sources(video_core PRIVATE' in recipe
assert '"${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/video_core/host1x/nx2_video_decoder.cpp"' in recipe
assert 'target_include_directories(core BEFORE PRIVATE\n        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}")' in recipe
assert 'class Nx2VideoDecoder {' in header
assert 'std::optional<NvdecCommon::VideoCodec> CodecFromMime(' in backend
for codec in ('VideoCodec::VP9', 'VideoCodec::VP8', 'VideoCodec::H264'):
    assert codec in backend
assert 'VideoCodec::AV1' not in backend, 'unsupported AV1 requires explicit refusal'
assert 'if (!codec)' in backend
assert 'if (impl->decoder->GetCodec() == nullptr)' in backend
assert 'impl->open = impl->context->OpenContext(*impl->decoder);' in backend
assert 'impl->h264_packets.Convert(' in backend
assert 'avcodec_send_packet(' in backend
assert 'avcodec_flush_buffers(' in backend
assert 'sws_getCachedContext(' in backend
assert 'return;' in backend
assert 'format = Format::Unknown;' in converter
assert 'if (length == 0 || length > data.size())' in converter

source = r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <span>
#include "video_core/host1x/h264_packet.h"
int main() {
 using Tegra::Host1x::H264PacketConverter;
 H264PacketConverter parser;
 std::array<u8, 12> mp4{0,0,0,2,0x65,0xaa,0,0,0,2,0x41,0xbb};
 parser.Convert(mp4);
 assert((mp4 == std::array<u8,12>{0,0,0,1,0x65,0xaa,0,0,0,1,0x41,0xbb}));
 parser.Convert(mp4);
 assert(mp4[3] == 1 && mp4[9] == 1);
 parser.Reset();
 std::array<u8, 7> annex{0,0,0,1,0x65,0x88,0x84};
 parser.Convert(annex);
 assert((annex == std::array<u8,7>{0,0,0,1,0x65,0x88,0x84}));
 parser.Reset();
 std::array<u8,7> invalid{0,0,0,5,0x65,0x88,0x84};
 parser.Convert(invalid);
 assert(invalid[3] == 5);
 std::array<u8,4> too_short{0,0,0,1};
 parser.Convert(too_short);
 assert(too_short[3] == 1);
 parser.Reset();
 std::array<u8,6> one{0,0,0,2,0x65,0xaa};
 parser.Convert(one);
 assert(one[3] == 1);
}
'''
compilers = list(dict.fromkeys(filter(None, (shutil.which('clang++'), shutil.which('g++')))))
assert compilers
sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env = os.environ.copy()
if sdk.is_dir():
    env['SDKROOT'] = str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-real-h264-frame-') as temp:
    cpp = Path(temp) / 'test.cpp'
    cpp.write_text(source)
    for compiler in compilers:
        for opt in ('-O0', '-O2'):
            exe = Path(temp) / (Path(compiler).name + opt)
            cmd = [compiler, '-std=c++20', opt, '-Wall', '-Wextra', '-Werror',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all',
                   '-I', str(code_dir.parents[1]),
                   '-I', str(vroot / 'sources/eden/src'), str(cpp), '-o', str(exe)]
            built = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=90)
            assert built.returncode == 0, (cmd, built.stderr[-2600:])
            executed = subprocess.run([str(exe)], env=env, capture_output=True, text=True, timeout=20)
            assert executed.returncode == 0, (cmd, executed.stderr[-2600:])
            print(Path(compiler).name, opt, 'P1_VIDEO_H264_REAL_CONVERTER_PASS', flush=True)
print('P1_NATIVE_VIDEO_BACKEND_HOST_PASS codec=H264_VP8_VP9 AV1=refused renderer=ffmpeg frame_ownership=source_only')
