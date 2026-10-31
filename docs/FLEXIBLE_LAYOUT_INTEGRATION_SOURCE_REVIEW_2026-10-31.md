# Re-review — flexible extracted and packaged title layouts (31 October 2026)

Scope: shared NS1 and experimental NS2 base discovery plus packed update/DLC
provider roots, extracted sibling RomFS and bounded update overlays. This is
**source-level integration review**, not a performance/FPS or PS5 runtime proof.
The historical F01–F07 optimization findings are not reclassified as closed.

## Selected source owners and precise Git blobs

| Source | Reviewed Git blob | New behavior, safety and review outcome |
| --- | --- | --- |
| `headless/game_files.h` | `736230b434d58406841e702e5dbd70d4c391f578` | Bound/symlink-free nested source selection, isolated add-on roots, one base candidate; avoid scanning RomFS/ExeFS during discovery |
| `headless/main.cpp` | `598d7632a39c4e58ab31acb26c789eae34762520` | Launch-time revalidation and native provider roots for the selected title; no GPU/JIT frame loop changed |
| `headless/metadata_bridge.cpp` | `0eb7bd4cb4cbf615b4cbd870d6bc87bf30fed9d5` | UI add-on snapshot aggregates global and collocated provider roots; same metadata-aware Update/AOC classification |
| `headless/metadata_bridge.h` | `a8ebfa5fad322c81b6562dedc6e2a7c680a5cfa9` | C ABI scanner receives ROM root for collocated add-ons; both headless call sites updated |
| `headless/prosperoeden/eden_services.cpp` | `4aa854ec4a00a9515b6015b7e3fad00e70247895` | One UI card per folder, new package base discovery, accurate game count and add-on display; worker IO, not per-frame |
| `headless/settings_store.h` | `e49667c282633a4ac0bf68976c78e4f4e1c1cd3e` | Persisted nested file selection validation; slash and traversal restrictions retained |
| `vendor/encore-active/eden-core/src/core/loader/deconstructed_rom_directory.cpp` | `af269102b7e8e41e8ba9dca6c2d68b88fba86e3f` | VFS sibling/ancestor RomFS, bounded versioned extracted update overlay; never mix two update versions |
| `vendor/encore-active/eden-core/src/core/file_sys/registered_cache.cpp` | `618ff99d2121741c190a9fd3ae8d0fd45f7eb9fe` | Packaged update/DLC provider skips expanded RomFS/ExeFS to prevent huge content scans; reviewed alongside the existing NCZ source delta |

## Review and invariants

1. **Base game selection** is limited to a unique, safe directory ExeFS or
   packaged NSP/XCI/NSZ/XCZ input; ambiguous base candidates fail closed.
   Updates/DLC are excluded from the library's base-title discovery, including
   case-variant named containers.
2. **Package add-ons** use `ExternalContentProvider` and their own Nintendo
   content records/title IDs. Folder names alone never grant DLC ownership.
   Both named and arbitrarily named nested folders containing packaged add-ons are discovered (excluding the selected base package) without copying games
   into process memory.
3. **Extracted updates** are a separately marked experimental virtual
   file overlay, not native NCA/BKTR patch emulation. The lookup is bounded
   (128 directories, five levels), requires a numeric version component,
   and never merges ExeFS from one update with RomFS of a different update.
4. **Extracted DLC** remains unregistered. An `id/slot/romfs` directory is
   a storage convention, not a functional AddOnContent mount.
5. **Performance owner**: these are cold startup/library/loader operations,
   never a per-frame rasterizer, shader, scheduler, or JIT modification.
   Disk traversal is bounded and skips huge expanded asset roots. No measured
   PS5 performance improvement is claimed.
6. **Validation**: `tools/check-exefs-directory-host.py` compiles the
   actual header/selector under Clang and GCC O0/O2 with UBSan, checks path
   isolation and root/package combinations. `tools/check-encore-ncz-sources.py`
   checks the registered-cache delta against immutable pinned source.
   The integrated PS5 native link and extracted DLC runtime remain unproved.

## Source audit decision

The reviewed-source blob pins in
`docs/EDEN_OPTIMIZATION_COVERAGE_2026-10-20.json` are advanced *only*
for these eight intentionally modified owners, to preserve the strict CI
source drift guard. Original per-function F01–F07 reviews remain historical.
Reopen this feature review on any future owner-source drift or a native
filesystem/title-association failure.
