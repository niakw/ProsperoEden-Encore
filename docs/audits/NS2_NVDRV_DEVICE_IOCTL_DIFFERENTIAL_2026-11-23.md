# NS2 — NVDRV device IOCTL differential (2026-11-23)

## Scope and pinned sources

- Encore engine `main:6256b97b54a055d0789802abcad0ee367ce746b0` and vendor `main:273680a5b33bff15c9ca12685cfadb2aa15ff9f1`.
- Lichii `nx2:e7893bead9329406cac8e2d95cca2c37089f8655`.
- EglantinePS5 `main:5eb70367ffde039f237b3b828856f4b4247ea09e`.
- Scope: source inspection only, not console execution or full IOCTL ABI certification.

## Newly inspected owners

1. Encore selected vendor `encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp` includes `Ioctl1/2/3`, NS2-specific `UsesNativeAbi` paths, `Ioctl3` native GPU characteristics and validation of buffer sizes. Lichii and Eglantine source `src/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp` have different dispatch bodies. A service-level 22/22 count does **not** cover these device IOCTLs.
2. `nvhost_ctrl_gpu::Ioctl1` in Encore has explicit `NotImplemented` returns for `G:0x10` (`WAIT_FOR_PAUSE`) and `G:0x1e` (`SET_DETERMINISTIC_OPTS`). This is a verified **open behavior/firmware-contract review**, not proof that either command is used by MKW/Bananza or that implementation is mandatory. Do not substitute blind success.
3. Encore's `nvhost_ctrl_gpu::Ioctl3` has additional native-ABI branches including `G:0x1f` and `G:0x13`. These must be judged by request/response layout, not assumed upstream missing features; preserve NS1 paths.
4. Encore selected `encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp` adds NS2 VA allocation, sparse remapping and guarded result codes for `A` device commands. Lichii's shorter `nvhost_as_gpu.cpp` cannot be copied wholesale without destroying these owners.

## Next closure gates

- Enumerate exact device-level NVDRV ioctl command tuples for all compiled owners (`Ioctl1/2/3`), with guest generation, payload sizes, output sizes and result codes. Separate true absence, NS2 specialization and intentional errors.
- Compare corresponding Lichii/Eglantine handlers, then add focused native host ABI tests for any proven discrepancy; guard all NS1 behavior.
- Audit A32/A64 SVC argument and return ABI, SVC memory ownership and firmware variants; separately test loader/NPDM, FS object children and GPU channel submission.
- On PS5, obtain linked process/AM/SVC/NVDRV/GSV traces proving `gpu_submit_sample > 0` and `guest_frame_handoff > 0` on MKW, Bananza and Z-A. No current source comparison certifies boot.

**Status: OPEN.** This complements, and does not close, `docs/audits/EDEN_ENCORE_NS2_IMPLEMENTATION_COMPLETENESS_REGISTER_2026-11-21.md` §20. No native PS5 build or console validation is claimed.
