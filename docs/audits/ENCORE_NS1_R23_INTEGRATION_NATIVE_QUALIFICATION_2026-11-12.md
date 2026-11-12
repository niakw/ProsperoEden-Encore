# E1 NS1 integration native qualification · 12 November 2026

**Experimental only.** Engine branch `integration/ns1-r23-e1-20261112` points to vendor candidate `32f5d9c1af5f391abd0b94291f335620911ef4d7` and integrates 32 selected NS1 vendor PR source owners with ten overlapping source files reconciled, plus the engine R23 PS5-selected CMake blocks and applet life-cycle candidate.

The 5 vendor research branches with duplicate owners (#59/#60/#67/#68/#69) must NOT be merged over their replacements (#61/#65/#71/#72/#75). This remains a source-stage experiment, not a production promise. Do not touch main or the unpublished release.

## Exit gates
1. Host/build guard checks unchanged, including source hashes, vendor lineage, and security.
2. Full native CMake selection/compile/link and package validator on **this** branch with no publication.
3. Regression against already-green engine main native build #43135290929.
4. Integration to main only after resolving any compile/ABI/driver mismatch, with new native build and a PS5 user first-frame test.

The unsupported 720p trained R09 Vulkan output remains unqualified. The eight on-demand user-only Daily WebP contract must not regress.
