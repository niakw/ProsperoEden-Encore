# Extracted game folders: base, updates and DLC

Status: **experimental integration**, 31 October 2026. Shared NS1/NS2
code path. This is a layout contract, **not** a claim of retail NS2 game
compatibility, cryptographic support, or successful PS5 gameplay.

## Preferred layout (one directory per game)

```text
/data/prosperoeden/roms/DonkeyKongBananza/
  base/
    exefs/
      main
      main.npdm
      rtld
      sdk
    romfs/
      <extracted game assets>
  updates/
    458752/
      exefs/
        <update executables, when present>
      romfs/
        <update assets, when present>
  dlc/
    040074a01bf13001/
      0/
        romfs/
          <DLC assets>
```

All three content categories may be stored **inside `/data/prosperoeden/roms/<title>/`**;
there is no requirement to place updates or DLC in a separate global
`/data/prosperoeden/updates/` directory. The base-title scanner deliberately
does not descend into `<title>/updates/` or `<title>/dlc/`, and excludes
root-level `/roms/updates` and `/roms/dlc` stores as independent games.
This **does not** mean the extracted DLC is mounted or functional yet.

The picker lists only **DonkeyKongBananza**, with the canonical saved
selection `DonkeyKongBananza/base/exefs/main`. Nested wrappers such
as `DonkeyKongBananza/base/export/exefs/main` are discovered with a
bounded, symlink-free search. ExeFS always needs `main` and
`main.npdm` as regular files; additional modules may be present.

Legacy extracted layout `roms/<game>/main` and normal NSP/XCI/NSZ/XCZ
and direct executable formats are preserved. No files need to be moved
or copied from `base/exefs` to the top level.

## Implemented in the feature branches

- **Picker / persistence / autoboot:** one game entry; bounded
  nested `exefs/main` discovery; safe path revalidation on launch.
  Updates and DLC are excluded from base-title discovery.
- **Shared vendor loader (experimental):** resolve the sibling
  `romfs/` directory and expose a virtual packed RomFS. The data
  remains VFS-backed rather than copied wholesale into process RAM.
- **Collocated extracted update:** for direct
  `<game>/updates/<decimal-version>/exefs` and/or `romfs`, choose
  the highest numeric version and layer its files above the base.
  This is a **file-level extracted overlay**, not guaranteed to
  implement Nintendo's actual binary update/patch semantics.
- **Security:** no symlinks or dot-segment title selections; bounded
  scan breadth/depth; only explicit `exefs` candidates are games.

## Still not supported / not claimed

- **Extracted DLC mount:** `<game>/dlc/<id>/<slot>/romfs` is a
  reserved organization convention. DLC needs its own content-ID,
  AOC registration and virtual filesystem mounting. It must **not**
  be merged into the base game's RomFS as though it were an update.
- **External extracted updates** under
  `/data/prosperoeden/updates/458752/exefs` and
  `.../458752/romfs`: the existing external scanner understands
  packaged content, not an unindexed extracted folder; the title
  association cannot be inferred safely from a decimal version alone.
- Arbitrary nested update/DLC folders need metadata-backed indexing,
  rather than guessing by directory name; package-format updates/DLC
  continue to follow existing handling.
- **Verification pending:** complete PS5 native build and hardware
  qualification for the new loader path; NS2 commercial runtime
  remains research-only.

## Validation

`python3 tools/check-exefs-directory-host.py` exercises real
launcher selection code under Clang/GCC and UBSan, including nested
base trees, symlink rejection, update-folder exclusion and legacy
format preservation. The source check does not emulate a game's
RomFS reads or apply content patches on a PS5.

Architecture: shared launcher code lives in `headless/` and the
engine implementation lives in the separate pinned `vendor`
repository. No title-specific game fix or duplicate engine is
introduced.
