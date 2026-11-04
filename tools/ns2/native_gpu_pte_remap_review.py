#!/usr/bin/env python3
"""Exact reverse replay of reviewed small/big-page GPU remap invalidations.

Only N51/P1.2 owns this source. Do not expand an old SHA allowlist to mask
unrelated edits: reverse these exact changes and require the PREVIOUS owner
SHA-1 to be recovered byte for byte in both independent source oracles.
"""
SMALL_OLD = """        [[maybe_unused]] const auto current_entry_type = GetEntry(current_gpu_addr, false);
        SetEntry(current_gpu_addr, entry_type, false);
#ifdef EDEN_NS2_GPU_RANGE_BATCH
        changed_runs.Record(current_gpu_addr, current_entry_type != entry_type,
                            notify_changed);
#else
        if (current_entry_type != entry_type) {
            rasterizer->ModifyGPUMemory(unique_identifier, current_gpu_addr, page_size);
        }
#endif
        if (entry_type == EntryType::Mapped) {
            const DAddr current_dev_addr = dev_addr + offset;
            const auto index = PageEntryIndex(current_gpu_addr, false);
            const u32 sub_value = static_cast<u32>(current_dev_addr >> cpu_page_bits);
            page_table[index] = sub_value;
        }"""
SMALL_NEW = """        const auto current_entry_type = GetEntry(current_gpu_addr, false);
        const auto page_index = PageEntryIndex(current_gpu_addr, false);
        const u32 previous_page = current_entry_type == EntryType::Mapped &&
                                          entry_type == EntryType::Mapped
                                      ? page_table[page_index] : 0;
        const u32 replacement_page = entry_type == EntryType::Mapped
                                         ? static_cast<u32>((dev_addr + offset) >> cpu_page_bits)
                                         : 0;
        const bool mapping_changed = Eden::GpuMemory::NeedsRasterizerUnmap(
            current_entry_type, entry_type, EntryType::Mapped, previous_page, replacement_page);
        SetEntry(current_gpu_addr, entry_type, false);
#ifdef EDEN_NS2_GPU_RANGE_BATCH
        changed_runs.Record(current_gpu_addr, mapping_changed, notify_changed);
#else
        if (mapping_changed) {
            rasterizer->ModifyGPUMemory(unique_identifier, current_gpu_addr, page_size);
        }
#endif
        if (entry_type == EntryType::Mapped) {
            page_table[page_index] = replacement_page;
        }"""
BIG_OLD = """        [[maybe_unused]] const auto current_entry_type = GetEntry(current_gpu_addr, true);
        SetEntry(current_gpu_addr, entry_type, true);
#ifdef EDEN_NS2_GPU_RANGE_BATCH
        changed_runs.Record(current_gpu_addr, current_entry_type != entry_type,
                            notify_changed);
#else
        if (current_entry_type != entry_type) {
            rasterizer->ModifyGPUMemory(unique_identifier, current_gpu_addr, big_page_size);
        }
#endif
        if (entry_type == EntryType::Mapped) {
            const DAddr current_dev_addr = dev_addr + offset;
            const auto index = PageEntryIndex(current_gpu_addr, true);
            const u32 sub_value = static_cast<u32>(current_dev_addr >> cpu_page_bits);
            big_page_table_dev.Set(index, sub_value);"""
BIG_NEW = """        const auto current_entry_type = GetEntry(current_gpu_addr, true);
        const auto page_index = PageEntryIndex(current_gpu_addr, true);
        const u32 previous_page = current_entry_type == EntryType::Mapped &&
                                          entry_type == EntryType::Mapped
                                      ? big_page_table_dev[page_index] : 0;
        const u32 replacement_page = entry_type == EntryType::Mapped
                                         ? static_cast<u32>((dev_addr + offset) >> cpu_page_bits)
                                         : 0;
        const bool mapping_changed = Eden::GpuMemory::NeedsRasterizerUnmap(
            current_entry_type, entry_type, EntryType::Mapped, previous_page, replacement_page);
        SetEntry(current_gpu_addr, entry_type, true);
#ifdef EDEN_NS2_GPU_RANGE_BATCH
        changed_runs.Record(current_gpu_addr, mapping_changed, notify_changed);
#else
        if (mapping_changed) {
            rasterizer->ModifyGPUMemory(unique_identifier, current_gpu_addr, big_page_size);
        }
#endif
        if (entry_type == EntryType::Mapped) {
            const DAddr current_dev_addr = dev_addr + offset;
            const auto index = page_index;
            big_page_table_dev.Set(index, replacement_page);"""

def recover_prior_memory_manager(actual: str) -> str:
    header = '#include "native_paged_scalar.h"\n'
    for new, old in (
        (header + '#include "native_gpu_page_remap.h"\n', header),
        (SMALL_NEW, SMALL_OLD),
        (BIG_NEW, BIG_OLD),
    ):
        assert actual.count(new) == 1, ("Unreviewed GPU remap owner mutation", new[:100])
        actual = actual.replace(new, old, 1)
    assert "native_gpu_page_remap" not in actual and "mapping_changed" not in actual
    return actual
