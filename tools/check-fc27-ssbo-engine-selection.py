#!/usr/bin/env python3
"""Engine/vendor source-selection proof for FC27 SSBO failed-search pruning."""
from pathlib import Path
import hashlib
import subprocess
import shutil

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(path: Path) -> str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

selected=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
gitlink=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
expected={"76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3","6f4bb38594b273fe7cc4fba960dfe62cdb9f508e","4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","e0d4143f55b5d4fee976d241d18ebcf7766ae4cf","1aa641ff566d688fbe34c7ec0ab1e25181e7f3b7","c0d65da6ae50aff83aae83c96bb6acadd34dae9c","b8883667410054db189d00b3a5144088f47d3af9"}
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

# GPU-53: exact maintained SSBO emitter + shared native SPIR-V context.
active_mem=V/"encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
pinned_mem=V/"sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
active_ctx=V/"encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
pinned_ctx=V/"sources/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
assert blob(active_mem)=="6e6994343df4a1e3930495f8fd575c4329bfa8c4"
assert blob(pinned_mem)=="bef4421fedce6d66af1c6ff0c1dcc835e976eb33"
assert blob(active_ctx)=="a3c36f45fd9b2b89f096258f54dd9189287a82d0"
assert blob(pinned_ctx)=="ef1f3f2ee83d3d44a571c03f19399dbe0697dd7e"

for needle in (
    'set(EDEN_NS1_SSBO_ALIGNMENT_SOURCE',
    'list(FIND eden_ns1_ssbo_emit_sources',
    'backend/spirv/emit_spirv_memory.cpp',
    'list(REMOVE_ITEM eden_ns1_ssbo_emit_sources "backend/spirv/emit_spirv_memory.cpp")',
    'list(APPEND eden_ns1_ssbo_emit_sources "${EDEN_NS1_SSBO_ALIGNMENT_SOURCE}")',
):
    assert needle in CMAKE,needle

mem_text=active_mem.read_text()
pinned_mem_text=pinned_mem.read_text()
assert "static bool VectorViewIsExact" in mem_text
assert "return offset.U32() % size == 0;" in mem_text
assert "return ctx.profile.min_ssbo_alignment >= size;" in mem_text
assert mem_text.count("VectorViewIsExact(ctx, offset, sizeof(u32[2]))")==2
assert mem_text.count("VectorViewIsExact(ctx, offset, sizeof(u32[4]))")==2
assert "VectorViewIsExact" not in pinned_mem_text

ctx_text=active_ctx.read_text()
pinned_ctx_text=pinned_ctx.read_text()
ns1_split="!Shader::Ampere::NativeSpirvCbufBoundsActive() && shift > 2"
assert ctx_text.count(ns1_split)==2
assert "profile.min_ssbo_alignment < (1U << shift)" in ctx_text
assert "std::array<Id, 4> words;" in ctx_text
assert "OpCompositeConstruct(type, std::span{words}.first(count))" in ctx_text
assert "callback(ssbo_pointer, ssbo_id, ssbo_index);" in ctx_text
assert ns1_split not in pinned_ctx_text

# Decision table used by the actual helper.
def vector_exact(aliasing, immediate, offset, alignment, size):
    if not aliasing:
        return False
    if immediate:
        return offset % size == 0
    return alignment >= size
for size in (8,16):
    assert vector_exact(True,True,0,4,size)
    assert vector_exact(True,True,size,4,size)
    assert not vector_exact(True,True,4,16,size) if size==8 else True
    assert not vector_exact(True,True,4,16,size)
    assert not vector_exact(False,True,0,16,size)
    assert not vector_exact(True,False,0,4,size)
assert vector_exact(True,False,0,8,8)
assert not vector_exact(True,False,0,8,16)
assert vector_exact(True,False,0,16,16)

# Compile the two real maintained translation units against the selected headers.
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler,"Clang required for GPU-53 syntax proof"
cpm=V/"sources/eden-cpm"
includes=[
    V/"encore-active/ns2-runtime/ampere",
    V/"encore-active/ns2-runtime/gpu_dispatch",
    V/"encore-active/ns2-runtime/hle",
    V/"encore-active/eden-shader/src",
    V/"sources/eden/src",
    V/"sources/eden/src/dynarmic/src",
    cpm/"fmt/12.1.0/include",
    cpm/"sirit/v1.0.5/include",
    cpm/"spirv-headers/vulkan-sdk-1.4.341.0/include",
    cpm/"vulkanheaders/v1.4.345/include",
]
boost=cpm/"boost/boost-1.90.0/libs"
assert boost.is_dir()
includes.extend(sorted(boost.glob("*/include")))
cmd=[compiler,"-std=c++20","-fsyntax-only","-Wno-unused-parameter",
     "-DPS5_NATIVE=1","-DFMT_HEADER_ONLY","-DCANNOT_EXPLICITLY_INSTANTIATE",
     *["-I"+str(inc) for inc in includes]]
for source_file in (active_mem,active_ctx):
    proc=subprocess.run(cmd+[str(source_file)],capture_output=True,text=True,timeout=120)
    assert proc.returncode==0,(source_file,proc.stderr[-6000:])
print("NS1_GPU53_SSBO_ALIGNMENT_PASS direct=64+128 global=maxwell_only pinned_immutable=1 syntax=2")

subprocess.run(["python3","-B",str(V/"tests/fc27_ssbo_search_pruning_host.py")],
               check=True,timeout=180)
subprocess.run(["python3","-B",str(V/"tests/ps5_ir_bfs_adaptive_host.py")],
               check=True,timeout=180)
print("FC27_SSBO_ENGINE_VENDOR_PAIR_PASS gitlink=exact source_pass=1 bfs_header=1 pinned_immutable=1 ps5_gameplay=unverified")
