# R23 — all 155 Eden upstream commits: complete changed-file enumeration

**Pinned comparison:** `eden-emulator/mirror@5f142c7926d0c7fcbbd0ce30794d72f638a43b2a` to `89d1a1cd7015ebd05ac1bb6a97d1a472bf28701b`. **Audit branch only; no source import, native build, or runtime proof.**

## Closed: upstream commit-to-file enumeration

- **155/155 commit SHAs, titles, dates:** [full initial metadata register](R23_EDEN_ALL_155_COMMITS_2026-11-10.json).
- **155/155 GitHub individual commit file lists inspected and saved:** [fully merged register](r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json), backed by 13 individual batches in `r23/`.
- **3/3 GitHub 300-file cap cases paginated to completion** with `per_page=100`, each final page shorter than 100: [commit #3: 309 paths](r23/R23_EDEN_FULL_PAGES_003.json), [commit #69: 588 paths](r23/R23_EDEN_FULL_PAGES_069.json), [commit #74: 392 paths](r23/R23_EDEN_FULL_PAGES_074.json).
- **2,376 observed per-commit file-change receipts**, *not* 2,376 unique source files. Every entry has the exact upstream commit and full changed path/status, no guessed patch ownership. **Unresolved file-list API caps: 0.**
- Conservative **first-pass path-only classification:** **123 commits** touch C++/C/headers in NS1-or-shared candidate directory families, **32** do not touch those paths but may affect dependencies, CMake, launcher/frontend assets, or build. This classifier **never certifies** the latter as entirely irrelevant to the PS5 project.
- Path-family change counts (changes, NOT unique files): `src/core` **1,205**, `src/video_core`+`src/shader_recompiler` **205**, `src/dynarmic` **147**, `src/audio_core` **65**, `src/common` **78**, `src/input_common` **24**, `src/network`+`src/web_service` **10**, other native `src/` **69**, desktop/mobile `src/` **256**, build/deps/doc/tests **62**, other paths **255**.

## Not closed: semantic applicability on PS5

The new 155-entry register answers **what each upstream commit touched**, not whether that code is part of Encore's actual selected translation units, implements a beneficial behavioral difference, has an existing equivalent or needs porting. **123 runtime candidates still require a source-semantic/parity disposition**, with unit/behavioral tests where applicable. **32 non-runtime-path-only candidates still require build, dependency, UI/asset or documentary relevance disposition** before saying the entire R23 audit is complete.

Prioritise real source owners and criticality, not commit title alone:
1. Dynarmic seven defects in `35f0dd7` including current compiled x64 SDIV32/FRINT/SQSHLU paths; exclude AVX512 runtime as unsupported on PS5 Zen2; determine SM4 and A32 decoder owner.
2. GPU, shader and driver patches touching selected CMake/Meson sources, including float NaN output and RADV command-stream split; do not confuse the two latter historical PS5 fork commits with this 155-Eden commit ledger.
3. HLE/IPC, audio, RomFS, kernel, guest memory and CPU→GPU synchronization with positive and negative host tests; maintain NS1/NS2 common code compatibility and zero gameplay performance assertions.
4. Build/SDK/core dependency changes in the 32 path-only candidates remain relevant to native reproducibility even where no C++ runtime code is changed.

**Source evidence level:** E0/E1 file-provenance and triage, **not E2 (current native build ownership), E3 (behavioral parity), or E4 (PS5 runtime)**. R23 semantic audit remains open while its capped-file-list subtask is **permanently closed** at this upstream pin.

## Avoid repeating this large scan

Use the 155-sha baseline and [all-file JSON](r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json) as the authoritative immutable inputs. On future upstream changes, compare only newly introduced commit SHAs and check inherited source ownership; do not re-fetch the existing 155. Do not bulk merge the newer Eden engine or alter `vendor/sources` because of this audit.
