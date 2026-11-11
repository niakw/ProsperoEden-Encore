# R23 — exact conditional source decisions, pass 3 (11 Nov 2026)

**Read-only audit PR #45.** Every case below is based on the original upstream per-commit diff and pinned native source. No ELF or console test implied.

| Commit | Exact evidence | Runtime disposition |
|---|---|---|
| #5 [`ae60f8e7`](https://github.com/eden-emulator/mirror/commit/ae60f8e7f85915a2b79d98b49e3134bbdbeca471) | Single `src/common/net/net.cpp` change, replacing `tag` with `r.tag_name` **inside** `#ifdef NIGHTLY_BUILD` in release/updater asset parser; pinned blob `5c45e1370184f72dc68dd5b6400177d48aef778d` | **Closed for PS5 guest-emulation runtime** (not for future Nightly updater packaging). No copy of updater-specific code |
| #123 [`c3f1e656`](https://github.com/eden-emulator/mirror/commit/c3f1e6562b6cb5aefcb9edd490b303867917f25e) | Title "Windows roots", but `SanitizePath` general algorithm also changes for non-Windows, not only guarded Windows drive/UNC special cases | **Open**, full native FS normalized-path semantics, traversal guards, POSIX parity tests |
| #141 [`5adaa5b0`](https://github.com/eden-emulator/mirror/commit/5adaa5b0f7e19df9bf9dbd883fe921dfe4952125) | Title "MSVC", but removes `constexpr` from a generic service framework handler-table constructor | **Open**, compiled source constructor initialization/ABI and thread-safety on PS5 |

This is one more **semantically disposed** commit, not a gameplay/performance validation. **105/155 runtime semantic cases remain**, along with 5 staged candidate fixes and 12 asset/dependency reviews. The remaining 17 vendor header receipts and 7 corrective lots are separate open dimensions.
