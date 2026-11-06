#!/usr/bin/env python3
"""P1.3 active NVDRV session/FD admission, using real owner C++ preflights."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
vendor_root = root / 'vendor'
if not (vendor_root / 'encore-active').exists():
    vendor_root = root.parent / 'vendor'  # isolated sparse host checkout
vendor = vendor_root / 'encore-active/eden-core/src/core/hle/service/nvdrv'
container = (vendor / 'core/container.cpp').read_text()
core_nvmap = (vendor / 'core/nvmap.cpp').read_text()
interface = (vendor / 'devices/nvmap.cpp').read_text()
cmake = (root / 'headless/CMakeLists.txt').read_text()
original = (vendor_root / 'sources/eden/src/core/hle/service/nvdrv/core/container.cpp').read_text()
assert 'return &impl->sessions[session_id.id];' in original
assert 'EDEN_MAINTAINED_NVDRV_NVMAP_CORE' in cmake
assert 'EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE' in cmake
assert 'list(APPEND core_sources' in cmake
for owner in ('hle/service/nvdrv/core/nvmap.cpp', 'hle/service/nvdrv/devices/nvmap.cpp'):
    assert owner in cmake
assert cmake.index('list(REMOVE_ITEM core_sources\n    hle/service/nvdrv/core/nvmap.cpp') < cmake.index('set_property(TARGET core PROPERTY SOURCES "${core_sources}")', cmake.index('EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE'))
assert core_nvmap.count('if (!session || !session->mapper)') == 1
assert core_nvmap.count('if (!session || !session->process)') == 1
assert core_nvmap.index('if (!session || !session->process)') < core_nvmap.index('session->has_preallocated_area')
assert 'EDEN_NVMAP_REJECT_ZERO_ADDRESS' in interface
assert 'EDEN_NVMAP_MAP_FAILED' in interface
assert interface.count('sessions[fd]') == 1  # only the OnOpen insertion
start = 'Session* Container::GetSession(SessionId session_id) {'
assert container.count(start) == 1
lookup = start + container.split(start, 1)[1].split('\n}', 1)[0] + '\n}'
assert 'session_id.id >= impl->sessions.size()' in lookup
assert 'session.is_active && session.process' in lookup

def section(code, begin, end):
    return code.split(begin, 1)[1].split(end, 1)[0]
alloc = section(interface, 'NvResult nvmap::IocAlloc(', 'NvResult nvmap::IocGetId(')
free = section(interface, 'NvResult nvmap::IocFree(', '} // namespace Service::Nvidia::Devices')
assert 'auto* const session = container.GetSession(session_it->second)' in alloc
assert 'auto* const session = container.GetSession(session_it->second)' in free
assert alloc.index('const auto session_it = sessions.find(fd);') < alloc.index('handle_description->Alloc(')
assert free.index('const auto session_it = sessions.find(fd);') < free.index('file.FreeHandle(')

def guard(s: str) -> str:
    start = '    const auto session_it = sessions.find(fd);'
    end = '    if (auto freeInfo{' if '    if (auto freeInfo{' in s else '    const auto result ='
    assert s.count(start) == 1 and s.count(end) == 1
    return s[s.index(start):s.index(end, s.index(start))]

# The complete checked fragments are compiled directly with a real deque and
# unordered_map; invalid FDs cannot call the simulated mutation counter.
fixture = r'''
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <limits>
#include <memory>
#include <unordered_map>
struct SessionId { std::size_t id; };
struct Session { bool is_active{}; void* process{}; };
struct ContainerImpl { std::deque<Session> sessions; };
struct Container {
 std::unique_ptr<ContainerImpl> impl = std::make_unique<ContainerImpl>();
 Session* GetSession(SessionId id);
};
__LOOKUP__
enum class NvResult {Success, BadValue};
struct Device {
 Container& container;
 std::unordered_map<int,SessionId> sessions;
 unsigned allocations{};
 unsigned frees{};
 NvResult CheckAlloc(int fd) {
__ALLOC_GUARD__
  ++allocations;
  return NvResult::Success;
 }
 NvResult CheckFree(int fd) {
__FREE_GUARD__
  ++frees;
  return NvResult::Success;
 }
};
int main() {
 Container c;
 Device dev{c,{},0,0};
 assert(c.GetSession({0}) == nullptr);
 assert(c.GetSession({std::numeric_limits<std::size_t>::max()}) == nullptr);
 c.impl->sessions.push_back({true,reinterpret_cast<void*>(1)});
 c.impl->sessions.push_back({false,reinterpret_cast<void*>(2)});
 c.impl->sessions.push_back({true,nullptr});
 assert(c.GetSession({0}) == &c.impl->sessions[0]);
 assert(c.GetSession({1}) == nullptr);
 assert(c.GetSession({2}) == nullptr);
 for(int fd : {-1,0,3,55}) {
  assert(dev.CheckAlloc(fd) == NvResult::BadValue);
  assert(dev.CheckFree(fd) == NvResult::BadValue);
 }
 assert(dev.allocations == 0 && dev.frees == 0);
 dev.sessions.emplace(20, SessionId{0});
 dev.sessions.emplace(21, SessionId{1});
 dev.sessions.emplace(22, SessionId{999999});
 assert(dev.CheckAlloc(21) == NvResult::BadValue);
 assert(dev.CheckFree(21) == NvResult::BadValue);
 assert(dev.CheckAlloc(22) == NvResult::BadValue);
 assert(dev.CheckFree(22) == NvResult::BadValue);
 assert(dev.CheckAlloc(20) == NvResult::Success);
 assert(dev.CheckFree(20) == NvResult::Success);
 assert(dev.allocations == 1 && dev.frees == 1);
 c.impl->sessions[0].is_active = false;
 assert(dev.CheckAlloc(20) == NvResult::BadValue);
 assert(dev.CheckFree(20) == NvResult::BadValue);
 assert(dev.allocations == 1 && dev.frees == 1);
}
'''
code = fixture.replace('__LOOKUP__', lookup)
code = code.replace('__ALLOC_GUARD__', guard(alloc))
code = code.replace('__FREE_GUARD__', guard(free))
compilers = list(dict.fromkeys(filter(None, (shutil.which('clang++'), shutil.which('g++')))))
assert compilers
sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env = os.environ.copy()
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-p13-fd-') as temp:
    source=Path(temp)/'owners.cpp'
    source.write_text(code)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            exe=Path(temp)/(Path(compiler).name+opt)
            cmd=[compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                 str(source),'-o',str(exe)]
            build=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
            assert build.returncode==0,(cmd,build.stderr[-3500:])
            run=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
            assert run.returncode==0,(cmd,run.stderr)
            print(Path(compiler).name,opt,'P1_3_NVDRV_SESSION_FD_OWNER_PASS',flush=True)
print('P1_3_NVDRV_OWNER_SELECTION_PASS active_cpp=3 valid_fd=1 false_fd=refused closed_session=refused mapped_rollback=retained')
