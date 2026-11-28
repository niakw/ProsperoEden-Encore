#!/usr/bin/env python3
"""Compile the maintained (CMake-selected) native TIC guard, offline."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
path = root / "vendor/encore-active/eden/src/video_core/texture_cache/util.cpp"
cmake = (root / "headless/CMakeLists.txt").read_text()
assert '"${PORT_ROOT}/vendor/encore-active/eden/src/video_core/texture_cache/util.cpp"' in cmake
assert 'list(APPEND video_sources "${EDEN_MAINTAINED_TEXTURE_UTIL}")' in cmake
data = path.read_text()
begin = data.index("bool IsValidEntry(")
end = data.index("\nboost::container::small_vector<BufferImageCopy", begin)
fn = data[begin:end]
assert fn.count("#ifdef PS5_NATIVE") == 2
assert 'config.format == static_cast<Tegra::Texture::TextureFormat>(0)' in fn
assert "if (config.is_sparse == 0)" in fn
fixture = r'''
#include <cstdint>
#include <cstddef>
#include <optional>
#include <cassert>
using GPUVAddr = std::uint64_t;
using DAddr = std::uint64_t;
namespace Tegra {
namespace Texture {
enum class TextureFormat : std::uint32_t { Invalid = 0, Valid = 1 };
}
struct MemoryManager {
    bool first{}, any{};
    std::optional<DAddr> GpuToCpuAddress(GPUVAddr) const {
        return first ? std::optional<DAddr>{4096} : std::nullopt;
    }
    std::optional<DAddr> GpuToCpuAddress(GPUVAddr, std::size_t) const {
        return any ? std::optional<DAddr>{8192} : std::nullopt;
    }
};
}
struct TICEntry {
    Tegra::Texture::TextureFormat format{Tegra::Texture::TextureFormat::Valid};
    int is_sparse{};
    GPUVAddr addr{8192};
    GPUVAddr Address() const { return addr; }
};
struct ImageInfo { explicit ImageInfo(const TICEntry&) {} };
std::size_t CalculateGuestSizeInBytes(const ImageInfo&) { return 16384; }
''' + fn + r'''
int main() {
    const Tegra::MemoryManager first{true, true};
    const Tegra::MemoryManager later{false, true};
    const Tegra::MemoryManager none{false, false};
    TICEntry t{};
    assert(IsValidEntry(first, t));
    t.addr = 0; assert(!IsValidEntry(first, t));
    t.addr = 1ULL << 40; assert(!IsValidEntry(first, t));
    t.addr = 8192;
#ifdef PS5_NATIVE
    t.format = Tegra::Texture::TextureFormat::Invalid;
    assert(!IsValidEntry(first, t));
    t.format = Tegra::Texture::TextureFormat::Valid;
    t.is_sparse = 0;
    assert(!IsValidEntry(later, t));
#else
    t.is_sparse = 0;
    assert(IsValidEntry(later, t));
#endif
    t.is_sparse = 1;
    assert(IsValidEntry(later, t));
    assert(!IsValidEntry(none, t));
}
'''
with tempfile.TemporaryDirectory(prefix="encore-active-tic-") as tmp:
    source = Path(tmp) / "tic.cpp"
    source.write_text(fixture)
    for label, flags in (("native", ["-DPS5_NATIVE"]), ("host", [])):
        output = Path(tmp) / label
        subprocess.run(["c++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror",
                        *flags, str(source), "-o", str(output)], check=True)
        subprocess.run([str(output)], check=True)
        print(f"ENCORE_ACTIVE_TIC_PASS variant={label}")

# GPU-43: the PS5 Vulkan ASTC owner (shared by NS1 and NS2) is the one
# compiled by CMake, not the archived Eden texture_cache.h. Reuse this
# already-executed host check to test the exact active SyncDescriptors body
# and both real TIC/TSC guard expressions; no new build path or workflow.
import shutil
owner_path = root / "vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h"
owner = owner_path.read_text()
assert 'vendor/encore-active/eden/src' in cmake
assert 'target_include_directories(video_core BEFORE PUBLIC' in cmake
assert '"video_core/texture_cache/texture_cache.h"' in cmake
start = owner.index("void TextureCache<P>::SynchronizeDescriptors(bool compute) {")
end = owner.index("\n}\n", start) + 2
sync = owner[start:end]
assert "constexpr u32 MaxDescriptorTableLimit = (1U << 21) - 1;" in sync
assert sync.count("MaxDescriptorTableLimit") == 5
for name in ("GetSamplerId(u32 index, bool compute)", "VisitImageView(u32 index, bool compute)"):
    start_guard = owner.index(name)
    end_guard = owner.index("\n}\n", start_guard)
    assert 'if (index > table.current_limit || index >= table.descriptors.size()) {' in owner[start_guard:end_guard]
guard = "index > table.current_limit || index >= table.descriptors.size()"
assert owner.count("if (" + guard + ") {") == 2

fixture = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <limits>
#include <vector>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
namespace Tegra::Engines {
struct Maxwell3D {
    struct Regs {
        enum class SamplerBinding { ViaHeaderBinding, Independent };
    };
};
}
struct FakeTable {
    u32 current_limit{};
    u64 address{};
    std::vector<int> descriptors{};
    bool Synchronize(u64 addr, u32 limit) {
        if (address == addr && current_limit == limit) return false;
        address = addr; current_limit = limit;
        return true;
    }
};
struct FakeRegsEntry {
    u32 limit{};
    u64 address{};
    u64 Address() const { return address; }
};
struct FakeKepler {
    struct { bool linked_tsc{}; } launch_description;
    struct { FakeRegsEntry tic{}, tsc{}; } regs;
};
struct FakeMaxwell {
    struct {
        Tegra::Engines::Maxwell3D::Regs::SamplerBinding sampler_binding{
            Tegra::Engines::Maxwell3D::Regs::SamplerBinding::Independent};
        FakeRegsEntry tex_header{}, tex_sampler{};
    } regs;
};
struct FakeChannel {
    FakeTable compute_sampler_table{};
    FakeTable compute_image_table{};
    FakeTable graphics_sampler_table{};
    FakeTable graphics_image_table{};
};
template<class P>
class TextureCache {
public:
    FakeChannel* channel_state{};
    FakeKepler* kepler_compute{};
    FakeMaxwell* maxwell3d{};
    u64 texture_bindings_serial{};
    void SynchronizeDescriptors(bool compute);
};
template<class P>
__NATIVE_SYNC__
bool Rejected(const FakeTable& table, u32 index) {
    return __NATIVE_GUARD__;
}
int main() {
    constexpr u32 Maximum=(1U<<21)-1;
    FakeChannel ch{};
    FakeKepler k{};
    FakeMaxwell m{};
    TextureCache<int> tc{};
    tc.channel_state=&ch;
    tc.kepler_compute=&k;
    tc.maxwell3d=&m;
    k.regs.tic={std::numeric_limits<u32>::max(),0x1000};
    k.regs.tsc={std::numeric_limits<u32>::max(),0x2000};
    tc.SynchronizeDescriptors(true);
    assert(ch.compute_image_table.current_limit==Maximum);
    assert(ch.compute_sampler_table.current_limit==Maximum);
    assert(tc.texture_bindings_serial==1);
    tc.SynchronizeDescriptors(true);
    assert(tc.texture_bindings_serial==1);
    k.launch_description.linked_tsc=true;
    k.regs.tsc.limit=1;
    tc.SynchronizeDescriptors(true);
    assert(ch.compute_sampler_table.current_limit==Maximum);
    m.regs.tex_header={std::numeric_limits<u32>::max(),0x3000};
    m.regs.tex_sampler={std::numeric_limits<u32>::max(),0x4000};
    tc.SynchronizeDescriptors(false);
    assert(ch.graphics_image_table.current_limit==Maximum);
    assert(ch.graphics_sampler_table.current_limit==Maximum);
    m.regs.sampler_binding=Tegra::Engines::Maxwell3D::Regs::SamplerBinding::ViaHeaderBinding;
    m.regs.tex_header.limit=3;
    tc.SynchronizeDescriptors(false);
    assert(ch.graphics_image_table.current_limit==3);
    assert(ch.graphics_sampler_table.current_limit==3);
    // Valid guest limits can exceed allocated descriptor capacity when
    // the inherited 32-bit rounding wraps. Never enter DescriptorTable::Read.
    FakeTable table{};
    table.current_limit=std::numeric_limits<u32>::max();
    assert(Rejected(table,0)); // not synchronized / no entries
    table.descriptors.resize(2);
    assert(!Rejected(table,0) && !Rejected(table,1));
    assert(Rejected(table,2));
    assert(Rejected(table,std::numeric_limits<u32>::max()));
    table.current_limit=0;
    assert(Rejected(table,1)); // allocated but forbidden by guest limit
    assert(!Rejected(table,0));
    // Native cap keeps the inherited (u32) 0x80000 rounding non-overflowing
    // without changing the table growth policy for real small limits.
    const u64 capped_count=(((u64)Maximum+0x80000ULL)&~0x7ffffULL)+1;
    assert(capped_count <= ((u64)1<<21)+1);
}
""".replace("__NATIVE_SYNC__", sync).replace("__NATIVE_GUARD__", guard)
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++ compiler required for GPU-43 descriptor guard"
with tempfile.TemporaryDirectory(prefix="encore-gpu43-descriptor-") as tmp:
    source = Path(tmp)/"descriptor.cpp"
    source.write_text(fixture)
    for opt in ("-O0", "-O2"):
        exe = Path(tmp)/("descriptor-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=15)
print("NS1_DESCRIPTOR_TABLE_BOUND_HOST_PASS active_owner=1 sampler_guard=1 "
      "image_guard=1 compute_cap=1 graphics_cap=1 linked_sampler=1 "
      "no_resync=1 allocated_boundary=1 empty_table=1 O0_O2=2 ASan_UBSan=1")
