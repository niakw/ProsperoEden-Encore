# PS5 native validation request — 2026-11-16 final retest candidate

This documentation-only commit intentionally carries the `[full-build]` marker to trigger the existing non-publishing native PS5 workflow after the Nov16 retest fixes and repository cleanup.

Exact candidate:
- engine runtime/source baseline after #257: `3963ba8e2e6e8c56df3b1c70bfd5ddaf1d763bb6`;
- engine main immediately before the first trigger: `052031ab7e44f94af8aec8aa07734615072a07bb`;
- corrected native-preflight successor receipt merged as #259, main: `568511473450bc4a805139b5472d0f249d109761`;
- selected vendor gitlink: `ffa519db0f68fb0d5d2acf791e381c898a34a175`;
- vendor repository main contains only later maintenance/cleanup beyond that selected runtime pin;
- firmware target: PS5 13.60.

Included source fixes requiring hardware validation:
1. #238 launcher GLAD/ODR null-dispatch crash candidate;
2. #239 exact ExeFS size path;
3. #242 NS2 RETAA/RETAB production translation;
4. #244/#248 stable square Home/Control artwork for ExeFS/NS2;
5. #246 DLC/update truth-state and game-language propagation;
6. #252 removal of duplicate startup add-on scan;
7. #256 opt-in privacy-minimized diagnostics sharing client;
8. #257 deterministic 31-language typography fallbacks and shaped Unicode Vulkan quick menu.

Repository state before build trigger:
- engine: only `main`, no open pull request;
- vendor: only `main`, no open pull request;
- unresolved issues requiring PS5 validation intentionally remain open.

This request does **not** carry `[release]`; no public release is authorized.

Acceptance for this run:
1. all early source/ownership/preflight gates pass;
2. selected vendor and RADV receipts are exact;
3. 31-locale/Noto generation and Vulkan HUD/font generation pass in the native path;
4. native compilation, link, staging and package succeed;
5. inspect warnings, errors, not-found messages, deprecations and dependency diagnostics;
6. retain and verify ELF, symbols, link map/provenance and distributable artifact hashes;
7. only after that mark the package ready for PS5 installation/testing.

Console validation remains separate from a green build.

Retry note: native run `43961249048` stopped before toolchain installation/compilation because the early post-F07 gate had stale exact blobs for `eden_services.{cpp,h}`. PR #259 updated only those reviewed receipts; no runtime/vendor source changed. This trigger is the corrected full build.

Second retry note: native run `43963114431` also stopped before toolchain installation. The same strict Post-F07 gate then exposed the remaining already-reviewed typography/diagnostics successors for `headless/hud.h` and `headless/prosperoeden/frontend.cpp`. PR #260 admitted those exact blobs. The full 40-entry Post-F07 register was then compared against the current tree with zero uncovered drifts. Main after #260: `6e863387f2513b55d95ecd07faab0f8389cfbf42`.

Third retry note: native run `43964516506` passed the early source gates but stopped in the startup/elevation/storage contract suite because `check-encore-ux.py` expected former hard-coded French overlay copy. PR #261 preserves a localized next-launch warning, verifies the maintained translation routing and removes the obsolete assertions. All three head workflows succeeded (`43966982330`, `43966982280`, `43966982446`). Engine main after #261: `54a05c04b61cd73fcded72e5634a8ee1cc4d1618`; vendor gitlink remains `ffa519db0f68fb0d5d2acf791e381c898a34a175`. User explicitly authorized a full build; no publication or bypass of source checks. The merged #261 branch may remain until cleanup verification. Hardware issues remain open until actual PS5 tests.
