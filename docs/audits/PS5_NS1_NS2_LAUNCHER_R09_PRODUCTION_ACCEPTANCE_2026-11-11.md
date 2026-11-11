# Eden Encore — production PS5 acceptance, 11 November 2026

**Engine source:** `1962612ab79ece59de72fd95cbce4a824ce266fa` (exact parent SHA for the ensuing full-native verification commit).
**Vendor source:** engine-pinned production submodule, not floating vendor main.
**Status:** native host checks and packaging are not a substitute for a real PS5 game boot.
**Scope:** NS1, NS2, launcher, R09 Min, packaging. No research branch was merged wholesale.

## Real console regressions (from the user's installed R457, not from a newer build)

| Failure | Measured R457 evidence | Current production owner / proof still required |
|---|---|---|
| NS1 FC27 crash | `SIGSEGV` at `eboot+0x39152f`; audio guest-memory span pointer null; the old KProcess was compiled with mismatched 4-/6-core layout (`0x160` vs `0x1b0`) | CPU6 header and ABI witness for audio_core, video_core, hid_core, core, dynarmic, native executable are integrated. **Still require FC27 guest AudioOut startup, first guest frame and audio on an installed new binary.** |
| NS2 memory allocation | `Backing allocation: Cannot allocate memory`, old attempt `12886999040` contiguous bytes where maximum free span was lower | PS5 `EDEN_NS2_SPARSE_BACKING` path reserves 12 GiB virtual guest space and lazily owns 2 MiB direct-memory commits with a 6 GiB physical budget; no equivalent 12 GiB contiguous direct commit in that exact branch. **Still require live console installation, native reserve/commit telemetry and NS2 first guest frame.** |
| First frame not displayed | R457 crashed before game presentation on NS1/NS2 | No source-only success claim. Capture first Vulkan guest framebuffer and display if boot proceeds. |

## Launcher console-test acceptance matrix

| Reported regression | Current production mitigation | Console gate |
|---|---|---|
| NS2 cover images load late; launch 3D box front looks pasted in | Up to two bounded concurrent CPU cover decoders and owner-thread GL uploads, cached WebP, 3D composed-case readiness checks | Verify real NS2 title with cold and warm cache, front/back arrive before the 3D case animation; no noticeable pasted-on front |
| Mario Kart World white left/right bars (Library and 3D case) | Native paper UV crop and shared physical case artwork limits | Verify the exact Mario Kart World image, front and back, on PS5; no white side bars and no crop of printed text |
| R1/L1 shortcuts navigate Recent or Updates | Shoulder destination table contains only Home, Library and Settings; Recent and Updates remain accessible through D-pad | Test both directions from all three destination tabs |
| Inverted official logo in Neon, Non-Neon, Dark, Light, or 3D loader | Selected official theme logo resources are packaged as WebP; no second `-flip`; automatic theme variants | Verify visually each theme plus 3D loader, all top-down correct |
| Background or selected Eden artwork upside down | Packaged background WebP uses normalized pixel order; incoming daily WebP converted via `-auto-orient` then metadata stripped | Inspect real PS5 default, custom theme and daily background orientation |
| Light theme game description and focused button text illegible | Contrast adjusts to opaque/bright hero background; dark focused nav uses white ink | Inspect Light theme with and without game hero, focused/unfocused |
| Settings gear hover/focus ring offset | Nav icon center and focus square share the same geometry | Inspect all four theme variants with controller focus |
| Firmware reads `0 NCA` though NS1/NS2 directories exist | Source distinguishes NCA/extracted/ZIP firmware and independent NS1/NS2 roots | Verify installed actual firmware format(s) and report precise valid counts; a directory is not by itself valid firmware |
| App update says `R1` when installed `R457` and summary hidden | Native `EDEN_LAUNCHER_BUILD_LABEL` drives installed version; status/notes moved into an opaque band below buttons | Check old-release metadata response against a newer local version; inspect band and button overlap |
| 3D jacket -> black -> purple Vulkan loading -> guest frame | Real GL jacket captured with bounded retries before EGL close and passed in-memory to Vulkan `LaunchHandoff` until upload succeeds | **Still unproven** when swapchain opens / readback/upload fails; record `EDEN_LOADER_JACKET_HANDOFF_CAPTURE` and Vulkan upload/provisional present; require no black or duplicate loading screen |
| Selected game artwork front appears late after rendered 3D box | Bounded 2-worker decode and readiness policy | Confirm front/back are already ready or case waits without visible cut/paste |

## Built-in media source and packaging rules

- **ALL built-in launcher images, including auto-fetched covers and daily wallpapers, are WebP.** Fixed logos/case art stay lossless where needed; daily game backgrounds are lossy WebP quality 80 at 1280x720. There must be no packaged `ui/art/daily/wall-*.jpg` or PNG/TGA art left as runtime UI resources. The PS5 system's `sce_sys/icon0.png` is a separate platform-mandated format, not a launcher runtime exception.
- **Only user-supplied/imported artwork** may remain PNG, JPEG, TGA or WebP; no forced conversion of personal content.
- Daily inventory: 16 newest verified released NS1/NS2 games (not preorders, duplicate titles or releases older than 180 days), `wall-00.webp` ... `wall-15.webp`; strict `index.json` manifest. A valid **rebuild** refreshes the catalog and retains unchanged WebP cache; failure is fail-safe. The **installed console only rotates locally by day** and does **not** autonomously fetch a new game catalog over the network yet.
- Correct EXIF orientation must be applied once before stripping metadata; image decoding/UI UVs must not invert it again. Real host fixture verifies pixel top/bottom after ImageMagick WebP conversion. **Hardware visual inspection is outstanding.**
- Asset redistribution rights need separate publication review; `EDEN_BAKE_DAILY_SWITCH_ART=0` disables auto-fetch for offline/legal reproductions.
- Release must contain one user-facing installable FTP app ZIP with canonical PPSA99008 root. CI may also upload a separate symbol/debug artifact; neither an unvalidated package nor an Actions artifact should be presented as a published GitHub Release.

## R09 DLSS-NR Min and native composition status

- Source implementations / size policies / isolated host witnesses from closed engine PR #43 and vendor PRs #34, #39, #40, #42 were adapted into current production sources without wholesale merging disabled research branches. Vendor #44 npm documentation dependency update is merged independently.
- ViT nine-slot pool, FSwin scratch lifetime, A4K output view and 720p readback represent **source integrations / guarded interfaces**, not a demonstrated 152-layer end-to-end 720p DLSS-NR GPU output.
- Current normal present path still has the 1080p admission gate; **do not claim** 720p neural + AA/spatial upscaler/frame-generation combinations are operational without real Vulkan GPU proof. Any unsupported route must refuse or fall back safely, never show stale graphics.
- Independent NS1 C03/RADV, AM/HID, audit research branches must not be silently merged into production by this build.

## Native acceptance process

1. Confirm current source QA: 6 mandatory source shards, 4 P0-P4 shards + witness, focused NS2 tests, built-in WebP packaging/orientation tests, vendor pin.
2. Build actual native PS5 executable from the **exact** engine/vendor source pins and validate full stage + signed ELF + symbol provenance + canonical FTP ZIP.
3. Load **this exact artifact** on PS5 with cache cleared, reproduce NS1 FC27 and NS2 game startup, gather minimal build-SHA-specific boot logs without publishing private paths; inspect user-requested launcher visual matrix.
4. Only after first guest frames and diagnostics: mark crashes and visual/transition defects resolved. CI/source-green status alone is not a console boot result.

**No live-console NS1/NS2 first-frame or visual proof has been supplied for this SHA.**
