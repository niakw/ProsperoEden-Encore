#!/usr/bin/env python3
"""R457 exact source graph: guest PTE + raw kernel fill -> resident PA -> GPU.

Host-only structural audit. It does not execute guest code or confirm
physical alias lifetime, PS5 SDK, GPU fences, or first frame.
"""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
vendor="0d2c22172dc82277388f290e3ea14557d3697005"
pinned=subprocess.check_output(["git","rev-parse","HEAD:vendor"],
                               cwd=root,text=True).strip()
assert pinned==vendor,(pinned,vendor)
def read(path): return (root/path).read_text()

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
