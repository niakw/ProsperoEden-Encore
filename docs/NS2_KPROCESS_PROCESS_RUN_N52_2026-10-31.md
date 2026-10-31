# NSW2 N52 — actual OS process run gate (2026-10-31)

Branch: `research/ns2-ps5-compatibility`. All modifications are opt-in and absent from shipping `main` and vendor.

## Real N48 failure mechanism
The pinned `Service::Process::Run` ignored the return value of **real** `Kernel::KProcess::Run` while marking `m_process_started=true`, even when thread allocation, stack admission or the scheduler rejected startup. N52 uses the real kernel result only for the PID registered by the NS2 ExeFS loader after genuine KProcess+NSO handoff. It logs `result.raw`, returns false, marks the start as attempted to prevent a second `KProcess::Run` on a potentially half-initialized process, and unregisters only the matching process's bounded SVC trace. Success returns true once. The unchanged Switch 1 path remains below the N52 gate.

Experimental CMake: `EDEN_NS2_PROCESS_RUN_GUARD_EXPERIMENTAL=ON`, available ONLY with native PS5, experimental ExeFS and experimental metadata, forbidden for final release. Source parity checker enforces exact insertion into the pinned OS process .cpp, no generic engine/vendor modification.

Clang/GCC UBSan host harness executes the extracted **actual** `Process::Run` body against fake kernel-run values: successful NS2, denied NS2 and no retry, non-NS2 legacy behavior, null process, stale PID and unrelated PID preservation. Separate Clang syntax checks compile the full selected owner against the pinned headers.

Evidence limits: the host harness stubs kernel responses and cannot establish real full-core Switch 2 boot. Native PS5 build and real `KProcess::Run` scheduling remain unobserved. No console test, merge or release.
