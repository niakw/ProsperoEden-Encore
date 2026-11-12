# Eden Encore PS5 native integration acceptance — 11 November 2026

Source SHA before build trigger: `f5ed4b6c4c83f2220f390edcc6d4210e4193c0f7`.

Integrated production sources: NS1 six-core ABI, NS2 12 GiB sparse virtual/physical owner, native R2/R3/R4, launcher cover dual-worker decode, PR47 warning/provenance, PR48 Node24, R09 vendor 720p/1080p readback, ViT nine-slot pool, FSwin shared scratch, A4K image/view return, R09 720p geometry/composition validation source.

## Native acceptance must prove

1. Native CMake selected actual PS5 source owners and compiled every changed translation unit.
2. Complete link and exactly one canonical distribution ZIP; no replay of previous R457 binary.
3. Proper R437 vs R2 exact source reconstruction and Vulkan additive SHA manifests.
4. On real PS5: NS1 actual game start, NS2 12 GiB guest VA backing with bounded committed physical memory, first frame and device/GPU alias lifetime.
5. Launcher actual console image orientation, complete front/rear case loading, light/dark/Neon focus, firmware family summary and transition without black flashes.
6. DLSS-NR Original/Compact 720p trained 152-stage Vulkan execution and output/image quality, separate from source/host qualification.

Host source validation does not establish gameplay success. This commit requests one canonical native application build and no GitHub Release publishing. The 720p trained DLSS-NR graph is not qualified yet; do not misreport success.


## Production native build rerun after validated host fixes

Host source preflight identified and fixed: dynamic hero title/caption checks in three independent scripts, three neutral workflow step labels, two whitespace defects in native NS2 workflow YAML, and the SHA-pinned shared R437/R2 source replay required by the source audit. First four source shards were green at run #43073115349; full PS5 SDK compilation is not yet qualified. Current code unchanged from 1cd6b31c155eb1b2d269e48d873caba6dbd41266; package must be generated from this new exact source SHA, never from the R457 checkpoint. No release publication without a green build and exact app+symbols provenance.

## Native acceptance retry after WebP package repair

The full native build #43074114537 linked all 1,588 native objects and staged
eboot.bin, but the package inventory rejected an optional daily wallpaper
family generated as JPEG. The reviewed correction now converts all bundled
daily Switch 1/2 backgrounds to WebP, checks RIFF content and exact indexed
filenames, retains existing user-imported PNG/JPEG/TGA/WebP files, and normalizes
EXIF orientation before stripping metadata. The duplicate JPEG inventory
validator was removed. Native preflight #43080730130 is green on source
11304bb3; the five shorter source-preflight shards are green. Vendor research
PRs #34/#39/#40/#42 and engine #43 are closed as source-superseded. Vendor
Dependabot #44 was merged for docs only. No research-only 720p GPU path has
been promoted to a qualified PS5 shader pipeline.

This requests exactly one fresh canonical PS5 package from the updated source
and its existing source-pinned vendor, with no GitHub Release publication.
Actual NS1/NS2 game boots, color/orientation on console, and R09 real PS5
output remain console acceptance gates.


## Superseding 12 November requirements

Earlier wording about **sixteen bundled daily WebPs** is superseded by the explicit user requirement: **eight user-selected, on-demand WebPs only**, none in install/update packages. Production code `e1a4b0a6` removes build-time art, `b79831d3` adds an async first-selection fetch and one-attempt-per-day cache receipt, and `2081099c` preserves the existing 31-locale translation source keys while keeping WebP user imports enabled. No final PS5 visual or gameplay proof is inferred from these commits. 33 NS1/global upstream work packages remain subject to integration/reconciliation; see the 12 November register on main. The draft release remains unpublished.
