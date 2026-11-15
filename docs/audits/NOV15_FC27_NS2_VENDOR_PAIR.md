# 2026-11-15 — combined FC27 / NS2 vendor integration

Engine parent: `2c293520f370c110f77efd528e8a5f60ae9607a0` (#205).
Vendor transition: `697159fd0c183f8a164d0493929ae3b4bcb391d1` → `0fc157b7ccef428e675ff945bc48eceb08fff607` (includes upstream-confirmed Maxwell CB_BIND guard #163; #162 is test-only).
Exact selected source receipts: [NOV15_FC27_NS2_VENDOR_PAIR_SOURCE_RECEIPT.json](NOV15_FC27_NS2_VENDOR_PAIR_SOURCE_RECEIPT.json).

| Symptom / target | Upstream and candidate | Individual vendor qualification | Physical acceptance |
| --- | --- | --- | --- |
| FC27 `0100C49025D3E000`, intermittent HUD/textures, frame-time spikes | [vendor #156](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/156), Lichii f06e901, Eglantine-ducky e27fbc6: stale GPU readback vs newer CPU writes | [MacBridge exact head](https://github.com/niakw/NiakGH-MacBridge/blob/5693db67744ebbccc6df8fa841d104d9949d2000/results/current.json), 20 GitHub checks passed | Issue #100 open; no causal claim or console result for this candidate |
| NS2 Bananza `040074A01BF12000`, MKW `0400C3F00006E000` | [vendor #157](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/157), Lichii e6e0304, missing LDSM single-matrix selector | [MacBridge exact head](https://github.com/niakw/NiakGH-MacBridge/blob/1bcfaf01883b50b33b69b2be8f4e5bcc52b04568/results/current.json) | Post-submit compatibility, not a demonstrated cause of zero-submit loading stall |
| NS2 first-frame wait, latest console trace GPU submit sample 0 | [vendor #158](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/158), upstream comparison Lichii e6e0304, completion-release contract | [MacBridge exact head](https://github.com/niakw/NiakGH-MacBridge/blob/b12b9448e93d6e98b7827f4b0d5366199bb79314/results/current.json), 10 GitHub checks passed | Issue #123 open; actual guest frame and sustained gameplay required |

## Combined engine qualification

MacBridge request `eden-engine-vendor-fc27-ns2-pair-182` on engine `85a1dbac4b7be00c7aa413f158ecc5ae776375c7`, exact vendor above:
three individual regression tests passed together; unified GPU source graph passed; 6/6 native GPU boot source TUs passed host syntax; loading and repository hygiene passed. Three historical audit checks failed on the newly selected bytes/owner lineage. The subsequent changes verify the new header/source blobs and restore only reviewed hunks in audit copies before comparing the immutable historical baseline. Requalification request `eden-engine-vendor-fc27-ns2-pair-183` submitted. Do not claim full host or native build qualification until actual results are green.

No new native PS5 build requested. Console launch, rendering, performance, and gameplay remain unverified. The PR stays draft during combined qualification.

## Final vendor successor

Vendor #163 adds the Lichii/Eglantine `ProcessCBBind` bounds guard: slots 0..17 remain valid and guest slots 18..31 are rejected before indexing the 18-entry state array. GitHub qualification: 11/11. This is a general memory-safety/compatibility correction, not proof of the current zero-submit NS2 stall.
