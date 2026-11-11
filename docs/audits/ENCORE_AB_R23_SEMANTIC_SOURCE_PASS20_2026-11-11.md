# R23 pass 20 — #57 NCE GPU-readback feature removed upstream after #47

**11 Nov 2026 · E1 source semantic audit, PR #45 only.** Official Eden [#57 `0e11fe8b5e`](https://github.com/eden-emulator/mirror/commit/0e11fe8b5e3d3b563946726ed06cb44b2bf5ccb3) is reviewed as a historical intermediate change, not an open PS5 optimization candidate.

## Scope of upstream #57

The commit removes the early `nce_invalidation_gpu_readback` setting from Android UI/resources, `src/common/settings.h` and Qt translations. It also modifies GPU invalidation and introduces `TryCacheInvalidation` in `rasterizer_interface.h` and `renderer_vulkan/vk_rasterizer.cpp/.h`. Its title "readback" therefore **must not** be used as evidence that all changes are Android-only; it once modified common GPU behavior.

## Explicit net-revert evidence

Official [#47 `b4d576001417`](https://github.com/eden-emulator/mirror/commit/b4d5760014176bfc42b60b7dc5661240c97c8e3b), later in this exact 155-commit window, removes the GPU readback implementation, including the `TryCacheInvalidation` changes. The existing [net Git blob proof](ENCORE_AB_R23_NCE_GPU_REVERT_NET_PROOF_2026-11-11.md) compares upstream **before #88** (`f8b76511041bb54070c52d1d09ea07d8108c592a`) with **after #47** (`b4d5760014176bfc42b60b7dc5661240c97c8e3b`): `core/memory.cpp`, `video_core/gpu.cpp/.h` and `vk_rasterizer.cpp/.h` are blob-identical; `rasterizer_interface.h` differs only in its SPDX notice. That covers every GPU C++ file modified by #57. Its remaining changes remove an already default-disabled temporary NCE setting and Android/Qt UI labels, not a PS5 x64 code path. The feature should **not** be reintroduced.

**Disposition:** `reviewed-NCE-GPU-readback-reverted-non-native-settings` for #57 only. This is an E1 retrospective net-code review, **not** a PS5 GPU correctness certification and **not** a reason to exclude #6's later, distinct shared GPU dirty-page ownership fix.

## Counts

After passes 18/19, 29 general semantic reviews → **28**. Retain **22** real source gaps, **8** scoped policy/refactor gates, **17** native header receipts and **7** corrective release gates. No main/vendor/NS2 changes, emulator compilation, or PS5 device test.
