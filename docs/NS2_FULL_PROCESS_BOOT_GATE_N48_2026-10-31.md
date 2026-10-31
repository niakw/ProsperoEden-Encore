# NSW2 N48 — real process bootstrap call-chain audit (31 October 2026)

Scope: `research/ns2-ps5-compatibility` only. Source audit, not a boot,
GPU render or console result. No change to production `main` or `vendor`.

## Verified source owners and actual launch chain

1. `vendor/sources/eden/src/core/core.cpp`: `System::Impl::Load`
   initializes the kernel and calls `Service::AM::CreateApplicationProcess`
   with the game file. It then registers the application handle, initializes
   GPU/CPU/system services and delegates startup to the applet manager.
2. `vendor/sources/eden/src/core/hle/service/am/process_creation.cpp`:
   `CreateProcessImpl` obtains the real `Loader::AppLoader`, constructs
   `Service::Process`, and calls `Process::Initialize`.
3. `vendor/sources/eden/src/core/hle/service/os/process.cpp`:
   `Process::Initialize` calls the real `KProcess::Create`, registers
   the kernel process, calls `loader.Load(*process, system)`, retains
   main-thread priority/stack and transfers ownership only on success.
4. Under experimental source selection,
   `headless/ns2/overrides/core/loader/deconstructed_rom_directory.cpp`
   drives actual `ProgramMetadata::Load`,
   `KProcess::LoadFromMetadata` and
   `AppLoader_NSO::LoadModule` on each ExeFS module. Only the exact
   opt-in path has NS2 preflight, KAC rights and process SVC trace.
5. `vendor/sources/eden/src/core/hle/kernel/k_process.cpp`:
   `KProcess::LoadFromMetadata` hands the computed process parameters to
   `KProcess::Initialize`, where real page tables, resource limits and
   kernel capabilities must be initialized; `KProcess::Run` later creates
   stack, handle table, a `KThread`, main-thread context and scheduler work.

## N44–N47 actual evidence (do not conflate levels)

- N44: unchanged real `KCapabilities::InitializeForUser` on the public
  `main.npdm`, Clang/GCC ASan/UBSan, with five authorized SVCs.
- N45: production ExeFS route rejects zero, misaligned, overflowed
  or unrepresentable combined NSO+patch process code page counts.
- N46: unchanged real **`KProcess::LoadModule` member body** runs on the
  cross-built public `main` NSO against fake guest memory/page table.
- N47: unchanged real **`KProcess::LoadFromMetadata` member body** runs
  on the paired public NPDM/NSO-derived attributes against fake
  `Initialize`, kernel resource and interface objects.
- Separately, the pinned guest AArch64 code runs under maintained
  Dynarmic with deterministic test SVC handlers.

All of these are host research contracts. None creates and schedules a
**complete real `KProcess`** in `Core::System::Load` or executes PS5 HLE
and RADV rendering.

## Specific boot-result diagnostic hazard found

Current `Service::Process::Run` invokes
`m_process->Run(m_system.Kernel(), m_main_thread_priority,
m_main_thread_stack_size)` but **does not check the returned `Result`**.
It unconditionally sets `m_process_started = true` and returns `true`
when the wrapper has been entered. Therefore a failed main-thread creation
or kernel scheduler admission may be reported as successful launch by this
wrapper. This is an upstream source-level finding, NOT an observed NSW2 boot
failure. Do not modify the generic Switch 1 owner as a quick fix.

## Next narrow host test / opt-in change

1. Add a source-bound `Service::Process::Initialize` / `Process::Run`
   lifecycle harness around the **actual** maintained method bodies,
   with controlled loader/kernel fakes, and assert process registration,
   rollback on load failure, ownership and no second start.
2. Add an **NS2-only, fail-closed** diagnostic path for a failed real
   `KProcess::Run` if the guarded source owner can be replaced safely;
   show the actual kernel `Result`, never fabricate HLE success. Test
   both permitted and denied startup, including repeated calls.
3. Only after successful owner-linked compilation, attempt a full-core
   headless ExeFS boot with a real initialized `KernelCore`, kernel
   `KProcess`, SVC bridge and bounded guest trace. Native PS5 hardware,
   RADV and live Switch 2 software are **not** demonstrated by these steps.

No console test is requested from the owner. No automatic merge or release.
