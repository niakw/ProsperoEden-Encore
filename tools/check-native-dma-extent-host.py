#!/usr/bin/env python3
"""Source parity and actual C++ DMA extent arithmetic under ASan/UBSan."""
from pathlib import Path
import shutil,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
def read(p):return (root/p).read_text()
pinned=read("vendor/sources/eden/src/video_core/engines/maxwell_dma.cpp")
native=read("vendor/encore-active/eden/src/video_core/engines/maxwell_dma.cpp")
vulkan=read("vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp")
bridge=read("vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_rasterizer_deferred.cpp")
cm=read("headless/CMakeLists.txt")
wf=read(".github/workflows/encore-core-preflight.yml")
# The merged NS1/NS2 MaxwellDMA has 18 major reviewed source groups over
# the old R23 native owner: 2D remap, mixed GPU/physical aliases, bounded
# tiled/1D copies, range checks and register guards. The frozen historic
# reconstruction below remains valid only for its own source generation.
# The active generation is checked by full Git blob and real host C++ fixtures.
def selected_sha(value):
    import hashlib
    raw = value.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
integrated_dma = selected_sha(native) in {
    "0c186d79194135a5d0b300c3a8a6fb0aa503810b",
    "df2ced96bc384af23e0529f8ab72eba8000a0995",
    "cb40e4c0de66f8f9d5f6126e6cf898fabacd8805",
    "a2979cc01cdd7679e71af373d187d08302355b9b",
    "3eb6d0462cde2cdcef613b2bf89d74574c18ea01",
    "d083d3298b3fb11373d7a7fc164a42ba92bdb2b5",
    "1fe0b4f25d6f4bbd24406e2f929868151d32c133",
}
if selected_sha(native) == "cb40e4c0de66f8f9d5f6126e6cf898fabacd8805":
    import re
    calls = re.findall(r"(?m)^\s*(?:Unswizzle|Swizzle)Subrect\([\s\S]*?\);", native)
    assert len(calls) == 9 and all(c.count("memory_manager.UsesNativeTiling()") == 1 for c in calls)
    assert "const u64 aligned_depth =" in native and "dst_size != dst_size_wide" in native
if selected_sha(native) in {
    "a2979cc01cdd7679e71af373d187d08302355b9b",
    "3eb6d0462cde2cdcef613b2bf89d74574c18ea01",
    "d083d3298b3fb11373d7a7fc164a42ba92bdb2b5",
    "1fe0b4f25d6f4bbd24406e2f929868151d32c133",
}:
    # Exact reviewed GOB3D successors use the same authenticated
    # source decoder; the new per-side Z arguments are not present in
    # historical Eden, so never replay them as an old patch hunk.
    import re
    calls = re.findall(r"(?m)^\s*(?:Unswizzle|Swizzle)Subrect\([\s\S]*?\);", native)
    assert len(calls) == 9 and all(c.count("memory_manager.UsesNativeTiling()") == 1 for c in calls)
    z_calls = sum(bool(re.search(r"memory_manager\.UsesNativeTiling\(\),\s*(?:regs\.)?(?:src|dst)(?:_params)?\.layer", c)) for c in calls)
    expected_z = {
        "a2979cc01cdd7679e71af373d187d08302355b9b": 4,
        "3eb6d0462cde2cdcef613b2bf89d74574c18ea01": 6,
        "d083d3298b3fb11373d7a7fc164a42ba92bdb2b5": 9,
        "1fe0b4f25d6f4bbd24406e2f929868151d32c133": 9,
    }[selected_sha(native)]
    # Remapped B0B5 reads layers through regs.src/dst_params;
    # the six other DMA paths use local source/destination parameter aliases.
    assert z_calls == expected_z, (z_calls, expected_z)
    assert "MAX_SOFTWARE_TILED_DMA_BYTES" in native
    assert "const u64 aligned_depth =" in native
    assert "std::vector<u8> tiled_dst" in native
if selected_sha(native) == "df2ced96bc384af23e0529f8ab72eba8000a0995":
    assert "const u64 aligned_depth =" in native
    assert "const u64 source_rows =" in native
    assert "dst_size != dst_size_wide" in native
    assert "regs.dst_params.block_size.depth > 5" in native
if integrated_dma:
    helper_begin = "// Signed 2D pitch geometry and device-address overlap are shared by"
    helper_end = "} // namespace\n\nMaxwellDMA::MaxwellDMA"
    assert native.count(helper_begin) == native.count(helper_end) == 1
    helper = native[native.index(helper_begin):native.index(helper_end)]
    for selected_guard in (
        "bool PitchDmaPhysicalOverlap(", "bool DmaSoftwareOverlap(",
        "bool CopyPitchDmaPlain(", "CanCoalescePitchDma(",
        "memory.GpuToCpuAddress(address)", "memory.IsFullyMappedRange(",
        "MAX_PHYSICAL_SEGMENTS = 16384", "CopyPitchRemap(",
        "memory.ReadBlock(", "memory.WriteBlock(",
        "std::vector<u8> snapshot",
    ):
        assert selected_guard in helper, ("Merged DMA guard drift", selected_guard)
    for path in (
        "bool MaxwellDMA::CopyBlockLinearRemap() {",
        "void MaxwellDMA::CopyBlockLinearToPitch() {",
        "void MaxwellDMA::CopyBlockLinearToBlockLinear() {",
    ):
        assert path in native, ("Merged native DMA entry lost", path)
    for token in (
        "MAX_ALIAS_SNAPSHOT",
        "memory_manager.IsFullyMappedRange(regs.offset_out",
        "memory_manager.WriteBlock(regs.offset_out, snapshot.data(), count)",
        "if (!CopyPitchDmaPlain(memory_manager, regs.offset_in, regs.offset_out,",
    ):
        assert token in native, ("Bounded guest DMA path removed", token)
    # Full blob locks all source bytes. Independent F04 and B0B5 tests
    # compile both real selected copy methods in O0/O2 separately.
    for test in (
        "tools/check-native-dma-pitch-remap-host.py",
        "tools/check-native-dma-tiled-remap-host.py",
        "tools/check-fc27-f04-native-remap-dma-upload-chain-host.py",
    ):
        assert (root / test).is_file(), ("Missing current DMA host gate", test)
    print("NATIVE_DMA_INTEGRATED_SOURCE_PASS",
          "selected=1 full_blob=1 physical_alias=1 bounded_remap=1")
else:
    o="    dst_operand.pitch = static_cast<u32>(std::abs(regs.pitch_out));"
    n="    // Widen before absolute value: s32 minimum cannot be negated in s32.\n    dst_operand.pitch = static_cast<u32>(std::abs(static_cast<s64>(regs.pitch_out)));"
    assert pinned.count(o)==1
    expected=pinned.replace(o,n)
    pairs=[
    ("    const size_t dst_size = dst_operand.pitch * regs.line_count;",
    """    const u64 dst_size_wide = static_cast<u64>(dst_operand.pitch) * regs.line_count;
        if (dst_size_wide > static_cast<u64>(~u32{0})) {
            LOG_WARNING(Render_OpenGL, "Oversized DMA linear destination");
            return;
        }
        const size_t dst_size = static_cast<size_t>(dst_size_wide);"""),
    ("    const size_t src_size = static_cast<size_t>(regs.pitch_in) * regs.line_count;",
    """    const u64 src_size_wide = static_cast<u64>(regs.pitch_in) * regs.line_count;
        if (src_size_wide > static_cast<u64>(~u32{0})) {
            LOG_WARNING(Render_OpenGL, "Oversized DMA linear source");
            return;
        }
        const size_t src_size = static_cast<size_t>(src_size_wide);"""),
    ("""    const u32 pitch = x_elements * bytes_per_pixel;
        const size_t mid_buffer_size = pitch * regs.line_count;""",
    """    const u64 pitch_wide = static_cast<u64>(x_elements) * bytes_per_pixel;
        const u64 max_transfer = static_cast<u64>(~u32{0});
        if (pitch_wide > max_transfer ||
            (regs.line_count != 0 && pitch_wide > max_transfer / regs.line_count)) {
            LOG_WARNING(Render_OpenGL, "Oversized DMA intermediate buffer");
            return;
        }
        const u32 pitch = static_cast<u32>(pitch_wide);
        const size_t mid_buffer_size = static_cast<size_t>(pitch_wide * regs.line_count);""")]
    for a,b in pairs:
     assert expected.count(a)==1
     expected=expected.replace(a,b)
    # An exact maintained-source parity extension: source is pinned plus
    # only the audited extent fixes and the non-overlap contiguous DMA fold.
    assert expected.count("using namespace Texture;" + chr(10)*2)==1
    expected=expected.replace("using namespace Texture;" + chr(10)*2, "using namespace Texture;" + chr(10)*2 + "namespace {\n// Fold a row-wise DMA into one guest-memory copy only when every row is\n// contiguous, both byte ranges are representable and do not overlap.\nconstexpr bool CanCoalescePitchDma(u64 source, u64 dest, u32 width, u32 rows,\n                                   s64 pitch_in, s64 pitch_out, u64& total) noexcept {\n    total = 0;\n    if (width == 0 || rows == 0 || pitch_in != static_cast<s64>(width) ||\n        pitch_out != static_cast<s64>(width) ||\n        width > (~u32{0}) / rows) {\n        return false;\n    }\n    const u64 bytes = static_cast<u64>(width) * rows;\n    if (source > ~u64{0} - bytes || dest > ~u64{0} - bytes) {\n        return false;\n    }\n    if (!(source + bytes <= dest || dest + bytes <= source)) {\n        return false;\n    }\n    total = bytes;\n    return true;\n}\n} // namespace\n\n")
    original_pitch_loop="        if (is_src_pitch && is_dst_pitch) {\n            for (u32 line = 0; line < regs.line_count; ++line) {\n                const GPUVAddr source_line =\n                    regs.offset_in + static_cast<size_t>(line) * regs.pitch_in;\n                const GPUVAddr dest_line =\n                    regs.offset_out + static_cast<size_t>(line) * regs.pitch_out;\n                memory_manager.CopyBlock(dest_line, source_line, regs.line_length_in);\n            }\n        } else {"
    folded_pitch_loop="        if (is_src_pitch && is_dst_pitch) {\n            if (!CopyPitchDmaPlain(memory_manager, regs.offset_in, regs.offset_out,\n                                   regs.pitch_in, regs.pitch_out, regs.line_length_in,\n                                   regs.line_count)) {\n                LOG_WARNING(Render_OpenGL, \"Unmapped or oversized aliasing pitch DMA\");\n                AssertFailSoftImpl();\n            }\n        } else {"
    assert expected.count(original_pitch_loop)==1
    expected=expected.replace(original_pitch_loop,folded_pitch_loop)
    # Correct the shipping CONST_A layout for B0B5 component sizes 1/2/3/4.
    # Compare the reviewed whole-source replacement, not a disabled test-only helper.
    old_remap = """            ASSERT(component_size == 1 || component_size == 2 || component_size == 4);
                if (component_size == 4) {
                    accelerate.BufferClear(regs.offset_out, regs.line_length_in, regs.remap_const.remap_consta_value);
                }
                read_buffer.resize_destructive(regs.line_length_in * sizeof(u32));
                std::ranges::fill(std::span<u32>(reinterpret_cast<u32*>(read_buffer.data()), regs.line_length_in), regs.remap_const.remap_consta_value);
                memory_manager.WriteBlockUnsafe(regs.offset_out, reinterpret_cast<u8*>(read_buffer.data()), static_cast<size_t>(regs.line_length_in) * component_size);"""
    new_remap = """            ASSERT(component_size >= 1 && component_size <= 4);
                const u64 byte_count = static_cast<u64>(regs.line_length_in) * component_size;
                if (byte_count != 0) {
                    // A guest-controlled clear can span GiBs. Validate its whole
                    // GMMU destination before ANY accelerated or CPU write, and
                    // bound temporary memory independently of LINE_LENGTH_IN.
                    if (byte_count > (std::numeric_limits<size_t>::max)() ||
                        !memory_manager.IsFullyMappedRange(regs.offset_out,
                                                           static_cast<size_t>(byte_count))) {
                        LOG_WARNING(Render_OpenGL, "Unmapped or oversized CONST_A DMA clear");
                        AssertFailSoftImpl();
                    } else {
                        if (component_size == 4) {
                            accelerate.BufferClear(regs.offset_out, regs.line_length_in,
                                                   regs.remap_const.remap_consta_value);
                        }
                        // A normal guest write notifies the TextureCache and
                        // BufferCache. WriteBlockUnsafe left cached textures stale,
                        // even though it wrote the right bytes to CPU backing.
                        constexpr size_t SCRATCH_BYTES = 64 * 1024;
                        const size_t chunk_elements = SCRATCH_BYTES / component_size;
                        const size_t chunk_bytes = chunk_elements * component_size;
                        read_buffer.resize_destructive(chunk_bytes);
                        u8* const bytes = read_buffer.data();
                        const u32 value = regs.remap_const.remap_consta_value;
                        if (component_size == 4) {
                            std::ranges::fill(
                                std::span<u32>(reinterpret_cast<u32*>(bytes), chunk_elements),
                                value);
                        } else {
                            for (size_t element = 0; element < chunk_elements; ++element) {
                                const size_t base = element * component_size;
                                for (u32 byte = 0; byte < component_size; ++byte) {
                                    bytes[base + byte] = static_cast<u8>(value >> (byte * 8));
                                }
                            }
                        }
                        for (u64 offset = 0; offset < byte_count;) {
                            const size_t count = static_cast<size_t>(
                                (std::min)(byte_count - offset, static_cast<u64>(chunk_bytes)));
                            memory_manager.WriteBlock(regs.offset_out + offset, bytes, count);
                            offset += count;
                        }
                    }
                }"""
    assert expected.count(old_remap)==1
    expected=expected.replace(old_remap,new_remap)
    # The native copy engine now supports all pitch-linear B0B5 component
    # selectors. Rebuild from the immutable Eden baseline plus prior reviewed
    # deltas, then insert the exact selected CPU-remap owner with a locked
    # checksum and semantic anchors. Everything else remains byte-identical.
    def fnv1a32(text):
        h=2166136261
        for char in text:
            h=((h ^ ord(char)) * 16777619) & 0xffffffff
        return h
    include_anchor='#include "common/algorithm.h"'
    extra_includes='#include <algorithm>\\n#include <array>\\n#include <limits>\\n#include <vector>\\n\\n'
    extra_includes=extra_includes.replace('\\n','\n')
    assert expected.count(include_anchor)==1
    expected=expected.replace(include_anchor,extra_includes+include_anchor,1)
    helper_begin='// Signed 2D pitch geometry and device-address overlap are shared by'
    helper_end='} // namespace\\n\\nMaxwellDMA::MaxwellDMA'.replace('\\n','\n')
    assert native.count(helper_begin)==1 and native.count(helper_end)==1
    helper=native[native.index(helper_begin):native.index(helper_end,native.index(helper_begin))]
    assert fnv1a32(helper)==2169658669 and len(helper)==16806, "Reviewed B0B5 helper changed"
    for token in ('Swizzle::NO_WRITE','Swizzle::CONST_A','Swizzle::CONST_B',
                  'std::vector<u8> snapshot', 'memory.ReadBlock',
                  'memory.WriteBlock','CanCoalescePitchDma',
                  'const u64 src_stride', 'const u64 dst_stride',
                  'const bool virtual_overlap', 'bool PitchDmaPhysicalOverlap(',
                  'constexpr bool PitchDmaEnvelope(', 'bool CopyPitchDmaPlain(', 'bool DmaSoftwareOverlap(',
                  'memory.GpuToCpuAddress(src_begin)',
                  'memory.GpuToCpuAddress(address)',
                  'MAX_PHYSICAL_SEGMENTS = 16384',
                  'const bool overlap = virtual_overlap ||',
                  'memory.IsFullyMappedRange(PitchDmaRowAddress(source',
                  'memory.IsFullyMappedRange(PitchDmaRowAddress(destination'):
        assert token in helper, token
    end_anchor='} // namespace\\n\\nMaxwellDMA::MaxwellDMA'.replace('\\n','\n')
    assert expected.count(end_anchor)==1
    expected=expected.replace(end_anchor,'\n'+helper+end_anchor,1)
    launch_start='    if (launch.remap_enable != 0 &&'
    launch_end='    if (launch.multi_line_enable) {'
    assert native.count(launch_start)==1
    insert=native[native.index(launch_start):native.index(launch_end,native.index(launch_start))]
    assert fnv1a32(insert)==933595590, "Selected B0B5 launch guard changed"
    assert 'CopyPitchRemap(memory_manager, regs.remap_const' in insert
    assert expected.count(launch_end)==1
    expected=expected.replace(launch_end,insert+launch_end,1)
    # The reviewed GOB-tiled 2D remap handler lives in the same selected TU;
    # do not misclassify the old raw-byte fallback as a second implementation.
    tiled_start='    if (launch.multi_line_enable != 0 && launch.remap_enable != 0 &&'
    assert native.count(tiled_start)==1
    tiled_launch=native[native.index(tiled_start):native.index(launch_end,native.index(tiled_start))]
    assert fnv1a32(tiled_launch)==695814491, "Reviewed tiled remap dispatch changed"
    assert 'if (!CopyBlockLinearRemap())' in tiled_launch
    expected=expected.replace(launch_end,tiled_launch+launch_end,1)
    method_start="bool MaxwellDMA::CopyBlockLinearRemap() {"
    method_end="void MaxwellDMA::CopyBlockLinearToPitch() {"
    assert native.count(method_start)==1 and native.count(method_end)==1
    tiled_method=native[native.index(method_start):native.index(method_end)]
    assert fnv1a32(tiled_method)==1662245954, "Reviewed tiled remap implementation changed"
    for proof in ("UnswizzleSubrect(", "SwizzleSubrect(", "IsFullyMappedRange(",
                  "needs_destination", "padded_width > MAX_BYTES / padded_height",
                  "memory_manager.WriteBlock(", "std::vector<u8> linear_src",
                  "std::vector<u8> linear_dst"):
        assert proof in tiled_method, proof
    expected=expected.replace(method_end,tiled_method+method_end,1)
    # Restore the complete historical 1D tiled branch from the immutable vendor,
    # then apply the byte-exact corrected native owner. The older two 16-byte loops
    # could overrun short transfers and overwrite unread aliased input.
    legacy_1d_start="            if (!is_src_pitch && is_dst_pitch) {"
    live_1d_start="            if (is_src_pitch != is_dst_pitch) {"
    # Include both the tiled and ordinary 1D branches: the ordinary path now
    # snapshots physical GMMU aliases before choosing Vulkan or cached CPU writes.
    end_1d="\n        }\n    }\n\n    ReleaseSemaphore();"
    def extract_1d(text, start):
        begin=text.index(start, text.index("        // TODO: allow multisized components."))
        return text[begin:text.index(end_1d,begin)]
    old_1d=extract_1d(pinned,legacy_1d_start)
    live_1d=extract_1d(native,live_1d_start)
    assert fnv1a32(old_1d)==3343909125 and len(old_1d)==2147
    assert fnv1a32(live_1d)==3851112244 and len(live_1d)==11871
    assert 'if (out.size() == 16384) return false;' in live_1d
    assert "mapped_ranges_overlap(tiled_begin" in live_1d
    assert "GpuToCpuAddress(address)" in live_1d
    assert "IsContinuousRange(first," in live_1d
    assert "memory_manager.WriteBlockCached(destination," in live_1d
    assert "memory_manager.IsFullyMappedRange(source, count)" in live_1d
    assert "MAX_ALIAS_SNAPSHOT" in live_1d
    assert "DmaSoftwareOverlap(memory_manager, regs.offset_in, count" in live_1d
    assert "memory_manager.WriteBlock(regs.offset_out, snapshot.data(), count)" in live_1d
    assert expected.count(old_1d)==1
    expected=expected.replace(old_1d,live_1d,1)
    # The base CPU swizzlers used soft UNIMPLEMENTED_IF guards that did not
    # stop execution. Accept only the exact reviewed early-return successors.
    REVIEWED_TILED_SOFTWARE_GUARDS = [
        ("    UNIMPLEMENTED_IF(regs.src_params.block_size.width != 0);\n    UNIMPLEMENTED_IF(regs.src_params.block_size.depth != 0);\n    UNIMPLEMENTED_IF(regs.src_params.block_size.depth == 0 && regs.src_params.depth != 1);\n",
         "    // Unsupported tile geometry is not a software copy permission. Eden\\'s\n    // soft assertions returned to this decoder and could corrupt guest bytes.\n    if (regs.src_params.block_size.width != 0 ||\n        regs.src_params.block_size.depth != 0 ||\n        (regs.src_params.block_size.depth == 0 && regs.src_params.depth != 1)) {\n        UNIMPLEMENTED_MSG(\"Unsupported source block-linear DMA geometry\");\n        return;\n    }\n"),
        ("void MaxwellDMA::CopyPitchToBlockLinear() {\n    UNIMPLEMENTED_IF_MSG(regs.dst_params.block_size.width != 0, \"Block width is not one\");\n    UNIMPLEMENTED_IF(regs.dst_params.layer != 0);\n\n",
         "void MaxwellDMA::CopyPitchToBlockLinear() {\n"),
        ("    if (accelerate.BufferToImage(copy_info, src_operand, dst_operand)) {\n        return;\n    }\n\n    const auto& dst_params = regs.dst_params;\n",
         "    if (accelerate.BufferToImage(copy_info, src_operand, dst_operand)) {\n        return;\n    }\n    // Keep an accelerator that explicitly supports this layout; the CPU\n    // swizzler cannot decode a nonzero block width or destination layer.\n    if (regs.dst_params.block_size.width != 0 || regs.dst_params.layer != 0) {\n        UNIMPLEMENTED_MSG(\"Unsupported destination block-linear DMA geometry\");\n        return;\n    }\n\n    const auto& dst_params = regs.dst_params;\n"),
        ("void MaxwellDMA::CopyBlockLinearToBlockLinear() {\n    UNIMPLEMENTED_IF(regs.src_params.block_size.width != 0);\n\n",
         "void MaxwellDMA::CopyBlockLinearToBlockLinear() {\n    if (regs.src_params.block_size.width != 0) {\n        UNIMPLEMENTED_MSG(\"Unsupported source block-linear DMA width\");\n        return;\n    }\n\n"),
    ]
    for previous, reviewed in REVIEWED_TILED_SOFTWARE_GUARDS:
        assert expected.count(previous) == 1, "Retired tiled DMA guard anchor drift"
        assert native.count(reviewed) == 1, "Maintained tiled DMA guard drift"
        expected = expected.replace(previous, reviewed, 1)
    # The Maxwell register file now rejects invalid direct/deferred method
    # indices even when ASSERT_MSG is soft. Only this reviewed owner changes.
    MAXWELL_METHOD_BOUNDS_RECEIPT = [
        ("void MaxwellDMA::ConsumeSinkImpl(Core::System& system) {\n    for (auto [method, value] : method_sink) {\n        regs.reg_array[method] = value;\n    }\n    method_sink.clear();\n}", "void MaxwellDMA::ConsumeSinkImpl(Core::System& system) {\n    for (auto [method, value] : method_sink) {\n        if (method >= NUM_REGS) {\n            ASSERT_MSG(false, \"Invalid deferred MaxwellDMA register\");\n            continue;\n        }\n        regs.reg_array[method] = value;\n    }\n    method_sink.clear();\n}"),
        ("    ASSERT_MSG(method < NUM_REGS, \"Invalid MaxwellDMA register\");\n\n    regs.reg_array[method] = method_argument;", "    if (method >= NUM_REGS) {\n        ASSERT_MSG(false, \"Invalid MaxwellDMA register\");\n        return;\n    }\n\n    regs.reg_array[method] = method_argument;"),
    ]
    for old, reviewed in MAXWELL_METHOD_BOUNDS_RECEIPT:
        assert expected.count(old) == 1, "Pinned DMA register sink drift"
        assert native.count(reviewed) == 1, "Reviewed native DMA guard drift"
        expected = expected.replace(old, reviewed, 1)
    # GPU-28: neither tiled-pitch conversion may calculate u32 GOB allocation
    # sizes on unbounded guest surface metadata. Verify reviewed C++ exactly.
    for begin, end, old_hash, old_size, new_hash, new_size in (
        ("void MaxwellDMA::CopyBlockLinearToPitch() {",
         "void MaxwellDMA::CopyPitchToBlockLinear() {",
         3167428731, 4881, 1037823203, 6448),
        ("void MaxwellDMA::CopyPitchToBlockLinear() {",
         "void MaxwellDMA::CopyBlockLinearToBlockLinear() {",
         516317152, 4460, 2414643095, 6186),
    ):
        assert expected.count(begin) == native.count(begin) == 1
        old_section = begin + expected.split(begin, 1)[1].split(end, 1)[0]
        new_section = begin + native.split(begin, 1)[1].split(end, 1)[0]
        assert fnv1a32(old_section) == old_hash and len(old_section) == old_size
        assert fnv1a32(new_section) == new_hash and len(new_section) == new_size
        for required in (
            "MAX_SOFTWARE_TILED_DMA_BYTES",
            "aligned_width > MAX_SOFTWARE_TILED_DMA_BYTES / aligned_height",
            "memory_manager.IsFullyMappedRange(regs.offset_in, src_size)",
            "memory_manager.IsFullyMappedRange(regs.offset_out, dst_size)",
        ):
            assert required in new_section, ("Missing tiled conversion preflight", required)
        expected = expected.replace(old_section, new_section, 1)
    # GPU-27: the genuine 2D tiled-to-tiled DMA owner must bound ALL three
    # intermediate allocations and the decoder's u32 padded-image extents
    # before any guest memory access. Keep whole-source parity byte-for-byte.
    tiled_begin = "void MaxwellDMA::CopyBlockLinearToBlockLinear() {"
    tiled_end = "void MaxwellDMA::ReleaseSemaphore() {"
    assert expected.count(tiled_begin) == native.count(tiled_begin) == 1
    assert expected.count(tiled_end) == native.count(tiled_end) == 1
    old_tiled = expected.split(tiled_begin, 1)[1].split(tiled_end, 1)[0]
    new_tiled = native.split(tiled_begin, 1)[1].split(tiled_end, 1)[0]
    assert fnv1a32(tiled_begin + old_tiled) == 2645167551 and len(tiled_begin + old_tiled) == 3217
    assert fnv1a32(tiled_begin + new_tiled) == 316318506 and len(tiled_begin + new_tiled) == 5713
    for required in (
        "src.block_size.width != 0 || dst.block_size.width != 0",
        "src.layer != 0 || dst.layer != 0",
        "src.depth != 1 || dst.depth != 1",
        "x_elements > src_width - src_x_offset",
        "x_elements > dst_width - dst_x_offset",
        "MAX_SOFTWARE_TILED_DMA_BYTES",
        "aligned_width > MAX_SOFTWARE_TILED_DMA_BYTES / aligned_height",
        "pitch_wide > MAX_SOFTWARE_TILED_DMA_BYTES / regs.line_count",
        "memory_manager.IsFullyMappedRange(regs.offset_in, src_size)",
        "memory_manager.IsFullyMappedRange(regs.offset_out, dst_size)",
    ):
        assert required in new_tiled, ("Missing bounded tiled DMA owner", required)
    expected = expected.replace(tiled_begin + old_tiled, tiled_begin + new_tiled, 1)
    assert expected==native
assert "EDEN_MAINTAINED_MAXWELL_DMA" in cm
assert 'target_include_directories(video_core BEFORE PUBLIC "${EDEN_MAINTAINED_MAXWELL_DMA_INCLUDE}")' in cm
header=(root/"vendor/encore-active/eden/include/video_core/engines/maxwell_dma.h").read_text()
assert "BitField<0, 16, u32> dst_components_raw" in header
assert "i * 4" in header
assert "remap.GetComponent(3)" in helper
assert 'list(REMOVE_ITEM video_sources engines/maxwell_dma.cpp)' in cm
assert 'python3 -B tools/check-native-dma-extent-host.py' in wf
# The selected integrated MaxwellDMA uses real u64 bounds / signed-pitch
# geometry and a newer 2D remap path. Compile its actual self-contained
# numeric helpers under UBSan, rather than splicing unrelated 2D decoder
# local variables into the historic row-wise arithmetic mock.
if integrated_dma:
    coalesce_begin = "constexpr bool CanCoalescePitchDma("
    envelope_begin = "constexpr bool PitchDmaEnvelope("
    row_begin = "constexpr GPUVAddr PitchDmaRowAddress("
    assert native.count(coalesce_begin) == native.count(envelope_begin) == native.count(row_begin) == 1
    selected_numeric = (native[native.index(coalesce_begin):native.index(envelope_begin)]
                        + native[native.index(envelope_begin):native.index(row_begin)])
    assert "width > (~u32{0}) / rows" in selected_numeric
    assert "const u64 delta = magnitude * (rows - 1);" in selected_numeric
    assert "bytes > MAX_ADDRESS - base - delta" in selected_numeric
    if selected_sha(native) == "1fe0b4f25d6f4bbd24406e2f929868151d32c133":
        begin = native.index("constexpr bool DmaVolumeLinearRows(")
        end = native.index("// MemoryManager::CopyBlock is an individual-row transfer", begin)
        assert begin < end and "return true;" in native[begin:end]
        selected_numeric += native[begin:end]
    cpp = """
#include <cassert>
#include <cstdint>
#include <limits>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s32 = std::int32_t;
using s64 = std::int64_t;
using GPUVAddr = u64;
__SELECTED_NUMERIC__
int main() {
    u64 count{}, begin{}, end{};
    const u64 mx = (std::numeric_limits<u64>::max)();
    assert(CanCoalescePitchDma(0, 128, 16, 4, 16, 16, count) && count == 64);
    assert(!CanCoalescePitchDma(0, 32, 16, 4, 16, 16, count));
    assert(!CanCoalescePitchDma(0, 128, 16, 4, -16, 16, count));
    assert(!CanCoalescePitchDma(0, 128, 0, 4, 0, 0, count));
    assert(!CanCoalescePitchDma(0, 128, u32{0xffffffff}, 2, 0xffffffff, 0xffffffff, count));
    assert(!CanCoalescePitchDma(mx - 5, 128, 16, 1, 16, 16, count));
    assert(PitchDmaEnvelope(100, 16, 4, 8, begin, end));
    assert(begin == 100 && end == 156);
    assert(PitchDmaEnvelope(100, -16, 4, 8, begin, end));
    assert(begin == 52 && end == 108);
    assert(PitchDmaEnvelope(100, (std::numeric_limits<s32>::min)(), 1, 1, begin, end));
    assert(begin == 100 && end == 101);
    assert(!PitchDmaEnvelope(5, -16, 2, 8, begin, end));
    assert(!PitchDmaEnvelope(mx - 10, 16, 2, 8, begin, end));
}
""".replace("__SELECTED_NUMERIC__", selected_numeric)
    if selected_sha(native) == "1fe0b4f25d6f4bbd24406e2f929868151d32c133":
        cpp = cpp.replace("int main() {", """int main() {
    u64 rows{};
    for (u32 h = 0; h <= 9; ++h)
      for (u32 d = 0; d <= 7; ++d)
        for (u32 z = 0; z <= d + 1; ++z)
          for (u32 y = 0; y <= h + 1; ++y)
            for (u32 n = 0; n <= 65; ++n) {
              const bool got = DmaVolumeLinearRows(h, d, z, y, n, rows);
              u64 consumed = 0, expected_rows = 0;
              if (h && d && z < d && y < h && n) {
                for (u32 slice = z; slice < d && consumed < n; ++slice) {
                  const u64 available = static_cast<u64>(h) - y;
                  const u64 pending = static_cast<u64>(n) - consumed;
                  const u64 take = pending < available ? pending : available;
                  consumed += take;
                  expected_rows = static_cast<u64>(slice - z) * h + take;
                }
              }
              const bool valid = h && d && z < d && y < h && n && consumed == n;
              assert(got == valid && rows == (valid ? expected_rows : 0));
            }
    assert(DmaVolumeLinearRows(8, 4, 1, 3, 9, rows) && rows == 12);
    assert(DmaVolumeLinearRows(8, 4, 1, 3, 11, rows) && rows == 17);
    assert(!DmaVolumeLinearRows(8, 4, 1, 3, 16, rows) && rows == 0);
    const u32 max32 = (std::numeric_limits<u32>::max)();
    assert(DmaVolumeLinearRows(max32, max32, 0, 0, max32, rows) && rows == max32);
    assert(DmaVolumeLinearRows(max32, max32, max32 - 1, max32 - 1, 1, rows) && rows == 1);
    assert(!DmaVolumeLinearRows(max32, max32, max32 - 1, max32 - 1, 2, rows));
""", 1)
    clang = shutil.which("clang++-18") or shutil.which("clang++")
    assert clang
    with tempfile.TemporaryDirectory(prefix="encore-selected-dma-extent-") as td:
        f = Path(td) / "numeric.cpp"
        f.write_text(cpp)
        for opt in ("-O0", "-O2"):
            out = Path(td) / ("test"+opt)
            subprocess.run([clang, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                            str(f), "-o", str(out)], check=True, timeout=55)
            subprocess.run([str(out)], check=True, timeout=20)
            print("DMA_EXTENT_SELECTED_HOST_PASS", opt,
                  "source_extracted=2 bounds=1 signed_pitch=1 no_wrap=1")
else:
    gpu="""    // Widen before multiplying, then respect the u32 buffer-cache span.
        const u64 buffer_size_wide = static_cast<u64>(buffer_operand.pitch) * buffer_operand.height;
        if (buffer_size_wide > static_cast<u64>(~u32{0})) {
            return false;
        }
        const u32 buffer_size = static_cast<u32>(buffer_size_wide);"""
    assert gpu in vulkan and gpu in bridge
    def cut(s,start,end):
     assert s.count(start)==1
     pos=s.index(start)
     return s[pos:s.index(end,pos)].strip()+"\n"
    dst=cut(native,"    const u64 dst_size_wide","\n    Tegra::Memory::GpuGuestMemory<u8")
    src=cut(native,"    const u64 src_size_wide","\n    GPUVAddr src_addr")
    mid=cut(native,"    const u64 pitch_wide","\n    intermediate_buffer.resize_destructive")
    acc=cut(vulkan,"    const u64 buffer_size_wide","\n#endif\n    static constexpr auto sync_info")
    # The extracted desktop arithmetic is inside #else; keep its closing #endif out.
    assert "#else\n    // Widen before multiplying" in vulkan
    cpp=r"""
    #include <cassert>
    #include <cstdint>
    #include <cstdlib>
    #include <cstddef>
    #include <optional>
    using u32=std::uint32_t; using u64=std::uint64_t;
    using s32=std::int32_t; using s64=std::int64_t;
    #define LOG_WARNING(...) ((void)0)
    struct Regs{u32 pitch_in;u32 line_count;};
    struct Buf{u32 pitch;u32 height;};
    std::optional<std::size_t> Dst(u32 pitch,u32 count){
     Buf dst_operand{pitch,0};Regs regs{0,count};
    __DST__
     return dst_size;
    }
    std::optional<std::size_t> Src(u32 pitch,u32 count){
     Regs regs{pitch,count};
    __SRC__
     return src_size;
    }
    std::optional<std::size_t> Mid(u32 x_elements,u32 bytes_per_pixel,u32 count){
     Regs regs{0,count};
    __MID__
     (void)pitch;return mid_buffer_size;
    }
    bool Acc(u32 pitch,u32 height){
     Buf buffer_operand{pitch,height};
    __ACC__
     return buffer_size==static_cast<u32>(static_cast<u64>(pitch)*height);
    }
    int main(){
     const u32 mx=~u32{0};
     assert(Acc(0,0) && Acc(256,1080) && Acc(mx,1));
     assert(!Acc(65536,65536) && !Acc(mx,2));
     assert(Dst(256,1080)==std::optional<std::size_t>{276480});
     assert(Src(256,1080)==std::optional<std::size_t>{276480});
     assert(!Dst(65536,65536) && !Src(65536,65536));
     assert(Dst(mx,1)==std::optional<std::size_t>{mx});
     assert(Mid(256,4,1080)==std::optional<std::size_t>{1105920});
     assert(Mid(mx,1,1)==std::optional<std::size_t>{mx});
     assert(!Mid(mx,2,1) && !Mid(mx,1,2));
     assert(!Mid(mx,mx,mx));
     assert(static_cast<u32>(std::abs(static_cast<s64>(-2147483647-1)))==2147483648u);
    }
    """
    for key,body in (("__DST__",dst),("__SRC__",src),("__MID__",mid),("__ACC__",acc)):
     assert cpp.count(key)==1
     cpp=cpp.replace(key,body.replace("return;","return std::nullopt;"))
    clang=shutil.which("clang++-18") or shutil.which("clang++")
    assert clang
    with tempfile.TemporaryDirectory(prefix="dma-extent-") as td:
     f=Path(td)/"main.cpp";out=Path(td)/"test";f.write_text(cpp)
     subprocess.run([clang,"-std=c++20","-O1","-Wall","-Wextra","-Werror",
                     "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                     str(f),"-o",str(out)],check=True,timeout=55)
     subprocess.run([str(out)],check=True,timeout=20)

if not integrated_dma:
    print("DMA_EXTENT_HOST_PASS real_arithmetic=4 native_owner=1 pinned_parity=1 asan_ubsan=1")
