#!/usr/bin/env python3
"""P1.3: exact shared EOS helper never invents video outputs or GPU fences."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vroot=root/'vendor'
if not (vroot/'encore-active').exists():vroot=root.parent/'vendor'
header=vroot/'encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/native_video_eos.h'
service=vroot/'encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp'
assert header.is_file() and service.is_file()
source=service.read_text()
assert '#include "core/hle/service/am/service/native_video_eos.h"' in source
assert 'VideoDecoderProtocol::MarkLastEos(m_pending, m_outputs)' in source
assert 'if (eos && decoded.empty() &&' in source
assert 'if (compressed.size() > MaxInputBytes || (compressed.empty() && !eos))' in source
assert 'if (m_pending.size() >= MaxFrames && !compressed.empty())' in source
assert 'm_decoder->Drain(decoded)' in source
assert 'Kernel::ResultNotFound' in source
assert 'ctx.BufferDescriptorA().empty()' in source
assert 'm_outputs.push_back({' in source and 'syncpoints.IncrementGuest(m_syncpoint)' in source
fixture=r'''
#include <cassert>
#include <deque>
#include "core/hle/service/am/service/native_video_eos.h"
struct Pending {int id{};bool eos{};};
struct Output {int id{};bool eos{};};
int main(){
 using Service::AM::VideoDecoderProtocol::MarkLastEos;
 std::deque<Pending> p;
 std::deque<Output> o;
 assert(!MarkLastEos(p,o));
 o.push_back({1,false});o.push_back({2,false});
 assert(MarkLastEos(p,o));
 assert(!o.front().eos && o.back().eos && o.size()==2);
 o.back().eos=false;
 p.push_back({3,false});p.push_back({4,false});
 assert(MarkLastEos(p,o));
 assert(!p.front().eos && p.back().eos);
 assert(!o.front().eos && !o.back().eos);
 p.clear();o.clear();
 assert(!MarkLastEos(p,o));
 p.push_back({5,false});
 assert(MarkLastEos(p,o) && p.back().eos);
 p.clear();o.push_back({6,false});
 assert(MarkLastEos(p,o) && o.back().eos);
}
'''
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-ns2-video-eos-') as directory:
    cpp=Path(directory)/'eos.cpp';cpp.write_text(fixture)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            exe=Path(directory)/(Path(compiler).name+opt)
            args=[compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                  '-fsanitize=undefined','-fno-sanitize-recover=all',
                  '-I',str(vroot/'encore-active/ns2-runtime/video_decoder'),
                  str(cpp),'-o',str(exe)]
            compile=subprocess.run(args,capture_output=True,text=True,timeout=90,env=env)
            assert compile.returncode==0,(args,compile.stderr[-2400:])
            output=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15,env=env)
            assert output.returncode==0,(args,output.stderr[-2400:])
            print(Path(compiler).name,opt,'P1_NATIVE_VIDEO_EOS_LAST_REAL_IMAGE_PASS',flush=True)
print('P1_NATIVE_VIDEO_EOS_HOST_PASS pending_last=1 completed_last=1 no_image=refused no_fake_syncpoint=1')
