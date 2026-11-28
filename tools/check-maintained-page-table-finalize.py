#!/usr/bin/env python3
"""Verify exact pinned G16 page-table replacement and source ownership."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
pinned = (root / "vendor/sources/eden/src/core/hle/kernel/k_page_table_base.cpp").read_text()
maintained = (root / "vendor/encore-active/eden/src/core/hle/kernel/k_page_table_base.cpp").read_text()
cm = (root / "headless/CMakeLists.txt").read_text()
original = """        // Get physical pages.
        KPageGroup pg(m_system.Kernel(), m_block_info_manager);
        this->MakePageGroup(pg, addr, size / PageSize);

        // Free the pages.
        pg.CloseAndReset(m_system.Kernel());
    };"""
replacement = """        // The memory manager is recreated after a kernel shutdown.
        if (m_system.Kernel().IsShuttingDown()) {
            return;
        }

""" + original
assert pinned.count(original) == 1, "upstream finalizer changed"
# The current reviewed NS2 kernel uses Lichii/Eglantine's 64 GiB alias
# geometry, with 32 GiB VAMM (InfoType 29/30). The experimental #1773
# generation-specific 128 GiB alias and its extra InitializeForProcess bool
# were deliberately removed from shipping vendor. Do not resurrect that ABI.
# The selected page-table translation unit must contain the exact G16 lifetime
# guard and the reviewed GPU-accessible attribute permission check.
expected = pinned.replace(original, replacement, 1)
# 7130ede3: GPU-accessible also requires a changeable memory state.
attribute_before = "        (True(mask & KMemoryAttribute::Uncached) ? KMemoryState::FlagCanChangeAttribute\n                                                 : KMemoryState::None) |"
attribute_after = "        (True(mask & (KMemoryAttribute::Uncached | KMemoryAttribute::GpuAccessible))\n             ? KMemoryState::FlagCanChangeAttribute\n             : KMemoryState::None) |"
assert expected.count(attribute_before) == 1
assert maintained == expected.replace(attribute_before, attribute_after, 1), (
    "G16 finalizer / GPU attribute permission delta drift")
page_h = (root / "vendor/encore-active/eden/src/core/hle/kernel/k_page_table_base.h").read_text()
address_cpp = (root / "vendor/encore-active/eden/src/core/hle/kernel/k_address_space_info.cpp").read_text()
assert maintained.count("Result KPageTableBase::InitializeForProcess(") == 1
assert "bool is_switch2" not in page_h
assert "bool is_switch2" not in maintained
assert "aslr_space_start, is_switch2" not in maintained
assert address_cpp.count(
    "std::size_t KAddressSpaceInfo::GetAddressSpaceSize(size_t width, KAddressSpaceInfo::Type type)"
) == 1
assert ".size = 64_GiB           , .type = KAddressSpaceInfo::Type::Alias" in address_cpp
assert "Ns2HeapInfo" in address_cpp and ".size = 16_GiB" in address_cpp
assert maintained.count("m_system.Kernel().IsShuttingDown()") >= 1
assert 'write_derived("${PORT_BUILD_DIR}/k_page_table_base.cpp"' not in cm
assert 'file(READ "${PROJECT_SOURCE_DIR}/src/core/hle/kernel/k_page_table_base.cpp"' not in cm
assert 'list(REMOVE_ITEM page_table_core_sources hle/kernel/k_page_table_base.cpp)' in cm
assert 'list(APPEND page_table_core_sources "${EDEN_MAINTAINED_PAGE_TABLE}")' in cm
assert 'set_property(TARGET core PROPERTY SOURCES "${page_table_core_sources}")' in cm
assert 'vendor/encore-active/eden/src/core/hle/kernel/k_page_table_base.cpp' in cm
print("ENCORE_MAINTAINED_PAGE_TABLE_FINALIZE_PASS G16=retired parity=exact ns2_alias=64GiB obsolete_128GiB_ABI=absent")
