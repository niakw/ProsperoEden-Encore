#!/usr/bin/env python3
"""Strict opt-in warning-only header overlays for the R09 Linux host build.

The SHA-pinned Eden source tree must remain byte-identical. The substitutions
are allowed only inside a disposable CMake binary directory; count-based
guards refuse unexpected upstream changes rather than silently patching.
"""
from pathlib import Path
import sys

PATCHES = {
    "common/page_table.h": [
        ("        constexpr void Store(bool marked, PageType type, u16 block, uintptr_t pointer) noexcept {",
         "        void Store(bool marked, PageType type, u16 block, uintptr_t pointer) noexcept {"),
        ("        constexpr void MarkRasterizerCached() noexcept {",
         "        void MarkRasterizerCached() noexcept {"),
        ("        constexpr void MarkDebug(u64 ptr, u16 block) noexcept {",
         "        void MarkDebug(u64 ptr, u16 block) noexcept {"),
    ],
    "core/hle/kernel/k_address_arbiter.h": [
        (
            "    Result WaitForAddress(uint64_t addr, Svc::ArbitrationType type, s64 value, s64 timeout) {\n"
            "        switch (type) {",
            "    Result WaitForAddress(uint64_t addr, Svc::ArbitrationType type, s64 value, s64 timeout) {\n"
            "        // HOS AArch64 ABI tag 3 is WaitIfEqual64; pinned enum remains immutable.\n"
            "        if (type == static_cast<Svc::ArbitrationType>(3)) {\n"
            "            R_RETURN(WaitIfEqual(addr, value, timeout, true));\n"
            "        }\n"
            "        switch (type) {",
        ),
        (
            "        // HOS AArch64 ABI tag 3 is WaitIfEqual64. The svc_types.h owner\n"
            "        // is an immutable verified backport, so decode this ABI value here.\n"
            "        case static_cast<Svc::ArbitrationType>(3):\n"
            "            R_RETURN(WaitIfEqual(addr, value, timeout, true));\n",
            "",
        ),
    ],
    "video_core/macro.h": [
        ("    [[nodiscard]] inline void SetMethodAddress(u32 address) noexcept {",
         "    inline void SetMethodAddress(u32 address) noexcept {"),
    ],
}


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: r09_prepare_host_warning_overlays.py EDEN_PINNED_SRC HOST_COMPAT_DIR")
    source = Path(sys.argv[1]).resolve()
    target = Path(sys.argv[2]).resolve()
    if not (source / "common/common_types.h").is_file():
        raise SystemExit("R09_HOST_WARNING_PINNED_EDEN_SOURCE_MISSING")
    if not target.is_dir() or target == source or source in target.parents:
        raise SystemExit("R09_HOST_WARNING_OVERLAY_MUST_BE_SEPARATE_BUILD_DIR")
    for rel, edits in PATCHES.items():
        original = source / rel
        data = original.read_text(encoding="utf-8")
        for before, after in edits:
            if data.count(before) != 1:
                raise SystemExit("R09_HOST_WARNING_UPSTREAM_ABI_DRIFT " + rel)
            data = data.replace(before, after)
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(data, encoding="utf-8")
    print("R09_LINUX_HOST_WARNING_OVERLAYS_PINNED_ONLY",
          len(PATCHES), "headers; original Eden unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
