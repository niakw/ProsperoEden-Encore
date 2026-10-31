# NSW2 N58 — Vulkan sparse image residency gate (2026-10-31)

Eglantine's sparse ASTC terrain optimization depends on **image residency**, not merely the ability to bind sparse memory. The native pinned PS5 Vulkan Device had only `IsSparseBindingSupported()`; that checks `sparseBinding` plus whether the chosen graphics queue supports sparse binding. Vulkan separately requires `sparseResidencyImage2D` for an image whose 2D tiles are independently backed.

This experimental source-owner overlay adds `Device::IsSparseResidencyImage2DSupported()` and requires all three conditions: sparse binding feature, 2D residency feature and graphics queue sparse-bind support. It only exposes the admission predicate; it does **not** allocate, bind, evict or synchronize sparse image memory.

`EDEN_NS2_SPARSE_RESIDENCY_GATE_EXPERIMENTAL=ON` selects this query on the native PS5 Vulkan NS2 research build. OFF by default, forbidden in final release; no change to `main`, pinned vendor or normal Switch 1. CI regenerates the full pinned Vulkan Device header, enforces exact source-owner parity, and compiles/executes the actual extracted predicate for all 8 feature combinations under Clang/GCC UBSan.

**Remaining sparse work:** verify real device capabilities, image sparse memory granularity, residency budget and per-layer mip tails; stage allocation/bind/queue synchronization with failure rollback, then couple to the N57 partial ASTC path. Without real PS5 tests, driver feature support is unknown and no working GPU residency is claimed.
