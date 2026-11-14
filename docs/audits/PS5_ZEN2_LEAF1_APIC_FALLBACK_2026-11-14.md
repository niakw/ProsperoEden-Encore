# PS5 Zen 2 physical CPU topology: leaf-1 APIC fallback

Date: 2026-11-14. **P1 performance candidate, source/host only. DO NOT call it an FC27 fix or a console qualification.**

## Observed user symptoms and log

The 2026-11-13 FC27 PS5 session has `EDEN_PS5_CPU_TOPOLOGY_REJECT reason=more_than_8_physical_ids observed=13`. PS5 13.60 reports 13 allowed OS logical CPUs. The selected `headless/performance.cpp::CheckWorkerTopology` has three conservative physical proofs: read-only FreeBSD scheduler SMT XML; authenticated AMD TopologyExtensions `0x8000001e`; x2APIC topology `0xB`. The firmware logs show the first two unhelpful (not exported or 13 distinct presumed physical IDs), while the third sometimes gives a single x2APIC core ID. It correctly keeps worker pinning OFF. Disabled pinning is NOT itself a proven cause of 835ms pipeline stalls or missing HUD textures.

## Verified upstream comparison, before local adaptation

[heydemoura/EglantinePS5 #19](https://github.com/heydemoura/EglantinePS5/pull/19) reports PS5 console CPUID `0xB` with a valid SMT shift of 1 but unusable x2APIC IDs (all zero). When pinned to a known OS logical CPU, CPUID `1` EBX[31:24] instead returned APIC `15-n`, correctly grouping sibling pairs. Their console result `EDEN_WORKER_TOPOLOGY ready=1 distinct_cores=5 cpus=0,2,4,6,8` and pinning verified on an earlier fork; their one-run Pokopia latency comparison is not a controlled FC27/MKW result.

## Adaptation in Encore

- Keep all existing AMD, x2APIC and OS scheduler checks unchanged. Use leaf 1 only if both authenticated AMD family 17h+ TopologyExtensions and valid CPUID `0xB` SMT level are present; require shift 1–7.
- Under the existing per-logical-CPU cpuset pin + verified readback and sleep/scheduling point, acquire EBX[31:24] (8-bit initial APIC ID). Refuse duplicate APIC IDs, missing CPU classifications, fewer than 5 or more than 8 physical groups, or any group holding over 2 *allowed* logical CPUs.
- Prefer genuine OS scheduler groups, valid AMD extended and valid x2APIC representations; only then select `amd_leaf1_apic_fallback`. Never assign physical cores by CPU index, and never enable experimental logical-only affinity as physical proof.
- Preserve existing restore-on-exit and fatal failure if original thread mask cannot be restored. No per-frame CPUID reads; test occurs on the startup topology probe.
- Source owner full blob `18ecba614f2c0077bbcc7044d68aa3eb714cb4b4` from original `2c6c4a9a9d6b8adc9dc8db130d24a63fb88a7a31`. Dedicated workflow pins the reviewed current blob. Historical October F07 review ledger is not rewritten.

## Host regressions (not console gameplay)

`tools/check-worker-affinity.py` compiles the **real maintained** CheckWorkerTopology source under ASan/UBSan with mocked FreeBSD affinity/sysctl/CPUID. Its new cases cover PS5 13 logical CPUs + zero x2APIC IDs + leaf 1 `15-n`, a duplicate leaf-1 ID, all-zero leaf-1 IDs, retained OS mask and the existing denied-affinity/restore/AMD and ULE groups. `tools/check-worker-topology.py` and `tools/check-experimental-performance.py` require the static provenance and fail-closed policy.

## Console acceptance before merge/release

1. Exact binary SHA, vendor SHA, firmware 13.60, actual raw CPUID/OS CPU logical count, `EDEN_PS5_CPU_TOPOLOGY_SOURCES`, and five real worker pin readbacks.
2. Compare **same FC27 title/scene and warm/cold shader cache** at original unpinned behavior vs leaf-1 fallback. Record 5-second late38/late50/late100, `EDEN_VULKAN_PIPELINE_WAIT`, cache wait domains, GPU fence/submit and worker logical physical masks. No fabricated FPS gains from host tests.
3. Verify **MKW and Bananza boot/teardown**, audio/video/PS5 launcher input and absence of console crashes. Retain one-run-only/scene-unmatched measurements as inconclusive.
4. Never merge based on host CI; keep P0 game issues open. Build PS5 only with exact paired engine/vendor source provenance and inspect symbol/package integrity.
