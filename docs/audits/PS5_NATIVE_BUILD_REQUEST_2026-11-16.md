# PS5 native validation request — 2026-11-16

This documentation-only commit intentionally carries the `[full-build]` marker to trigger the repository's existing non-publishing native PS5 build workflow.

Runtime source under test is unchanged from engine main immediately before this request:
- engine runtime/source baseline: `1c6c1ffe84e838b0c95c2047c2feaae35a7d3c83`
- selected vendor: `50a849a93494f442d47573b8ce8b8797c3cecd26`
- firmware target: PS5 13.60

This request does **not** carry `[release]`; no public release is authorized.

Acceptance for this run:
1. native source/preflight gates pass;
2. selected vendor and RADV source receipts are exact;
3. native compilation/link/staging/package succeed;
4. inspect all warnings/errors/not-found/deprecation diagnostics;
5. retain ELF, symbols, link map/provenance and distributable artifact hashes;
6. only then request hardware validation for FC27, Bananza, MKW, launcher handoff/library and app exit.
