#!/usr/bin/env python3
"""N51: exact source-owner parity guard, including PS5 native GPU path."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
ORIG=R/'vendor/encore-active/eden-core/src/video_core/memory_manager.cpp'
PORT=R/'headless/ns2/eglantine/video_core/memory_manager.cpp'
cmake=(R/'headless/CMakeLists.txt').read_text()
def once(s,a,b):
    assert s.count(a)==1, 'native source owner drift: '+a[:80]
    return s.replace(a,b)
def adapt(s):
    inc='#include "video_core/memory_manager.h"'
    s=once(s,inc,inc+'\n#include "video_core/ns2_egl_gpu_range_batch.h"')
    for fn,nxt,pg in (('GPUVAddr MemoryManager::PageTableOp','GPUVAddr MemoryManager::BigPageTableOp','page_size'),
                      ('GPUVAddr MemoryManager::BigPageTableOp','void MemoryManager::BindRasterizer','big_page_size')):
        a,z=s.index(fn),s.index(nxt,s.index(fn)+len(fn))
        q=s[a:z]
        loop='    for (u64 offset{}; offset < size; offset += '+pg+') {'
        old='        if (current_entry_type != entry_type) {\n            rasterizer->ModifyGPUMemory(unique_identifier, current_gpu_addr, '+pg+');\n        }'
        init=('    // Eglantine f9fc1e1: batch only contiguous changed GPU PTE pages.\n'
              '    Eden::NS2::Eglantine::ChangedPageRuns changed_runs('+pg+');\n'
              '    const auto notify_changed = [this](GPUVAddr address, u64 length) {\n'
              '        rasterizer->ModifyGPUMemory(unique_identifier, address, length);\n'
              '    };\n')
        q=once(q,loop,init+loop)
        q=once(q,old,'        changed_runs.Record(current_gpu_addr, current_entry_type != entry_type,\n                            notify_changed);')
        tail=('    kind_map.Map(gpu_addr, gpu_addr + size, kind);' if pg=='page_size'
              else '    {\n        std::unique_lock<std::mutex> lock(guard);')
        q=once(q,tail,'    changed_runs.Flush(notify_changed);\n'+tail)
        s=s[:a]+q+s[z:]
    return s
assert PORT.read_text()==adapt(ORIG.read_text()),'N51 GPU source overlay differs from maintained PS5 owner'
assert 'EDEN_NS2_EGLANTINE_GPU_RANGE_BATCH_EXPERIMENTAL OR' in cmake
assert 'NOT PS5_NATIVE OR NOT EDEN_NS2_METADATA_EXPERIMENTAL OR EDEN_FINAL_RELEASE_PROFILE' in cmake
assert 'list(REMOVE_ITEM video_sources "${EDEN_NATIVE_GPU_MEMORY_MANAGER}")' in cmake
print('N51_NATIVE_GPU_PTE_OWNER_PARITY_PASS')
