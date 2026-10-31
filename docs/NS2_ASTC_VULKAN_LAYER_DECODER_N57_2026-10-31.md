# NSW2 N57 — PS5 native ASTC per-layer Vulkan decoder (2026-10-31)

Branch `research/ns2-ps5-compatibility`; no main/vendor/release change. Explicit `EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL=ON` only, OFF by default.

This adds a **real but not yet invoked** per-layer ASTC compute entrypoint, generated from the maintained PS5 Vulkan texture and compute source owners, not from upstream desktop replacement files. Core portions:
- a distinct storage view per array layer and host mip level, retaining and owning each VkImageView for the image lifetime;
- `ASTCDecoderPass::AssembleLayers` targeting each selected 2D array layer with one z=1 compute dispatch and the existing PS5 descriptor queue, scheduler barriers and flush;
- runtime `AccelerateImageUploadLayers` rejecting non-ASTC / unavailable accelerated decoders instead of silently marking upload successful;
- a bounded preflight contract ensuring staging contains every whole layer, layers are unique and in-bounds, mip byte offsets are valid, and the image is **already initialized**. Images with a skipped host mip chain are rejected pending further verification.

The full normal `ASTCDecoderPass::Assemble` remains unchanged. CMake replaces only two actual native PS5 Vulkan translation-unit sources and two pinned headers, keeping PS5 HDR, screen, rasterizer, scheduler and normal Switch 1 path unchanged.

Tests: source-conservative generator / exact owner checks and Clang/GCC UBSan contract tests. **Limitation:** the texture-cache writer still uses the full-image upload path: N55's dirty-layer planner is not yet wired to this decoder. No native PS5 compilation/console result, image readback, FC27 regression conclusion or NSW2 title compatibility claim. Next: safely connect the dirty-write recorder, staged batches and GPU completion barrier, then attempt automated Vulkan readback validation. No console test requested.

## N57b pinned image metadata correction
N57 initially referenced `Image::host_level_offset`, present upstream but absent from the pinned native PS5 vendor. N57b removes the nonexistent member and rejects skipped-mip staging where the first level or first buffer offset is nonzero. It also explicitly includes `<stdexcept>` in the generated Vulkan compute source and tests these guards. Full native PS5 Vulkan compilation remains unverified.

## Vendor ownership update

N57's fail-closed layer/mip preflight now lives once in `vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_astc_decode_preflight.h`. The original `headless/ns2` copy is removed. The experimental Vulkan source adapter remains research-only until audited native compilation and GPU readback.
