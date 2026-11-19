# PS5 R457 cc8044ce — native build and downloaded-artifact audit (2026-11-19)

**Result: install/test candidate qualified; PS5 execution and gameplay UNTESTED.** Native [run #44520885201](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44520885201), 2026-11-19 12:07–12:28 UTC: `build` success, all actual build/stage/validate/artifact steps passed; `release` job intentionally skipped (no publish event). Examined **8,403 job-log lines** and independently downloaded **both** authenticated GitHub artifacts, not merely their metadata.

## Provenance
- Engine source: `cc8044cee42ad0e74af4edadaac6595de9128c31`.
- Vendor gitlink + actual checked-out submodule: `6c38328fbef33de747f5c31ea30d13541a513a4a`.
- Title: `PPSA99008`; version `R457 / 01.400.457`; `encore-release.json` inside the package binds this exact commit. **R457 is not sufficient to distinguish this build from previous R457 tests.**
- GitHub `main` advanced only by three documentation commits after this build (as verified at audit): the compiled binary is pinned to the SHA above.
- Host preflight 6/6 green, core fast gate green, CodeQL workflow 3/3 green on previous code commit `f55fb7ad`; vendor security/quality workflows 2/2 green at its pinned SHA. Security workflow success does not mean all Dependabot findings are closed.

## Downloaded bytes and deep verification

| Container | Artifact | SHA256 | Contents |
|---|---|---|---|
| FTP download | [ID 14529741327](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44520885201/artifacts/14529741327) | `7d807367f0ed037ca1f9f10751e49a7d94b739f6c9112497352c033e7ae418ac` | 41,188,080 compressed bytes; 200 title files, one `PPSA99008/` root |
| Release bundle | [ID 14529910902](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44520885201/artifacts/14529910902) | `db0c21ef6672e6d266a9c7def995459be8dcb72f6b943871718f6ee52758baf0` | 163,362,504 compressed bytes; 7 members (two distributions, notes, checksums, ELF, map, provenance) |
| Nested complete distribution | `dist/Prospero.Eden-Encore-R457.zip` | `9968a2528aa868e4b0bffc5145e6d34088df43e7b761ece21e1a72e1164e524e` | 279 files: 200 exact application files, 79 top-level docs/licenses |
| Nested minimal FTP distribution | `dist/Eden-Encore-R457-cc8044ce-FTP-PPSA99008.zip` | `4953a23ca75303ac381322588bc5bbd51332572c8f3cf34f64e68e447f4b6100` | 87 runtime files, intentionally excludes 82 installed legal texts and 31 ShadowMount companion `.txt` catalogs |

Entire ZIP member CRC checks passed on all four archives. **200/200 full-app SHA256 hashes** are identical between FTP artifact and complete distribution; **87/87** minimal runtime SHA256 hashes also identical. No duplicate members, unsafe paths, encrypted members, symlinks or case-insensitive filename collisions in staged application. The 31 `.po` catalogs are present in all distributions; companion `.txt` files are byte-identical in the full archive. `tools/ci/make-dist.py` intentionally excludes the 113 files from its minimal FTP ZIP; **not a regression**. All 20 WAVs have valid WAVE signatures and 48 kHz sample rates; 9 UI WebPs have valid RIFF/WEBP markers; 74 top-level license files included in complete distribution.

## Exact compiled binary and symbols
- `PPSA99008/eboot.bin`: **79,980,575 bytes**, SHA256 `af2a10fb7c3faf7291357a800d1c66c143c9c22d28894f8ac1cb6319a10b8b70`; valid PS5 SELF magic, same byte content across full/FTP archives.
- `build/symbols/Prospero.Eden-Encore-R457.elf`: **202,775,120 bytes**, SHA256 `719895f14998f0001000d2437bb5c516bf22f7d65ed39b9a2216c1afcf603a27`; unstripped ELF64 x86-64 PIE with `.symtab`, `.debug_info`, `.debug_line` and further DWARF sections.
- `build/symbols/link.map`: **55,309,353 bytes**, SHA256 `3a5c4442fc5f74ffcbaca39eb7f87d8d78711671564812f5163c913e0b8d8460`.
- Actual `build/symbols/crash-provenance.json` hashes, byte lengths and run SHA independently verified against all three files. Correct manifest flags: `confirmed_same_console_binary=false`, `native_ps5_execution_verified=false` (console not tested yet).
- Actual SELF and ELF both contain session-boundary/failure receipts, NS2 guest-fault receipt, extracted-update and shader miss diagnostics strings. Presence confirms linked ownership, **not in-game execution**.

## Log exceptions reviewed, rather than erased

| Log line | Result |
|---:|---|
| 3107–3108 | Mesa `u_process.c` `#pragma message`: per-application configuration may not work for target OS; informational compiler note |
| 3668 | Mesa/Meson: TLS dialect cannot be auto-detected while cross-compiling; compiler default chosen; PS5 ABI behavior untested |
| 8202 | Node `[DEP0005] Buffer()` deprecation in GitHub download action, not native PS5 app |
| 2835–2838 | GCC NIR generated-source note: `-Wmisleading-indentation` column tracking disabled due huge source; optional `-flarge-source-files` |
| 6036, 6042 | Negative CMake feature probes; configuration and native compilation completed |
| 6044, 6120–6122; 6135; 6283 | Optional RenderDoc, libinotify and libusb unavailable; no required-link failure |
| 6142 | SDL source revision `SDL-3.4.8-HEAD-HASH-NOTFOUND`; bundled SDL3 release version reported |
| 8081 | `Native weak imports resolved to NULL: 5719`; intended two-pass linker resolution per `tools/link-headless-native.sh`, but actual optional runtime API call safety still needs PS5 verification |
| 2023–2036 | Six intentionally failing *historical negative tests* against uncorrected GPU-lifetime behavior; corrected scenarios passed |
| 2414–2422 | Historical FC27 replay: `STUTTER_REGRESSION_PASS` explicitly **recognizes** old bad baseline `stutter_sla: FAIL`: 858 frames >50 ms, 10 frames >500 ms, worst 1288.1 ms. **No new gameplay improvement demonstrated.** |
| 8120 | `EDEN_RELEASE_EXPERIMENTS_COMPILED sparse=on native_profile=release cross_core_shared_jit=off batch=off alias_runtime_probe=pending hardware=untested` |
| 8282 | Provenance explicitly says PS5 hardware execution NOT verified |

No real compiler `error:`, failed final link, `##[error]`, failing ZIP validation, or corrupt member was found in full log. Shell `::error::` trap lines are dormant script literals; no error event occurred. The CLI reports 1,251 Ninja progress events of denominator 1,252, including a successful final `eden-headless` link; stage and package validators followed successfully.

## Required console validation (issue closure blocked)
1. **FC27 NS1:** cold start/match, text and HUD propagation, pause latency, frame pacing, exit/relaunch in same Encore process, logging ON/OFF lifecycle; earlier stutters/OOM remain P0/P1 until observed fixed.
2. **MKW and Bananza NS2:** first guest PC/LR/SP and loader/update result, test whether `PC=0x4` remains; do not misattribute to shaders if no graphics execution occurs.
3. Retain this exact SHA and run number in console logs, with matching ELF/map for symbolication. Do not overwrite the only diagnostic copy or remove save data.

**Audit boundary:** all checks above are real host/ZIP/ELF tests; no firmware-13.60 installation or in-game NS1/NS2 result was fabricated.