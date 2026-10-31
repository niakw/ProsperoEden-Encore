# Flexible game storage: base, updates and DLC

Status: **experimental integration**, 31 October 2026. The library discovery
and base selection are shared between NS1 and NS2. These storage conventions
are not evidence that a commercial NS2 game boots or that every add-on type
is registered successfully.

## No mandatory storage layout

All examples below may coexist. The root remains `/data/prosperoeden/roms/`.

```text
roms/
  Zelda.xci                            # existing flat single-file base
  DonkeyKongBananza/
    base/
      exefs/main                       # extracted base executable
      exefs/main.npdm
      romfs/                           # extracted base assets
    updates/458752/exefs/              # optional collocated extracted update
    updates/458752/romfs/
    dlc/040074a01bf13001/0/romfs/     # optional extracted add-on layout
  AnotherGame/
    base.nsp                           # packaged base in a folder
    updates/v2/update.nsp              # packaged update (registration pending)
    dlc/bonus.nsp                      # packaged DLC (registration pending)
  ThirdGame/
    archives/original/game.xci         # nested packaged base
  OneMoreGame/
    exefs/main                         # extracted without a "base" wrapper
    exefs/main.npdm
    romfs/
```

An existing independent `/data/prosperoeden/updates/` store remains valid
for supported packaged NSP/XCI updates and DLC. Updates/DLC may also be
physically collocated with the base in `roms/<title>/`; the filesystem
layout itself does not decide which add-on belongs to which game.

## What is implemented now

- **Flat files:** NSP, XCI, NSZ, XCZ and direct loader inputs at the root
  retain their prior library/launch behavior.
- **Extracted bases:** `<title>/main` and bounded nested
  `<title>/.../exefs/main`, requiring `main.npdm`, are recognized.
- **Packaged bases in folders:** a single candidate NSP/XCI/NSZ/XCZ
  under a game folder is recognized; a uniquely named `base.*` or
  `game.*` can disambiguate. Multiple other plausible packages are
  deliberately **not guessed** to be a base. Nested package selections
  are checked against symlink/traversal changes on launch.
- **No duplicate library cards:** updates/DLC subtrees are excluded
  from base selection. An ordinary title folder creates at most one card.
- **Extracted RomFS (vendor experimental):** sibling `romfs/` is exposed
  through the virtual filesystem rather than copied into process RAM.
- **Extracted updates (vendor experimental):** only direct
  `<title>/updates/<decimal-version>/(exefs|romfs)` directories are layered,
  with the highest numeric version preferred. This is a file overlay,
  not a full implementation of native update/patch semantics.

## Still requires engine work

- **Packaged updates/DLC collocated in `roms/`:** the base picker deliberately
  ignores these as games, but the native content provider does not yet index
  every collocated package location. They are not guaranteed to be applied.
- **Extracted DLC:** content identity, AOC registration and separate RomFS
  mount remain unimplemented; do not overlay extracted DLC onto base RomFS.
- **Arbitrary update wrappers or loose updates without a Title ID:**
  directory placement or a version number cannot reliably associate a
  package with a base title. Use validated package metadata, or show an
  explicit unresolved add-on instead of silently mounting the wrong content.
- **Ambiguous packaged base sets:** automatic base selection fails closed
  rather than selecting an arbitrary package. A structured `base/` folder
  or uniquely named `base.nsp` resolves this without converting the content.
- **Verification:** the new layout feature remains in draft PRs; native PS5
  compilation, launch validation and NS2 commercial runtime proof are pending.

## Safety and architecture

The discovery scan is bounded (up to six nested wrapper levels; maximum
128 directories and 128 entries inspected per directory) and avoids symlinks
for extracted files and nested packages. No game-specific compatibility
override is introduced. Launcher changes stay in `headless/`; shared
filesystem/loader changes remain in the separately pinned `vendor` tree.

Run `python3 tools/check-exefs-directory-host.py` to exercise the real
source-level picker rules under Clang/GCC and UBSan. A host discovery
regression test is not proof of successful game execution on PS5.
