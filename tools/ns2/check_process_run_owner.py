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
assert blob(current)=="848222cf5d15e9f45ef7a26c4b739f3fc1e18926", "N52 native vendor owner changed"
expected=once(current,
    '#include "common/scope_exit.h"\n#ifdef EDEN_NS2_PROCESS_RUN_GUARD\n#include "common/logging.h"\n#include "core/loader/ns2_svc_trace.h"\n#endif',
    '#include "common/scope_exit.h"')
start="#ifdef EDEN_NS2_PROCESS_RUN_GUARD\n    // N52: only the real NS2 ExeFS process"
end="#endif\n\n    // Start."
assert expected.count(start)==expected.count(end)==1, "N52 admission block changed"
i=expected.index(start);j=expected.index(end,i)
expected=expected[:i]+"    // Start."+expected[j+len(end):]
assert blob(expected)=="5e46de245d9086a8b86ff95d8638585ee0229468", "N52 modified unrelated Switch 1 process logic"
assert 'inline void Unregister(std::uint64_t pid)' in TRACE.read_text()
assert 'EDEN_NS2_PROCESS_RUN_GUARD_EXPERIMENTAL OR' in CMAKE
assert 'target_compile_definitions(core PRIVATE EDEN_NS2_PROCESS_RUN_GUARD=1)' in CMAKE
assert 'NOT PS5_NATIVE OR NOT EDEN_NS2_EXEFS_EXPERIMENTAL OR' in CMAKE
assert 'list(REMOVE_ITEM eden_ns2_process_sources "hle/service/os/process.cpp")' in CMAKE
assert 'list(APPEND eden_ns2_process_sources "${EDEN_NS2_NATIVE_PROCESS_SOURCE}")' in CMAKE
assert 'headless/ns2/overrides/core/hle/service/os/process.cpp' not in CMAKE
print("N52_REAL_VENDOR_OS_PROCESS_OWNER_EXACT_BASELINE_PASS")
