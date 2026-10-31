# NSW2 / EglantinePS5: real-console gap and shared-engine corrective action
Date: 2026-10-31
Scope: research/ns2-ps5-compatibility; main untouched.

## Source evidence reviewed

- EglantinePS5 3bd1f78:
  https://github.com/heydemoura/EglantinePS5/commit/3bd1f7866b8ce940651af89d9b7b735d82280472
  Author reports a Switch 2 guest running ~4 minutes on a real PS5 before the
  shared CPU/GPU pool is exhausted: guest ~4.6 GiB; heap ~2.6 GiB in use;
  graphics allocator ~2.3 GiB. This is THEIR console observation, not ours.
- EglantinePS5 4cf7004:
  https://github.com/heydemoura/EglantinePS5/commit/4cf7004310
  Uses lazily backed guest physical memory, shrinkable heap arenas, lazy JIT
  memory commitment, exact-size staging and direct-memory free-block metrics.
  The CPU guest and Vulkan allocations compete for the same console pool.
- EglantinePS5 ca54313:
  https://github.com/heydemoura/EglantinePS5/commit/ca54313588
  BC6H 8192 x 8192, 68 layers, 12 mips (~5.8 GiB entire chain) overwhelmed
  sparse driver ranges. Trimming high-resolution mips trades visual fidelity
  for memory. It is not proof of full sparse residency.
- EglantinePS5 1aeeb8c:
  https://github.com/heydemoura/EglantinePS5/commit/1aeeb8cf1e
  The first heap instrumentation read execute-only PS5 code, crashed, and
  required correction. Never port this unsafe probe or scan unmapped stacks.

## Actual Encore reuse (Switch 1 + Switch 2)

Already shared: maintained Dynarmic A64/JIT, Vulkan renderer, PS5 Mesa/RADV,
scheduler, VMA native allocation, Image/ImageView RAII, texture cache.
The independent vendor repository is pinned as a Git submodule.
Importantly, Encore already has direct-pool memory measurements in
headless/performance.h, feeding Device::GetDeviceMemoryUsage on PS5 with
the shared-pool-backed mode. Do not claim we lacked this feature entirely.

NS2-specific: Ampere ISA and translation, SVC/IPC and new GPU channel
semantics, NS2 metadata/loader, process permissions and shader capture.
These adapt to existing owners. A whole second renderer is not justified.

Shared cross-generation candidates: memory headroom, allocation scheduling,
sparse residency, page/heap alignment, shader queue synchronization, texture
view retirement, fault-safe logging and cache pressure detection.

## N75 -- implemented in common Vulkan vendor code

New native Vulkan owner:
vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_shared_gpu_budget.h

Eden::Vulkan::MemoryPolicy::SparseBackingBudget receives shared-pool capacity,
reported usage and whether the metric is genuinely pool-backed, plus the
existing per-image sparse limit. When measured, reserve 1 GiB (or 1/8 for a
smaller pool) for the rest of the emulator and console before allowing VMA
pages. Do not double-count visible VRAM, and never infer unavailable metrics.

The existing cache-side research probe feeds the actual PS5 shared-pool
usage ONLY if the common performance metric is in pool-backed mode. A
limited GPU memory pool must reject an expensive sparse image globally,
not only after reaching the static per-image 384/768 MiB cap.
The nonresearch dense image path is completely unchanged.

Clang/GCC UBSan tests cover unknown and corrupt metrics, normal free space,
actual shared-pool pressure, and admission rejection before binding.

This is a shared-engine infrastructure improvement, not a claim that
Encore can boot a Switch 2 game.

## Revised critical path

1. Diff Eglantine's actually tested guest lazy backing, GPU channel and
   KProcess boot against our maintained owners. Integrate portable fixes
   with proper credit; no wholesale renderer or core snapshots.
2. Real NSW2 program to main NSO, KProcess, GPU channel, Ampere shader,
   native Vulkan image and visible PS5 frame. Host tests are not console proof.
3. Control shared CPU/GPU residency, huge BCn/ASTC arrays and fidelity.
   Do not silently drop mips in general-purpose emulation.
4. Once a change proves safe, promote common infrastructure for NS1 and
   NS2 through vendor; never make game-name/serial-specific exceptions.
5. Keep research isolated. Do not merge into main until explicitly asked
   and actual PS5 validation permits it.

Percent complete is not quantifiable from mocked contracts. Real NSW2
gameplay on Encore PS5 remains unverified.
