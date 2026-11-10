# R23 — 32 Eden commits without NS1/shared source paths: explicit dispositions

**Audit PR #45, pinned Eden upstream through `89d1a1cd`.** Decisions based on complete per-commit path lists, not on a title-only heuristic. Paths verified in [155-commit index](r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json). **No native compile, package or PS5 runtime equivalence asserted.**

| Category | Number | Disposition |
|---|---:|---|
| Android/Qt/docs/policy/gitignore only | **20** | No emulator native-runtime code to import; release policy/UX separate |
| Dist assets/translations | **8** | Need actual packaged-asset and attribution check |
| CMake/CPM/dependency inputs | **4** | Need exact native CMake/CPM/link ownership |

These 20 explicit source-only exclusions are **not** a completed runtime-performance audit. The 12 build/asset dependencies are still open. The separate 123 commits changing NS1/shared source paths remain subject to source semantics, actual-owner and regression decisions.

## Commit-by-commit evidence

| # | Upstream commit | Changed paths | Classification |
|---:|---|---|---|
| 4 | [`295823040`](https://github.com/eden-emulator/mirror/commit/295823040bb33cc9f473fea382e4eecd35ecd4fa) | 30 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |
| 8 | [`8e81d8478`](https://github.com/eden-emulator/mirror/commit/8e81d847811111e07d9f1c0f4425cd452c64af18) | `src/android/app/src/main/res/drawable/ic_stoat.xml` | not-applicable-to-native-runtime-source |
| 14 | [`626568290`](https://github.com/eden-emulator/mirror/commit/626568290a5bf6c42b9ba985f1aa32a7a7447053) | `README.md` | not-applicable-to-native-runtime-source |
| 15 | [`083b77850`](https://github.com/eden-emulator/mirror/commit/083b778508e16f0ea580e6004323e7309f766a03) | `src/android/app/src/main/res/values/strings.xml` | not-applicable-to-native-runtime-source |
| 16 | [`7f1bc0c9d`](https://github.com/eden-emulator/mirror/commit/7f1bc0c9d1872a0623dad8dd3bce7acafd1d39dc) | `src/yuzu/user_data_migration.cpp` | not-applicable-to-native-runtime-source |
| 20 | [`885b333c0`](https://github.com/eden-emulator/mirror/commit/885b333c08760ccc406202a02a5b3d3fa5eab60b) | `CMakeLists.txt` | native-build-or-dependency-review |
| 21 | [`5df599128`](https://github.com/eden-emulator/mirror/commit/5df599128d6828fa0e42968909da848c255d22b1) | `src/yuzu/main_window.cpp` | not-applicable-to-native-runtime-source |
| 23 | [`fa03b58f0`](https://github.com/eden-emulator/mirror/commit/fa03b58f04e994c8967f59a20df6a3e40f25f1b4) | `README.md` | not-applicable-to-native-runtime-source |
| 26 | [`060026dc2`](https://github.com/eden-emulator/mirror/commit/060026dc2d1daa749cf0b39378f132f506cbfd93) | 33 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |
| 27 | [`92f54a034`](https://github.com/eden-emulator/mirror/commit/92f54a034aa90b03ce33ca7571f24f58ddb380b0) | 4 files; first: `docs/build/Android.md` | not-applicable-to-native-runtime-source |
| 28 | [`7a6d05509`](https://github.com/eden-emulator/mirror/commit/7a6d055094846b7787f9b8c0f238c0c68709f632) | `src/yuzu/bootmanager.cpp`, `src/yuzu/main_window.cpp` | not-applicable-to-native-runtime-source |
| 34 | [`972860ac8`](https://github.com/eden-emulator/mirror/commit/972860ac8fcb7be36c13d572890a7349353397ce) | 19 files; first: `dist/dev.eden_emu.eden.svg` | asset-and-translation-package-review |
| 36 | [`be21ccce2`](https://github.com/eden-emulator/mirror/commit/be21ccce25ed598059ea7e679f227d0ac26e1e4e) | `docs/README.md` | not-applicable-to-native-runtime-source |
| 37 | [`db83070bf`](https://github.com/eden-emulator/mirror/commit/db83070bf2ca788131fa0eac3db6a7a83b75a24c) | `.github/FUNDING.yml` | not-applicable-to-native-runtime-source |
| 38 | [`e903d70d9`](https://github.com/eden-emulator/mirror/commit/e903d70d9eb46232c2b958674256ee04cf4e56c4) | 4 files; first: `.github/PULL_REQUEST_TEMPLATE.md` | not-applicable-to-native-runtime-source |
| 43 | [`072da7751`](https://github.com/eden-emulator/mirror/commit/072da775164ab258f2bbe62eecf935a99e7f36f1) | 4 files; first: `src/android/app/src/main/res/drawable/ic_forgejo.xml` | not-applicable-to-native-runtime-source |
| 51 | [`a2aa4d97e`](https://github.com/eden-emulator/mirror/commit/a2aa4d97e10a8345babfe647e1abd5ed5909c623) | `.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, `docs/policies/AI.md` | not-applicable-to-native-runtime-source |
| 61 | [`05f36d990`](https://github.com/eden-emulator/mirror/commit/05f36d990ce5301b310871451201a72e4c52b4df) | `.gitignore` | not-applicable-to-native-runtime-source |
| 62 | [`eb88a40a8`](https://github.com/eden-emulator/mirror/commit/eb88a40a8eb0fe847281ea6913fcc7ff7daedcd2) | `src/yuzu/main_window.cpp` | not-applicable-to-native-runtime-source |
| 66 | [`e0d47f279`](https://github.com/eden-emulator/mirror/commit/e0d47f2790e3f758fa2188926a0bb2f56af6b310) | `CMakeModules/find/Findlz4.cmake` | native-build-or-dependency-review |
| 67 | [`d8c6c59b6`](https://github.com/eden-emulator/mirror/commit/d8c6c59b679867d2595fdc0953df033475e23380) | `src/android/app/src/main/res/values-ar/strings.xml`, `src/android/app/src/main/res/values-zh-rTW/strings.xml` | not-applicable-to-native-runtime-source |
| 73 | [`6b3cb5772`](https://github.com/eden-emulator/mirror/commit/6b3cb5772b6e4875f088e5b48e089a3b3fda7f0d) | 5 files; first: `.github/PULL_REQUEST_TEMPLATE.md` | not-applicable-to-native-runtime-source |
| 76 | [`9580e54f2`](https://github.com/eden-emulator/mirror/commit/9580e54f2f4787986abde4c7601177d0c5cd2792) | 29 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |
| 83 | [`48aeedd3b`](https://github.com/eden-emulator/mirror/commit/48aeedd3b3c915b89aecfbda23c2462c0ed5746f) | 29 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |
| 85 | [`d3550c457`](https://github.com/eden-emulator/mirror/commit/d3550c45718609dc563d8b58adfc0d846feefd03) | `src/yuzu/game/common.h` | not-applicable-to-native-runtime-source |
| 86 | [`963119e7c`](https://github.com/eden-emulator/mirror/commit/963119e7cc3851007252c9981e4fae3e88b7687f) | `cpmfile.json` | native-build-or-dependency-review |
| 87 | [`2a7e9b53b`](https://github.com/eden-emulator/mirror/commit/2a7e9b53b12711f679238ee738a2ce57cc42c8ed) | `src/android/app/src/main/java/org/yuzu/yuzu_emu/model/DriverViewModel.kt` | not-applicable-to-native-runtime-source |
| 89 | [`f8b765110`](https://github.com/eden-emulator/mirror/commit/f8b76511041bb54070c52d1d09ea07d8108c592a) | 27 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |
| 105 | [`9cd24e85c`](https://github.com/eden-emulator/mirror/commit/9cd24e85c2c24016cfdba50e3533395561536f7e) | 31 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |
| 106 | [`74b5e10dc`](https://github.com/eden-emulator/mirror/commit/74b5e10dc553bb24ccb3460529b15b3c3198bb10) | `src/android/app/src/main/jni/native.cpp` | not-applicable-to-native-runtime-source |
| 134 | [`10c07d700`](https://github.com/eden-emulator/mirror/commit/10c07d700c33fa1ff78d5f616c2da2872fc5d43f) | `.patch/boost/0001-clang-cl.patch`, `CMakeLists.txt`, `cpmfile.json` | native-build-or-dependency-review |
| 140 | [`1a48de6e5`](https://github.com/eden-emulator/mirror/commit/1a48de6e55d6894722e5f235bc1fc14beb308e27) | 49 files; first: `dist/languages/ar.ts` | asset-and-translation-package-review |

## Provenance and closure policy

- The inspected `headless/CMakeLists.txt` is a custom PS5 CMake overlay; no direct `src/yuzu`/`src/android` source owners were found in its explicit patch/owner selectors. That is static source evidence only, not proof that every transitive build asset is absent.
- Do not port Qt/Android gameplay-window, logo, UI or policy changes as emulator code. This exclusion is about **native runtime source changes**, not the user-facing launcher or licensing.
- `dist/` assets are not declared missing in PS5 packages without comparing actual packaging and their source origins. The PS5 packaging script uses separate application assets and legal notices; keep an explicit packaging gate.
- The four build/dependency commits may still be relevant, especially lz4 static/bundling, ffmpeg GPU decoder dependency and Boost distribution; no automatic upstream CMake replacement.
- No counts are reused as performance gains or native ELF compatibility evidence.
