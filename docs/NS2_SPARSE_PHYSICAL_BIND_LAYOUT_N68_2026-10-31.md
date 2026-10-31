# NSW2 N68 — real sparse tile and mip-tail region layout

Research-only, OFF in final releases.

N63's **existing vendor owner** `ns2_sparse_layer_budget.h` now contains
`MakeSparsePhysicalBindPlan`. It converts a ready N63 transaction into
a bounded list of exact per-layer/per-mip texel rectangles for
`VkSparseImageMemoryBind` and opaque mip-tail offsets for
`VkSparseMemoryBind`, derived from actual driver requirements passed by
the caller (N65): sparse granularity, tail first LOD, tail offset/stride,
tile backing alignment and maximum virtual image allocation size.

It rejects duplicate/out-of-range layer indexes, partial/oversized tile lists,
out-of-range or overlapping mip-tail strides, offsets beyond signed Vulkan
image coordinate limits, byte/budget mismatch against N63, and overflow.
`SINGLE_MIPTAIL` is represented once; per-layer tails use the true stride.
All successful transactions remain below N66's 65,536-tile/4,096-tail caps.
The dense texture cache and existing renderer are unchanged.

Updated host source-owner tests compile the exact vendor header on GCC and
Clang under UBSan and exercise normal layers, shared vs independent tails,
stale/impossible layouts and oversized workloads. No GPU proof is claimed.

**Outstanding before native consumption:** validate sparse aspect and format
flags (including compressed granularity), allocate each region with N62 VMA
while retaining every token, build actual `VkSparseImageMemoryBind` /
`VkSparseMemoryBind` arrays, submit via N66/N67 and wait/retire safely.
Only after that may existing texture-cache images opt into sparse backing
and N57/N60 ASTC decoding. Native PS5 capability and image readback
remain unproven; no separate renderer or per-game patches.
