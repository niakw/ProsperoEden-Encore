# NSW2 N54 — maintained vendor ASTC scratch trim (31 October 2026)

N54 is a generic **experimental** CPU scratch optimization. It remains OFF by default and cannot be enabled in the final PS5 release profile. No title IDs or game-specific behavior are used.

## Maintained source
- `vendor/encore-active/ns2-astc/include/common/scratch_buffer.h`: `release()` drops oversized transient storage, and zero-byte copy after release is avoided.
- `vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h`: **based on the shipping patched Eden backport**, with >64 MiB swizzle/unswizzle scratch trimmed at `TickFrame`. A capacity of exactly 64 MiB stays cached.
- The old N54 CMake header generator was removed. The pinned research submodule points to one versioned vendor owner; the original Eden source archive remains immutable.

## Build and verification
The optional `EDEN_NS2_ASTC_SCRATCH_RELEASE_EXPERIMENTAL=ON` requires PS5-native NSW2 research metadata. Its include override applies to `common` and `video_core` only for opt-in development builds, not the normal Switch 1/release execution. When N60 is enabled, its still-experimental ASTC cache integration uses the exact same vendored texture-cache owner, guarded independently via `EDEN_NS2_ASTC_CACHE_BRIDGE`. No copy is constructed from that file.

The N54 host gate checks byte-for-byte scratch source parity, source-extracts the real maintained frame-trim implementation, and the companion N60 gate pins the complete combined texture-cache owner to its reviewed Git object SHA. Clang/GCC ASan/UBSan exercise the **actual vendor header** and extracted `TickFrame` logic; N60 checks that both contracts compose. No real GPU readback, PS5 RAM/FPS measurements, concurrent decode proof, or console tests are claimed.

Remaining migration: N57 and N60 ASTC Vulkan/cache adapters; older N56 and kernel overlays. Sparse residency is not activated.
