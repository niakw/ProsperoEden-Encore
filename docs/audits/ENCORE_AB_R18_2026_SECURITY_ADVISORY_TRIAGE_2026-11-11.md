# A/B R18 — security advisory and actual package exposure triage

**11 November 2026, source security review only, PR #45.** Pinned vendor `f8f5d8ee`, source family tree `99ffa030` unchanged since `22b69d6`. This is **not a declaration of a vulnerable or clean PS5 executable**: only exact native link, build flags, runtime reachability and package SBOM can prove shipping exposure.

## HarfBuzz 12.3.2 — two relevant 2026 CVEs, conditional WebAssembly shaper

- **CVE-2026-113679** (out-of-bounds write, affected HarfBuzz versions 8.0.0–14.6.0, includes **12.3.2**): [OSV entry](https://osv.dev/vulnerability/CVE-2026-113679), fixed upstream in [`5e821de8256d01780566b5c8ab7886fae4c93da8`](https://github.com/harfbuzz/harfbuzz/commit/5e821de8256d01780566b5c8ab7886fae4c93da8) on 19 Oct 2026. The issue involves a wrong WAMR host import signature in the **experimental WebAssembly shaper**.
- **CVE-2026-113680** (WASM shaper invalid pointer dereference, same affected range): [OSV entry](https://osv.dev/vulnerability/CVE-2026-113680), fixed in [`a71aa86c2bac114fafb6b47f8da02024ecb44fa6`](https://github.com/harfbuzz/harfbuzz/commit/a71aa86c2bac114fafb6b47f8da02024ecb44fa6).
- Real pinned source check: `vendor/sources/harfbuzz/meson_options.txt` Git blob `a35ab48607a146253641d9fc5e6e13820ff28dd1` line 30 sets **`option('wasm', ... value: 'disabled')`**. Its `meson.build` gates `wasm_dep` on that opt-in and sets `HAVE_WASM` only after finding `iwasm`. Pinned `CMakeLists.txt` blob `3ad5e433f2d55aa9a6c1d4e6d8c90b8e7ba0cb8b` contains no WASM/WAMR build option. Thus **source-default reachability is low**; no proof has yet established the *actual native compile definition and linked HarfBuzz* in the shipped PS5 package. Do not claim confirmed exploitable runtime, but do not call source unaffected.
- **Release gate:** actual compile flags, CMake/Meson owner, symbol/string reachability (`HAVE_WASM`, `iwasm`, `hb_wasm_*`), and comparison with upstream fixes. Do not enable experimental WASM functionality to test or solve these advisories. Source patch/backport can be reviewed only on the correct owner if unexpectedly linked.

## FFmpeg 2026-02 pin — cannot assert patched July/September advisories

- Vendored `FFmpeg/FFmpeg@c7b5f1537d9c52efa50fd10d106ca015ddde1818` is an official master commit dated **22 Feb 2026** (GitHub object: `CONTRIBUTING.md: Add Forgejo`). It is **earlier** than the later official [FFmpeg 2026 security fixes](https://ffmpeg.org/security.html), including CVE-2026-8461 and CVE-2026-30999; the project's [downloads/release log](https://ffmpeg.org/download.html) lists multiple security-maintained later branches. Date ordering alone does **not** certify a specific vulnerable decoder or guarantee the snapshot lacks a cherry-pick.
- **Release gate:** enumerate the exact enabled codec/bitstream parsers, FFmpeg native compile flags, object/link hashes, and affected code/fix commit ancestry for each relevant 2025–2026 CVE. Prioritize decode paths reachable from guest NVDEC/video streams, including malformed input tests. Do not hot-upgrade all FFmpeg source without SDK/codec compatibility proofs.

## Mesa and other dependencies

- Vendored source includes Mesa 26.2.0 and a **diverged** PS5 Mesa fork, plus 12 locally overlaid RADV C units. The [official Mesa 26.2.0 notes](https://docs.mesa3d.org/relnotes/26.2.0.html) identify this as a development release and enumerate driver, RADV and security fixes; presence in the source tree is *not* evidence any specific driver/object was compiled or vulnerable. Require Meson CDB, selected-source SHA, Vulkan ABI and hardware tests, not blind cherry-picks.
- `libwebp` is pinned to an exact v1.6.0 Git source tree; [Debian libwebp security tracker](https://security-tracker.debian.org/tracker/source-package/libwebp) is one external advisory reference, not a proof that the PS5-selected decode path is clean. Continue actual package reachability and malicious WebP/cover-image negative tests.
- Boost 1.90 source checkout has a 1,527-byte unexplained lock total; 22 CPM upstream download hashes were not independently verified. This is a provenance/compliance issue, not automatically a CVE.
- Licences/notices: audit actual packaged ELF/archives and derivative source attribution for FFmpeg, OpenSSL, HarfBuzz, libwebp, Mesa/RADV, Boost, GLFW/SDL, ImGui/NanoVG/Sokol/OpenGNM, SDK/payload and the active maintained vendor overrides. Verify actual linked path before attributing a missing notice or claiming compliance.
- GitHub security CodeQL green is **not** equivalent to an SBOM-wide OSV/CVE/license scan. The 26-root tree and object hashes being unchanged do not discharge vulnerability exposure checks.

## Concrete fail-closed outcome

**Findings:** 2 version-range matches for HarfBuzz's optional WASM shaper; unknown actual PS5 exposure; FFmpeg source pin predates publicly listed fixes; Mesa provenance and native override ABI incomplete; no complete package SBOM/licence proof. All must be tracked independently under **R18 security**, not silently absorbed into the generic 28 upstream semantic cases or marked passed by a successful host job. No vendor/main/production changes were made.
