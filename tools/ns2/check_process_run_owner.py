#!/usr/bin/env python3
"""N52: byte-strict generic vendor Process::Run and NS2 compile-guard owner."""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp"
TRACE=ROOT/"vendor/encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(txt):
    data=txt.encode()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def once(src,old,new):
    assert src.count(old)==1, "N52 maintained source drift "+old[:65]
    return src.replace(old,new)

current=SRC.read_text()
# H01 introduced two independently executed transaction guards in the
# same maintained Process owner. Reconstruct the immutable pre-H01 N52
# source exactly before auditing N52's original Switch 1 baseline.
# Neither the historical byte hash nor any other owner line is rebaselined.
assert blob(current)=="d2e06b2992d2745940f0c0640b747aae18074986", (
    "H01+N52 exact native process owner changed without review")
pre_h01=once(current,
    '''    auto* const process = Kernel::KProcess::Create(m_system.Kernel());
    // The slab allocator can fail before an ExeFS/NSO handoff exists.
    // Never register or dereference a null kernel process on that path.
    if (!process) {
        out_load_result = Loader::ResultStatus::ErrorNotInitialized;
        return false;
    }
    Kernel::KProcess::Register(m_system.Kernel(), process);''',
    '''    auto* const process = Kernel::KProcess::Create(m_system.Kernel());
    Kernel::KProcess::Register(m_system.Kernel(), process);''')
pre_h01=once(pre_h01,
    '''    if (load_result != Loader::ResultStatus::Success) {
        return false;
    }
    // Success without loader parameters is malformed: touching the optional
    // would be undefined behavior and may publish a partially initialized
    // KProcess into the scheduler. The scope guard closes it on failure.
    if (!load_parameters) {
        out_load_result = Loader::ResultStatus::ErrorUnableToParseKernelMetadata;
        return false;
    }

    // TODO: remove this, kernel already tracks this''',
    '''    if (load_result != Loader::ResultStatus::Success) {
        return false;
    }

    // TODO: remove this, kernel already tracks this''')
assert blob(pre_h01)=="848222cf5d15e9f45ef7a26c4b739f3fc1e18926", (
    "H01 guard normalization changed unrelated N52 owner code")
expected=once(pre_h01,
    '#include "common/scope_exit.h"\n#ifdef EDEN_NS2_PROCESS_RUN_GUARD\n#include "common/logging.h"\n#include "core/loader/ns2_svc_trace.h"\n#endif',
    '#include "common/scope_exit.h"')
start="#ifdef EDEN_NS2_PROCESS_RUN_GUARD\n    // N52: only the real NS2 ExeFS process"
end="#endif\n\n    // Start."
assert expected.count(start)==expected.count(end)==1, "N52 admission block changed"
i=expected.index(start);j=expected.index(end,i)
expected=expected[:i]+"    // Start."+expected[j+len(end):]
assert blob(expected)=="5e46de245d9086a8b86ff95d8638585ee0229468", "N52 modified unrelated Switch 1 process logic"
assert 'inline void Unregister(std::uint64_t pid)' in TRACE.read_text()
assert 'option(EDEN_NS2_PROCESS_RUN_GUARD_EXPERIMENTAL' not in CMAKE
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM AND' in CMAKE
assert 'target_compile_definitions(core PRIVATE EDEN_NS2_PROCESS_RUN_GUARD=1)' in CMAKE
assert 'if(EDEN_SHARED_NS2_EXEFS)' in CMAKE and 'EDEN_NS2_EXEFS_EXPERIMENTAL' not in CMAKE
assert 'list(REMOVE_ITEM eden_ns2_process_sources "hle/service/os/process.cpp")' in CMAKE
assert 'list(APPEND eden_ns2_process_sources "${EDEN_NS2_NATIVE_PROCESS_SOURCE}")' in CMAKE
assert 'headless/ns2/overrides/core/hle/service/os/process.cpp' not in CMAKE
print("N52_REAL_VENDOR_OS_PROCESS_OWNER_EXACT_BASELINE_PASS H01_guarded_transaction=1 historical_ns1_hash_unchanged=1")
