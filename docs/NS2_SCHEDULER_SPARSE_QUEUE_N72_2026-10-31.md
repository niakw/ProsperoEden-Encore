# NSW2 N72 — sparse binding through the existing Vulkan submission mutex

Experimental PS5-native NS2 research only. Switch 1 and final builds stay unchanged.

The original Encore `Scheduler::SubmitExecution` already serializes its graphics queue through `submit_mutex`. Calling `device.GetGraphicsQueue().BindSparseImage` independently would violate Vulkan's external synchronization requirement when the scheduler's worker concurrently submits ordinary command buffers.

N72 adds a macro-gated `Scheduler::BindSparseImage` to the **same maintained native Vulkan scheduler**, using the existing `submit_mutex`. It delegates to the N66/N67 wrapper, forwarding optional wait/signal semaphores and completion fence without holding the mutex during a fence wait. No separate renderer, scheduler instance, copied source tree or game-specific workaround.

Selection: `EDEN_NS2_SPARSE_QUEUE_EXPERIMENTAL`, OFF by default; requires PS5_NATIVE, EDEN_PS5_VULKAN, EDEN_NS2_METADATA_EXPERIMENTAL and a non-release profile. The N69 transaction's queue parameter can consume the scheduler directly when integrated by the texture cache.

The research host test compiles the **exact vendor scheduler method** with Clang/GCC UBSan, verifies invalid requests and device failures propagate, and fires concurrent submissions while a mock queue checks the scheduler mutex is held for each call. The Vulkan fork parity oracle normalizes only the explicitly delimited N72 header/source additions, so the remaining generated baseline must stay byte identical.

**Still pending before PS5 textured output:** a texture-cache owner to create/select/bind sparse VkImage instances, exact safe lifetime across ImageView/TextureCache image release, compressed ASTC format requirements, GPU sample/readback and full native console validation. This is a queue integration, not a demonstrated gameplay milestone.
