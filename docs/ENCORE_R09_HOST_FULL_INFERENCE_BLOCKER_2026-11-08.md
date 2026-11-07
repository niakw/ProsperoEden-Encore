# R09 — real frame evidence, host limitation and diagnostics

The authentic model has passed native import and 599 individual SHA checks,
plus CPU graph preflight and two real learned 32-channel Vulkan projections.
The earlier 80x45 PNGs are **synthetic fixtures**, not neural inference.

## New diagnostic boundaries

\`NrRdna2FrameSession\` now exposes \`LastInitializePhaseName()\`,
\`LastRecordPhaseName()\` and \`EnqueuedSchedulerCallbacks()\`.
The renderer emits those values when model initialization or graph recording
is rejected. The latter number counts queued Scheduler callbacks, **NOT**
152 native plan operations, completed dispatches, fences, or pixels.
No model data is included in logs.

## Full-model acceptance (still OPEN)

For a valid host proof, a Linux adapter must instantiate the *real*
\`Vulkan::Device\`, \`MemoryAllocator\`, \`Scheduler\`, and
\`NrRdna2FrameSession\`; allocate a guest source VkImage and output
RGBA32F VkImage, transition them to GENERAL; use an authenticated local
Original pack and native 152-row plan; call Initialize and Record; submit
and wait on a real Vulkan fence; and perform a VkImage-to-staging-buffer
readback to produce image bytes. The readback must be checked against a
truly independent reference, using a real non-fixture input image.
The host adapter does not currently exist and is not substituted with an
I/O fixture or synthetically generated dispatch list.

The existing PS5 present integration cannot by itself serve as a Linux host
adapter; its Vulkan context, memory allocator and scheduler are engine-owned
and rely on a large upstream runtime. No PS5 build or console check is
part of this change. Do not claim complete Original inference.
