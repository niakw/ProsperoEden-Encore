# R23 pass 10 — #29 Unicode conversion is a source-level behavioral divergence

**11 Nov 2026, isolated audit PR #45.** Official upstream [`c6fa5c1f77ba40bcb091b1a53492230f40d97ded`](https://github.com/eden-emulator/mirror/commit/c6fa5c1f77ba40bcb091b1a53492230f40d97ded) changes exactly one file, `src/common/string_util.cpp`, replacing `std::wstring_convert`/`codecvt` in UTF16/UTF8/UTF32 helpers with hand-written loops. Its author marks the refactor **untested**. This is not just a mechanical syntax change.

## Evidence and host execution

- Frozen pinned source `vendor/sources/eden/src/common/string_util.cpp`: Git blob **`9543a6234376dc4e85ce035a653b41805b8aa072`**; `src/common/CMakeLists.txt` (blob `61e0e64aa8b926a86041b0420ab67f2ece9f0c68`) includes `string_util.cpp` for `common`. The audit's `headless/CMakeLists.txt` does not replace it.
- The exact pinned `UTF8ToUTF16` uses `std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t>::from_bytes`. The upstream loop parses 2-byte UTF-8 prefixes with `(c & 0xE0) == 0xC0` but does not reject overlong encodings, surrogates or code points above U+10FFFF.
- A source-extracted C++20 test using Clang 17 and libstdc++ with ASan/UBSan passed locally: valid ASCII/euro/emoji input matches, while malformed bytes `C0 80` cause a pinned `std::range_error` but upstream yields **U+0000** (NUL). The test is checked in as [`tests/audit_r23_utf_conversion_host.cpp`](../../tests/audit_r23_utf_conversion_host.cpp) for independent CI rerun.
- An additional local source-derived `UTF16ToUTF8` probe found that an isolated high surrogate is encoded by the upstream loop as invalid `ED A0 80` while the current libstdc++ pinned function returned an empty string (not an exception). This second probe is an explanatory observation, not part of the committed host test.

## Decision and reopen contract

**`reviewed-UTF-conversion-non-equivalence-deferred-host-differential`**. Do **not** import this upstream refactor to fix compiler deprecation warnings or chase unmeasured speed. It changes malformed-input semantics in shared code, and current pinned path uses a deprecated API that may eventually require replacement. Revisit only when there is a confirmed toolchain need, with a deliberate strict/repair policy for invalid Unicode, full valid+malformed corpus, source-compiled selected `common` TU, guest filename/path and localization tests on PS5.

**E1 + source-extracted host proof only.** No real emulator linked unit or PS5 title/console test. No vendor patch or `main` modification. Count after review: 55 generic semantic cases + two scoped policy gates (Vulkan/OpenGL #52 and UTF #29), 12 confirmed source gaps, 17 changed-header native receipt gaps, 7 full corrective-batch exit gates.
