# R457 PS5 native artifact audit — 18 November 2026

## Provenance and status

- Engine: [`5245de8a08245475cdad617bb9be32d751f72864`](https://github.com/niakw/ProsperoEden-Encore/commit/5245de8a08245475cdad617bb9be32d751f72864)
- Pinned vendor: [`2ccc4b0a714ca621ac2879768f87118a64ed65f6`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/2ccc4b0a714ca621ac2879768f87118a64ed65f6)
- [Native build run #44347485302](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44347485302): **success**. Native target build/link/staging, FTP upload, release-bundle upload and cache save all completed successfully.
- Target title: `PPSA99008`; metadata `01.400.457` / `R457`, launcher title `Prospero.Eden Encore`, default parameter locale `en-US`.
- **PS5 installation, game launch, gameplay, GPU/guest boot and crash-free exit were not tested in this audit**. `build/symbols/crash-provenance.json` correctly records `confirmed_same_console_binary=false` and `native_ps5_execution_verified=false`.

## Authentic downloaded GitHub artifacts

Both ZIP assets were downloaded from the exact native run and examined directly, not inferred from filenames.

| GitHub artifact ID | Archive | Bytes on disk | SHA-256 |
|---|---|---:|---|
| `14447679359` | `Eden-Encore-PS5-FTP-PPSA99008.zip` | `41,165,660` | `6a2407fc77aed366662223e63048e943d148154dad71616d606899c5e3816767` |
| `14449141322` | `Prospero.Eden-Encore-release.zip` | `163,301,645` | `7432da22765cd8b55d1b6d937436f1ab7819d13e07ba033010cd416e00ba5f72` |

These SHA-256 sums **match GitHub's artifact digests**. Both ZIPs passed the complete CRC check; neither contained an unsafe absolute/traversal path, duplicate member, case-insensitive collision or ZIP symlink.

- Standalone FTP artifact: **200 files**, `115,511,132` bytes uncompressed, all rooted in `PPSA99008/`; upload extraction layout passed in CI.
- Release bundle: **7 members**, `338,500,557` bytes uncompressed, including `build/symbols/Prospero.Eden-Encore-R457.elf`, `build/symbols/link.map`, `build/symbols/crash-provenance.json`, the full install ZIP, the minimal FTP ZIP, SHA sums and release notes.
- Full release ZIP inside bundle: **279 members**, CRC pass; the extra top-level installation and legal documents are intentional.
- Minimal FTP ZIP inside bundle: **87 members**, CRC pass. Its `eboot.bin` and all 87 shared entries are byte-for-byte identical to the standalone 200-file FTP artifact. The 113 omitted files are installed legal notices (82) and 31 `ui/lang/*.txt` companions. This is **intentional** in `tools/ci/make-dist.py`: the minimal manual-FTP distribution excludes installed legal files and ShadowMount-only text companions. **Do not report this as file corruption.**
- Internal `dist/SHA256SUMS` correctly matches both ZIP files inside the release bundle. The standalone 200-file FTP ZIP is a different deliverable and has its own GitHub SHA-256.

## Binaries and crash symbolization

| File | Uncompressed size | Validation |
|---|---:|---|
| `PPSA99008/eboot.bin` | `79,939,295` bytes | Sony SELF magic `4f153d1d`; SHA `77f3e8c6b5669937ef5e80f5bf5222a98f2ff2d5a75b8d4f221334447b2f3e9e` |
| `build/symbols/Prospero.Eden-Encore-R457.elf` | `202,734,144` bytes | ELF64 PIE x86-64, unstripped, `.symtab` and `.debug_info` present; SHA `23640dcd8ede4f10f70141f3f8d6a0f6a07484272d32cd5f4054ee2bb8a9057b` |
| `build/symbols/link.map` | `55,272,630` bytes | SHA `9ec20be25b5090dbb72e703497a2197b2177761d25c3e8d0355c43b90659ff79` |
| `PPSA99008/sandbox-elevator.elf` | `551,464` bytes | Valid x86-64 ELF64 PIE |
| `PPSA99008/self-updater.elf` | `840,632` bytes | Valid x86-64 ELF64 PIE |
| `PPSA99008/sce_module/libc.prx` | `1,284,674` bytes | Present in installed app; proprietary PRX wrapper (do not parse as ordinary ELF) |

All **three crash-provenance hashes** independently matched the downloaded file bytes. The unstripped ELF has a debug symbol table and `link.map`; console crash reports must reference this exact build and address mapping.

ELF `DT_NEEDED` dependencies are target-side SPRX/PRX imports (12 total): `libSceRandom`, `libScePad`, `libSceUserService`, `libSceAgc`, `libSceVideoOut`, `libkernel`, `libSceSystemService`, `libSceAudioOut`, `libSceAgcDriver`, `libSceSysmodule`, `libSceLibcInternal`, `libSceNet`. No host Linux `.so` appears as a `DT_NEEDED` dependency. This is a **static import audit**, not proof that all target firmware modules resolve at runtime.

The unstripped ELF contains build-runner absolute paths in `DT_RUNPATH`; the full corresponding RUNPATH string is **not present in the packaged SELF**. Do not infer a PS5 loader failure from a debug ELF runpath without actual console evidence.

## Assets, localization and integrity

- Images: **13/13** PNG, DDS and WebP files parsed and structurally verified; included 512×512 app icon and 3840×2160 `pic0.dds`/`pic1.dds`.
- Audio: **20/20** WAV files decoded as valid WAV headers, all 48 kHz; `sce_sys/snd0.at9` exists, but proprietary AT9 decode on PS5 was not verified.
- Fonts: **8/8** TTFs parsed with valid character maps (Montserrat plus Greek, Arabic, Japanese, Korean, Simplified/Traditional Chinese and Thai fallbacks); **7/7** fallback subset size/SHA receipts matched.
- Localization: all **31 `.po` and 31 companion `.txt`** files were present in the standalone FTP package and byte-identical in pairs. The CI reports `missing=0` for all language catalogs; however, an `english_fallbacks` count still exists (e.g. `fr-FR=73` out of 615 catalog keys), which is a **localization completeness** question rather than a missing-file failure.
- No archive member path pointed outside the installation root. Other app assets, UI sounds, box-art indices and network configuration files are present.

## Full native job log: warning and missing-dependency classification

The completed native build job contained **8,596 log lines**. No C/C++ compiler `warning:` or `error:` diagnostic or unresolved link symbol was found in the log scan. Target link and staging were successful; syntax preflight passed for **37 selected translation units**.

| Observation | Classification | Evidence/next action |
|---|---|---|
| `Could NOT find RenderDoc (RenderDoc_INCLUDE_DIR)` | Non-blocking optional debugging tool | CMake continued, native build/link succeeded |
| `Package 'libinotify' ... not found` | Non-blocking host/platform-dependent optional package | No linked Linux runtime dependency; keep PS5 code path independent |
| `Could NOT find libusb` | Non-blocking optional host input dependency | No linked Linux runtime dependency; keep target pad/USB backend separately tested |
| `HAS_COMPILE_FLAG - Failed` twice | CMake capability-probe rejection | Not a native TU build failure |
| `(node:...) [DEP0005] DeprecationWarning: Buffer()` | Third-party GitHub artifact-download action/tooling | Logged during download of the uploaded FTP artifact for re-verification, **not** a compiled application warning; maintenance only |
| `RUNPATH` in debug ELF references runner toolchain folders | Non-blocking artifact hygiene observation | No full runner RUNPATH string in packaged SELF; reassess only if runtime loader trace implicates it |
| 31 locale catalogs with some English fallbacks | P2 translation review | Not a package corruption or build stop |

The `failed` / `missing` text in intentional negative host tests should not be counted as an actual build failure. Actual CI job conclusion: **success**.

## Distinguish validation gates

| Gate | Status |
|---|---|
| Engine/vendor source pinned and paired | **PASS** |
| Host source tests, 37-TU native syntax preflight | **PASS** |
| Native PS5 compilation and linker | **PASS** |
| SELF generated, staging and ZIP layouts | **PASS** |
| GitHub artifact digests, ZIP CRC, images, WAV, fonts and language files | **PASS** |
| ELF/link map/eboot cryptographic provenance | **PASS** |
| Package installed and started on PS5 FW 13.60 | **Awaiting console evidence** |
| FC27 UI response and match smoothness, MKW/Bananza guest frame, crash-free exit | **Awaiting console evidence** |

**Do not close runtime stability/compatibility tickets on the basis of this successful artifact audit.** Preserve the exact engine `5245de8...` and vendor `2ccc4b0...` pair in all console logs and crash reports.
