# A/B NS1/R18 — current-main vendor drift, shared code reachability and immutable source-family provenance

**Evidence date:** 11 Nov 2026. **Production freeze for this finding:** `niakw/ProsperoEden-Encore@6456590a2b5764412798e2effdfa061c17b4359e` with gitlink `niakw/Prospero.Eden-Encore-vendor@f8f5d8ee3a94a4202886a40badb5c0203d05da30`. This is a different pin from the original A/B audit `22b69d6053db41b74edac2633c012f925b84f69e`. No main, vendor, release or native build edited by PR #45.

## 1 — Exact Git Merkle evidence: immutable dependency roots are still byte-identical

REST Git trees for *both* vendor commit SHAs return identical source-family tree `sources@99ffa030450df670cf039788445e4274d99ebcfb` and archived-object root `objects@43cee153fefe99164820145902d95bce90b2bc8e`. The 26 `vendor/sources` roots and source-object inventory therefore **do not need a second full bytewise recount merely because the gitlink moved**. This is exact Git tree identity, not an official upstream archive digest or linked SBOM. The original source-level findings carry forward unchanged: 35 modified Eden original blobs, 3 inaccessible historic upstream origins, 6/6 local archive byte streams and 8/8 local compiler-rt file checksums, 21/22 CPM inventory totals, Boost 1.90 checkout -1,527 bytes vs lock; 17 missing exact compiler include receipts. See [R18 26-family provenance](ENCORE_AB_R18_26_SOURCE_FAMILY_PROVENANCE_2026-11-10.md) and [Boost/CPM reconciliation](ENCORE_AB_R18_CPM_BOOST_BYTE_DRIFT_2026-11-11.md).

## 2 — The maintained source root **changed** and cannot be waved away

Vendored `encore-active` Git tree changed `dbe71828d37839bc46d29f78067a9b60132b4c98` → `883fa1ee1af407aba0dd6e0c0e619770eed03c7c`. The four ordered commits after the old audited vendor pin are:
- `f9f08786` — shared NS1/NS2 OpenGL template GPU pin guard
- `90c9c8a2` — ASTC/Vulkan cache native pin consistency
- `4b624448` — NS2 R2/R3/R4/sparse native owners
- `f8f5d8ee` — source selector promotion of staging/volume/sparse implementations

**23 file changes** in the exact vendor comparison (including CI/tests). Runtime-risk families include `eden-core/src/core/memory_native_a32.cpp`, `memory_native_standard.cpp`, common `video_core/buffer_cache/buffer_cache.h`, `video_core/textures/decoders.cpp`, Vulkan `vk_buffer_cache_cost.cpp`, `vk_staging_buffer_pool.cpp`, `vulkan_scheduler.cpp`, modified Vulkan headers, and the actual `ns2-astc` TextureCache header. Those are shared engine owners and require NS1 non-regression even if introduced to support NS2. Historical native linker evidence for `main@ec8b519` is not an attestation for `main@6456590` + vendor `f8f5d8e`.

## 3 — Actual source-selector behavior; do not mistake comments for behavior

At frozen main `headless/CMakeLists.txt`, lines 14–18 set `EDEN_REVIEWED_DUAL_NPDM=ON` when `PS5_NATIVE`; lines 209–224 then choose `EDEN_NS2_SPARSE_BACKING` for that native profile and add the exact PS5 C++ owner and compile definitions. Lines 693–715 select one maintained full core memory C++ source depending on `EDEN_A32_FASTMEM` (ON by default at line 258), which makes the changed `memory_native_a32.cpp` directly pertinent to NS1. Lines 1158–1177 use the same dual-NPDM condition for the staging source/header and `EDEN_NS2_STAGE_BACKING=1`; lines 1410–1431 for the actual NS2 ASTC volume code and `EDEN_NS2_VOLUME_COPY=1`; and lines 1492–1517 for the maintained GOB16 decoder. `headless/vulkan.cmake` selects maintained Vulkan owners, not the pristine Eden source.

**Blocking discrepancy:** some CMake/vendor comments say *research*, *experiment*, *off by default*, or *do not enable in production*, but the **source selectors turn these units on for the native dual-NPDM PS5 target**. A comment cannot be used to assert an inactive path. In line with the single-production requirement, classify these as **active candidate production paths needing exact compiler and console qualification**, not as innocuous dormant research. This audit does not invent or enable an experimental user setting.

## 4 — Mandatory shared NS1 regression contract before calling current main qualified

- Freeze one exact main/vendor pair and inspect **actual configured** native `compile_commands.json`, generated headers/depfiles, and link map: one core memory TU, one staging TU, one ASTC TextureCache owner, no double Vulkan/cache/decoder definitions. Revalidate the 17 original header dependencies, plus newly modified shared headers at `f8f5d8e`. Historic CDB and CMake string checks alone do not satisfy this.
- Compile matched *current* maintained memory/graphics owners; test A32 fastmem and standard fallback, allocation denial and guest-page table publication, BufferCache destructor and GPU retirement, partial GPU-written ranges, stage-copy bounds under binding-offset aliasing, sampler/image lifetime, ASTC volume copy and GOB16 decoder under both NS1 and NS2. Negative cases and monotonic GPU completion are mandatory.
- Verify native PS5 binary link/device, FP/CPU6 ABI, NS1 FC27 title launch/frame/audio, renderer/depth/texture/HLE and driver behavior. No successful current-commit console receipt has been supplied by this audit.
- Keep the upstream 155-commit E1 audit [exact semantic ledger](ENCORE_AB_R23_28_RUNTIME_EXIT_CROSSWALK_2026-11-11.md), AB-01..06 correctness, P0 AudioIn/RomFS/RADV/SPIR-V and R18 security/SBOM/licences independent. Nothing in the new vendor pin automatically closes those issues.

## 5 — Security/distribution and what remains unproven

**Proven:** exact historical source trees unchanged for all 26 families and object bundles; locally restored archive digest streams 6/6 and compiler-rt 8/8, existing 21/22 CPM count/size inventory. **Not proven:** independent official archive signatures/checksums for all 22 CPM components, external origin for three 404 pins, Boost archive-vs-lock normalized bytes, actual 12 RADV Meson override object digests/ABI for newest pin, full link/staged SBOM, notices/licences for the exact shipped package, CVEs/security advisories relative to real linked versions, PS5 console runtime. These are **open obligations, not zero risk and not proof of non-compliance**.

**Audit boundary:** no NS2-specific title optimization work or merging. This report exists to prevent false closure of NS1/shared correctness when NS2-related changed sources enter a single shared PS5 binary.
