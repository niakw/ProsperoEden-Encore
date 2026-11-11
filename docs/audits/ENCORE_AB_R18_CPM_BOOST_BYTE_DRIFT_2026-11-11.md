# R18 — 22 CPM sources: real symlink accounting and pinned Boost byte drift

**Frozen source:** `niakw/Prospero.Eden-Encore-vendor@22b69d6053db41b74edac2633c012f925b84f69e`, read-only A/B audit PR #45, **11 November 2026**. No vendor file, `main` source, build or gitlink changed.

## Independently executed receipts

- [R18 read-only CI #42933079966](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42933079966) completed successfully as an **inventory analyzer**, uploading `r18-vendored-downloads-and-cpm-tree-witness`. It cryptographically rechecks **6/6 vendored archive byte streams** and **8/8 compiler-rt individually pinned files**. This does not establish independent official signature or PS5 binary linkage.
- After excluding filesystem links from regular-file counts, **21/22** CPM source-tree file counts and byte totals equal the recorded `VENDOR-CPM-LOCK.json`. The lock's original `cpmfile.json` SHA-256 also matches. **None** of the 22 declared CPM upstream tar archive SHA256/SHA512 digests has been compared to a separately obtained original archive in this CI.
- MoltenVK's extra link points at `MoltenVK.framework/MoltenVK` (target size **10,485,064 bytes**). zstd has `unzstd` and `zstdcat` links (combined target size **324 bytes**). These are **3 links**, not 3 additional regular source files, explaining the two former false size/count mismatches.

## Only remaining CPM inventory deviation — Boost 1.90.0

| Measurement | Files | Bytes |
|---|---:|---:|
| Declared lock | **59,798** | **550,701,340** |
| Pinned checkout regular files | **59,798** | **550,699,813** |
| Pinned Git object regular blobs | **59,798** | **550,699,124** |

- Checkout vs lock: **−1,527 bytes**; Git blobs vs checkout: **−689 bytes**; lock vs pinned Git blobs: **+2,216 bytes**.
- [Exact read-only receipt from #42933079966](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42933079966) isolates the **+689 checkout-vs-Git bytes to only five Windows build scripts** (all other 59,793 regular-file sizes equal the pinned Git blob sizes):
  - `boost/boost-1.90.0/tools/build/bootstrap.bat` **+37**
  - `boost/boost-1.90.0/tools/build/src/engine/build.bat` **+207**
  - `boost/boost-1.90.0/tools/build/src/engine/config_toolset.bat` **+265**
  - `boost/boost-1.90.0/tools/build/src/engine/guess_toolset.bat` **+107**
  - `boost/boost-1.90.0/tools/build/src/engine/vswhere_usability_wrapper.cmd` **+73**
- Such byte deltas are **consistent with line-ending transformations** of Windows scripts. **Content-level equivalence to the original upstream Boost archive is not proven**, and the remaining **2,216-byte lock-vs-Git-blob difference** cannot be reconciled from aggregate size receipts alone. Do not label it a corruption, repair it by guessing, or rewrite the pinned vendor lock inside the audit PR.

**Exit requirement:** compare the official pinned Boost source archive bytes or an authoritatively matching content manifest, with per-file normalized and raw hashes; report whether the lock was generated against the pre-import archive or current source Git tree. If a metadata correction is justified, apply it via its own reviewed vendor commit *after* native build synchronization, not by changing the historic snapshot. The other **21 CPM regular-file count/size rows are reconciled**, but this is still not archive-level cryptographic provenance.

**Additional independent R18 blockers:** 3 official pinned Git origins in currently inaccessible `blackbearreloaded` repositories, 22 original CPM archive digests not independently revalidated from original downloads, actual linked PS5 SBOM/licence and complete binary ABI proof. They must remain separately accounted for; do not summarize R18 as 100%.
