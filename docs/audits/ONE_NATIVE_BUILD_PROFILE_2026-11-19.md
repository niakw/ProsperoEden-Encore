# Encore — single native PS5 test and production profile (19 November 2026)

The **same** compiled PS5 application serves development tests and production. Detailed logs are an operator runtime setting, not a second compiler profile.

## Reviewed decisions on engine main

- `headless/gpu_native_observability.cmake` selects one fixed reviewed `fermi_2d_observed.cpp` owner. The `EDEN_UNQUALIFIED_FERMI2D_COPY` ON/OFF selector and CMake branch have been deleted. Unqualified extended 3D/pitch software copies are not compiled. The historical `fermi_2d_experimental.cpp` remains a static *source-only oracle* for review, not a selectable product.
- `headless/CMakeLists.txt` no longer includes the dormant developer `guest_write_deferred_bridge.cmake` recipe. The bridge and its historical CPU/GPU tests remain non-shipping review evidence; `kNativePostStorePublicationReady=false` still documents unresolved publication/read ordering hazards. Never turn it ON without proof.
- The inert, separately installable NS2 research workflow (`if: false`) and its research package script have been **removed** from the active tree. The single standard native workflow produces the only installable PS5 title.
- Exact host contracts now require a **fixed** Fermi2D owner, no developer-only guest-write bridge in native CMake, and no alternative research release pipeline. CMakeCache still rejects attempts to set old research flags ON; historical OFF cache entries cannot enable a source no longer gated by that option.
- `PS5_NATIVE`, real hardware/guest capability conditions, the runtime user setting for detailed logs and third-party `_LIBCPP_ENABLE_EXPERIMENTAL` (libc++ API availability) are not test-vs-production variants and remain untouched.

**Runtime qualification remains separate.** Removing the alternate build configuration neither cures FC27 cache contention nor fixes NS2 `PC=0x4`. The vendor-side FC27 deferred page-protection candidate needs exact engine/vendor source-provenance validation, successful PS5 native compilation and a console A/B run before any claim of corrected gameplay.

Source evidence: [FC27 #100](https://github.com/niakw/ProsperoEden-Encore/issues/100), [NS2 #123](https://github.com/niakw/ProsperoEden-Encore/issues/123), and [R457 19-Nov audit](PS5_R457_2026-11-19_FC27_NS2_LAST_SESSION.md).
