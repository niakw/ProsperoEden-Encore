#!/usr/bin/env python3
"""Engine/vendor selection proof for FC27 SSBO failed-search pruning."""
from pathlib import Path
import hashlib
import subprocess

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(path: Path)->str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

selected=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
gitlink=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
assert selected==gitlink=="76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3",(selected,gitlink)

active_bfs=V/"encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h"
active_pass=V/"encore-active/eden-shader/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
pinned_bfs=V/"sources/eden/src/shader_recompiler/frontend/ir/breadth_first_search.h"
pinned_pass=V/"sources/eden/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"

assert blob(active_bfs)=="fa5e7572ef99bba3db17154c63f60dddba7a87c6"
assert blob(active_pass)=="41ad0f5cef1e070e552b43ea49648d5e74f10bad"
assert blob(pinned_bfs)=="ec5542554920826ea52b33fd4170c5a8e69648df"
assert blob(pinned_pass)=="4ce1ff6c19c4937855d4460a515aec6a8a1e07e0"

for needle in (
    'set(EDEN_R23_PHI_HEADER',
    'set(EDEN_FC27_SSBO_SOURCE',
    'list(FIND eden_fc27_ssbo_sources',
    'list(REMOVE_ITEM eden_fc27_ssbo_sources "ir_opt/global_memory_to_storage_buffer_pass.cpp")',
    'list(APPEND eden_fc27_ssbo_sources "${EDEN_FC27_SSBO_SOURCE}")',
):
    assert CMAKE.count(needle)==1,needle

bfs=active_bfs.read_text()
owner=active_pass.read_text()
assert "BreadthFirstSearchPruned" in bfs
assert "exhausted.contains" in bfs
assert "BreadthFirstSearchPruned" in owner
assert "Track(low_addr, &nvn_bias)" in owner
assert "Track(low_addr, nullptr)" in owner

for test in (
    "fc27_ssbo_search_pruning_host.py",
    "ps5_ir_bfs_adaptive_host.py",
    "ns1_r23_58_bindless_phi.py",
    "ns1_r23_58_conditional_phi.py",
):
    subprocess.run(["python3","-B",str(V/"tests"/test)],check=True,timeout=180)

print("FC27_SSBO_ENGINE_VENDOR_PAIR_PASS gitlink=exact bfs=pruned owner=selected pinned_immutable=1 ps5_perf=unverified")
