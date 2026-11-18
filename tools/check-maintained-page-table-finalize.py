#!/usr/bin/env python3
"""Verify exact pinned G16 page-table replacement and source ownership."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
pinned = (root / "vendor/sources/eden/src/core/hle/kernel/k_page_table_base.cpp").read_text()
maintained = (root / "vendor/encore-active/eden-core/src/core/hle/kernel/k_page_table_base.cpp").read_text()
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
# The maintained shipping kernel also owns the NS2 address-space extension.
# Rebuild its exact reviewed delta from pinned Eden before applying G16:
# legacy NS1 callers must continue to select is_switch2=False.
legacy_signature = """Result KPageTableBase::InitializeForProcess(Svc::CreateProcessFlag as_type, bool enable_aslr, bool enable_das_merge, bool from_back, KMemoryManager::Pool pool, KProcessAddress code_address, size_t code_size, KSystemResource* system_resource, KResourceLimit* resource_limit, Core::Memory::Memory& memory, KProcessAddress aslr_space_start) {
    // Calculate region extents."""
ns2_signature = """Result KPageTableBase::InitializeForProcess(Svc::CreateProcessFlag as_type, bool enable_aslr, bool enable_das_merge, bool from_back, KMemoryManager::Pool pool, KProcessAddress code_address, size_t code_size, KSystemResource* system_resource, KResourceLimit* resource_limit, Core::Memory::Memory& memory, KProcessAddress aslr_space_start) {
    R_RETURN(this->InitializeForProcess(as_type, enable_aslr, enable_das_merge, from_back, pool,
                                        code_address, code_size, system_resource, resource_limit,
                                        memory, aslr_space_start, false));
}

Result KPageTableBase::InitializeForProcess(Svc::CreateProcessFlag as_type, bool enable_aslr, bool enable_das_merge, bool from_back, KMemoryManager::Pool pool, KProcessAddress code_address, size_t code_size, KSystemResource* system_resource, KResourceLimit* resource_limit, Core::Memory::Memory& memory, KProcessAddress aslr_space_start, bool is_switch2) {
    // Calculate region extents."""
old_extent = "return KAddressSpaceInfo::GetAddressSpaceSize(m_address_space_width, type);"
ns2_extent = "return KAddressSpaceInfo::GetAddressSpaceSize(m_address_space_width, type, is_switch2);"
assert pinned.count(legacy_signature) == 1, "upstream process initializer changed"
assert pinned.count(old_extent) == 1, "upstream address-space extent changed"
expected = pinned.replace(legacy_signature, ns2_signature, 1).replace(old_extent, ns2_extent, 1)
assert expected.count(original) == 1, "G16 finalizer anchor changed"
expected = expected.replace(original, replacement, 1)
assert maintained == expected, "G16/NS2 exact source parity broken"
assert maintained.count("m_system.Kernel().IsShuttingDown()") >= 1
assert 'write_derived("${PORT_BUILD_DIR}/k_page_table_base.cpp"' not in cm
assert 'file(READ "${PROJECT_SOURCE_DIR}/src/core/hle/kernel/k_page_table_base.cpp"' not in cm
assert 'list(REMOVE_ITEM page_table_core_sources hle/kernel/k_page_table_base.cpp)' in cm
assert 'list(APPEND page_table_core_sources "${EDEN_MAINTAINED_PAGE_TABLE}")' in cm
assert 'set_property(TARGET core PROPERTY SOURCES "${page_table_core_sources}")' in cm
assert 'vendor/encore-active/eden-core/src/core/hle/kernel/k_page_table_base.cpp' in cm
print("ENCORE_MAINTAINED_PAGE_TABLE_FINALIZE_PASS G16=retired parity=exact")
