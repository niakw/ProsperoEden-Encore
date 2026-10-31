# Extracted DLC (AOC) installation bridge — source review

**Scope:** NS1 / experimental NS2 common filesystem, *not* PS5 build or gameplay
qualification. Both guest services use the same vendor-owned title ID/path
registry; there are no per-game overrides or additional emulation engines.

## Selection and activation

\`\`\`text
/data/prosperoeden/roms/<game>/
  base/exefs/main
  base/exefs/main.npdm
  base/romfs/
  dlc/010074a01bf13001/0/romfs/<assets>
  dlc/010074a01bf13002/romfs/<assets>

/data/prosperoeden/updates/<any-wrapper>/010074a01bf13003/romfs/<assets>
\`\`\`

- The shared launcher already registers add-on roots for the selected title
  plus the global update store using \`Settings::values.external_content_dirs\`.
- \`ExtractedAoc::Scan\` inspects those registered paths with bounded depth,
  entry, and directory budgets. It requires a **full 16-hex AOC Title ID**
  directory (offset \`0x1000..0x17ff\`), not merely a folder called \`dlc\`.
  An ID is accepted only within its encoded base-title family. Symlink
  directories, missing \`romfs\` and ambiguous duplicate AOC IDs fail closed.
  Extracted asset trees are **never** recursively traversed by discovery.
- The native \`aoc:u\` service enumerates these IDs together with genuine
  packaged/NCA DLC. Title IDs are deduplicated before counting or listing.
  Existing DLC-disable settings and base-title scoping still apply, including\nwhen guests request the raw extracted data storage directly.
- \`RomFSFactory::Open\` prefers actual NCA content, falling back to an
  independently constructed read-only virtual RomFS only for AOC **Data**
  IDs and eligible storage types. The shared virtual filesystem outlives the
  guest file handles. The normal FSP data-storage path remains unchanged.

## Important limitation

Extracted DLC has no encrypted NCA/CNMT metadata to authenticate. Its Title ID
is an **explicit local directory convention**, verified syntactically and
against the caller's base-title family. It must not be presented as metadata
authenticated by a package. No arbitrary-named \`dlc/bonus/romfs\` can be
matched safely to a title without real metadata; use a full AOC Title ID.

The launcher already discovers packaged NSP/NSZ/XCI/XCZ updates and DLC in
arbitrary nested folders **by package metadata**. Extracted update overlays
remain experimental file-level overlays rather than complete BKTR/NCA patching.

## Source audit and host witness

| Reviewed source | Git blob | Role |
| --- | --- | --- |
| \`vendor/encore-active/eden-core/src/core/file_sys/extracted_aoc_paths.h\` | \`b08428c7e79be3f86f235f0450bca0bd61c042ef\` | Pure bounded parsing, base ID scoping, symlink and duplicate protection |
| \`vendor/encore-active/eden-core/src/core/file_sys/extracted_aoc.h\` | \`31805b346029990e22040fc7e957f91ca2b0ef0f\` | Shared runtime registry and read-only virtual RomFS |
| \`vendor/encore-active/eden-core/src/core/file_sys/romfs_factory.cpp\` | \`cd11cb32429efcceaf6b3e1144d495cce1569383\` | NCA-first extracted AOC Data storage fallback |
| \`vendor/encore-active/eden-core/src/core/hle/service/aoc/addon_content_manager.cpp\` | \`c329c6ba2c60c2641046f282c412567ada8c4aac\` | Combined packaged/extracted AOC enumeration through aoc:u |

\`python3 -B tools/check-extracted-aoc-layout-host.py\` compiles the actual
shared path parser under Clang and GCC with UBSan; it tests valid IDs,
wrong-base rejection, duplicate ambiguity, symlink exclusion, arbitrary
wrappers, and source selection. This does **not** prove native link, DLC assets'
semantic correctness or commercial NS2 gameplay. Any source blob drift must
reopen this review; the historical F01–F07 performance results are unchanged.
