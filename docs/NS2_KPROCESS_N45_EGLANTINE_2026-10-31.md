# N45 — ExeFS → KProcess code-size admission and external Eglantine triage

Date: 2026-10-31. Branch: `research/ns2-ps5-compatibility` only.
No `main` change, production vendor rewrite, merge, release or PS5-console test.

## Actual owner risk and change

The maintained `vendor/sources/eden/src/core/hle/kernel/k_process.cpp`
`KProcess::LoadFromMetadata` converts `code_size / PageSize` to
`s32 code_num_pages`. Without guarding the **combined** module + NCE
patch footprint before that call, a partial 4-KiB page is silently truncated,
an empty ExeFS can request zero pages, a sum may wrap and an excessive
page count can narrow to a signed 32-bit value.

Experimental `AppLoader_DeconstructedRomDirectory::Load` now calls
`AdmitKProcessCode` immediately **before** the original addition and real
`KProcess::LoadFromMetadata`. It rejects empty module code, size_t addition
overflow, non-4-KiB page alignment and a total exceeding `INT32_MAX`
pages. The positive path is unchanged and uses the original kernel loader.
Switch 1 paths and final-release configuration are untouched.

Host test: `tools/ns2/test_kprocess_code_admission.cpp`, run by
`.github/workflows/ns2-research-host.yml` with Clang and GCC under
ASan/UBSan. Tests cover valid 1- and 2-page images, valid maximum signed
page count, partial pages, missing module code, addition overflow and first
unrepresentable page count. CI also asserts the original vendor source still
contains its signed-page conversion; fail closed if that upstream owner changes.
These tests DO NOT instantiate `KProcess`, load the synthetic NSP into an
emulated process, prove shader rendering or run on a PS5.

## PokeDinner-a-Eglantine-Fork — 1.5.0 release evidence

Public release listing:
https://git.eden-emu.dev/Franseven/PokeDinner-a-Eglantine-Fork/releases

Version `1.5.0`, published 2026-10-31 01:11:53 +01:00,
claims Pokopia sky is consistently blue, improved tree reflections,
fixed Donkey Kong terrain (credited to The_Zar_ar), and the title-screen
shattered-glass particles rendering. Binary archives are listed for
Linux x86_64, Windows and macOS ARM64. These are meaningful
**reported PC graphics changes**, not a demonstrated NS2/PS5 boot.

At review time, the public release *listing* was readable, but the
individual tag/compare/source paths returned fetch failures. Therefore:
- exact code diff, Vulkan backend path, license details and regression scope
  remain unverified;
- no file or binary was copied or executed, and no automatic cherry-pick
  or vendor replacement is justified;
- revisit any narrow shader/texture fix only after obtaining attributable
  source diff, identifying the corresponding Encore owner and running host
  plus native PS5-specific tests.

## Next genuine integration boundary

Full-core `Core::System::Load` + `KProcess::LoadFromMetadata` + NSO
`LoadModule` through an authorized homebrew ExeFS is still NOT proven.
The existing separately tested NPDM reader, KCapabilities, NSO staging and
Dynarmic guest execution are necessary but insufficient. Keep the research
branch isolated until that process path and later HLE/GPU output are tested.
