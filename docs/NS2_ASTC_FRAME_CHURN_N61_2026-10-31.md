# NSW2 N61 — synthetic streaming texture freshness stress

Standalone test of **real N55/N59 C++ planner + bounded staging coordinator** with 68 virtual layers × 21 MiB, over 2,400 synthetic frames.

Each frame deterministically modifies 1–5 layers and verifies that submitted staged bytes match their guest layer addresses, no batch exceeds 64 MiB, each decoded layer receives the latest available guest epoch, and no stale layer survives successful completion. Every 47th frame injects a CPU write during a decode; N59 must reject the stale generation and preserve pending writes. Every 149th frame injects a failed guest read; N59 must invalidate and a simulated full-image upload restores coherency. The test also tracks saved guest transfer volume versus the entire virtual array and runs Clang/GCC with UBSan.

This represents only the data-movement and generation logic. **It does not consume real FC27 assets, run a PS5 GPU, allocate sparse Vulkan images, measure FPS, or prove N60's native texture-cache lock/thread behavior.** No console validation requested. N60 remains OFF by default; this stress test does not authorize shipping it.

Additional owner-composition gate: N60's generated texture cache must also retain N54's >64 MiB scratch trim when both options are chosen. CMake watches the underlying header/adapter inputs for regeneration.
