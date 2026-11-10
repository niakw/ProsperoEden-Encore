# R18 — complete inventory of the 26 vendored source-family roots

**Audit:** 10 November 2026 · **Vendor pin:** `niakw/Prospero.Eden-Encore-vendor@22b69d6053db41b74edac2633c012f925b84f69e` · **Encore:** [isolated audit PR #45](https://github.com/niakw/ProsperoEden-Encore/pull/45). **Read only**: no repin, no main/vendor changes, no PS5 build. This is a **source-provenance snapshot**; archive hashes are declared pins unless independently tested, not an ELF SBOM or licences sign-off.

## Scope and exact totals

- Git tree `vendor/sources` = `99ffa030450df670cf039788445e4274d99ebcfb`: **26 immediate source-family roots**.
- Of these, **22** have root `VENDOR-ORIGIN.json`. The four without it are `eden-cpm`, `libwebp`, `ps5-fsr3-optical-flow`, `ps5-mihawkgen`. The first has a separate `VENDOR-CPM-LOCK.json`; the last three have byte-exact official **Git tree SHA** matches independently checked (below).
- `tools/deps.json` is a **fetch inventory of 22 items**: **15 Git, 6 archives, 1 files collection**. This is *not* a list of the 26 actual source roots: e.g. `pacbrew` is a downloaded archive not one of the 26 source-family roots, while frame-generation forks and `libwebp` are vendored source roots without an entry in this fetch file.
- All 15 pinned Git items were looked up by exact commit via GitHub. **12** official Git commit objects and trees were available; **3** pinned commits belonging to **2 unavailable blackbearreloaded repositories** could not be obtained.

## All 26 roots, with honest provenance evidence

| # | Vendored source-family root | Official pin / source | Proof and disposition |
|---:|---|---|---|
| 01 | `boilerplate-setup-0` | zlib 1.3.2, SHA256 `bb329a...` | Vendor origin marker identifies archive; **byte equivalence not independently verified** here; not the main boilerplate Git source |
| 02 | `boilerplate` | `blackbearreloaded/ps5-native-app-boilerplate@dd44bbd` | **Blocked**: official GitHub repository and pinned commit return 404 through current access |
| 03 | `compiler-rt` | LLVM 18.1.8 eight individually SHA256-pinned files | Source origin marker contains file count; 8 per-file fetch hashes in `tools/deps.json`; actual file hashes not independently re-run here |
| 04 | `eden-cpm` | Eden `cpmfile`, `VENDOR-CPM-LOCK.json` | **22** nested CPM components each identify repository, version, declared SHA256 and upstream SHA512; lock presence/inventory checked, **digest-to-vendored-bytes not rehashed** here |
| 05 | `eden` | `eden-emulator/mirror@5f142c79`, archive SHA256 `35ec0bb9...` | Official-vendored Git tree diff: **35 modified `src/` blobs** despite original-source immutability contract. Exact full blobs in [R18 35-difference manifest](R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json); no silent correction |
| 06 | `encore-overrides` | `niakw/encore-overrides@95f21edf` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |
| 07 | `ffmpeg` | `FFmpeg/FFmpeg@c7b5f153`, SHA512 declared | Archived snapshot with source origin marker; not independent source equality/linked decoder proof |
| 08 | `fmt` | `fmtlib/fmt` v12.1.0, SHA256 declared | Archived snapshot with origin marker; independent archived-byte attestation pending |
| 09 | `harfbuzz` | v12.3.2, SHA256 declared | Archived snapshot with origin marker and COPYING; independent archived-byte and runtime linkage proof pending |
| 10 | `libwebp` | `webmproject/libwebp` v1.6.0, commit `4fa2191233` | **Exact full Git source tree** `3a7830b9713d9187cf1211862d4571ff58b0d507`; zero added/removed/changed entries or file modes |
| 11 | `opengl-imgui` | `ocornut/imgui@f5befd2` | Exact pinned Git source tree **except added** `VENDOR-ORIGIN.json` |
| 12 | `opengl-mesa-26-2` | Mesa 26.2.0 source tarball, SHA256 `efd4bb08...` | Declared archive/source origin marker; byte equivalence not independently checked here |
| 13 | `opengl-nanovg` | `memononen/nanovg@ce3bf745` | Added origin marker; **two blob changes** (`LICENSE.txt`, `example/stb_image_write.h`) independently compared and **identical after CRLF→LF normalization**. No semantic/licence text change found |
| 14 | `opengl-native-boilerplate` | `blackbearreloaded/ps5-native-app-boilerplate@4f531c4` | **Blocked**: the referenced upstream repo and commit return 404. Distinct from row 02 and not a substitute for its pin |
| 15 | `opengl-opengnm-psbc` | `PS4-OpenGNM/opengnm-psbc@a92a122` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |
| 16 | `opengl-opengnm` | `PS4-OpenGNM/opengnm@4b295ca` | Added origin marker; one documentation-only change: `docs/requirements.txt` sets `mkdocs-material==9.7.7` rather than official `9.5.49`. Other source subtrees match exactly |
| 17 | `opengl-sokol` | `floooh/sokol@48c8590` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |
| 18 | `opengl-source` | `blackbearreloaded/ps5-opengl@ad2807d` | **Blocked**: official referenced repo and commit return 404; do not assert verified external SDK source purity |
| 19 | `opengl-spirv-headers` | `KhronosGroup/SPIRV-Headers@0d25db9` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |
| 20 | `opengl-vulkan-headers` | `KhronosGroup/Vulkan-Headers@b51f6b8` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |
| 21 | `ps5-fsr3-optical-flow` | `Swordpdf/ps5-framegen@64362101757cdd6f7df9eeb984cb53f03f1fbfca` | **Exact full Git tree** `85e34d638cd9e8b211e08fb19d1a57a588bb8d76`, no root marker required for this snapshot |
| 22 | `ps5-mesa` | `mihawk-99/PS5_Mesa@0b2d6d1` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json`. This does not attest native Mesa's **12 overlaid RADV units** or its linker |
| 23 | `ps5-mihawkgen` | `mihawk-99/PS5_MihawkGen@c57232a9f16bcb6df5fe07c9bb631518f2b1cc0e` | **Exact full Git tree** `e3b42f5b89775469bec04795b93f048b74aff207`, no root marker required |
| 24 | `ps5-payload-sdk-fork` | `mihawk-99/PS5_PayloadSDK@95c08f2` | Added origin marker; **3 blobs** differ: `host/win/prospero-deploy.cmd`, `include/freebsd/crypto/skipjack.h`, `include/ps5/kernel.h`. Each is independently **identical after CRLF→LF normalization** |
| 25 | `ps5-vulkan-tools` | `mihawk-99/PS5_Vulkan@3f3ee69` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |
| 26 | `zbic` | `kinnay/zbic@11b08f2` | Exact pinned Git tree **except added** `VENDOR-ORIGIN.json` |

**Cross-check:** 9 Git source families = original official tree plus root origin marker only; 2 Git families = marker + newline normalization; 1 Git family = marker + documentation dependency version change; 3 Git fetch entries blocked by repository access. Together these cover all **15 Git entries**. The **3 extra** byte-identical non-fetch Git source families are counted separately; the **22-entry CPM lock** is a different subsystem. These categories must not be summed into a fake '100% native dependencies safe' percentage.

### Why the Git comparisons are meaningful

For each of the 12 accessible Git origins, fetched the **exact pin's commit object** and its **official root Git tree SHA**. Compared each immediate tree entry by filename, type, mode and underlying Git blob/subtree SHA to the vendored source subtree. Unchanged recursive subtrees are byte-identical by Merkle identity; changed subtrees were independently expanded for PS5 SDK `host/` + `include/`, OpenGNM `docs/`, and NanoVG `example/`, with `truncated=false`. The six non-marker blob differences in SDK/NanoVG were fetched and CRLF-normalized before comparing full contents. Therefore no upstream code changes other than the documentation requirement difference were found **in these 12 audited Git families**.

**Limits:** Git's file identity checks do not prove that those bytes were linked into the PS5 ELF, contain no vulnerability, were built with proper flags, or are compatible with the console SDK. The 404 references must not be silently replaced by a different fork. The 35 `sources/eden` modified files are a separate known active provenance policy defect. Archive/CPM checksum claims require their own file-level verification. This audit does **not** authorize an upstream repin.

## Remaining full R18 exit obligations

1. Prove the three unavailable historical blackbearreloaded Git pins via trustworthy original archives, mirrors with verifiable hashes, or supply-chain custody evidence; do not invent an official replacement.
2. Hash actual installed archive bytes for the six archive downloads, eight compiler-rt individual files, and the 22 CPM lock entries. Distinguish declared checksum from observed.
3. Inspect **actually linked and distributed artifacts**, library attribution, notices/licences, PS5 SDK ABI/linker, and remaining applicable security advisories. Missing a NOTICE filename at root does not imply a violation when upstream notices or file SPDX identifiers exist.
4. Resolve the **35 edited original Eden blobs** with exact active source owners and test parity, without modifying `main`/`vendor` under this audit. Validate the 17 changed headers via real compiler include receipts rather than merely CMake's `compile_commands.json`; the ninth-run cache did not contain a usable Ninja dependency ledger.
5. Keep NS2 research separate. Only common source compatibility/NS1 non-regression can enter this A/B audit.

**Decision:** 26/26 **source-family identities inventoried**; **not** 26/26 externally certified or linked. R18 remains open for explicit verification above. No main build/vendor change.
