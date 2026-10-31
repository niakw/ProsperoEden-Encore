#!/usr/bin/env python3
"""N51 vendor-native GPU PTE range batching, exact source baseline parity."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/encore-active/eden-core/src/video_core/memory_manager.cpp"
HELPER = ROOT / "vendor/encore-active/ns2-helpers/include/video_core/ns2_egl_gpu_range_batch.h"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()

def blob(t: str) -> str:
    b = t.encode()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def once(t: str, old: str, new: str) -> str:
    assert t.count(old) == 1, ("N51 native PS5 source-owner drift", old[:72])
    return t.replace(old, new)

t = OWNER.read_text()
assert blob(t) == "f1d32ed9c48f21c0f4890e814a19b70f6de1d29c"
assert HELPER.is_file() and "class ChangedPageRuns" in HELPER.read_text()
t = once(t,
    '#include "video_core/memory_manager.h"\n#ifdef EDEN_NS2_GPU_RANGE_BATCH\n'
    '#include "video_core/ns2_egl_gpu_range_batch.h"\n#endif',
    '#include "video_core/memory_manager.h"')
for page in ("page_size", "big_page_size"):
    init = (
        "#ifdef EDEN_NS2_GPU_RANGE_BATCH\n"
        "    // Coalesce only adjacent changed PTE pages; preserve unchanged holes.\n"
        f"    Eden::NS2::Eglantine::ChangedPageRuns changed_runs({page});\n"
        "    const auto notify_changed = [this](GPUVAddr address, u64 length) {\n"
        "        rasterizer->ModifyGPUMemory(unique_identifier, address, length);\n"
        "    };\n"
        "#endif\n")
    t = once(t, init, "")
    old = (
        "        if (current_entry_type != entry_type) {\n"
        f"            rasterizer->ModifyGPUMemory(unique_identifier, current_gpu_addr, {page});\n"
        "        }")
    altered = (
        "#ifdef EDEN_NS2_GPU_RANGE_BATCH\n"
        "        changed_runs.Record(current_gpu_addr, current_entry_type != entry_type,\n"
        "                            notify_changed);\n"
        "#else\n"+old+"\n#endif")
    t = once(t, altered, old)
flush = "#ifdef EDEN_NS2_GPU_RANGE_BATCH\n    changed_runs.Flush(notify_changed);\n#endif\n"
assert t.count(flush) == 2
t = t.replace(flush, "")
assert blob(t) == "f30099dfb5df01d9cd787d199e3e61f28205669a", "N51 changed unrelated PS5 GPU logic"
assert "EDEN_NS2_EGLANTINE_GPU_RANGE_BATCH_EXPERIMENTAL OR" in CMAKE
assert "EDEN_NS2_GPU_RANGE_BATCH=1" in CMAKE
assert "EDEN_FINAL_RELEASE_PROFILE" in CMAKE
assert "headless/ns2/eglantine/video_core/memory_manager.cpp" not in CMAKE
print("N51_NATIVE_GPU_SINGLE_VENDOR_OWNER_AND_F07_BASELINE_PASS")
