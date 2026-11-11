# R23 — Dynarmic x64 page-table lookup: 4 upstream commits, 3 source-equivalent decisions

**Date:** 11 November 2026. **Scope:** NS1 A32/A64 guest on PS5 x64 host, E1 source parity only; audit PR #45. No build, vendor modification or main merge.

## Frozen source owners and executable selection

| Evidence | Exact reference |
|---|---|
| Pinned original Eden header | `vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_memory.h`, Git blob `9686e4fc047f78d0863df3ccb5149c8ecc9dc484` |
| Maintained PS5 x64 header | `vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_memory.h`, Git blob `c34906cc34a7b9576025520f1eb7f6416543ef33` |
| Upstream Eden final header | `eden-emulator/mirror@89d1a1cd` `src/dynarmic/src/dynarmic/backend/x64/emit_x64_memory.h`, Git blob `102d451bde6197e46e08cdc9d372755bfe3bce82` |
| Native selection | `headless/CMakeLists.txt` copies the maintained header to `${PORT_BUILD_DIR}/include/dynarmic/backend/x64/emit_x64_memory.h` and adds `${PORT_BUILD_DIR}/include` BEFORE to the `dynarmic` target. Two memory emitter translation units also use maintained complete bodies. **This is a CMake-owner/source-byte proof only; 17 divergent Eden headers still lack live depfile/-H receipts.** |

## Upstream commits assessed against the final native source

| R23 # | Upstream | Semantic source decision |
|---|---|---|
| **#125** | [`7bf95be2`](https://github.com/eden-emulator/mirror/commit/7bf95be2c29328a4cfeb8b2384ce34c6fb6d890c): fix A32 wrong Xbyak LEA scale | **E1 source-equivalent:** actual selected maintained A32 uses `tmp * (1 << page_table_log2_stride)` for stride 0–3, shifted `tmp` fallback for larger strides, not the incorrect `tmp * log2_stride`. No fresh native A32 JIT integration test. |
| **#122** | [`4fe5f62c`](https://github.com/eden-emulator/mirror/commit/4fe5f62c38e71b045d425dc5f4cc4ab83feeafbe): fast A64 scaled page-table lookup | **E1 source-equivalent for final net behavior:** selected maintained A64 same scaled indexing 0–3 and shift fallback above 3. The upstream #122's intermediate change to sign-extension (`63 - shift`) was later reverted in #117. Do not port the intermediate version. |
| **#117** | [`6374f7f5`](https://github.com/eden-emulator/mirror/commit/6374f7f51f0254358fc26a0b3a182f06a9d84ec9): partial revert A64 sign extension | **E1 source-equivalent:** selected maintained A64 uses `code.shl(page, *ctx.conf.page_table_sign_extension)` then arithmetic `sar`, matching final upstream after #117. This is not a statement about all possible PS5 table encodings. |
| **#136** | [`1575f55a`](https://github.com/eden-emulator/mirror/commit/1575f55abee50a563502e5afb098ebed9d5d8995): A32 lookup optimization and changed sign-extension formula | **OPEN — conditional source divergence:** A32 scale path is corrected in maintained code, but the **final upstream A32** shifts by `63 - int(*ctx.conf.page_table_sign_extension)` while the maintained header uses `*ctx.conf.page_table_sign_extension` (and an explicit packed-bit/mask optimization). The two are **not generally equivalent**. Determine which `A32JitConfig.page_table_sign_extension` values/bitmap meanings PS5 actually uses; execute JIT positive/negative translation and invalid/unmapped page tests before calling it safe or importing upstream. |

The original pinned Eden header is older than all four upstream changes; looking only at `vendor/sources` would falsely report every one absent. Equally, seeing the maintained header in a directory does not prove the compiler included it in a particular object. The source-level decisions are therefore E1, **not** E3/E4 or a guarantee against A32 crashes.

## Required negative test to close #136

Trace `page_table_sign_extension` and `page_table_pointer_mask` in the actual A32 JIT configuration, then compare both formulae for representative mapped/marked/unmapped pages and all supported stride sizes (0–3 fast branch; larger fallback). Include addresses with high bits set and the maintained packed pointer-mask branch. Capture compiler header inclusion, A32 JIT source ownership, source-compiled execution and PS5 hardware results at a frozen SHA.

**R23 after source class update:** three source-semantic decisions can be marked conditional E1 equivalence (#117, #122, #125); #136 remains open. Counts should fall from 76 to **73** semantic reviews pending once the source guard CI passes. All 17 divergent header inclusion receipts remain separately open.
