#!/usr/bin/env python3
"""R457 exact source graph: guest PTE + raw kernel fill -> resident PA -> GPU.

Host-only structural audit. It does not execute guest code or confirm
physical alias lifetime, PS5 SDK, GPU fences, or first frame.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
# Only the exact historical and reviewed integrated vendor commits are
# admitted. The sparse PTE/slab/GPU publisher owners are byte-identical.
reviewed_vendors={
    "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864",
    "fe9edd661d6f0824c7339865d50aa9cf99cab150",
    "c339fd06f02e42e67d5416ae82194ba619b7ee68",
    "47568425c71d534b72cc966d1500412c9ae4fc16",
    "447e08718c9b6625508da6ce63796ed1f4285d2f",
    "97fdc316fcf5b42e08c26845887f298feac2a424",
    "99ca67babe955398e157c6b28b22a79cbb88967e",
    "7bd7a85e6c1886035c75395c86b05b231375bbf5",
    "7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6",
    "0267753219c4b6a6f3fa086a356b698cd5295f78",
    "78a903a7479f0f58f3cbd3c2fcfd329012a11e10",
    "13ee2fff7be6c0bac225b377a4367b1d0b3073a0",
    "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767",
    "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028",
    "72faa8edd26f6fcb16b08f321211fb94427c4ebb",
    "a946785d1ad02752ae47f9b32032e99bdbb53e02",
    "db33f8ad0c325c84bd80047d992fafa5c2908151",
    "0264f2ae94ef5889e8585171b5bfcb11fd3659ff",
    "bc78a7610425e95d6645685cbd023a67b729ec24",
    "7b7c4d2a37f9b0b248d3f3d6d9cce40596ed0c99",
    "b9f6052a65ef01e23ca4a46ba1654ed3a58cf181",
    "76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3",
    "6f4bb38594b273fe7cc4fba960dfe62cdb9f508e",
    "4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175",
    "9e38066a508716fd959477eccf32c7fb2fde3356",
    "e298a9b05732346141b685eb4c9850bfa02d9e58",
    "f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771",
    "7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0",
    "dfc39fcc087738955b0373b45fa97facdeb2fc47",
    "b806bc497049819e716ef6de81f2a85312b188ce",
    "a0e17271e94342c32b02acdc3199c3f258a8aecf",
    "772f06c8f5b12fdc81066e61f3db2dedfe3eed81",
    "568ae541c07691518e9663aa0fc5f3b017a98d53",
    "dcfe3d2384bd800c6139ede672518ea2c66922a6",
    # Vendor PR #185: shim+tiling header/test/workflow only;
    # sparse kernel and GPU publisher blobs are still checked below.
    "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc", "8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776",
}
reviewed_vendors.add("42b34a5dc46b594cb029362e8f130900adf4424e")
reviewed_vendors.add("77b736148129ffa72c9f6c081695b7c7515c3ed9")
reviewed_vendors.add("4354add020afac574198f63d87167f3022bff9c6")
pinned=subprocess.check_output(["git","rev-parse","HEAD:vendor"],
                               cwd=root,text=True).strip()
selected=subprocess.check_output(["git","-C",str(root/"vendor"),"rev-parse","HEAD"],
                                 text=True).strip()
if pinned in {"17253dc91e9fe1eb2d9980f261f59d227bfcd1a1", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd"}:
    if pinned in {"95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd"}:
        tree_sha = subprocess.check_output(
            ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        assert tree_sha == {
            "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
            "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
            "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
            "150a3a79ca103061f73a9a50ca8f463a3b4712f3": "39fb9a3efe65f67115dfcdebe39a55334a702f2d",
            "fcd62408fdbc33af01a4caebc8fd44c8500b628f": "8447712e2cecf661910fd1a32613f0b844ceaeb0",
            "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb": "067c72d30a71a79faefd1ad14876e2a46f02755c",
            "dbef23055897b1649f83c20cf7a0516e64f3d5cd": "9e28e5b83cf9c0f4086a33d6838904353a8fd541",
        }[pinned], ("R457 vendor tree drift", pinned, tree_sha)
    # Admission requires exact C++ predecessor replay, not a SHA alone.
    sys.path.insert(0,str(root/"vendor/tests"))
    from native_msaa_handle_receipt import (
        GUEST_CACHE_LOCK_SUCCESSOR, INTEGRATED_RASTERIZER,
        restore_guest_cache_lock_successor, blob)
    raster=(root/"vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
    assert blob(raster.encode("utf-8"))==GUEST_CACHE_LOCK_SUCCESSOR
    assert blob(restore_guest_cache_lock_successor(raster).encode("utf-8"))==INTEGRATED_RASTERIZER
    reviewed_vendors.add(pinned)
assert pinned==selected and pinned in reviewed_vendors,(pinned,selected)
def read(path): return (root/path).read_text()
def gitblob(path):
    raw=(root/path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
for path,expected in (
    ("vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp",
     "88f3e2c9220ee03fd6600ef12441d7ece7527c9d"),
    ("vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp",
     "130eb7bd53e29b816bb81fec3fa053a584cd4b6e"),
    ("vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc",
     "852a0272696c7ce182bc05aee92bc7cbb195446b" if selected in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"} else "daf493ce6e863397ec44bfae467c4f7533570477"),
):
    assert gitblob(path)==expected,("Unexpected sparse kernel source owner",path)

if selected in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
    deferred_header = "vendor/encore-active/eden-core/overrides/core/deferred_cached_updates.h"
    assert gitblob(deferred_header) == "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0"
    device = read("vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc")
    assert device.count('::Eden::DeferredCachedUpdates::WaitForPublished();') == 1
    assert device.count('::Eden::DeferredCachedUpdates::active_collector') == 1
    assert device.count('::Eden::DeferredCachedUpdates::BeginPublish();') == 0
    assert device.count('#include "core/deferred_cached_updates.h"') == 1
cmake=read("headless/CMakeLists.txt")
kernel_rel="vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp"
kernel=read(kernel_rel)
# Preserve every upstream kernel behavior except the four PS5 residency
# precommit guards. A new unreviewed kernel semantic delta blocks admission.
import re
baseline=read("vendor/sources/eden/src/core/hle/kernel/k_memory_manager.cpp")
guarded=(r"^#if defined\(PS5_NATIVE\) && "
         r"defined\(EDEN_NS2_SPARSE_BACKING\)\n"
         r"[\s\S]*?^#endif\n")
assert len(re.findall(guarded,kernel,flags=re.MULTILINE))==4
stripped=re.sub(guarded,"",kernel,flags=re.MULTILINE)
stripped=stripped.replace("#include <new>\n#include <limits>\n","")
normalize=lambda source: re.sub(r"\n\s*\n","\n\n",source).strip()
assert normalize(stripped)==normalize(baseline), "kernel semantics drift"
assert "set(EDEN_NS2_SPARSE_BACKING OFF)" in cmake
assert "set(EDEN_NS2_SPARSE_BACKING ON)" in cmake
# KPort and KPageBuffer both write guest physical pages before a process
# maps them. The linked sparse direct-memory owner must commit both first.
assert 'EDEN_R457_SPARSE_SLAB_SRC' in cmake
assert 'list(REMOVE_ITEM eden_r457_sparse_kernel_units' in cmake
assert 'set_property(SOURCE "${EDEN_R457_SPARSE_SLAB_SRC}"' in cmake
subprocess.run([sys.executable, "-B",
    str(root / "vendor/tests/ns2_r457_kernel_slab_precommit_host.py")], check=True)

assert kernel_rel.replace("vendor/","") in cmake
assert 'list(REMOVE_ITEM eden_r457_sparse_kernel_units' in cmake
assert 'hle/kernel/k_memory_manager.cpp' in cmake

# Slabs are direct host writes before the kernel PTE/metadata paths.
# Preserve exactly the original source with only two sparse/native guards,
# including one call before DeviceMemory::GetPointer or freelist initialization.
slab_rel = "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"
slab = read(slab_rel)
slab_baseline = read("vendor/sources/eden/src/core/hle/kernel/init/init_slab_setup.cpp")
slab_guarded = re.findall(guarded, slab, flags=re.MULTILINE)
assert len(slab_guarded) == 3, "slab direct-memory diff exceeded declaration and two reviewed guards"
assert normalize(re.sub(guarded, "", slab, flags=re.MULTILINE)) == normalize(slab_baseline), (
    "unreviewed slab kernel semantics drift")
start = slab.index("    if (size > 0) {")
end = slab.index("    return start + size;", start)
direct_slab = slab[start:end]
assert direct_slab.count("EdenNs2CommitGuestBacking(") == 1
assert direct_slab.index("EdenNs2CommitGuestBacking(") < direct_slab.index(
    "void* backing_kernel_memory")
assert 'throw std::bad_alloc{};' in direct_slab
page_slab = slab.split("void KPageBufferSlabHeap::Initialize(",1)[1]
assert page_slab.count("EdenNs2CommitGuestBacking(") == 1
assert page_slab.index("EdenNs2CommitGuestBacking(") < page_slab.index(
    "KPageBuffer::InitializeSlabHeap(")
assert 'physical - Core::DramMemoryMap::Base, slab_size' in page_slab

assert slab_rel.replace("vendor/", "") in cmake
assert 'hle/kernel/init/init_slab_setup.cpp" eden_r457_sparse_slab_original' in cmake
assert 'TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"' in cmake

for variant in ("memory_native_a32.cpp","memory_native_standard.cpp"):
    owner=read("vendor/encore-active/eden-core/src/core/"+variant)
    begin=owner.index("    void MapMemoryRegion(")
    end=owner.index("    void UnmapRegion(",begin)
    section=owner[begin:end]
    assert section.count("EdenNs2CommitGuestBacking(")==1,variant
    assert section.index("EdenNs2CommitGuestBacking(")<section.index("MapPages(page_table"),variant
    assert 'throw std::bad_alloc{};' in section,variant

metadata=kernel.split("void KMemoryManager::Impl::InitializeOptimizedMemory",1)[1].split(
    "void KMemoryManager::Impl::TrackUnoptimizedAllocation",1)[0]
assert metadata.index("CommitKernelDirectGuestRange(")<metadata.index("GetPointer<u64>(")
assert metadata.index("CommitKernelDirectGuestRange(")<metadata.index("std::memset(")
optimized=kernel.split("bool KMemoryManager::Impl::ProcessOptimizedAllocation",1)[1].split(
    "size_t KMemoryManager::Impl::CalculateManagementOverheadSize",1)[0]
assert optimized.index("CommitKernelDirectGuestRange(")<optimized.index("GetPointer<u64>(")
assert optimized.index("CommitKernelDirectGuestRange(")<optimized.index("std::memset(")
assert 'num_pages > std::numeric_limits<size_t>::max() / PageSize' in optimized
assert 'Core::DramMemoryMap::Base' in kernel

gpu=read("vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc")
mapping=gpu.split("void DeviceMemoryManager<Traits>::Map(",1)[1].split(
    "void DeviceMemoryManager<Traits>::Unmap(",1)[0]
assert mapping.count("AtomicStorePhysical(valid, phys_addr);")==1
assert mapping.index("process_memory->GetPointerSilent(")<mapping.index(
    "AtomicStorePhysical(valid, phys_addr);")
assert gpu.count("AtomicStorePhysical(")==3, "Unexpected new GPU PA publisher: review separately"

physical=read("src/ns2_sparse_guest.cpp")
start=physical.index("    bool Commit(std::size_t offset, std::size_t length)")
end=physical.index("\n};",start)
transaction=physical[start:end]
assert transaction.index("Common::CommitMemoryRange(")<transaction.index(
    "plan.Publish(*admit)")
host=read("src/host_memory.cpp")
assert host.index("if (requested == Ns2Dram)")<host.index(
    "AllocateMemoryPages(requested)")
assert "if (impl->sparse && !impl->sparse->Commit(offset, length))" in host
print("R457_NS2_KERNEL_PTE_GPU_RESIDENCY_CHAIN_SOURCE_PASS"
      " native_runtime_unqualified=1 gpu_fences_unqualified=1")
