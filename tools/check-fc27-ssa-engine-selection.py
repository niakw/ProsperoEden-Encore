#!/usr/bin/env python3
"""Engine/vendor source-selection proof for FC27 block-local SSA storage."""
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
# Vendor #180 is the reviewed PS5 fragment-shuffle successor. Keep the\n# exact gitlink allow-list: no branch/range acceptance.\nassert selected==gitlink and selected in {"76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3","6f4bb38594b273fe7cc4fba960dfe62cdb9f508e","4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356"},(selected,gitlink)

active_header=V/"encore-active/eden/src/shader_recompiler/frontend/ir/basic_block.h"
active_ssa=V/"encore-active/eden/src/shader_recompiler/ir_opt/ssa_rewrite_pass.cpp"
pinned_header=V/"sources/eden/src/shader_recompiler/frontend/ir/basic_block.h"
pinned_ssa=V/"sources/eden/src/shader_recompiler/ir_opt/ssa_rewrite_pass.cpp"
assert blob(active_header)=="0a23d1ce0f43524e6195bd8219349ef632cfb719"
assert blob(active_ssa)=="26c42a9900256e5573735394753c1d5264611664"
assert blob(pinned_header)=="d3a66caac9b0955dd72526b23cf7caab8b12976f"
assert blob(pinned_ssa)=="b5cd2339924f0cbd725249140ff67cfb8f79a360"

needles=[
    'set(EDEN_FC27_SSA_ROOT',
    'configure_file("${EDEN_FC27_SSA_HEADER}"',
    'list(FIND eden_fc27_ssa_sources "ir_opt/ssa_rewrite_pass.cpp" eden_fc27_ssa_index)',
    'list(REMOVE_ITEM eden_fc27_ssa_sources "ir_opt/ssa_rewrite_pass.cpp")',
    'list(APPEND eden_fc27_ssa_sources "${EDEN_FC27_SSA_SOURCE}")',
    'target_include_directories(shader_recompiler BEFORE PUBLIC "${EDEN_FC27_SSA_INCLUDE}")',
]
for needle in needles:
    assert CMAKE.count(needle)==1,needle

# Source/header must be selected as one pair: the maintained SSA source calls
# the block-local accessors that do not exist in the immutable predecessor.
assert "block->SsaPredValue(variable)" in active_ssa.read_text()
assert "block->SetSsaPredValue(variable, value)" in active_ssa.read_text()
assert "SsaPredValue" in active_header.read_text()
assert "SsaPredValue" not in pinned_header.read_text()

subprocess.run(["python3","-B",str(V/"tests/fc27_ssa_definition_storage_host.py")],
               check=True,timeout=180)
print("FC27_SSA_ENGINE_VENDOR_PAIR_PASS gitlink=exact source_header_pair=1 pinned_immutable=1 ps5_gameplay=unverified")
