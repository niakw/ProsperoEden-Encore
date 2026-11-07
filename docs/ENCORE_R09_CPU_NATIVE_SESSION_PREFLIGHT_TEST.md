# R09 — CPU-only full session preflight

The actual `NrRdna2FrameSession` calls
`PreflightR09Session` before constructing **any** Vulkan shader modules,
descriptor owners, command stages, or GPU buffers.

The shared source-level gate checks model-pack index integrity, exact
Original/Compact manifest, native 152/76-step plan, Split-Swin/ViT/U-Net
dependencies, all eight FSwin segment identities, and transposed
1920×1080 source/destination geometry. It transfers the validated
resources into the GPU session only on success.

The host CI test creates tiny **synthetic** NRMODEL1 indexes with all
599 / 255 authentic *names*, but expressly **not** any NVIDIA model
weights. It validates both plans and rejects wrong-variant, truncated
plan, missing weight-name and invalid source/output geometry. It also
tests the optional authentic temporal scalar's name and index.

A successful preflight is an index/graph proof, **not a neural GPU
inference** or correctness proof of the numeric weights.
