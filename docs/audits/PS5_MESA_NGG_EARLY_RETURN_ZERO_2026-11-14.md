# 2026-11-14 — Mesa NGG mesh early-return zero output adaptation (P0 candidate)

**Related:** [engine issue #132](https://github.com/niakw/ProsperoEden-Encore/issues/132), [upstream PS5 Mesa issue #8](https://github.com/mihawk-99/PS5_Mesa/issues/8). This document is source/host triage only. No known causal link to Encore FC27, MKW or Bananza faults; no GPU/PS5 package tests yet.

## Why a safety candidate is warranted

The exact pinned PS5 RADV Mesa source `vendor/sources/ps5-mesa/src/amd/common/nir/ac_nir_lower_ngg_mesh.c` (Git blob `1809ccb1538e1ccfaabbd4d55968b5b82206121c`) creates local `state.vertex_count_var` and `state.primitive_count_var` without an initial definition. The finale and output publication load these vars, whereas `SetMeshOutputsEXT` is optional on early-return paths. Mihawk issue #8 documents a native PS5 GPU hang with undefined GS_ALLOC_REQ counts and a concrete two-store initialization that succeeds with shader early-return; 1,198 unaffected shader binaries were identical in reporter's host comparison. This evidence does NOT show our firmware/mk-world reproduces the same GPU path.

## Scoped source correction, preserving vendor immutability

- `tools/ci/ps5_radv_ngg_mesh_zero.py`: accepts only the **exact original pinned Git blob**, changes only the `nir_builder` startup anchor, adds a zero `nir_store_var` for each count *before* the API shader and finale, and can reconstruct the original byte-for-byte. Refuses arbitrary source mutations or repeated additions.
- `tools/install-vendored-radv.py`: keeps original 14 maintained active RADV source owners, but now patches the **15th** `src/amd/common/nir/ac_nir_lower_ngg_mesh.c` only in the *disposable staged* `mihawk-vulkan-review/.deps/work/radv-src` after the original frozen Mesa export. It refuses stage paths missing, symlinked or containing unknown prior edits; writes atomically and refreshes mtime for incremental Ninja. Existing `--repair-owned-stage` does **not** authorize arbitrary mesh overwrite. A staged source change invalidates prior RADV archive provenance before second native compiler pass.
- `tools/radv-active-inputs.py` includes exact reviewed post-image bytes of the 15th source in the driver archive fingerprint, even though there is intentionally no `encore-active/ps5-mesa/.../ac_nir_lower_ngg_mesh.c` clone. Stamping after a native compile requires **all 15** matching staged inputs. Old 14-input source stamps can never silently pass.
- `tools/check-vendored-radv-fork.py` replays stage install and idempotency from the exact immutable Mesa file with the 15th candidate, while retaining all original 12/14 generated source oracles.
- `tools/check-ps5-radv-ngg-mesh-zero-host.py` validates original source SHA, exact inserted count defaults before GPU lowering, inverse normalization, negative source drift/double patch, and a simple C semantic model under UBSan. It does **not** compile the real Mesa shader compiler or prove console behavior.

**Critical build boundary:** the unchanged upstream Mihawk build script first builds an original driver archive, then Encore installs its 14 maintained source overrides plus this single verified 15th mesh source in the scratch tree, then builds a second time. A changed stage must cause the second pass to rebuild and link; the separately pinned 15-source stamp is applied only after a successful second native archive. If this path does not trigger exact rebuild or upstream overwrites the stage, the source/archive attestation must hard-fail. Do NOT disable upstream Git source hashes, delete the fixed source, or suppress Vulkan device-lost errors.

## PS5 exit gates

1. Exact review of upstream Mesa status and license; pristine source remains unchanged under `vendor/sources/ps5-mesa`.
2. Complete host CI + per-path source pin, stable replay/idempotency and negative drift fixtures.
3. Native PS5 Mesa/RADV full **clean** stage build (no cached old object), compare archive source stamp, compiled symbol list, native warnings and package SHA; verify early return in actual generated NIR→ACO code.
4. On a PS5 13.60 controlled synthetic mesh test with safe GPU-recovery plan, compare early return vs explicit `SetMeshOutputsEXT(0,0)` and normal output shaders, verify no GPU reset and continued console operation *after app exit*. Do not run unqualified GPU-hang test on a user console.
5. FC27/MKW/Bananza game tests separately with precise driver/GPU/guest log signatures. A green mesh test does not prove first guest frame or solve CPU guest PC=4.

**Status:** engine draft pending CI and native PS5 qualification; no merge, release, issue closure or gameplay claim.
