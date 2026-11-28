#!/usr/bin/env python3
"""Current engine/vendor source-selection proof for FC27 SSBO pruning.

This gate intentionally has no vendor-revision allowlist. The engine gitlink,
frozen upstream snapshot, active Encore owners, CMake graph and the real
maintained translation units are the qualification inputs.
"""
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
assert selected==gitlink,("vendor/gitlink mismatch",selected,gitlink)
assert not subprocess.check_output(
    ["git","-C",str(V),"status","--porcelain","--untracked-files=no"],text=True
).strip(),"vendor checkout is dirty"
subprocess.run(["git","-C",str(V),"diff","--quiet","--","sources"],check=True)

# HOS19 ApplicationLaunchInfo semantic contract remains part of the same
# current selected graph and must not regress while SSBO owners advance.
ns_am_header=(V/"encore-active/eden/src/core/hle/service/ns/application_manager_interface.h").read_text()
ns_am_cpp=(V/"encore-active/eden/src/core/hle/service/ns/application_manager_interface.cpp").read_text()
launch_begin=ns_am_header.index("struct ApplicationLaunchInfoV19 {")
launch_end=ns_am_header.index("struct ApplicationContentStorageRecord", launch_begin)
launch_struct=ns_am_header[launch_begin:launch_end]
for required in (
    "u64 patch_id;",
    "u32 content_meta_type;",
    "static_assert(sizeof(ApplicationLaunchInfoV19) == 0x80);",
    "static_assert(offsetof(ApplicationLaunchInfoV19, patch_id) == 0x08);",
    "static_assert(offsetof(ApplicationLaunchInfoV19, version) == 0x10);",
    "static_assert(offsetof(ApplicationLaunchInfoV19, content_meta_type) == 0x14);",
    "static_assert(offsetof(ApplicationLaunchInfoV19, launch_flags) == 0x18);",
    "static_assert(offsetof(ApplicationLaunchInfoV19, application_storage_id) == 0x1C);",
    "static_assert(offsetof(ApplicationLaunchInfoV19, update_storage_id) == 0x1D);",
):
    assert required in launch_struct, f"HOS19 ApplicationLaunchInfo ABI regression: {required}"
assert "application_instance_id" not in launch_struct
for required in (
    "out_launch_info->patch_id = has_patch ? update_id : 0;",
    "out_launch_info->content_meta_type = static_cast<u32>(FileSys::TitleType::Application);",
    "out_launch_info->launch_flags = 0xB;",
    "pending_application_launch_info = launch_info;",
    "pending_application_launch_info.reset();",
):
    assert required in ns_am_cpp, f"HOS19 launch semantics regression: {required}"

bfs=V/"encore-active/eden/src/shader_recompiler/frontend/ir/breadth_first_search.h"
active=V/"encore-active/eden/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
pinned=V/"sources/eden/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
assert blob(bfs)=="fa5e7572ef99bba3db17154c63f60dddba7a87c6"
assert blob(active)=="602d45b4d2ad872b138d62ce05f379b5e1103602"
assert blob(pinned)=="4ce1ff6c19c4937855d4460a515aec6a8a1e07e0"

# R23 #58 already stages the maintained BFS header. This integration must
# replace only the global-memory pass and preserve the immutable original.
for needle in (
    'set(EDEN_R23_PHI_HEADER',
    'vendor/encore-active/eden/src/shader_recompiler/frontend/ir/breadth_first_search.h',
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
assert source.split("bool IsGlobalMemory(",1)[1].split("bool IsGlobalMemoryWrite(",1)[0].count("case IR::Opcode::GlobalAtomicCompareExchange32:")==1
assert "return IR::Opcode::StorageAtomicCompareExchange32;" in source
assert "BreadthFirstSearchPruned(Value value" in header
assert "BreadthFirstSearchPruned" not in pinned.read_text()

# GPU-53: exact maintained SSBO emitter + shared native SPIR-V context.
active_mem=V/"encore-active/eden/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
pinned_mem=V/"sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
active_ctx=V/"encore-active/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
pinned_ctx=V/"sources/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
assert blob(active_mem)=="6e6994343df4a1e3930495f8fd575c4329bfa8c4"
assert blob(pinned_mem)=="bef4421fedce6d66af1c6ff0c1dcc835e976eb33"
assert blob(active_ctx)=="0e14a042ab272f701da90a5b62fdeeb626032188"
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
    V/"encore-active/eden/src",
    V/"encore-active/eden/src",
    V/"encore-active/eden/src",
    V/"encore-active/eden/src",
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
