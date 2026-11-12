# Eden Encore — R25 Appearance / R21 Application Updates

Status: maintained PS5 launcher integrated on engine main. This is a running architecture/behavior register, not a hardware visual test receipt.

## R25 — Personalization architecture

The launcher layout and theme colors are independent. Existing Encore Neon
remains the default. The selectable themes are Neon, Switch, Non-Neon, Dark,
and Light. Switch retains its dedicated original controls and style.

The three official new logos were copied unchanged from the supplied files:
assets/branding/encore-noneon.png, encore-white.png and encore-dark.png.
They are packaged as lossless WebP by the native build pipeline, along with the
original Neon branding. The original Switch logo and source artwork are kept.
Automatic logo choices are Neon for Neon, Non-Neon for Non-Neon, White for
Dark and Dark for Light. The user can override the choice using the same
four official logos; no arbitrary image is accepted as an app logo.

Settings > Appearance includes a controller-first 20-row editor:
theme, logo, accent, background, local image, two swatch presets and six
R/G/B channels (0..255) for solid/gradient colors, focus neon on/off and
strength, image darkness, motion, fit, selected-game background on/off,
and reset to Neon. Left/Right change RGB by 8, Cross changes by 1. The selections persist in the existing
atomically written prosperoeden.json, with backwards-compatible defaults and
range/type checks. They do not write any game configuration.

Local personal wallpaper folder: <Eden::UserDir()>/wallpapers.
Personal wallpapers remain in their original PNG, JPEG, TGA or WebP format
(up to 12 MiB and a basename no longer than 120 characters). Packaged launcher
art and downloaded cover caches use WebP. Decoding occurs
on the existing launcher texture worker, never synchronously in draw().

Daily Switch 1/2 is strictly opt-in. The base install and future app updates
include **zero** daily game images, and no initial background request is
performed at launcher start. Only the first explicit selection of the Daily
background allows the asynchronous first download under:
`<Eden::UserDir()>/wallpapers/daily/`

The cache contains at most **8** currently released NS1/NS2 titles (newest
verified release dates first); every downloaded/built-in image is WebP. Source
media is decoded, normalized for portrait/landscape with no double vertical
flip, resized to the target raster, and cached atomically. The selected
background rotates by local calendar day. Only while the option remains
selected may a later day trigger a bounded refresh; disabled mode must never
download or update the catalog. Temporary failures keep any valid local
snapshot; no network operation runs on the render thread.

The optional host generator `tools/launcher/fetch_daily_switch.py` is for
test/explicit off-console maintenance only, NOT for standard package builds.
A prior package-generated catalog is not a reason to fetch before opt-in.
All user-supplied backgrounds may remain in their original PNG/JPEG/TGA/WebP
format: this personal-import exception does not apply to packaged or
downloaded game artwork.

Redistribution/licensing of third-party artwork still needs independent rights
review. A missing cache falls back to the standard Encore artwork; never
render a black screen or block game launch.

## R21 — Application updates

An Application settings category exposes manual forced checking and an
opt-in check at launcher startup (off by default). Stable metadata comes
solely from:
https://api.github.com/repos/niakw/ProsperoEden-Encore/releases/latest

A background worker performs the query. The worker holds an isolated, reference-free
release query task and a shared result; destruction of the launcher does not
join the network request or block game admission. The parser rejects drafts,
prereleases, unexpected JSON, hostile tags, unsupported assets, and
network failures without interrupting normal navigation. R revisions are
compared numerically rather than lexically. The parser now lives in
`headless/prosperoeden/launcher_update_release.hpp`: it checks the exact
GitHub asset URL, PPSA99008 identity, format, declared byte size (1 MiB to
1 GiB) and SHA-256 digest metadata. **These checks qualify metadata only**;
they never authorize execution, even if the published digest is present.

Automatic checking is performed at most once per application process. The
worker and its last result are shared across launcher reconstruction after
starting a game or switching languages. An in-progress check can finish
while the player is in a game, then be reported on returning Home. A newer
stable version causes at most one controller-dismissable informational notice
per version and running process, with a bounded official changelog excerpt.
Manual `Check now` always starts a fresh check once no request is in flight,
regardless of the automatic-check switch. Invalid/offline responses do not
show a popup. No automatic downloading or installing occurs.

**Important safety limitation:** no installation/download button is exposed
until a verified native PS5 installer exists. Current official releases
publish an FTP ZIP, not a proven atomic PS5 self-install package.
This PR never overwrites an active executable or touches saves/settings.
Completing R21 requires an audited installer, SHA-256 verification, explicit
confirmation popup, cancellation, restart strategy and real-console proof.

### R21 — offline directory ZIP preflight (not installation)

The host-only tool tools/launcher/preflight_app_update_zip.py accepts an
already-downloaded ZIP, the official release SHA-256, and the installed PS5
contentVersion. It does NOT download, extract or modify any app:

    python3 tools/launcher/preflight_app_update_zip.py release.zip \
      --sha256 HEX_DIGEST_FROM_OFFICIAL_RELEASE \
      --installed-version 01.000.041

The check rejects wrong SHA-256, corrupt archives, traversal, symlinks,
duplicate filenames, app/user data paths, ZIP expansion bombs, wrong
PPSA99008 title/content identity, missing eboot or libc and native
contentVersion that does not increase. Quotas: 1 GiB archive, 8192 entries,
512 MiB per file, 2 GiB total uncompressed size. It never extracts the ZIP.

The official public R1 release (October 15, 2026) is an FTP directory ZIP.
The upstream PS5 Native App Boilerplate has a self-update helper that runs
after the app exits and can swap a folder-install with a backup. However,
the original ProsperoEden integration refuses image-mounted installations
(mount_img.lnk). Its proof on some firmware does not qualify an Encore
.ffpfsc image install nor our target firmware 13.60. Never overwrite a
running eboot.bin or delete the app's saves, settings, ROMs, firmware or keys.

The visible R revision and PS5 contentVersion are independent. A future
native updater must verify both and refuse stale package versions even
if the release R tag increases. Real download/restart/cancellation/helper,
signed source, mount-kind checks, rollback and PS5 hardware tests remain P5.
No installation is enabled by this host-only tool.

## Release/version identity and localization (05 November 2026)

The release's **R revision** has exactly one origin: the exact native build's
EDEN_LAUNCHER_BUILD_LABEL compiler definition. Neither a workflow run number,
the current publisher checkout's HEAD, an old README heading, nor a constant
R1 in a header can override the compiled value. A custom/unversioned host
preview shows Unversioned, and a native build without a verified R number is
rejected instead of claiming to be R1.

The native packager writes a small encore-release.json alongside eboot.bin
with build_revision (Rx), source_sha (the same SHA CMake compiled) and
native_content_version (the numeric PS5 contentVersion). The release
resolver checks that these agree with the approved native artifact and its
sce_sys/param.json before deriving the GitHub tag, title, FTP ZIP basename
and generated release notes. make-dist.py uses that manifest for both the
normal ZIP and the .ffpfsc image name. The PS5 numeric version is distinct
from the user-facing R revision and **must increase** for a real upgrade.
The native builder derives it monotonically using
tools/ci/native-content-version.py: new R1 = 01.400.001,
R25 = 01.400.025, R323 = 01.400.323, R385 = 01.400.385.
The immutable 2026 public R1 artifact alone retains 01.000.041; it
is recognized by its exact source SHA and original native version.
The fixed 01.400.xxx format intentionally rejects R1000 and above
rather than silently inventing a rollover convention.
CMake compiles both version identifiers, package-headless-native.sh
checks the matching CMakeCache entries, and the release resolver refuses
artifacts whose manifest/param.json version does not match their R label.
No future release can silently inherit the original 01.000.041
contentVersion. Host previews without a compiled revision are Unversioned.

One immutable historical exception exists: the previously published
encore-R1-56293953 FTP artifact has no attestation because it predates the
change. Only the exact pinned source SHA together with its original PS5
contentVersion 01.000.041 may be identified as R1. Old release assets are
not rewritten. Later missing or inconsistent attestations fail closed.
No native update installation is activated by these metadata changes.

**Language-selector scope (9 November 2026): the native launcher must expose only the exact 31 PS5 console-language choices**, no extras, with 29 catalogs. See [strict PS5 system-language policy](PS5_SYSTEM_LANGUAGE_POLICY.md) and [Sony's official list](https://www.playstation.com/fr-fr/legal/language-support/).

All **29 existing locale catalogs** now include the 466 active UI strings,
including the R21 manual/automatic checking controls and R25 theme, logo,
RGB, wallpaper and overlay settings. Both maintained French catalogs and
the Spanish primary catalog receive contextual UI translations; additional
language text includes provisional short labels requiring native font,
layout and human wording review. The French embedded fallback and
launcher.pot have been regenerated from the same source set.
The strings checker and the full-coverage gate pass. Release status
messages are localized on the launcher owner thread; the background
GitHub worker returns structured status and never accesses a translation
catalog while performing the network request.

## Header update control and folder-only release policy (05 November 2026)

The Home header places an update/check icon immediately to the left of the
Settings gear in both Encore and Switch themes. The icon is green only
after a verified current stable release, amber when a newer official
release exists (including when it cannot yet be installed), blue while
checking and gray for unknown/offline/incompatible. Controller focus
opens a confirmation; Cross starts a fresh manual check and Circle
cancels. Confirming a check does NOT trigger an installation or write to
the console. App settings still support optional startup checks.

R21 now accepts only a SHA-256-bound FTP ZIP candidate for the single
folder installation target /data/homebrew/PPSA99008. The historic R1 FTP
ZIP retains its original filename; future ZIP names use the compiled R
revision and source SHA. Image-mounted FFPFSC/retail PKG files are not
considered installable, and images are no longer built in the default
release path. The developer --image-only command remains opt-in.

The reviewed upstream updater's helper engine is imported for isolated
development. It rejects a destination other than the literal
/data/homebrew/PPSA99008, inspects ZIP contents, and refuses a folder replacement that would
remove any existing nested file, including user-managed keys, firmware,
ROMs, updates, DLC, mods or saves. The host test runner also checks the
real C++ ZIP-directory
inspector and extraction engine on disposable archives: two accepted
app ZIPs and seven rejected unsafe cases (traversal, symlinks,
duplicate entries, protected data, missing required contents). An
unrelated second app is not extracted, matching the helper's documented
single-title isolation policy. None of these tests uses /data/homebrew
or executes a payload.

Host tests exercise destination refusal, conflict
preservation and backup creation. The engine is NOT invoked by the
launcher: there is no PS5-qualified download-to-helper, restart handoff,
rollback/recovery or real 13.60 console test. Do not enable installation
before those gates pass or call these host tests a complete R21.

## Tests and remaining qualification

- Seven launcher C++ sources compile in host syntax checks.
- R21 version, R21 release-metadata scenario matrix and R25 theme-preference
  host executables passed (including
  corrupted configuration and hostile wallpaper paths).
- Five hermetic Python unit tests passed for feed dates, platform validation,
  safe image sources, atomic writes and outage recovery.
- A real current snapshot generated 16 images, 8 NS1 plus 8 NS2, ~2.2 MB.
- R21 offline ZIP preflight: 19 hermetic Python scenarios pass; no extract/install.
- Still required: full native PS5 build, five-theme screenshots/contrast and
  navigation audit, capture-gallery permission audit, and secure native
  installation before closing R21 or all of R25.
