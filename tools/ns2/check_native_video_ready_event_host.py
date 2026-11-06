#!/usr/bin/env python3
"""P1.3: replay actual maintained auto-clear ready-event lifetime semantics."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vroot=root/'vendor'
if not (vroot/'encore-active').exists():vroot=root.parent/'vendor'
base=vroot/'encore-active/ns2-runtime/video_decoder/core/hle/service/am/service'
header=(base/'native_video_ready_state.h').read_text()
owner=(base/'graphics_video_decoder_session.cpp').read_text()
recipe=(root/'headless/CMakeLists.txt').read_text()
assert 'class NativeVideoReadyState' in header
assert 'std::scoped_lock lock{m_mutex};' in header
assert 'if (m_running && m_room && m_pulse) m_pulse();' in header
assert 'm_pulse = {};' in header
assert 'm_ready->Attach([event, &kernel = system.Kernel()]' in owner
assert 'm_ready_timer = Core::Timing::CreateEvent(' in owner
assert 'ScheduleLoopingEvent(Interval, Interval, m_ready_timer)' in owner
assert 'std::chrono::milliseconds{4}' in owner
assert 'm_ready->Detach();' in owner
assert 'system.CoreTiming().UnscheduleEvent(m_ready_timer)' in owner
assert owner.index('m_ready->Detach();') < owner.index('m_context.CloseEvent(m_event)')
assert 'm_ready->Set(m_started, m_pending.size() < MaxFrames);' in owner
assert 'm_ready->Set(false, false);' in owner
# A terminal guest Finalize must retire the CoreTiming periodic callback
# immediately, before the original event handle can be cleared or closed.
# Merely disabling readiness while leaving a 4ms loop alive leaks work for
# as long as the finalized IPC object remains referenced.
finalize = owner.split('void IGraphicsVideoDecoderSession::Finalize(', 1)[1].split(
    '\nvoid IGraphicsVideoDecoderSession::GetEvent(', 1)[0]
assert finalize.count('m_ready->Detach();') == 1
assert finalize.count('system.CoreTiming().UnscheduleEvent(m_ready_timer);') == 1
assert finalize.count('m_ready_timer.reset();') == 1
assert finalize.index('m_ready->Set(false, false);') < finalize.index('m_ready->Detach();')
assert finalize.index('m_ready->Detach();') < finalize.index('UnscheduleEvent(m_ready_timer)')
assert finalize.index('m_ready_timer.reset();') < finalize.index('m_event->Clear(system.Kernel())')
assert finalize.index('m_event->Clear(system.Kernel())') < finalize.index('m_finalized = true;')
assert 'native_video_ready_state.h' in recipe
assert 'm_ready->SetRoom(m_pending.size() < MaxFrames);' in owner
fixture=r'''
#include <atomic>
#include <cassert>
#include <memory>
#include <thread>
#include "core/hle/service/am/service/native_video_ready_state.h"
int main() {
 using Service::AM::VideoDecoderProtocol::NativeVideoReadyState;
 auto state=std::make_shared<NativeVideoReadyState>();
 std::atomic<unsigned> pulses{};
 state->Attach([&pulses] { pulses.fetch_add(1, std::memory_order_relaxed); });
 state->Notify();
 assert(pulses.load()==0);
 state->Set(true,true);
 state->Notify();state->Notify();
 assert(pulses.load()==2);
 state->SetRoom(false);
 state->Notify();assert(pulses.load()==2);
 state->SetRoom(true);state->Notify();assert(pulses.load()==3);
 state->Set(false,true);state->Notify();assert(pulses.load()==3);
 state->Set(true,true);
 std::atomic<bool> stop{};
 std::thread worker([state,&stop] {
  while (!stop.load(std::memory_order_acquire)) state->Notify();
 });
 state->Detach();
 const auto snapshot=pulses.load();
 for(int i=0;i<2048;++i)state->Notify();
 assert(pulses.load()==snapshot);
 stop.store(true, std::memory_order_release);
 worker.join();
 state->Set(true,true);state->Notify();
 assert(pulses.load()==snapshot);
}
'''
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
env=os.environ.copy();sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-video-ready-state-') as tmp:
    cpp=Path(tmp)/'ready.cpp';cpp.write_text(fixture)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            exe=Path(tmp)/(Path(compiler).name+opt)
            args=[compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                  '-fsanitize=undefined','-fno-sanitize-recover=all',
                  '-pthread','-I',str(vroot/'encore-active/ns2-runtime/video_decoder'),
                  str(cpp),'-o',str(exe)]
            built=subprocess.run(args,env=env,text=True,capture_output=True,timeout=90)
            assert built.returncode==0,(args,built.stderr[-2800:])
            run=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=15)
            assert run.returncode==0,(args,run.stderr[-2800:])
            print(Path(compiler).name,opt,'P1_NATIVE_VIDEO_READY_EVENT_PASS',flush=True)
print('P1_NATIVE_VIDEO_READY_EVENT_HOST_PASS event_autoclear_rearm=1 full_ring_silent=1 stop_silent=1 detach_safe=1')
