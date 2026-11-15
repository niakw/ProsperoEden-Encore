# Encore final pre-build receipt — 2026-11-15

This receipt authorizes one native PS5 build of the reviewed current main graph. It is not a release approval and does not claim console qualification.

## Exact source graph

- Engine integration merge: `feb97af6ae0f1249c60ac94d7caf646d5d53a759` (PR #187).
- Repository cleanup policy commits after integration: `eaafea27aed3212c51e6a5b35255284a7fdab271`, `848e28ecacb0e4e0a9355cea5d70ba0c55fa9470`.
- Selected vendor gitlink: `4572e581d011c444fd59428d5c042098f05dcfca`.
- Vendor #149 preserves the bounded Bananza low-guest-write diagnostic in the selected CPU6 A64 owner and passed its focused host gates.
- Vendor security/quality and Python/JS/dependency QA passed on the final vendor graph.

## Integrated work

- R458 continuous GL -> Vulkan loading ownership candidate.
- Fail-closed PS5 stop-timeout policy.
- Reviewed native MSAA split texture-handle fallback.
- FC27 block-local SSA and SSBO failed-search pruning owner selection.
- Final P0 diagnostics vendor graph, including Bananza/MKW instrumentation.
- Deterministic vendor documentation dependency locks and reviewed cleanup workflow security pin.

## Open validation gates

Do not infer runtime success from this build. Keep hardware acceptance open for:
- #97 Circle/app-exit crash and relaunch safety;
- #100 FC27 intro video, HUD/text, textures and pacing;
- #101 launcher/loading/UI visual acceptance;
- #123 Bananza PC=4 and MKW first guest frame;
- #124 library/home media latency and icon survival;
- #132 RADV NGG mesh early-return GPU safety;
- #118 actual CodeQL alert states;
- #108 fresh full native warning inventory.

## Build policy

This commit intentionally carries `[full-build]` to trigger the existing native build/package workflow. It does **not** carry `[release]`; no public release is authorized. Preserve complete compiler output, artifacts, symbols and exact source provenance.


## First native attempt and exact retry qualification

Native run [43659261343](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43659261343) stopped before native compilation in `tools/vendor-eden-cpm.py --check`. The only failing contract was the frozen Boost CPM tree receipt: final vendor intentionally changed exactly three docs-only npm metadata files to pin `isomorphic-git` 1.44.13 deterministically, producing whole-tree digest `ec9292f7566e9ac21a135fc89fe7e84bde991d65610d0e87df977314a72ae67f`, 59,798 files, 550,709,823 bytes.

Engine commits `2f2fa4917a9a71317126f8be6bc7709f94958a39` and `28fa3c36164af9ffc7091128e4eee224e3429dce` add that exact reviewed snapshot as an accepted security/docs delta while preserving the immutable original lock witness. The final-vendor comparison shows only:
- `libs/openmethod/doc/package.json`
- `libs/url/doc/package.json`
- `libs/url/doc/package-lock.json`

No compiled/runtime Boost source changed. This retry remains build-only, with no release authorization or console-success claim.
