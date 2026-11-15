# PS5 Library / Control icon / MSAA source review — 2026-11-15

## Scope

Physical PS5 retest of native package built from engine `20ec9a25380ad5446bf39fe32582a0f647692362`
and selected vendor `4572e581d011c444fd59428d5c042098f05dcfca` reported:

- very slow Library readiness and return-to-Library latency;
- extracted NS2 Home tiles showing portrait/late artwork, with local icons appearing only after focus/enrichment;
- MSAA choices exposing only the selected value, without useful help text.

This review does **not** claim those symptoms fixed on PS5. It records the source cause/candidate,
upstream evidence and host qualification required before the next console A/B.

## Console/log evidence

The 2026-11-15 archive contains extracted-title size observations around 23.5 GiB and 9.2 GiB.
The shipping Library scan called `ExtractedBaseBytes(entry.path(), cancel)` for every deconstructed
title before publishing the initial snapshot. That helper recursively enumerates the extracted tree,
so title size was on the navigation-critical Library scan rather than selected-title enrichment.

The same session showed delayed NS2 tile media and repeated media resolutions. The source Home path
for installed-but-unplayed extracted titles used only an existing cached `CoverPath`; it did not
attempt the title's local Control icon before Nlib/full Library enrichment.

## Upstream / format references checked before correction

- hacBrewPack Control metadata convention:
  https://github.com/The-4n/hacBrewPack
  (`control.nacp` and localized `icon_<Language>.dat`, standard application icon content).
- suyu/yuzu-family Control metadata loaders use localized Control RomFS icons rather than treating
  `exefs/main` as an application icon source.
- Encore's own `headless/metadata_bridge.cpp` already reads Control RomFS
  `icon_<Language>.dat` for packaged NSP/XCI titles.

The correction therefore reuses the established Control-content convention for extracted titles
instead of inventing a PS5-specific thumbnail format.

## Source correction

Branch: `fix/nov15-library-icons-msaa`.

1. Initial Library enumeration no longer recursively measures every extracted title.
   Deconstructed titles publish size as unknown (`—`) and log
   `EDEN_EXEFS_SIZE ... status=deferred`.
2. Exact extracted size is measured only by the selected-title asynchronous media enrichment worker.
3. `ExtractedLocalCover` prefers symlink-safe `control/` or `base/control/`
   `icon_<Language>.dat`, validates JPEG/PNG content and chooses the current supported game/UI
   language first, then falls back to another valid icon.
4. Home's shallow installed-title scan surfaces that local square Control icon immediately for an
   extracted title when no cached cover exists. It does not wait for Nlib/network/full-media focus.
5. Legacy loose ExeFS/root artwork remains a fallback.
6. MSAA 2x/4x/8x/16x share localized help explaining geometry multisampling and PS5 GPU/memory cost;
   the selected value continues to identify the sample count.

## Host qualification

MacBridge run 43700408854 proved the earlier source state with:

- 31 locale catalogs: zero missing/stale entries;
- launcher string checker: zero problems/warnings;
- extracted-library real-source Clang/GCC O0/O2 witness PASS;
- Nov13 launcher regression gate PASS;
- unified dynamic loading source contract PASS;
- startup contract PASS.

A subsequent run correctly caught stale one-argument calls in the extracted-cover test fixture after
the localized API was introduced. The fixture was corrected and now includes explicit French and
American-English Control icon cases. Final branch-head qualification is required before merge.

## Acceptance still pending

- PS5 cold Library time and return-from-game time.
- NS2 tiles visible immediately without focus, network or Nlib completion.
- Square/contain-fit visual quality of the selected Control icon.
- Exact selected-title size appearing later without blocking navigation.
- MSAA help-card appearance and localization on physical PS5.

No PS5 runtime, FPS or gameplay claim is made by this source review.
