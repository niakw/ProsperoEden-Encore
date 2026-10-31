# NSW2 N71 — sparse residency ownership follows one texture image

Research-only correctness hardening of the shared native VMA transaction.

A `SparseBindOwner` now pins exactly one `VkImage` as soon as a sparse page
transaction can reach the GPU. Further layer requests must reference that same
image: otherwise an unrelated texture might be marked resident while its pages
are bound to a different image. The token remains pinned even after a failed
or timed-out queue submission. Only a successful `WaitIdle`, followed by the
caller's image/view destruction callback and VMA memory release, clears the
image identity and restores N63's budget.

The N69 native host regression adds an identity-mismatch case, verifies no
second queue submission or allocation, and verifies safe reuse after retirement.

This is an **invariant required by the texture-cache integration**, not yet a
proof of GPU sampling or a working NSW2 renderer. Default Switch 1 uses the
unchanged dense cache; no per-game exceptions and no changes to `main`.
