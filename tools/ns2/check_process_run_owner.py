#!/usr/bin/env python3
"""N52: byte-strict generic vendor Process::Run and NS2 compile-guard owner."""
from pathlib import Path
import hashlib
from ps5_kprocess_postload_receipt import normalize_process_receipt

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

current, postload_registered=normalize_process_receipt(SRC.read_text())
# Native H01 adds an explicit filesystem-controller include. Remove only
# this known overlay before checking the unchanged historical NS1 hashes.
current=once(current,
    '''#include "core/loader/ns2_svc_trace.h"
#include "core/hle/service/filesystem/filesystem.h"
#endif''',
    '''#include "core/loader/ns2_svc_trace.h"
#endif''')
# Undo the native-only late-Run finalization before the immutable N52 owner
# hash comparison. NS1's historical Run() method is never modified.
current=once(current,
    '''            // A late failure leaves no runnable NS2 process. Merely
            // clearing its trace would strand the published KProcess and
            // its guest code pages in the kernel process list. KProcess::Run
            // has already unwound its transient stack/thread reservations;
            // Finalize now closes the process, retires RomFS and removes the
            // kernel registration on the same failure path.
            this->Finalize();
            // Do not let a second Run() on the empty failed instance report
            // legacy success. A fresh Initialize() clears this terminal bit.
            m_process_started = true;''',
    '''            // KProcess may already have allocated/rolled back resources; never
            // start it twice without Finalize and a fresh loader handoff.
            m_process_started = true;
            Eden::NS2::SvcTrace::Unregister(m_process->GetProcessId());''')
# H01 has three additional native-only guards in Process::Initialize /
# Finalize. Unwind them IN REVERSE without touching any other owner byte.
# The immutable historical H01 and N52 digests below remain unchanged.
reviewed=once(current,
    '''    SCOPE_EXIT {
        process->Close(m_system.Kernel());
    };
#ifdef EDEN_NS2_PROCESS_RUN_GUARD
    // The NS2 loader may register its SVC trace before Initialize has
    // published the KProcess. Roll it back on every rejected handoff,
    // including missing NPDM parameters or a later allocation failure.
    // This guard runs before the KProcess reference is closed.
    bool process_committed = false;
    SCOPE_EXIT {
        if (!process_committed) {
            // The loader may register RomFS before it installs the SVC
            // trace. A malformed NPDM/NSO or allocation failure in that
            // interval must still release the process-owned filesystem
            // record. UnregisterProcessIfPresent is idempotent for a PID
            // with no registration (including non-NS2 failed loads).
            const auto pid = process->GetProcessId();
            m_system.GetFileSystemController().UnregisterProcessIfPresent(pid);
            Eden::NS2::SvcTrace::Unregister(pid);
        }
    };
#endif

    // Insert process modules into memory.''',
    '''    SCOPE_EXIT {
        process->Close(m_system.Kernel());
    };

    // Insert process modules into memory.''')
reviewed=once(reviewed,
    '''    m_process = process;
    m_process->Open(m_system.Kernel());
#ifdef EDEN_NS2_PROCESS_RUN_GUARD
    process_committed = true;
#endif

    // We succeeded.''',
    '''    m_process = process;
    m_process->Open(m_system.Kernel());

    // We succeeded.''')
reviewed=once(reviewed,
    '''    if (m_process) {
#ifdef EDEN_NS2_PROCESS_RUN_GUARD
        // Retire this PID's filesystem ownership even when the global SVC
        // trace has moved to another process (or was already unregistered).
        // The filesystem operation is idempotent for absent/non-NS2 records;
        // tying it to active_pid leaked RomFS registrations on late teardown.
        const auto pid = m_process->GetProcessId();
        m_system.GetFileSystemController().UnregisterProcessIfPresent(pid);
        // A different active trace belongs to its own process and must
        // survive this teardown.
        if (Eden::NS2::SvcTrace::active_pid.load(std::memory_order_acquire) == pid) {
            Eden::NS2::SvcTrace::Unregister(pid);
        }
#endif
        m_process->Close(m_system.Kernel());''',
    '''    if (m_process) {
        m_process->Close(m_system.Kernel());''')
assert blob(reviewed)=="d2e06b2992d2745940f0c0640b747aae18074986", (
    "H01 rollback normalized to immutable original owner")
pre_h01=once(reviewed,
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
print("N52_REAL_VENDOR_OS_PROCESS_OWNER_EXACT_BASELINE_PASS H01_guarded_transaction=1 H01_trace_rollback=1 H01_independent_romfs_teardown=1 historical_ns1_hash_unchanged=1 postload_registration="+str(int(postload_registered)))
