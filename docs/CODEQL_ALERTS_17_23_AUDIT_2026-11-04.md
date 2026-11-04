# CodeQL alerts #17–#23 — November 4, 2026

## Scope and constraints

Eden Encore `main` pinned vendor commit `97c01069f04fc48c3e0648e13e4962e29ab594a6` at audit time. The six high-severity C++ notices point **inside upstream Boost 1.90.0 snapshot source files**, under `vendor/sources/eden-cpm/boost`; these are not locally modified Encore allocator implementations. The allocator paths below were compared with the code at the exact pinned vendor commit. A CodeQL report does not by itself establish a memory-safety defect. Equally, this source-only review is **not** a dynamic allocator execution proof.

| Alert | Source location | Source ownership / symmetry evidence | Disposition |
| --- | --- | --- | --- |
| [#23](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/23) | `container/vector.hpp:453` | `vector_alloc_holder` destructor invokes `this->deallocate(m_start, m_capacity)`; `allocate` uses `allocator_traits_type::allocate` at ~483, and `deallocate` uses `allocator_traits_type::deallocate` at ~488 | Third-party allocator pair; no unsafe replacement with `delete` |
| [#22](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/22) | `unordered/detail/fca.hpp:581` | Constructor exception rollback deallocates buckets using the same `bucket_alloc` used for allocation at ~564 | Third-party allocator rollback, not mismatched `new/free` |
| [#21](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/21) | `unordered/detail/fca.hpp:671` | Groups allocated with `group_alloc` at ~567; group destructors run before matching `allocator_deallocate(group_alloc, groups, num_groups)` | Third-party allocator pair |
| [#20](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/20) | `unordered/detail/fca.hpp:656` | Buckets allocated with `bucket_alloc` at ~564; bucket destructors run before matching deallocation at ~656 | Third-party allocator pair |
| [#19](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/19) | `unordered/detail/implementation.hpp:625` | Node memory allocated with `node_allocator_traits::allocate` at ~632 and object placement-constructed; destructor invokes explicit `destroy` at ~624 and same allocator's `deallocate` at ~625 | Third-party allocator pair |
| [#18](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/18) | `unordered/detail/foa/core.hpp:1097` | `storage_traits::allocate` stores `arrays.elements_` at ~1051; `delete_` uses `storage_traits::deallocate` for that buffer | Third-party allocator pair |
| [#17](https://github.com/niakw/ProsperoEden-Encore/security/code-scanning/17) | `tools/check-ns2-title-catalog-host.py:14` | Former substring assertion over the **contents of a C++ source file**, not validation of a runtime URL. Hardened to capture the exact two CDN origins from the `image_host` assignment and compare their complete URLs and parsed components. | Test code corrected |

## Scanner configuration

The CodeQL workflow already uses `config-file: ./.github/codeql/codeql-config.yml`, with `build-mode: none` for C/C++. Its positive `paths` include `headless`, `src`, `tools`, and `vendor/encore-active`, **not** the immutable `vendor/sources` snapshot. Four exact Boost source file exclusions document the verified third-party boundaries; they must not become a blanket ignore of active renderer or first-party code. The executable `tools/check-codeql-allocator-pairs-host.py` fails if the paired upstream allocator calls change or first-party scanning is removed.

These changes **do not assert that GitHub has closed/dismissed any alert**. Existing CodeQL alerts can remain open until the relevant code-scanning analysis updates its results or a maintainer reviews the alert details in the Security UI. The linked GitHub connector does not expose alert dismissal or private SARIF locations. Do not mark these as `fixed` based solely on a source assertion; if a future report includes an actual violating allocation path in active runtime code, investigate independently.
