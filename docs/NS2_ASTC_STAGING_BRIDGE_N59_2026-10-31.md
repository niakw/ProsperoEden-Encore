# NSW2 N59 — bounded per-layer ASTC staging transaction

Research branch only. This is an **executable C++ upload coordinator** for the N55 dirty-layer planner, but is not yet invoked by the normal texture-cache refresh.

N59 makes the staging and GPU-decode callbacks act as one logical transaction. It creates at most one bounded staging allocation per batch, reads exactly the selected guest layer ranges into the associated staging offsets and calls the N57 per-layer decode backend with the matching layer indices. It only clears dirty bits after all decoder callbacks report success. A concurrent guest CPU write advances the N55 generation and prevents commit; no write is dropped.

On allocation, guest read or Vulkan submission failure, N59 invalidates the partial state so the next refresh must use the existing full-image fallback. A guest base overflow or malformed staging range also fails closed. The callback interface is synchronous; the future N60 native backend must ensure dispatch completion/synchronization before returning and must not release staging memory while GPU reads it.

Host test: real N55 planner with a synthetic 68×21 MiB virtual ASTC terrain array and seven dirty layers, which reduces the simulated guest bytes read to 147 MiB in three ≤63 MiB staging batches. Allocation/read/dispatch failures, race, overflow, no-op and full fallback verified under Clang/GCC UBSan. These are **not FPS or real Vulkan GPU performance measurements**.

Remaining: introduce N60 image lifetime tracking and connect the N59 coordinator to the pinned native PS5 `TextureCache<P>::WriteMemory/RefreshContents`, with a true Vulkan backend `ASTCDecoderPass::AssembleLayers` and correct mip/layer staging, then validate images and GPU synchronization. No console test requested.
