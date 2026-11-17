#!/usr/bin/env python3
"""Engine/vendor source-selection proof for FC27 SSBO failed-search pruning."""
from pathlib import Path
import hashlib
import subprocess

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(path: Path) -> str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

selected=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
gitlink=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
expected={"76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3","6f4bb38594b273fe7cc4fba960dfe62cdb9f508e","4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771"}
assert selected==gitlink and selected in expected,(selected,gitlink)

bfs=V/"encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h"
active=V/"encore-active/eden-shader/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
pinned=V/"sources/eden/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
assert blob(bfs)=="fa5e7572ef99bba3db17154c63f60dddba7a87c6"
assert blob(active)=="41ad0f5cef1e070e552b43ea49648d5e74f10bad"
assert blob(pinned)=="4ce1ff6c19c4937855d4460a515aec6a8a1e07e0"

# R23 #58 already stages the maintained BFS header. This integration must
# replace only the global-memory pass and preserve the immutable original.
for needle in (
    'set(EDEN_R23_PHI_HEADER',
    'vendor/encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h',
    'set(EDEN_FC27_SSBO_SOURCE',
    'list(FIND eden_fc27_ssbo_sources "ir_opt/global_memory_to_storage_buffer_pass.cpp"',
    'list(REMOVE_ITEM eden_fc27_ssbo_sources "ir_opt/global_memory_to_storage_buffer_pass.cpp")',
    'list(APPEND eden_fc27_ssbo_sources "${EDEN_FC27_SSBO_SOURCE}")',
):
    assert CMAKE.count(needle)==1,needle
assert CMAKE.count("global_memory_to_storage_buffer_pass.cpp")==3

source=active.read_text()
header=bfs.read_text()
assert "BreadthFirstSearchPruned(value, pred, exhausted)" in source
assert "biased_exhausted" in source and "unbiased_exhausted" in source
assert "BreadthFirstSearchPruned(Value value" in header
assert "BreadthFirstSearchPruned" not in pinned.read_text()

subprocess.run(["python3","-B",str(V/"tests/fc27_ssbo_search_pruning_host.py")],
               check=True,timeout=180)
subprocess.run(["python3","-B",str(V/"tests/ps5_ir_bfs_adaptive_host.py")],
               check=True,timeout=180)
print("FC27_SSBO_ENGINE_VENDOR_PAIR_PASS gitlink=exact source_pass=1 bfs_header=1 pinned_immutable=1 ps5_gameplay=unverified")
