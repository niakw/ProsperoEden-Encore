# Eden Encore — R457 draft changelog addendum · 12 November 2026

**UNPUBLISHED DRAFT PRERELEASE. No release assets, no published download and no real PS5 boot qualification.**

## Native PS5 integration and crash diagnosis
- The previous R457 NS1 FC27 crash had a proven 4-core/6-core KProcess header ABI mismatch between core and audio (null read of Memory::GetSpan). The current native source explicitly selects the same six-core header for core/audio/video/HID and compiles ABI probes. **A new installed-console NS1 boot is not yet proven.**
- Previous NS2 failure `Backing allocation: Cannot allocate memory` came from treating a 12 GiB guest address region as a monolithic host allocation. Current native source uses sparse guest VA and bounded physical pages with source/host tests. **A new installed-console NS2 first frame is not yet proven.**
- Native build #43074114537 compiled and linked 1,588 steps, produced a signed `eboot.bin` (76.7 MB) but its package staging validator rejected older bundled daily-media inventory. The package has since been corrected and requires an exact-source full build. No earlier R457 ZIP is substituted for a new native compile.

## Launcher and artwork
- Both case faces are independently fetched/decoded as bounded concurrent tasks, with GL uploads serialized on the owner thread; real NS2 cover-load timing and Mario Kart World physical side margins remain console test items.
- Explicit OpenGL last-jacket capture / Vulkan handoff with bounded retries exists; transition black flash is not yet hardware-qualified.
- Preset logo assets and built-in launcher backgrounds are WebP. Explicit personal imports support PNG, JPEG, TGA and WebP without modifying user originals.
- **Daily background is opt-in:** zero daily artworks in initial install or app updates; no request before first user selection; only then may the async worker download **at most eight** newest dated NS1/NS2 game promo images. WebP is encoded at 1280×720 with EXIF orientation handling; daily selection rotates locally. An on-device daily receipt prevents repeated fetches on the same date. Subsequent refreshes run only while Daily remains selected. No game art is shipped to users without opt-in.
- 31 official PS5 system locales/catalogs remain selected, with no new untranslated UI source strings.

## Neural rendering R09 and NS1 upstream
- Vendor R09 native owner includes A4K x2 image/view handoff, 720p/1080p readback dimensions, ViT and FSwin scoped memory-policy sources. The 152-stage trained 720p DLSS-NR Vulkan graph and subjective image output are **not** qualified on a physical PS5. Host shader and policy green do not imply functional GPU output.
- The 33 upstream NS1/global discrepancies are enumerated in `docs/audits/ENCORE_NS1_GLOBAL_R23_33_GAPS_PR_BRANCH_HANDOFF_2026-11-12.md` with original PRs and branches. At the audit snapshot **32 engine plus 37 vendor PRs are open**. Research branches are not production integrations; notable overlaps include Dynarmic JIT, savedata/RomFS, HID reconnection, SGSR applet layers and conditional-Phi shader IR. No claim that all 33 were integrated into the candidate build.
- Vendor docs-only Dependabot PR #44 was squash-merged; R09 research PRs vendor #34/#39/#40/#42 and engine #43 were closed as superseded by selected source incorporation, not as GPU proof.

## Testing / release policy
- Preserve this GitHub Release as **draft + prerelease** until native build, package ZIP, CMake/linker provenance, and user console regression are verified. **No automatic publication**.
- User PS5 acceptance: NS1 launch/audio, NS2 memory allocator / first frame, launcher images/orientation, quick menu shortcuts, theme accessibility, firmware count, app revision and seamless jacket-to-Vulkan frame.
- Published R1 is unchanged; no R457 candidate is claimed installable until a green final build and exact ZIP digest exist.
