# NSW2 N46 — executable original KProcess::LoadModule host contract

Branch: \`research/ns2-ps5-compatibility\`. Date: 2026-10-31.
No release or \`main\` merge. Public source/fixture only; no firmware or keys.

The previous N44 contract tested real \`KCapabilities\` decoding and real
Dynarmic A64 execution separately; N45 bounded ExeFS page-count conversion.

## New executable kernel boundary
\`.github/workflows/ns2-research-jit.yml\` now runs
\`tools/ns2/test_real_kprocess_loadmodule.py\` after building the pinned,
independently sourced HOS AArch64 \`main\` NSO and before executing Dynarmic.

The harness extracts the **exact unchanged method body** of
\`Kernel::KProcess::LoadModule\` from
\`vendor/sources/eden/src/core/hle/kernel/k_process.cpp\`, verifies anchors,
then compiles that source as C++20 under **Clang and GCC ASan/UBSan**.

It builds the publicly audited three-segment image from actual NSO0 bytes:
text at +0, rodata at +0x1000, data at +0x2000, 0x1000 BSS,
with all header boundaries, compressed size, overlap and markers verified.
The real kernel member method is then **executed**, with only its enclosing
\`KProcess\`, guest memory \`WriteBlock\`, \`KernelCore\` and page-table permission
setter replaced by deterministic host fakes. Assertions verify:
- one exact guest-memory write, matching the entire staged source image;
- actual original AArch64 text, rodata and data at original virtual offsets;
- zero-filled BSS and gaps;
- all three memory-permission calls: R-X, R, and RW at base+segment offsets;
- fail-closed invalid magic, compressed flag, overlap and truncated NSO input.

This is **real \`KProcess::LoadModule\` method execution, not a real
\`KProcess\` instance**: \`LoadFromMetadata\`, page tables, process memory,
service manager, SVC dispatcher, scheduler, \`Core::System::Load\` and native PS5
renderer are **not** executed. The fixture is generic lawful HOS homebrew,
not a commercial Nintendo Switch 2 game.

Remaining actual boot prerequisite: run the complete ExeFS
\`AppLoader_DeconstructedRomDirectory::Load\` with an initialized production
\`Kernel::KProcess\` and run the guest SVC trace through real HLE. Host-fake
execution is meaningful narrowing, never evidence of Switch 2 game support.
