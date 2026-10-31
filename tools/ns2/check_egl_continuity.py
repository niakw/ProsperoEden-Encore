#!/usr/bin/env python3
"""N50: assert Eglantine continuity patch only extends the pinned PS5 owner."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc'
PORT=ROOT/'headless/ns2/eglantine/core/device_memory_manager.inc'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
inc='#include "core/device_memory_manager.h"'
map_anchor='    tracked_entries.CommitRegion(start_page_d, start_page_d + num_pages);\n    for (size_t i = 0; i < num_pages; i++) {'
unmap_anchor='    tracked_entries.CommitRegion(start_page_d, start_page_d + num_pages); // should already be committed, but just in case\n    for (size_t i = 0; i < num_pages; i++) {'
call='''    // Eglantine PR #48: an old page run must not cross a changed map
    // range. The pinned PS5 atomic fields and reverse-map policy stay intact.
    Eden::NS2::Eglantine::CutContinuityAt(start_page_d,
        [&](size_t index) { return AtomicLoadContinuity(tracked_entries[index]); },
        [&](size_t index, u32 new_count) {
            AtomicStoreContinuity(tracked_entries.GetUnchecked(index), new_count);
        });
'''
original=SRC.read_text()
assert all(original.count(x)==1 for x in (inc,map_anchor,unmap_anchor))
expected=original.replace(inc,inc+'\n#include "core/ns2_egl_continuity_guard.h"')
expected=expected.replace(map_anchor,'    tracked_entries.CommitRegion(start_page_d, start_page_d + num_pages);\n'+call+'    for (size_t i = 0; i < num_pages; i++) {')
expected=expected.replace(unmap_anchor,'    tracked_entries.CommitRegion(start_page_d, start_page_d + num_pages); // should already be committed, but just in case\n'+call+'    for (size_t i = 0; i < num_pages; i++) {')
assert PORT.read_text()==expected, "PS5 memory owner drift; do not compile"
assert 'EDEN_NS2_EGLANTINE_CONTINUITY_EXPERIMENTAL OR' in CMAKE
assert 'target_include_directories(core BEFORE PUBLIC "${eden_ns2_egl_memory_root}")' in CMAKE
assert 'target_include_directories(video_core BEFORE PRIVATE "${eden_ns2_egl_memory_root}")' in CMAKE
print("N50_EGLANTINE_DEVICE_MEMORY_OWNER_PARITY_PASS")
