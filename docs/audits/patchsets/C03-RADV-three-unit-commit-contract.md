# C03 — RADV transfer/barrier split: frozen implementation inputs

**Status:** preparation only; no RADV code changed, no Meson compilation, no vendor repin. Keep C03 separate from C00–C02 and from P5.

**Actual corrective PR #46 gitlink:** `22b69d6053db41b74edac2633c012f925b84f69e` as read from the source branch's Git tree, rather than the `f9f08786`/`90c9c8a2` pins seen in transient GitHub PR merge checkouts. All three source blobs are unchanged from the audit baseline. The isolated patchset CI now checks the PR head, not a moving merge tree. No RADV integration or vendor repin is implied.

## Three C translation units — all required

| Unit | Exact pinned Git blob | Required owner decision |
|---|---|---|
| Maintained `encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c` | `9dd12c19a1a277a2753432e1411a449fdf923c4a` | `radv_split_cmd_stream_if_due` is currently **static** at about line 13933; `radv_CmdPipelineBarrier2` at 17370. Export the helper within the driver only if the bridge is ABI-safe; add pre-barrier split without duplicating an existing split. |
| Pinned `sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_buffer.c` | `559272a4c99014a1cfb6c62aa7d81b2301729fd7` | Copy the **full** file into a maintained `encore-active/ps5-mesa` override; add pre-transfer split for Fill/Copy/Update, and change Meson source selection to that maintained owner. Do **not** modify `sources/`. |
| Pinned `sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_copy.c` | `b48ad04b1637898c5e2b95e438e2e9ae9ac522a1` | Same ownership migration, with pre-transfer split for CopyBufferToImage, CopyImageToBuffer and CopyImage. |

The original helper and command functions are present in the stated SHA-specific sources. The historic [Swordpdf patch `1862764`](https://github.com/Swordpdf/ProsperoEden/commit/18627649ca7f72fcc7e3959bdac8d27d8f68fcf9) is a **reference**, not directly reusable as a transient Python rewrite or as a ready Mesa update.

### Non-negotiable verification before creating a vendor commit

1. Preserve the maintained 12-override RADV list and **explicitly register both meta TUs** as full maintained source owners. The copy-and-patch staging script must never modify pristine `sources/ps5-mesa` or bypass Meson's compilation receipt.
2. Show the exact Meson compile database paths + SHA-256 of all **three** source units before claiming the patch is effective.
3. Test long transfer-only and barrier-only command streams, short mixed workloads, driver split at active queries, inherited render passes, image layouts, fence lifetime and concurrent BO release; no duplicate/preemptive split.
4. Run a focused native driver compile first, followed by PS5 ABI/WSI tests, and only then a general emulator build. A syntax-only successful CI is not GPU/device evidence.
5. Return the vendor commit and the coordinated Encore gitlink bump only when independently authorized and proven. Do not touch the running `main` native build.

**This is a pre-commit source contract, not an implemented patch.**
