# Selected scalar SPIR-V constant cache integration — 2026-11-14

Vendor candidate `5f53497bf6067dd68b6529b56aa7c9cf6eb5f598` adds only the focused scalar-ID cache from Lichii #1320 / Eglantine #825 on top of vendor integration `97fdc316fcf5b42e08c26845887f298feac2a424`. Vendor #120 passed 4/4 independently and combined vendor #117 passed 18/18 at this pin.

Engine selection already uses `vendor/encore-active/eden-shader/src` as the shared Task/Mesh shader include root. This candidate pins the new vendor SHA, keeps historical allowlists exact, verifies header blob `844a118358c874b0666aebda116c1d6a0c9a8ceb`, executes the vendor +0/-0/NaN/type-domain test and subgroup receipt, then syntax-compiles the existing selected shared NS1/NS2 SPIR-V owners.

Scope is deliberately narrow: no pipeline eviction, shader-cache file format, async scheduling, RAM budget, descriptor policy or title-specific behavior changes. Full retained emitted-SPIR-V corpus equivalence, FC27 timing improvement and PS5 runtime remain unverified.
