#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage real, tightly scoped native Vulkan image-format ABI for Linux R09.

The upstream Linux Vulkan wrapper does not export the one maintained R24
GetImageFormatProperties method and does not load its instance dispatch
pointer. An unchanged R24 MSAA owner therefore links unsuccessfully.

Generate a build-directory ONLY overlay using the *pinned pristine* upstream
implementation plus the exact method from the *pinned maintained* vendor.
No main/vendor source edit; no dummy return, no synthetic physical device,
no substitute driver, and no whole PS5 wrapper substitution.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def exactly_one(text: str, needle: str, label: str) -> None:
    count = text.count(needle)
    if count != 1:
        raise ValueError(f"R09_HOST_WRAPPER_SOURCE_DRIFT_{label} count={count}")


def stage(upstream: str, maintained: str) -> str:
    loader_old = "X(vkGetDeviceProcAddr) && X(vkGetPhysicalDeviceFormatProperties) &&"
    loader_new = (
        "X(vkGetDeviceProcAddr) && X(vkGetPhysicalDeviceImageFormatProperties) &&\n"
        "           X(vkGetPhysicalDeviceFormatProperties) &&"
    )
    exactly_one(upstream, loader_old, "UPSTREAM_DISPATCH")
    exactly_one(maintained, loader_new, "MAINTAINED_DISPATCH")
    method_start = "bool PhysicalDevice::GetImageFormatProperties("
    method_after = "VkFormatProperties PhysicalDevice::GetFormatProperties("
    exactly_one(maintained, method_start, "MAINTAINED_METHOD")
    exactly_one(upstream, method_after, "UPSTREAM_METHOD_ANCHOR")
    if method_start in upstream:
        raise ValueError("R09_HOST_WRAPPER_ALREADY_PATCHED")
    begin = maintained.index(method_start)
    end = maintained.index(method_after, begin)
    method = maintained[begin:end].strip()
    if (
        method.count("dld->vkGetPhysicalDeviceImageFormatProperties(") != 1
        or "== VK_SUCCESS;" not in method
        or "physical_device, format, type, tiling, usage, flags, &properties" not in method
        or not method.endswith("}")
    ):
        raise ValueError("R09_HOST_WRAPPER_NATIVE_METHOD_ABI_DRIFT")
    # Keep the exact pinned upstream implementation otherwise, so the native
    # performance profiling and optional PS5 mesh extensions are not linked.
    output = upstream.replace(loader_old, loader_new)
    output = output.replace(method_after, method + "\n\n" + method_after)
    exactly_one(output, method_start, "OUTPUT_METHOD")
    exactly_one(output, "X(vkGetPhysicalDeviceImageFormatProperties)", "OUTPUT_POINTER")
    return output


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--maintained", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        for source in (args.upstream, args.maintained):
            if source.is_symlink() or not source.is_file():
                raise ValueError("R09_HOST_WRAPPER_SOURCE_MISSING_OR_SYMLINK")
        result = stage(args.upstream.read_text(encoding="utf-8"),
                       args.maintained.read_text(encoding="utf-8"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print("R09_HOST_REAL_VULKAN_IMAGE_FORMAT_WRAPPER_OVERLAY_PASS "
              "native_entry=1 native_loader=1 source=pristine+owned", flush=True)
        return 0
    except (OSError, ValueError) as exc:
        print(f"R09_HOST_WRAPPER_OVERLAY_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
