#!/usr/bin/env python3
"""P1.3: real native codec TMEM ownership / guest-handle lifetime admission."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vendor=root/'vendor'
if not (vendor/'encore-active').exists():vendor=root.parent/'vendor'
root_dir=vendor/'encore-active/ns2-runtime/video_decoder'
header=root_dir/'core/hle/service/am/service/native_video_work_buffer.h'
session_cpp=(root_dir/'core/hle/service/am/service/graphics_video_decoder_session.cpp').read_text()
session_h=(root_dir/'core/hle/service/am/service/graphics_video_decoder_session.h').read_text()
assert header.is_file()
assert '#include "core/hle/service/am/service/native_video_work_buffer.h"' in session_cpp
assert 'VideoDecoderProtocol::IsWorkBufferOwned(memory.GetPointerUnsafe(),' in session_cpp
assert 'VideoDecoderProtocol::IsValidWorkBufferSize(memory->GetSize())' in session_cpp
assert session_cpp.index('m_work_buffer = std::move(memory);') < session_cpp.index('m_initialized = true;')
assert 'm_work_buffer.Reset(nullptr);' in session_cpp
assert 'Kernel::KScopedAutoObject<Kernel::KTransferMemory> m_work_buffer;' in session_h
assert 'm_work_buffer{system_.Kernel()}' in session_cpp
assert 'KScopedAutoObject' in session_h

source=r'''
#include <cassert>
#include <cstddef>
#include <memory>
#include "core/hle/service/am/service/native_video_work_buffer.h"
struct Process { int id{}; };
struct Transfer {
 const Process* owner{};
 bool initialized{};
 std::size_t size{};
 bool IsInitialized()const{return initialized;}
 const Process* GetOwner()const{return owner;}
 std::size_t GetSize()const{return size;}
};
int main(){
 using namespace Service::AM::VideoDecoderProtocol;
 Process a{1},b{2};
 Transfer one{&a,true,4096};
 assert(IsWorkBufferOwned(&one,&a));
 assert(!IsWorkBufferOwned(&one,&b));
 assert(!IsWorkBufferOwned(&one,static_cast<Process*>(nullptr)));
 assert(!IsWorkBufferOwned(static_cast<Transfer*>(nullptr),&a));
 one.initialized=false;
 assert(!IsWorkBufferOwned(&one,&a));
 one.initialized=true;
 one.owner=nullptr;
 assert(!IsWorkBufferOwned(&one,&a));
 assert(!IsValidWorkBufferSize(0));
 assert(!IsValidWorkBufferSize(4095));
 assert(IsValidWorkBufferSize(4096));
 assert(!IsValidWorkBufferSize(4097));
 assert(IsValidWorkBufferSize(4096*129));
 assert(!IsValidWorkBufferSize(4096*129+1));
}
'''
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-ns2-video-workbuf-') as directory:
    cpp=Path(directory)/'workbuf.cpp';cpp.write_text(source)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            exe=Path(directory)/(Path(compiler).name+opt)
            cmd=[compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                 '-I',str(root_dir),str(cpp),'-o',str(exe)]
            built=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=80)
            assert built.returncode==0,(cmd,built.stderr[-2200:])
            executed=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=20)
            assert executed.returncode==0,(cmd,executed.stderr[-2200:])
            print(Path(compiler).name,opt,'P1_VIDEO_WORK_BUFFER_OWNERSHIP_PASS',flush=True)
print('P1_NATIVE_VIDEO_TMEM_OWNER_PASS foreign=refused closed=refused invalid_size=refused kernel_ref=retained')
