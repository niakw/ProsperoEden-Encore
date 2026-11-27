#!/usr/bin/env python3
"""Verify the active Lichii #414 quad-LUT retirement, never the archived first-buffer fence."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
cost = (root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_buffer_cache_cost.cpp").read_text()
upstream = (root / "vendor/sources/eden/src/video_core/renderer_vulkan/vk_buffer_cache.cpp").read_text()
workflow = (root / ".github/workflows/encore-core-preflight.yml").read_text()

start = cost.index("void UpdateBuffer(u32 num_indices_)")
end = cost.index("\n    void BindBuffer(", start)
method = cost[start:end]
assert "Lichii #414" in method
assert "scheduler.Finish();" not in method
assert method.count("memory_allocator.CreateBuffer(") == 1
assert "buffer = memory_allocator.CreateBuffer(" in method
assert "scheduler.Record([src_buffer = staging.buffer" in method
assert "const bool host_visible = buffer.IsHostVisible();" in method
assert "std::vector<std::pair<u64, vk::Buffer>> retired_buffers;" in cost
assert "scheduler.Finish();" in upstream  # The pinned predecessor must remain untouched.
assert "python3 -B tools/check-ps5-quad-index-initial-fence-host.py" in workflow

retire = "retired_buffers.emplace_back(scheduler.CurrentTick(), std::move(buffer));"
drain = "while (!retired_buffers.empty() && scheduler.IsFree(retired_buffers.front().first))"
assert retire in method and drain in method
assert method.index(drain) < method.index("if (num_indices_ <= num_indices)") < method.index(retire)
assert "std::numeric_limits<u32>::max() - num_indices" in method
assert "num_indices = (std::max)(num_indices_, grown);" in method

# Compile the actual active retirement-and-growth C++ statements in a small
# independent lifetime fixture. A completed tick releases only its retired LUT;
# an outstanding tick keeps its VkBuffer alive without Finish() stalling a draw.
fragment = method[method.index("        while (!retired_buffers.empty()"):
                  method.index("        index_type = ")]
fixture = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <limits>
#include <memory>
#include <utility>
#include <vector>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
struct Buffer {
    std::unique_ptr<int> value;
    explicit operator bool() const noexcept { return !!value; }
};
struct Scheduler {
    u64 tick = 5, completed = 0;
    u64 CurrentTick() const { return tick; }
    bool IsFree(u64 t) const { return t <= completed; }
};
struct LUT {
    Scheduler& scheduler;
    Buffer buffer{};
    std::vector<std::pair<u64, Buffer>> retired_buffers;
    u32 num_indices = 0;
    int next_id = 0;
    void UpdateBuffer(u32 num_indices_) {
__ACTIVE_RETIRE__
        buffer.value = std::make_unique<int>(++next_id);
    }
};
int main() {
    Scheduler scheduler;
    LUT lut{scheduler, {}, {}, 0, 0};
    lut.UpdateBuffer(8);
    assert(lut.retired_buffers.empty() && *lut.buffer.value == 1 && lut.num_indices == 8);
    lut.UpdateBuffer(16);
    assert(lut.retired_buffers.size() == 1 && lut.retired_buffers[0].first == 5);
    assert(*lut.retired_buffers[0].second.value == 1 && *lut.buffer.value == 2);
    scheduler.tick = 6;
    lut.UpdateBuffer(17);
    assert(lut.num_indices == 24 && lut.retired_buffers.size() == 2);
    assert(lut.retired_buffers[1].first == 6 && *lut.buffer.value == 3);
    lut.UpdateBuffer(20);
    assert(lut.retired_buffers.size() == 2 && *lut.buffer.value == 3);
    scheduler.completed = 5;
    lut.UpdateBuffer(20);
    assert(lut.retired_buffers.size() == 1 && lut.retired_buffers[0].first == 6);
    scheduler.completed = 6;
    lut.UpdateBuffer(24);
    assert(lut.retired_buffers.empty() && *lut.buffer.value == 3);
    scheduler.tick = 7;
    lut.UpdateBuffer(25);
    assert(lut.num_indices == 36 && lut.retired_buffers.size() == 1);
    assert(lut.retired_buffers[0].first == 7 && *lut.retired_buffers[0].second.value == 3);
    scheduler.completed = 7;
    lut.UpdateBuffer(25);
    assert(lut.retired_buffers.empty());
    LUT near_limit{scheduler, {}, {}, 0, 0};
    near_limit.num_indices = std::numeric_limits<u32>::max() - 1;
    near_limit.UpdateBuffer(std::numeric_limits<u32>::max());
    assert(near_limit.num_indices == std::numeric_limits<u32>::max());
}
""".replace("__ACTIVE_RETIRE__", fragment)

cc = shutil.which("clang++-18") or shutil.which("clang++")
assert cc, "Clang is required"
with tempfile.TemporaryDirectory(prefix="encore-quad-lut-retirement-") as temp:
    src = Path(temp) / "case.cpp"
    binary = Path(temp) / "case"
    src.write_text(fixture)
    subprocess.run([cc, "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    str(src), "-o", str(binary)], check=True, timeout=45)
    subprocess.run([str(binary)], check=True, timeout=30)
print("QUAD_INDEX_RETIREMENT_HOST_PASS first_no_wait=1 outstanding_retained=2 completed_reclaimed=2 growth=1 overflow=0")
