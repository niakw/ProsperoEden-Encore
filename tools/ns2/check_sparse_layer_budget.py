#!/usr/bin/env python3
"""N63 sparse 2D array tile/mip-tail byte budget, allocation transaction tests."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
N58=(ROOT/"vendor/sources/eden/src/video_core/vulkan_common/vulkan_device.h").read_text()
N62=(ROOT/"vendor/encore-active/eden-vulkan/vulkan_memory_allocator.cpp").read_text()
HEADER=ROOT/"vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_sparse_layer_budget.h"
assert "sparseResidencyImage2D" in N58
assert "VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT" in N62
assert "ResetAfterGpuRetire" in HEADER.read_text()
assert "bind_shared_tail" in HEADER.read_text()
with tempfile.TemporaryDirectory(prefix="n63-sparse-budget-") as td:
    for cxx in ("clang++","g++"):
        exe=Path(td)/("n63-"+cxx.replace("+","p"))
        subprocess.run([cxx,"-std=c++20","-O2","-Wall","-Wextra","-Werror",
             "-fsanitize=undefined","-fno-sanitize-recover=all",
             "-I",str(ROOT/"vendor/encore-active/ns2-helpers/include"),
             str(ROOT/"tools/ns2/test_sparse_layer_budget.cpp"),
             "-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N63_SPARSE_IMAGE_PLAN_ORACLE_PASS")
