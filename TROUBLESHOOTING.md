# Troubleshooting — Prospero.Eden Encore

[← Main README](README.md) · [Installation / upgrading](INSTALL.md) · [Languages](LANGUAGES.md) · [Support](SUPPORT.md)

This is a practical guide to common problems, not a compatibility guarantee. Encore has been tested on a PS5 running **firmware 13.60 only**. Earlier firmware might work but is not qualified; no minimum firmware is established.

## Before changing anything: protect your data

**Never delete `/data/prosperoeden/` to “fix” an install.** It can contain your settings, saved games, keys and other important files. Back up both the complete application `/data/homebrew/PPSA99008/` and persistent `/data/prosperoeden/` data, plus any selected external-storage root.

Encore and the original native ProsperoEden **share application ID `PPSA99008`**. They do not normally install as separate applications. Use [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) to update Encore—not an arbitrary upstream release.

## Find your problem

| Symptom | What to check first |
| --- | --- |
| **App won't open, black screen or crash** | Correct package, complete file layout, homebrew environment and Diagnostics/logs |
| **“Setup incomplete”** | Current Storage root and your `keys/prod.keys` and firmware files |
| **Games missing from Library** | Correct `roms/` under the *selected* storage root; supported file extension |
| **Launcher stuck in English** | Settings → Language and complete `PPSA99008/ui/lang/` catalogs |
| **A title fails after changing its settings** | One-session **Safe Launch**, without deleting saved data |
| **Artwork or screenshots missing** | Artwork fetching/metadata and network; sample art is fictional, not a compatibility list |
| **Stutter, stale HUD, pause/half-time freeze** | Known outstanding gameplay issues; collect a reproducible example |
| **Wrong buttons or glyphs in games** | Per-game Controls profile; a game's own button images may remain Nintendo-style |
| **NSZ/XCZ extremely slow** | Solid compression may need decompression and free space |
| **ZIP vs FFPFSC conflicting installs** | Identify which `PPSA99008` is being launched/mounted before updating |

## Application doesn't start

1. Get the package from [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) and verify any published checksum. A passing CI artifact does not automatically equal a console-tested release.
2. In a regular ZIP/FTP install, you need a **single complete** `PPSA99008/` directory containing `eboot.bin`, `sce_sys/param.json` and `ui/lang/`. Avoid the accidental `PPSA99008/PPSA99008/` nesting.
3. With **FFPFSC/ShadowMountPlus**, use the image-specific mount/update steps. Do not unpack the image into the ordinary app folder.
4. Verify the required PS5 homebrew environment is working. General jailbreak, FPKG/PPR entitlement and kstuff issues are outside Encore's support scope.
5. Check the app Diagnostics screen and `/data/prosperoeden/logs/` without publishing sensitive information.

[Full ZIP/FTP and FFPFSC instructions](INSTALL.md).

## Launcher stays in English

The **language menu offers 18 choices representing 13 distinct languages**, while a complete package includes **29** `ui/lang/*.po` translation catalogs. A few catalogs are not selectable in the current launcher.

Select **Settings → Language**. If the selected language is ignored after a manual FTP upgrade, reinstall the **entire application directory including `ui/lang/`**, and follow [the old-development-language-override checks](INSTALL.md#if-encore-is-set-to-french-but-the-launcher-stays-in-english). Do not remove unknown files blindly.

## Library, storage, keys or firmware

The selected Storage root normally has `keys/`, `firmware/`, `roms/`, `updates/` and other subdirectories. An external drive must use the **same structure beneath the selected root**.

Check the root actually selected in Settings → Storage. Direct NRO/NSO/NCA/NAX/KIP files might not contain a complete bootable title. A compressed NSZ/XCZ title can also need extra free storage and decompression work.

Encore never bundles keys, proprietary firmware or commercial games. Use only files and content you are entitled to use.

## Performance, gameplay and controller issues

A successful build or host regression test **does not prove stable PS5 frame times**. The active investigations include first-use shader compilation, pipeline waiting, texture freshness, game-input mapping and freezes during pause or half-time. Start with the **Recommended** video profile and change one setting at a time; see [Settings](SETTINGS.md).

The emulator's controller profile cannot universally replace **button graphics drawn inside a game**. Try the PlayStation, Switch or per-title Custom profiles before reporting a mapping bug.

**Switch 2:** compatibility research is isolated in a separate branch; it is not included in the current PS5 release. Frame generation and automatic updates appear on the roadmap but are not available as verified shipped features.

## Reporting an issue

Please include the Encore release or **commit SHA**, console firmware, installation method (ZIP or FFPFSC), renderer, selected storage, language, controller profile, steps to reproduce, expected/actual behavior and whether the test used a **real PS5**. Redact logs from `/data/prosperoeden/logs/`.

**Never upload console keys, identifying information, account data, save files or commercial game files.** File regular bugs via [GitHub Issues](https://github.com/niakw/ProsperoEden-Encore/issues/new/choose); report security issues privately using [SECURITY.md](SECURITY.md).
