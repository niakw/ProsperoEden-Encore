# NS2 SVC → NVDRV → GPFIFO diagnostic pair — 2026-11-15

## Physical symptom

Native PS5 package built from engine `20ec9a25380ad5446bf39fe32582a0f647692362`
and selected vendor `4572e581d011c444fd59428d5c042098f05dcfca`:

- Mario Kart World `0400C3F00006E000`
- Donkey Kong Bananza `040074A01BF12000`

Both reach the Vulkan loading renderer and `guest_run_begin`, but the 10 s / 30 s
witnesses remain:

```
guest_frame_handoff=0
gpu_submit_sample=0
gpu_worker_completed_floor64=0
```

The console archive contains no `EDEN_NS2_GPFIFO` line. That existing marker is too
late to distinguish “the guest never issued the NVDRV route” from an admission rejection
before the actual GPU push.

## Upstream-first review

Current Lichii `nx2` and Eglantine `nx2` were reviewed before adding local diagnostics.
They route H:0x8/H:0x1b and Ioctl2 H:0x1b through their GPFIFO submission path and now
reach later rendering stages on MKW/Bananza. Their later syncpoint, mesh, shader and
renderer fixes do not prove the cause of Encore's earlier zero-submit PS5 signature.

Therefore this pair adds observability only. It does not remove Encore's FD ownership,
guest mapping, native-plan, fence, channel/GMMU or owner-binding checks.

## Vendor side

The selected vendor successor from the tested `4572e581d011c444fd59428d5c042098f05dcfca`
contains exactly three reviewed observability commits, not an unrelated feature stack:

- #150 `f7ee793f1ee1bb1c2b1a35f68073844163658262`: bounded Detailed-Logging stderr
  witnesses for FC27 NVDEC decode / VIC input / VIC output. It changes no decode or
  composition semantics. Reviewed successor blobs are FFmpeg
  `1f3834ef66b97033fc662d7c7c9ee3456cb62bca` and VIC
  `279255ee6527d6fc13b77147f73168917e427ea8`.
- #151 `3f019c64c2907ac3e84baa9b6200de8898f30636`: gate the bounded SVC witness
  behind the shipping Detailed Logging preference.
- #152 `f0324324768bdc090a003079bbf121df862bc7f7`: bounded pre-submit GPFIFO
  route/base/impl/reject witnesses.

Engine source receipts explicitly pin the #150 successor blobs and assert the runtime
Detailed Logging gate, so selecting the newer vendor cannot silently turn those witnesses
into an unconditional release log path.

Vendor PR #151 (merged `3f019c64c2907ac3e84baa9b6200de8898f30636`) makes the existing
bounded real-SVC witness respect the shipping Detailed Logging preference through weak
`eden_native_detailed_logging()`.

Vendor PR #152 merged as `f0324324768bdc090a003079bbf121df862bc7f7` and adds bounded pre-submit GPFIFO breadcrumbs, also Detailed-Logging-only:

- `EDEN_NS2_GPFIFO_ROUTE`: Ioctl1 submit/kickoff or Ioctl2 kickoff reached;
- `EDEN_NS2_GPFIFO_BASE`: Base1/Base2 reached;
- `EDEN_NS2_GPFIFO_IMPL`: SubmitGPFIFOImpl reached;
- `EDEN_NS2_GPFIFO_REJECT`: exact pre-push reject reason.

The three categories are capped at 32 samples. Guest command words/buffers are not dumped.

## Engine side

The selected real SVC source is compiled only in the reviewed PS5 NS2 owner and receives,
for that source file only:

```
PS5_NATIVE=1
EDEN_NS2_SVC_TRACE=1
```

Both definitions are required: `PS5_NATIVE` keeps `ns2_svc_trace.h::Next()` behind the
user's explicit Detailed Logging preference in the static `core` target.

The host contract asserts that the selected vendor header actually contains that runtime
gate; an engine/vendor mismatch must fail qualification.

## Paired MacBridge qualification before gitlink update

Engine branch head `54c1045c491214c436b2d54df5c8f23a7bd89c27` was first tested with the vendor
worktree detached at PR #152 head `fca26ef01d923542561f0fabeab9358204c44b2d`.

Request `eden-engine-svc-gpfifo-pair-135`: PASS for:

- real GPU-access/SVC source ownership and process lifetime;
- native GPFIFO kickoff Clang/GCC O0/O2;
- per-FD native ABI isolation;
- native GPU fetch admission / UBSan witnesses;
- loading GPU worker progress source contract;
- Nov13 PS5 regression source gate;
- repository hygiene.

The engine branch then selected merged vendor `f0324324768bdc090a003079bbf121df862bc7f7` through the real gitlink (`20f9ee02ea817b624ffa503ce43db2bbc3f0ea81`). Final selected-gitlink host qualification is recorded separately by the MacBridge request attached to the PR.

No PS5 runtime compatibility claim follows from these host tests.

## Next physical PS5 acceptance

Run MKW and Bananza with Detailed Logging enabled and retain, in order:

1. `EDEN_NS2_SVC`
2. `EDEN_NS2_GPFIFO_ROUTE`
3. `EDEN_NS2_GPFIFO_BASE`
4. `EDEN_NS2_GPFIFO_IMPL`
5. `EDEN_NS2_GPFIFO_REJECT` when present
6. existing `EDEN_NS2_GPFIFO`
7. guest-frame / GPU-submit / worker-complete milestones

Interpretation:

- SVC witness but no GPFIFO route: guest/service path has not reached NVDRV submit.
- route without Base: wrapper/shape mismatch.
- Base without Impl: guest-header/session/span rejection.
- Impl plus REJECT: exact native admission boundary is named.
- existing `EDEN_NS2_GPFIFO` plus submit counter: submission reached the GPU worker;
  investigation moves to macro/syncpoint/worker/render stages.

A new native PS5 build remains a separate, user-authorized gate.
