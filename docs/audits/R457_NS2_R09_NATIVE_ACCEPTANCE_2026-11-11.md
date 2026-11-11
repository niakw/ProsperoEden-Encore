# Eden Encore PS5 native integration acceptance — 11 November 2026

Source SHA before build trigger: `f5ed4b6c4c83f2220f390edcc6d4210e4193c0f7`.

Integrated production sources: NS1 six-core ABI, NS2 12 GiB sparse virtual/physical owner, native R2/R3/R4, launcher cover dual-worker decode, PR47 warning/provenance, PR48 Node24, R09 vendor 720p/1080p readback, ViT nine-slot pool, FSwin shared scratch, A4K image/view return, R09 720p geometry/composition validation source.

## Native acceptance must prove

1. Native CMake selected actual PS5 source owners and compiled every changed translation unit.
2. Complete link and exactly one canonical distribution ZIP; no replay of previous R457 binary.
3. Proper R437 vs R2 exact source reconstruction and Vulkan additive SHA manifests.
4. On real PS5: NS1 actual game start, NS2 12 GiB guest VA backing with bounded committed physical memory, first frame and device/GPU alias lifetime.
5. Launcher actual console image orientation, complete front/rear case loading, light/dark/Neon focus, firmware family summary and transition without black flashes.
6. DLSS-NR Original/Compact 720p trained 152-stage Vulkan execution and output/image quality, separate from source/host qualification.

Host source validation does not establish gameplay success. This commit requests one canonical native application build and no GitHub Release publishing. The 720p trained DLSS-NR graph is not qualified yet; do not misreport success.
