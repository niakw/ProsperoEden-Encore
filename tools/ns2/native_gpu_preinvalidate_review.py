#!/usr/bin/env python3
"""P1.2/N51: reverse only the audited pre-invalidation GPU memory diff.

A cache unmap must retire the previous backing before any PTE replacement.
The reviewed 4K/big-page source diff restores the exact predecessor blob;
changing both the code and this witness still requires predecessor parity.
"""
import hashlib
import runpy
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools/ns2/p1_2_gpu_preinvalidate.patch"
PREVIOUS_SHA = "b43eae6863527b47b98892f5bfa68b7f685c0b28"
PATCH_SHA = "f778404d0de2bb98e1f68428113b4c4bffe1eafe"
SOURCE = Path("encore-active/eden-core/src/video_core/memory_manager.cpp")

def blob(content: str) -> str:
    data = content.encode()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def recover_prior_memory_manager(actual: str) -> str:
    # Authentic new 4K/big-page range bounds are removed only on the audit copy.
    if blob(actual) == "c0ba367f8c4452a5c49015ae0fe201ae7a7bdb86":
        addition = "    // Do not publish out-of-range GPU PTEs, even for a caller that bypasses\n    // the ioctl layer's range validation. Match Eglantine's native guard.\n    if (size != 0 && (gpu_addr >= address_space_size || size > address_space_size - gpu_addr)) {\n        LOG_ERROR(HW_GPU, \"GPU mapping {:#x}+{:#x} is outside the {:#x}-byte address space\",\n                  gpu_addr, size, address_space_size);\n        return gpu_addr;\n    }\n"
        assert actual.count(addition) == 2, "GPU range guard drift"
        actual = actual.replace(addition, "")
        assert blob(actual) == "9a9479580fb2037cc49fe2ed5c6a284331a78b97", "GPU guard predecessor drift"
    # NS2 Worker 212 may change PTE kind without changing physical backing.
    # Reverse the exact reviewed successor before the older owner replay.
    if "A native kind change can reinterpret" in actual:
        assert blob(actual) == "9a9479580fb2037cc49fe2ed5c6a284331a78b97", "unreviewed kind-change invalidation owner"
        old_check = "        const bool mapping_changed = Eden::GpuMemory::NeedsRasterizerUnmap(\n            current_entry_type, entry_type, EntryType::Mapped, previous_page, replacement_page);"
        new_check = "        // A native kind change can reinterpret the same physical page. Retire\n        // the old cache owner while both the PTE and the old kind are visible.\n        // The lookup is only needed for Mapped -> Mapped with unchanged backing.\n        const bool mapping_changed = Eden::GpuMemory::NeedsRasterizerUnmap(\n            current_entry_type, entry_type, EntryType::Mapped, previous_page, replacement_page) ||\n            (current_entry_type == EntryType::Mapped && entry_type == EntryType::Mapped &&\n             GetPageKind(current_gpu_addr) != kind);"
        assert actual.count(new_check) == 2
        actual = actual.replace(new_check, old_check)
        # Only the first writer (4K) gained the existing kind-map guard.
        old_writer = "    kind_map.Map(gpu_addr, gpu_addr + size, kind);\n    gpu_page_table_revision.fetch_add(1, std::memory_order_release);"
        guarded_writer = "    {\n        std::unique_lock<std::mutex> lock(guard);\n        kind_map.Map(gpu_addr, gpu_addr + size, kind);\n    }\n    gpu_page_table_revision.fetch_add(1, std::memory_order_release);"
        assert actual.count(guarded_writer) == 2
        actual = actual.replace(guarded_writer, old_writer, 1)
        assert blob(actual) == "4fc858082c9528520027cd416ac1a942dbce8bc5", "kind-change predecessor drift"
    # FC27 P1 merged physically touching DMA invalidation spans before
    # BufferCache ownership claims, without changing page protection or the
    # NVN shim. Peel only its exact 1739-byte audited addition before older
    # syncpoint, range-cache and PTE historical parity checks.
    if "A GPU-addressed CB_DATA batch may revisit" in actual:
        assert blob(actual) == "4fc858082c9528520027cd416ac1a942dbce8bc5", (
            "unreviewed merged P1 GPU invalidation owner")
        added = "#ifdef PS5_NATIVE\n        // A GPU-addressed CB_DATA batch may revisit the same physical pages\n        // through separate GPU ranges or aliases. All writes have already\n        // reached guest memory, so combine ONLY overlapping/touching device\n        // intervals before the existing CPU-write ownership claim. This\n        // shortens GPU-held BufferCache/TextureCache work without moving\n        // page protection, skipping invalidation, or changing draw ordering.\n        // Keep disjoint physical ranges separate (including sparse mappings).\n        if (page_stash2.size() > 1) {\n            std::sort(page_stash2.begin(), page_stash2.end(),\n                      [](const auto& lhs, const auto& rhs) {\n                          return lhs.first < rhs.first;\n                      });\n            size_t retained = 0;\n            for (size_t read = 0, count = page_stash2.size(); read < count; ++read) {\n                const auto [addr, size] = page_stash2[read];\n                if (retained != 0 && size != 0) {\n                    auto& previous = page_stash2[retained - 1];\n                    // The GMMU returns valid, bounded device spans. The\n                    // subtraction also avoids comparing overflow-prone ends.\n                    const DAddr offset = addr - previous.first;\n                    if (previous.second != 0 && offset <= previous.second) {\n                        previous.second = std::max(previous.second,\n                                                   static_cast<size_t>(offset) + size);\n                        continue;\n                    }\n                }\n                page_stash2[retained++] = {addr, size};\n            }\n            page_stash2.resize(retained);\n        }\n#endif\n"
        assert actual.count(added) == 1, "FC27 P1 physical invalidation hunk drift"
        actual = actual.replace(added, "", 1)
        assert blob(actual) == "46f0157cc2fd61e63220461261d851b8429ea4fd", (
            "FC27 P1 GPU source predecessor parity")
    # Lichii 12125bc / vendor 8157c79 adds a read-only NVN syncpoint
    # virtual shim to this same maintained owner after the range-cache review.
    # Peel it first, proving the complete successor and predecessor blobs.
    if "native_syncpoint_shim" in actual:
        recover_shim = runpy.run_path(
            str(ROOT / "tools/ns2/native_syncpoint_shim_review.py")
        )["recover_before_syncpoint_shim"]
        actual = recover_shim(actual)
    if "gpu_page_table_revision" in actual:
        # Peel back only the pinned, independently reviewed performance
        # extension; the original 4K/big-page predecessor hash still MUST
        # match byte-for-byte under the existing reverse-patch chain.
        recover = runpy.run_path(
            str(ROOT / "tools/ns2/native_gpu_range_cache_review.py")
        )["recover_before_contiguous_cache"]
        actual = recover(actual)
    assert blob(PATCH.read_text()) == PATCH_SHA, "unreviewed GPU pre-invalidation patch"
    assert actual.count("All old mappings have been evicted") == 1
    assert actual.count("Commit big-page backing only after the old cache owner") == 1
    assert actual.count("NeedsRasterizerUnmap(") == 2
    with tempfile.TemporaryDirectory(prefix="encore-preinvalidate-replay-") as tmp:
        target = Path(tmp) / SOURCE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(actual)
        result = subprocess.run(["git", "apply", "--reverse", str(PATCH)],
            cwd=tmp, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        previous = target.read_text()
    assert blob(previous) == PREVIOUS_SHA, "P1.2 predecessor bytes not recovered"
    return previous
