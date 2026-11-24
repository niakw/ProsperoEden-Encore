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
expected={"76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3","6f4bb38594b273fe7cc4fba960dfe62cdb9f508e","4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","e0d4143f55b5d4fee976d241d18ebcf7766ae4cf","1aa641ff566d688fbe34c7ec0ab1e25181e7f3b7","c0d65da6ae50aff83aae83c96bb6acadd34dae9c","b8883667410054db189d00b3a5144088f47d3af9","7eb559a9a2bcf68e91145c241082644c38ff0dfc","3c831706f615566b0eb4c99e9168e6c9236896d2","92d985482a6181c67626794e684f67d9a131a763","fbdd6a44158716d8ba1ae69b85aac30a87af389c","cabc153d337d49871cae36c183d575e834c14383","daff359876ecf35a4f5f4742e483a248c8103d84","463e17ef842b5e230946d47f29409b014a75117f","4bd93a797d922c6234d4a543a36b41462204ce0c","d81f5dd5e08400816b65091645016e97c0dbf3f7","ba3377a0b95db903760c7e7a3c84f60f3c473825","7ccc5721d5525ecacd3d55ea7e59b7f62d0473bb","4934fa18843112cad024ee41f4e28e1dc99d581f","21d480ac95486d545d50371608b038cf98efb24e","20d2457b83e65aa6623ea5d1fed5d2e9d423aeaf","decf9b4a91ca1fc218c33d6829f3e86616b87787","e81e40171ec9e07fd26c1ea8022116ad97e602af","c07a9974d3d91de5fd4780c7849428251a90ed0c","11dcdc5627348a291d7ca0ed89319ffb2049a68f","17b77950adfd0f091e81359cc73cd192e8c18b41","b381340215a07c72075b7114a55bb594cb2bfb86","fa460ecaa86fd6528514ad2283d8fc289639111f","c57862fdec84ef6049fbb24b0fffeba78a81ea9b","6129078b641b12b5ed8028f69b6847a64adf416f","72b27310a39dae20b5a569132133c2486f6d6ce2","69f7e3453d676f7538f62ebe70b9197cd1614f2b","df8a5e2f59895d315b7c3b69f87bb78502afa8c7","bd8424573816c1d80fe4400d0aa4731435bc07d9","0b6214c56f51d59e5a0aa253ea5801b49e2bf475","fde8c9de9e3df8167afe8baa1b40493de7c78758"}
expected.add("42b34a5dc46b594cb029362e8f130900adf4424e")
expected.add("77b736148129ffa72c9f6c081695b7c7515c3ed9")
expected.add("4354add020afac574198f63d87167f3022bff9c6")
# This integration changes only the reviewed GPU readback method and its
# source receipts; the active SSBO shader/CMake blobs are checked below.
expected.add("17253dc91e9fe1eb2d9980f261f59d227bfcd1a1")
# The merged vendor commit has the exact reviewed 17253dc9 source tree.
expected.add("ac880cd408116e6eb53ba2400abc52970b81f539")
expected.add("95343060f948601930f2e62b919da0789f0830bb")
expected.add("12ab9a8411f5c9df1b5cc73f01c923ad9479c8af")
expected.add("224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c")
# Exact two-file SampleMask successor: the native FC27 SSBO owners are unchanged.
expected.add("150a3a79ca103061f73a9a50ca8f463a3b4712f3")
# Source-only MaxwellDMA successor; current SSBO shader graph is unchanged.
expected.add("fcd62408fdbc33af01a4caebc8fd44c8500b628f")
# Release FC27 NVDRV process-lifetime correction; no SSBO owner changed.
expected.add("b6b9e98e0dd16c4702f21f2e0b5e322126abeecb")
# PS5 FC27 cached-pipeline warm admission expands without touching SSBO source.
expected.add("dbef23055897b1649f83c20cf7a0516e64f3d5cd")
# Exact NS2 SelfController and NUP/IPC successors preserve FC27 shader/SSBO owners.
expected.add("dc526f06d277dfa0a4afa48b4cf8b3153ebe7267")
expected.add("87964d15e91b6b6523c88682e5ca017f6e1a808b")
expected.add("ae6f59a9865a3f4f178c4d836a3e04c93cceb69a")
expected.add("f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0")
expected.add("d22b7066410c627230f9bfa8b3b5be8baff4fcdf")
expected.add("f4f5d53596879960b19a3701bbd2272ef1f3c634")
# Subsequent NX2-only supervisor, VI2, content and account source deltas do
# not change FC27's SSBO shader graph. The immutable blobs are verified below.
expected.add("2873d15edcc36e52fe1d7163684b9f78976200bf")
expected.add("ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3")
# New vendor revision only changes GPU-session HLE table and NIFM comma:
# the SSBO shader owner blobs and CMake source graph are sealed below.
expected.add("716e069f212b89b6fd13af56b0677343cf41ba07")
# Test-only vendor successor: active runtime blobs remain byte-identical.
expected.add("6c15ec8d1143eb1ae3092a2b984f0bc5bfcc364b")
# GPU-time fail-closed successor leaves FC27 shader owners byte-identical.
expected.add("93c3dd6c86627e91999f965c45c05cd8e50e17eb")
expected.add("eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb")
expected.add("93da3b707ef147385380eb0690e0d93fc8e907ad")
expected.add("a6240909b823492d9ff20070c09387a732d83007")
# FC27+NS2 shutdown/trace successor: the complete active SSBO and CMake blobs
# remain byte-sealed below; this pinned vendor was verified against a62409.
expected.add("0390980a5752808dfba7b8edaa7d113cc4e4e6eb")
# Lichii/Eglantine AM window one-shot and LM NS2/NS1 split change no sealed SSBO source.
# Verify shader/BFS owner blobs and CMake selections below before allowing this pin.
expected.add("273680a5b33bff15c9ca12685cfadb2aa15ff9f1")
expected.add("84b9975726092a32d1cb2aa714b96e4f5f85d7c4")
expected.add("84ec89ce112b83603b2095a9f6bb785f8e999ef6")
expected.add("97fa38381d9ce23b63b3bf3751615dc254ab3634")
expected.add("b099bd7cbefaa1a35d6626d4fd3161afcefa1b48")
expected.add("bfdf39014db15f237a16d4a50e6cdfd68bdd87b8")
expected.add("4626d87be155c0b42904610323098c1205515450")
expected.add("c32704e63844449b1c18a03deb2cd92939999b90")
expected.add("fab5ebbfda09ebd3fc414b3127e135c66025ccb8")
expected.add("acb42e2a2b18fee17673d07e06b2f29709de2fb5")
expected.add("99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3")
expected.add("04e252186aa42bacde0899e0c9224035c83a6b0d")
expected.add("44f5b75bc93bcea146ad6fba3ac294405ae8709b")
expected.add("70789b12dea4d72ce9e7f054c5b6f552ec488f5d")
expected.add("9db97fb12db1a390d6b2410f0c18333aa31e37da")
if selected in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd", "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267", "87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
    reviewed_tree = subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    assert reviewed_tree == {
        "ac880cd408116e6eb53ba2400abc52970b81f539": "01c09ec124779e7d976718af09a0e5e94cb4ac20",
        "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
        "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
        "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
            "150a3a79ca103061f73a9a50ca8f463a3b4712f3": "39fb9a3efe65f67115dfcdebe39a55334a702f2d",
            "fcd62408fdbc33af01a4caebc8fd44c8500b628f": "8447712e2cecf661910fd1a32613f0b844ceaeb0",
            "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb": "067c72d30a71a79faefd1ad14876e2a46f02755c",
            "dbef23055897b1649f83c20cf7a0516e64f3d5cd": "9e28e5b83cf9c0f4086a33d6838904353a8fd541",
            "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267": "e21b2c70c00c50fc7d682150cb62e87fe856306c",
            "87964d15e91b6b6523c88682e5ca017f6e1a808b": "c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab",
            "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a": "e125210acec0eaef51c6c038d200cc9c12981ace",
            "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0": "68acadcd14d23135fd02df0a0e508c668917168c",
            "d22b7066410c627230f9bfa8b3b5be8baff4fcdf": "805d74f7ccf0ddf060782615d2bd94bb8d26b412",
            "f4f5d53596879960b19a3701bbd2272ef1f3c634": "e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf",
    }[selected], ("Vendor reviewed source tree drift", selected, reviewed_tree)
expected.add("60fa67b98286bd84bd591987c5690ae9b15bda3f")
expected.add("bf981e9d39d4a908d0d5b6f8407cca814c609bdb")
expected.add("8026fcca228d0feda62ffd9625e16ee0429d621e")
expected.add("887bf44af34999e8b6c5b63dc7c01c6c13b82c8f")
expected.add("1a928783cce2c2692d8fe9fd958400a2de060bbf")
expected.add("9632ac089f8b2d89a6856a42e8fb55206cdba1fa")
if selected in {"b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777"}:
    # AM lifetime successor changes no shader or sparse kernel owner.
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == ("1660883553006cfca7e80465ad5521b4c2ca33b1" if selected == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "668fb8effa6963be062d780e3bd145a5233d6b7e")
    expected.add(selected)
if selected in {"1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777"}:
    assert blob(V/"tests/ns1_r23_18_tir_host.py") == "005280fde5bbd862d64a4def0d17d90a35bbe5e9", (
        "Vendor host-only TextureCache TIR witness drift")
assert selected==gitlink and selected in expected,(selected,gitlink)

bfs=V/"encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h"
active=V/"encore-active/eden-shader/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
pinned=V/"sources/eden/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
assert blob(bfs)=="fa5e7572ef99bba3db17154c63f60dddba7a87c6"
assert blob(active)=="602d45b4d2ad872b138d62ce05f379b5e1103602"
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
assert source.split("bool IsGlobalMemory(",1)[1].split("bool IsGlobalMemoryWrite(",1)[0].count("case IR::Opcode::GlobalAtomicCompareExchange32:")==1
assert "return IR::Opcode::StorageAtomicCompareExchange32;" in source
assert "BreadthFirstSearchPruned(Value value" in header
assert "BreadthFirstSearchPruned" not in pinned.read_text()

# GPU-53: exact maintained SSBO emitter + shared native SPIR-V context.
active_mem=V/"encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
pinned_mem=V/"sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
active_ctx=V/"encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
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
