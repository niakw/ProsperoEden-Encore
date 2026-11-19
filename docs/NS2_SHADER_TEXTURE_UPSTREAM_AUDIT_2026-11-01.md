# NS2 graphics and shader upstream gap audit — 2026-11-01

The goals are (1) first **real guest image on PS5**, and (2) correct sky, terrain, textures and rendering without regressing Switch 1. A green native compile does **not** prove either.

## Independent sources examined

1. Original user link: `https://git.eden-emu.dev/gamecorner-033/eden-nx2` — currently not reachable to the audit tools. Accessible related fork: `https://git.eden-emu.dev/Takoroka/eden-nx2` (`eden-nx2` branch and 2026-10-29 release). This is not proof the inaccessible original has identical commits.
2. `https://github.com/heydemoura/EglantinePS5` (`main` e1de9c0, separate `fix/bananza-startup-and-terrain` e0b9f8d6). Its unmerged compatibility patch files 0003–0006 were compared by feature. Do **not** represent unmerged patch functionality as included in the official PS5 main.
3. `https://github.com/zortos293/Eglantine` (`nx2` d8a9528, `NX2_NOTES.md`, build 31 source badc91e). Notes document exact 100+ guest boot/render regressions, including rows 69, 82, 84, 86–99.
4. Additional relevant derived comparison: `https://github.com/Wael3rd/Eglantine-MKW`, release `mkw-2026-10-30-pre` and `NX2_VRAM.md`. Useful for dynamic VRAM budget and ASTC BC3, but neither PC results nor its driver assumptions automatically apply to PS5.
5. EglantinePS5's pinned `Djihads80/Eglantine` submodule is a *different* source snapshot from the zortos293 `nx2` branch; compare both rather than using its latest-branch label interchangeably.

## Current source changes (integrated as opt-in NS2 shader headers and vendor research owners)

**Source ownership:** original `vendor/sources/eden/src` remains immutable. Generic31 and the 32 storage bindings are copied into `vendor/encore-active/ns2-runtime/shader_resource/include` and selected only by the `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL` research CMake switch. This avoids modifying the pinned baseline and preserves the NS1 release.

| Component | Actual prior gap | Current change | Confidence / qualification |
|---|---|---|---|
| Vertex / geometry shader varyings | `shader_recompiler/frontend/ir/attribute.h::IsGeneric` excluded `Generic31Y/Z/W`, despite 32 x 4 attribute slots | Entire last vec4 now valid; host fixture checks every component | Exact one-line fix from EglantinePS5 0005; no console validation yet |
| Shader resource slots | `video_core/buffer_cache/buffer_cache_base.h` offered only 16 storage bindings | 32 slots + mask capacity assertion; mirrors EglantinePS5 0003 | Can prevent dropped NVN2 shader descriptors; NS1 must still be regression-tested |
| GPU-only 214 backing | Unbacked sparse GPU VA was wrongly treated as sufficient for render targets | Experimental mode-0 dense allocation through kernel page groups, process alias/NVMap, transactional 216 mapping with 512 MiB / 2 GiB limits; mode-1 remains explicit sparse | Compiler and runtime validation pending; no claim of a first NS2 frame |
| Native Geometry ATEXIT | Generated ISA table did not recognize LEPC/BMOV even though the lowering had partial cases; capture also stopped at the first EXIT before the handler | Strict opcode-mode preflight, verified NVN 5-opcode prologue detection, forward handler capture, EXIT relocation, and zero-handler clear; host CI #41318257305 succeeded | Vendor research-only; no stand-alone Geometry/Vulkan pipeline claim |
| Geometry OUT CBUF/uniform | Ampere table recognized 0xb24/0xd24 but lowering rejected both | Source-mode-aware stream materialization with fail-closed masks and Clang/GCC host fixture | Does not enable the missing interstage Geometry/Task/Mesh Vulkan pipelines |
| Native Ampere LDC | `lower_to_maxwell.h` rejected 8/16-bit constant loads (widths 1–3) | Reviewed signed/unsigned 8/16-bit forms accepted; widths 6/7 remain rejected | Exact opcode/format review based on EglantinePS5 0004; two compiler fixture |
| Native Ampere half predicates | 0x234 HSETP2 had no lowering case | Reviewed packed half register predicate mode added, unsupported modes still rejected | Based on EglantinePS5 0004; no real game shader proof yet |
| NS2 Compute/QMD3 | Eglantine NX2 0xC7C0, TU104 MME, 3 QMD release slots | Ampere class/execute path and per-process dependency scheduler added in prior lot | Nonempty Compute shaders remain **not executed**; do not fake fence completion |
| VI2 VSync | NS2 31/32 entirely missing | 60 Hz vblank events now provided in experimental service | PS5 compile success, first guest image still unverified |

The shader host fixtures are `tools/ns2/test_shader_generic31.cpp`, `tools/ns2/test_native_shader_texture_semantics.cpp`, plus the QMD3/CPU isolation fixtures in the host CI.

## Remaining gaps, ranked by first-image / visual impact

| Priority | Upstream evidence | Why it could cause reported symptoms | Next bounded step |
|---|---|---|---|
| P0 boot | Eglantine `NX2_NOTES.md` rows 42–60, 82–85 | Guest GMMU mapping / subchannel synchronization / present fences / event waits can stop all guest frames | Correlate actual PS5 `EDEN_NS2_IPC`, `EDEN_NS2_VI2_VSYNC`, `EDEN_NS2_GPFIFO`, `EDEN_NS2_GPU_BIND`, `EDEN_NS2_COMPUTE_QMD_UNSUPPORTED`, `guest_frame_handoff` |
| P0 visual | Eglantine rows 86, 88–93 | Missing sky / atmosphere can be a failed native pixel/geometry/volume shader, uniform predicate bug or missing task/mesh program | Produce negative-cache reason histogram by stage / opcode and correlate with skipped draws; check 32x32x32 volume textures |
| P0 geometry | EglantinePS5 0004 (LEPC, BMOV ATEXIT, geometry OUT), rows 89/97 | Native geometry output and interstage linkage remain incomplete; a statically verified ATEXIT prologue is now captured and relocated instead of ending at its first EXIT | Validate ATEXIT fixture and the complete geometry stage/pipeline; dynamic PC, task/mesh, and non-reviewed exit handlers remain unsupported |
| P0 texture | Eglantine rows 57, 68–70, 87, 94, 99; Wael `NX2_VRAM.md` | Black/flickering texture can be **missing physical backing**, stale GPU writes, wrong GOB/ASTC swizzle, or VRAM overcommit rather than shader lowering | Check actual per-frame VRAM budget, resident image extent/layers/mips, sparse unmapped detection, ASTC decode and texture generation. Never expose an unbacked image as a valid texture |
| P1 shader | EglantinePS5 0004 opcode compatibility and Eglantine rows 63, 88–93 | Native opcode omissions lead to skipped draws/shader failures; shader 0x234 and LDC 8/16 were concrete gaps now addressed | Import individually tested missing lowering forms, preserve precise source mapping and stage policy |
| P1 performance | Eglantine row 90 and EglantinePS5 current main | Repeated rejected shader translations/logs and broken driver disk cache cause frame-time spikes | Negative compile cache invalidated on GPU memory writes; atomic persistent shader cache after source-owner verification |
| P1 VRAM | Wael 2026-10-30: driver heap double-count and ASTC uncompressed budget overflow | Flashing garbage then crash, or black substitutes if sparse image is unbacked | Evaluate on PS5's special shared-pool allocator first: it already uses a graphics pool free-memory callback; *do not simply copy PC heap sums or force BC3 everywhere* |
| P2 Bananza | EglantinePS5 0006 Bananza-specific depth/color terrain workaround | Can repair terrain under particular verified passes but masks a generic cross-pass dependency flaw | Analyze generic pass resource / indirect-draw synchronization before game-ID-specific override |

## Source-owner boundaries

- Switch 1 is not a retrofitted Ampere title. Keep native GMMU/class/QMD shader owners opt-in and process-bound; global buffer/attribute bounds fixes must pass host tests and a Switch 1 gameplay regression.
- Native `vk_texture_cache_cost.cpp::ProbeSparseImage` currently exercises a *research probe*, **not** a fully resident live guest texture path. Its presence is not evidence that 8192x8192 layered textures render correctly.
- Experimental shader compile success does not mean the fragment/geometry programs' outputs, GPU image memory, or VI2 frame handoff are correct. Request on-console proof before claiming a fix.

## Validation receipts

- `41313252594`: PS5 experimental native build success for previous GPU/VI2/Compute lot `ea2a5cb`; artifact contains **none** of the new shader/texture fixes here.
- A subsequent host run is required to verify Generic31, 32 storage bindings, and native LDC/HSETP2 changes; mark as *source-integrated, not console-tested* until it finishes.
- No claim that all upstream commits were ported: this audit is about **high-impact structural and visual gaps**, not a full diff of every third-party tree.


## 2026-11-19 verification — Ampere architecture references and live PS5 owner

**This section supersedes the historical "opt-in/research" status descriptions above.**
The one native PS5 build currently selects the maintained native Ampere translation
and NVDRV/GPU paths for authenticated NS2 titles via
`headless/CMakeLists.txt`. It does **not** enable an experimental app profile.
The vendor source examined here is `6c38328fbef33de747f5c31ea30d13541a513a4a`;
the engine gitlink matches this commit at the time of review.

### Independent architectural evidence and scope

- NVIDIA, [*Ampere Tuning Guide*](https://docs.nvidia.com/cuda/ampere-tuning-guide/index.html):
  async global-to-shared copies, split arrive/wait barriers, warp-wide reductions,
  tensor math modes, L1/L2 residency and occupancy. The explicit A100/SM80 and
  SM86 resource figures are **not** constants for the Nintendo T239.
- H. Abdelkhalik et al., [*Demystifying the Nvidia Ampere Architecture through
  Microbenchmarking and Instruction-level Analysis*](https://arxiv.org/abs/2208.11174),
  arXiv:2208.11174v1 (2022), especially pp. 3–7 (PTX-to-SASS mapping,
  dependent versus independent instructions, Tables III–V). Table IV's
  measured A100 values are approximately 290 cycles for global memory,
  200 for L2, 33 for L1, and 23/19 for shared load/store. These are
  **A100 microbenchmark measurements**, not PS5 RADV timings or a reliable
  model of Switch 2 T239 shader latency.
- Independent PS5 implementation:
  [EglantinePS5 native Ampere lowerer](https://github.com/heydemoura/EglantinePS5/blob/main/Eglantine/src/shader_recompiler/frontend/ampere/lower_to_maxwell.h).
  Compare against [Lichii](https://github.com/zortos293/Lichii/blob/nx2/src/shader_recompiler/frontend/ampere/lower_to_maxwell.h)
  and [Eglantine](https://github.com/Eglantine-Community/Eglantine/blob/main/src/shader_recompiler/frontend/ampere/lower_to_maxwell.h)
  before lifting any opcode encoding; implementations are not byte-identical.
- The paper studies CUDA/PTX and Ampere SASS on a Tesla A100. Encore processes
  **guest NVIDIA graphics/compute instructions**, lowers reviewed native SASS
  forms to a Maxwell-compatible intermediate form, then emits host SPIR-V and
  executes through **PS5 AMD RADV**. A CUDA launch optimization does not directly
  improve this host path; an emulator instruction *semantic* correction can.

### Source-level audit of the currently selected NS2 translation

| ISA or dependency concern | Active vendor source | Evidence and decision |
|---|---|---|
| Global-to-shared async copy | `ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h`: `0xfae` LDGSTS, `0x9af` LDGDEPBAR, `0x91a` DEPBAR | Restricted encodings lower via **synchronous** guest memory copy plus ordering. Supported modes have explicit guards. Do **not** replace this with CUDA `cp.async` or omit barriers; test producer/consumer ordering against actual guest shader captures. |
| Warp reconvergence and memory visibility | Same lowerer: `0x948` full-mask WARPSYNC, `0x348` register-mask WARPSYNC, `0x992` MEMBAR | Selected modes are processed, including branch reachability and outer-convergence tests; other modes deliberately fail closed. The lightweight `classify.h` tag `OpKind::Nop` is **not** evidence that the final lowerer silently ignores all WARPSYNC/DEPBAR semantics. |
| Tensor instructions and lane layout | Same lowerer: `0x23a` MOVM, `0x83b` LDSM, `0x23c` HMMA | Contains bounded 8x8 transpose/shared matrix loads and software FP16 HMMA expansion. The A100 WMMA shapes and cycles in the paper cannot be transplanted as hardcoded PS5 costs or host Tensor Core operations. |
| Missing native integer tensor lowering | `ampere_isa_table.h` lists `Imma` as `0x237`; `lower_to_maxwell.h` lacks `case 0x237` and ends in `unsupported native opcode` | **P1 candidate:** a captured NS2 shader using this opcode may be rejected. Neither user logs nor the document demonstrate that MKW/Bananza needs it. Obtain stage, exact opcode words, and shader identity before implementing; keep rejection rather than emitting an incorrect computation. |
| Warp reductions and atomics | `0x3c4` Redux handled in lowerer; `renderer_spirv_bridge.cpp` checks native QMD atomic binding and SPIR-V admissibility | Protect stage-specific ordering and native-width support. Do not promote unsupported 64-bit atomics to ordinary non-atomic stores. |
| Guest boot PC=0x4 | `headless/ns2_fault_receipt.cpp`, selected NS2 kernel, loader and Dynarmic | **Still P0 and independent of this shader audit.** Existing MKW/Bananza guest faults occur before any proved Ampere shader failure; no GPU timing table can establish their cause. |

### Next bounded verification before the native build

1. Confirm real vendor/engine SHAs and CMake graph (the existing
   `tools/ns2/check_shared_ampere_source_host.py` and
   `tools/ns2/check_shared_ns2_spirv_compiler_host.py`).
2. Check actual shader-capture status/rejection counters against the last
   console evidence; only prioritize unsupported opcode `0x237` if exercised.
3. Keep all memory-order / fence tests and fail-closed SPIR-V stage guards;
   no speculative NVIDIA timing constants or new experimental switches.
4. Close outstanding source/host-CI regressions, then qualify one native PS5
   build and confirm package symbols and exact gitlink. Guest gameplay is
   **not** proven by compilation.

**Result:** upstream architecture research and three lowerer implementations
compared; **no runtime Ampere correction claimed** on the strength of this paper
alone. Recheck on PS5 13.60 after a genuinely qualified build.

## Maxwell/Ampere primary-source cross-reference — 2026-11-19

The nine NVIDIA and academic architecture sources, real Encore GPU/cache source owners, explicit applicability limits and NS1/NS2 console qualification gates are tracked in [`docs/audits/NVIDIA_GPU_ARCHITECTURE_REFERENCE_REGISTER_2026-11-19.md`](audits/NVIDIA_GPU_ARCHITECTURE_REFERENCE_REGISTER_2026-11-19.md). Measurements on GTX980 and A100 are *not* PS5 or Nintendo GPU timing constants. No unsupported opcode is implemented on the strength of these papers alone.
