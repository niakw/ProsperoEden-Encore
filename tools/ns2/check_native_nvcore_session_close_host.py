#!/usr/bin/env python3
"""P1.3: host replay of real NVDRV SessionId close-admission C++.

Runs invalid/duplicate/reused FD-facing SessionId probes under UBSan with
real std::deque and std::mutex; no console IOCTL execution or process Close.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCE=(ROOT/'vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/container.cpp').read_text()
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
BASELINE=(ROOT/'vendor/sources/eden/src/core/hle/service/nvdrv/core/container.cpp').read_text()
start='void Container::CloseSession(SessionId session_id) {'
stop='    impl->file.UnmapAllHandles(session_id);'
assert SOURCE.count(start)==SOURCE.count(stop)==1
head=SOURCE[SOURCE.index(start):SOURCE.index(stop,SOURCE.index(start))]
assert 'std::unique_lock lk(impl->session_guard);' in head
bounds='if (session_id.id >= impl->sessions.size()) {'
admit='if (!session.is_active || session.ref_count <= 0 || !session.process) {'
assert head.count(bounds)==head.count(admit)==1
assert head.index('std::unique_lock')<head.index(bounds)<head.index('auto& session =')<head.index(admit)<head.index('if (--session.ref_count > 0)')
assert 'session.ref_count--' not in head
assert 'if (session_id.id >= impl->sessions.size())' not in BASELINE
assert 'set(EDEN_MAINTAINED_NVDRV_CONTAINER' in CMAKE
assert 'list(APPEND core_sources "${EDEN_MAINTAINED_NVDRV_CONTAINER}")' in CMAKE
assert 'std::atomic_thread_fence(std::memory_order_acquire);' in SOURCE
assert 'std::scoped_lock lk(impl->session_guard);' not in SOURCE.split('Session* Container::GetSession(',1)[1].split('NvMap& Container::GetNvMapFile()',1)[0]

fixture=r'''
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <limits>
#include <memory>
#include <mutex>
struct SessionId {std::size_t id;};
struct Session {bool is_active{};int ref_count{};void* process{};};
struct ContainerImpl {
    std::mutex session_guard;
    std::deque<Session> sessions;
    unsigned cleanup_calls{};
};
struct Container {
    std::unique_ptr<ContainerImpl> impl=std::make_unique<ContainerImpl>();
    void CloseSession(SessionId id);
};
__REAL_CLOSE_PREFLIGHT__
    // All GPU unmaps/ASID release/process Close happen only after this point.
    ++impl->cleanup_calls;
    session.is_active=false;
    session.process=nullptr;
}
int main(){
    Container c;
    c.CloseSession({0});
    c.CloseSession({(std::numeric_limits<std::size_t>::max)()});
    assert(c.impl->cleanup_calls==0 && c.impl->sessions.empty());
    c.impl->sessions.push_back({true,2,reinterpret_cast<void*>(0x1)});
    c.CloseSession({0});
    assert(c.impl->sessions[0].ref_count==1 && c.impl->cleanup_calls==0);
    c.CloseSession({8});
    assert(c.impl->sessions[0].ref_count==1 && c.impl->cleanup_calls==0);
    c.CloseSession({0});
    assert(c.impl->cleanup_calls==1 && c.impl->sessions[0].ref_count==0);
    c.CloseSession({0});
    assert(c.impl->cleanup_calls==1 && c.impl->sessions[0].ref_count==0);
    c.impl->sessions.push_back({false,1,reinterpret_cast<void*>(0x2)});
    c.CloseSession({1});
    assert(c.impl->sessions[1].ref_count==1 && c.impl->cleanup_calls==1);
    c.impl->sessions[1]={true,2,nullptr};
    c.CloseSession({1});
    assert(c.impl->sessions[1].ref_count==2 && c.impl->cleanup_calls==1);
    c.impl->sessions[1]={true,0,reinterpret_cast<void*>(0x2)};
    c.CloseSession({1});
    assert(c.impl->sessions[1].ref_count==0 && c.impl->cleanup_calls==1);
    c.impl->sessions[1]={true,1,reinterpret_cast<void*>(0x3)};
    c.CloseSession({1});
    assert(c.impl->cleanup_calls==2 && c.impl->sessions[1].ref_count==0);
    assert(c.impl->sessions[0].ref_count==0);
}
'''.replace('__REAL_CLOSE_PREFLIGHT__',head)
compiler=shutil.which('clang++-18') or shutil.which('clang++') or shutil.which('g++')
assert compiler,'C++20 compiler required'
env=os.environ.copy()
if sys.platform=='darwin' and not env.get('SDKROOT'):
    sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-nvcore-session-close-') as folder:
    source=Path(folder)/'session.cpp';source.write_text(fixture)
    for opt in ('-O0','-O2'):
        exe=Path(folder)/('session'+opt)
        subprocess.run([compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all',
                        str(source),'-o',str(exe)],check=True,env=env,timeout=55)
        subprocess.run([str(exe)],check=True,env=env,timeout=30)
        print('P1_3_NVCORE_SESSION_CLOSE_HOST_PASS',opt,flush=True)
print('P1_3_NVCORE_CLOSE_VALIDATION_PASS malformed=refused duplicate=refused inactive=refused process=guarded valid=one_release ns1_normal=preserved')
