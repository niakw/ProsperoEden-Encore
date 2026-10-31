#!/usr/bin/env python3
"""N52 exact production OS Process::Run body parity plus single NS2-only insertion."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'vendor/sources/eden/src/core/hle/service/os/process.cpp'
PORT=ROOT/'headless/ns2/overrides/core/hle/service/os/process.cpp'
TRACE=ROOT/'vendor/encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
def once(s,a,b):
    assert s.count(a)==1,'OS process source owner drift: '+a[:80]
    return s.replace(a,b)
old='''    // Start.
    if (m_process) {
        m_process->Run(m_system.Kernel(), m_main_thread_priority, m_main_thread_stack_size);
    }'''
new='''    // N52: only the real NS2 ExeFS process registered during loader handoff
    // must treat a kernel scheduling failure as a failed launch. Keep Switch 1
    // semantics byte-for-byte below, until generic behavior is independently audited.
    if (m_process && m_process->GetProcessId() != 0 &&
        Eden::NS2::SvcTrace::active_pid.load(std::memory_order_acquire) ==
            m_process->GetProcessId()) {
        const auto result =
            m_process->Run(m_system.Kernel(), m_main_thread_priority, m_main_thread_stack_size);
        if (R_FAILED(result)) {
            LOG_ERROR(Service_LDR, "NS2 KProcess::Run rejected pid={} result={:#x}",
                      m_process->GetProcessId(), result.raw);
            // KProcess may already have allocated/rolled back resources; never
            // start it twice without Finalize and a fresh loader handoff.
            m_process_started = true;
            Eden::NS2::SvcTrace::Unregister(m_process->GetProcessId());
            return false;
        }
        m_process_started = true;
        return true;
    }

    // Start.
    if (m_process) {
        m_process->Run(m_system.Kernel(), m_main_thread_priority, m_main_thread_stack_size);
    }'''
original=SRC.read_text()
expect=once(original,'#include "common/scope_exit.h"','#include "common/scope_exit.h"\n#include "common/logging.h"\n#include "core/loader/ns2_svc_trace.h"')
expect=once(expect,old,new)
assert expect==PORT.read_text(),'N52 production Process.cpp parity changed; reject'
assert 'inline void Unregister(std::uint64_t pid)' in TRACE.read_text()
assert 'EDEN_NS2_PROCESS_RUN_GUARD_EXPERIMENTAL OR' in CMAKE
assert 'list(FIND eden_ns2_os_sources "hle/service/os/process.cpp"' in CMAKE
assert 'NOT PS5_NATIVE OR NOT EDEN_NS2_EXEFS_EXPERIMENTAL OR' in CMAKE
print('N52_REAL_OS_PROCESS_OWNER_PARITY_PASS')
