# PS5 native build request — 2026-11-15

Base engine before request: `8eb2a16c55494c0cb03c6b23b43d9f9e92744727`.

Purpose: trigger one non-publishing native PS5 build after the final G11/Bananza diagnostic parity correction and repository cleanup.

Selected vendor at request time: `4572e581d011c444fd59428d5c042098f05dcfca`.

Pre-request evidence on the base engine:
- PR #190 P0-P4 host qualification: PASS.
- PR #190 full source preflight: PASS.
- PR #190 CodeQL: PASS.
- Post-merge P0-P4 on main: PASS.
- Post-merge core fast gate: PASS.
- Post-merge source preflight: PASS.
- No public release requested.

This receipt does not claim PS5 runtime compatibility. Native compilation/package integrity and physical-console validation remain separate gates.
