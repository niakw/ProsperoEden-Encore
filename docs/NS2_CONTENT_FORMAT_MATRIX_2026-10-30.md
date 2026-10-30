# Nintendo Switch 2 — content, game-card and executable formats
_Audit 2026-10-30 — Encore research branch `research/ns2-ps5-compatibility`_

## Key distinction: MKW is a game, not a file type

**MKW means Mario Kart World.** A social post describing 5 FPS versus 30 FPS is
a performance claim about a game and an unspecified emulator build. It does
not establish a new `.mkw` file format, a reproducible emulator, or acceptable
frame timing on PS5. Verify build, machine, scene, shader state, logs and
evidence before treating any FPS claim as a benchmark.

## Content and transport matrix

| Content / delivery | File or asset name | Existing Encore research behavior | Switch 2 support status |
| --- | --- | --- | --- |
| Traditional cartridge dump | `.xci` | XCI container parsing/secure partition route exists | Old file extension alone does not establish Switch 2 cartridge, crypto or metadata support |
| Compressed cartridge image | `.xcz` | Classified into existing XCI route | Actual decompression/NS2 archive layout not validated |
| eShop installable package | `.nsp` | NSP install/loader route exists | No Switch 2-specific encrypted package handling demonstrated |
| Compressed installable package | `.nsz` | Classified into existing NSP route | Actual decompression/NS2 package support not validated |
| Content archive (program, update, DLC, etc.) | `.nca` | NCA archive parser exists, used for indexed programs | Switch 2 archive header, encryption and rights handling unverified |
| Registered encrypted content | `.nax`, special basename `00` | Existing NAX/NCA magic and name routes | Switch 2 decryption support unverified |
| Unpacked executable | `exefs/main` + `main.npdm` | **Experimental** standalone ExeFS main/NSO and extended NPDM/ACID handling already integrated | Earliest practical NS2 research path; not proof of running a commercial title |
| Other ExeFS modules | `.nso` (or module without extension, detected by magic) | Existing NSO recognizer | Switch 2 runtime HLE, service dependencies, GPU unsupported end-to-end |
| Homebrew | `.nro` | Existing NRO route | This is not the Switch 2 retail container format |
| Kernel module | `.kip` | Existing KIP route | Not a standard game container |
| Game assets | `romfs`, `romfs.bin`, RomFS directory | Assets only; no independent playable loader | Asset extraction is not full emulation |
| NSP game update/DLC and Switch 2 Edition upgrade | Often packaged as content archives | Content-provider/program-index routes exist | Correct title IDs, metadata, versions, rights and layered update combination need independent verification |
| **Full physical game card** | Physical media, no universal new extension | Card-to-file extraction is external | Need verified media format, card image layout, decryption, title program and graphics |
| **Game-key card** | Physical entitlement/activation, not a ROM | No standalone game payload to load from card | Full game data downloaded separately; no file extension can represent the card by itself |
| Digital game / virtual game card | Licensed/downloaded content | Existing NSP/NCA routes are only first-generation parsing candidates | Requires independent ownership/content availability and compatible Switch 2 metadata/crypto |
| Nintendo Switch 1 game via Switch 2 backward compatibility | Existing first-generation assets | Current Switch 1 emulator path remains separate | Does not automatically mean native Switch 2 game compatibility |

**Unverified extensions**: there is no grounded reason to register
`.xci2`, `.nsp2`, `.nca2` or `.mkw` as real Switch 2 file extensions.
The string **NCA2** can also denote an *older internal NCA archive variant*,
not a new Nintendo Switch 2 suffix. Do not invent handlers for these labels.

## Existing implementation check — 2026-10-30

- `headless/ns2/overrides/core/loader/loader.cpp` already probes XCI, NSP,
  NCA, NSO and other first-generation formats by magic, plus standalone ExeFS
  `main` **before** generic NSO identification.
- `headless/ns2/overrides/core/file_sys/program_metadata.cpp` adds
  experimental Switch 2/extended ACID NPDM handling.
- **Not found in this research overlay**: a verified Switch 2 NCA/cart/NSP
  archive parser, Switch 2 encryption/rights bridge, Switch 2 Edition upgrade
  composition, or end-to-end title loader for `Mario Kart World`.
- New `ns2_content_formats.h` makes the established loader-name routes
  explicit and distinguishes executable/container/archive from metadata-only
  and RomFS-only inputs. The experimental actual loader calls it; no shipping
  Switch 1 or `main` code changes.
- New `test_content_formats.cpp` checks extension case, legacy names,
  compressed wrappers, ExeFS, NPDM, RomFS, unknown suffixes and game-key
  card labels. CI compiles the pure header and syntax-checks the actual
  loader overlay. Name recognition is **not** decryption or game launch.

## Priorities to reach MKW on PS5

1. **P0 — verifiable game load**: obtain only legally sourced metadata and
   synthetic headers for analysis; validate correct NCA/card package versions
   and content IDs without accepting an extension as proof. Verify
   game-key-card downloads are not confused with on-card data.
2. **P0 — executable and Horizon services**: NS2 metadata, ExeFS modules,
   permissions and HLE calls, memory model, missing services, and title
   process startup.
3. **P0 — correct GPU work**: CPU6/A64, Ampere/Turing engines, shader ISA,
   GMMU, textures, render targets and Vulkan RADV. The research GPFIFO
   and sparse work is compiled host-side, not benchmarked on PS5.
4. **P1 — real FPS**: collect hardware, scene, duration, FPS distribution,
   GPU/CPU frametimes, shader warmup, Vulkan stalls and correctness screenshots.
   A single low-detail 5 FPS boot/demo does not establish 30 or 60 FPS support.

## References

- Nintendo Switch 2 FAQ and Switch 2 Edition game-card content:
  https://www.nintendo.com/us/gaming-systems/switch-2/faq/
- Nintendo: regular game cards vs game-key cards (not carrying full game):
  https://www.nintendo.com/fr-fr/Hardware/Nintendo-Switch-2/Nintendo-Switch-2-Cartes-cle-de-jeu-2785635.html
- Switchbrew XCI (first-generation card image documentation):
  https://www.switchbrew.org/wiki/XCI
- OunceCake describes extraction of **decrypted RomFS and ExeFS** for
  digital titles, game cards, Editions and DLC, not a generic ROM loader:
  https://git.eden-emu.dev/mirror/OunceCake
- Community experiment notes (not a validated 30 FPS build):
  https://git.eden-emu.dev/Takoroka/eden-nx2/releases

## Upstream review alert — Eden's current NS2 draft

Eden Forgejo now has a **draft, not merged** Switch 2 support PR
[eden-emu/eden #4588](https://git.eden-emu.dev/eden-emu/eden/pulls/4588)
with Ampere shader lowering, 6 CPU cores, Horizon services, video decoder
and disk-cache changes. The public PR shows failed/blocked build checks and
reported freezes in individual test scenes. Do **not** treat that WIP as a
stable 30-FPS Mario Kart World release or import its entire diff into PS5.
The next compatibility audit should compare its ExeFS, NCA/content-ID,
NPDM and graphics patches *per file* with Encore's isolated research overlay,
then test in CI before any merge.
