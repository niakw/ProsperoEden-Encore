# Flexible game storage: base, updates and DLC

Status: **integration under test**, 31 October 2026. The discovery and
content-provider paths are shared by NS1 and experimental NS2. This is
not proof of commercial Switch 2 game boot or PS5 hardware qualification.

## No mandatory base layout

```text
/data/prosperoeden/
  roms/
    Zelda.xci                           # legacy standalone image
    DonkeyKongBananza/
      base/
        exefs/main                      # extracted base
        exefs/main.npdm
        exefs/rtld
        exefs/sdk
        romfs/                          # all extracted base assets
      updates/
        458752/exefs/                   # extracted update (experimental)
        458752/romfs/
        patch-v2.nsp                    # packaged update
      dlc/
        040074a01bf13001/0/romfs/      # extracted DLC (NOT mounted yet)
        bonus.nsp                       # packaged DLC
    AnotherGame/
      base.nsp                          # packaged base
      DLC_1.nsp                         # loose packaged add-on, next to base
      updates/version2/patch.nsp
    ThirdGame/
      archives/original/game.xci        # packaged base in wrapper folders
      custom/addons/extras.nsp
    ExtractedNoBaseWrapper/
      exefs/main
      exefs/main.npdm
      romfs/
    updates/
      0100title/v3/patch.nsp            # central add-on folder under roms/
  updates/
    any-title/patch.nsp                 # legacy central add-on folder
```

A top-level `roms/<title>` is **one game card**. A base can be a standalone
NSP/XCI/NSZ/XCZ file, a unique nested package, a uniquely named
`base.*`/`game.*`, or a nested extracted ExeFS. Existing direct-loader
files at the `roms/` root remain supported.

The game selector does not list extracted update/DLC folders as games.
Update/DLC package discovery is independent of base selection: it finds
content-container folders named `updates`, `update`, `patches`, `dlc`,
`addons`, or `add-ons` (case-insensitive), even with intermediate wrapper
directories. Loose packaged add-ons directly beside a base package or an
extracted base are also passed to the native content provider.

## Implemented in the feature PRs

- Shared library, recents, autoboot and launch validation for extracted
  and packaged bases; one library card per title folder.
- Bounded scanning with symlink/traversal checks; extracted RomFS/ExeFS
  payloads are not recursively inspected for packaged add-ons.
- Existing global `/data/prosperoeden/updates/` plus collocated packaged
  update/DLC locations are sent to the native `ExternalContentProvider`
  at boot and indexed for Home/Library summaries. The provider determines
  **Update** versus **AOC** from package metadata, not a folder label.
- The vendor loader exposes sibling/ancestor extracted `romfs/` through the
  VFS and experimentally overlays the highest numeric update, accepting
  intermediate wrappers under `<title>/updates/`. Each selected candidate
  contains its own matching `exefs/` and/or `romfs/`.
- Legacy flat package and direct loader formats remain available.

## Known limits — not to be presented as functional

- **Extracted DLC** (`dlc/<id>/<slot>/romfs`) still needs native AOC
  registration and an independent RomFS mount. A folder alone is not DLC.
- **Extracted update overlays** are file-level experiments, not Nintendo
  NCA patch/BKTR semantics. The lookup is bounded to five levels and
  128 visited directories, requires a numeric version component, and
  cannot infer ownership from a global version-only folder.
- **Unknown update/DLC contents** lacking valid Title ID and other package
  metadata cannot be associated reliably. Multiple plausible base packages
  in one folder are not arbitrarily selected.
- Individual update packages placed *directly* among unrelated flat files
  at `roms/` root should instead be placed under `roms/updates/` or
  `/data/prosperoeden/updates/` to avoid scanning every game image.
- Scans are bounded to keep PS5 library response safe: six levels for
  packaged/extracted base wrappers, five for add-on container search, and
  finite per-title directory/entry budgets.
- Full native PS5 linking, hardware tests and commercial NS2 runtime
  compatibility remain unverified. Discovery is not proof of boot.

## Tests and code ownership

`python3 tools/check-exefs-directory-host.py` exercises the real
selection code under Clang/GCC and UBSan, including wrapper folders,
ambiguous bases, unsafe symlinks, loose add-ons and named add-on roots.
This is a host source test, not actual NCA patch/gameplay validation.

Launcher/UI and scanning changes live in `headless/`. Vendor filesystem
and loader changes live in the pinned vendor repository, not copied into
a second NS2-specific engine. There are no game-name-specific rules.
