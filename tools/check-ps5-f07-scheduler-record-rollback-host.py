#!/usr/bin/env python3
"""F07: a rejected Vulkan command record cannot preserve an unsubmitted binding memo."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
header=(root/"headless/vk_scheduler_ps5.h").read_text()
implementation=(root/"headless/vulkan_scheduler_ps5.cpp").read_text()
rasterizer=(root/"vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
buffer_runtime=(root/"headless/vk_buffer_cache_shutdown_ps5.cpp").read_text()
cmake=(root/"headless/vulkan.cmake").read_text()
generator=(root/"tools/prepare-vulkan-port.py").read_text()
assert 'configure_file("${EDEN_PORT_DIR}/vulkan_scheduler_ps5.cpp"' in cmake
assert 'configure_file("${EDEN_PORT_DIR}/vk_scheduler_ps5.h"' in cmake
assert 'configure_file("${EDEN_PORT_DIR}/vk_buffer_cache_shutdown_ps5.cpp"' in cmake
begin="    template <typename T>\n        requires std::is_invocable_v<T, vk::CommandBuffer, vk::CommandBuffer>\n    void RecordWithUploadBuffer(T&& command) {"
stop="    template <typename T>\n        requires std::is_invocable_v<T, vk::CommandBuffer>\n    void Record(T&& c) {"
assert header.count(begin)==header.count(stop)==1
method=header[header.index(begin):header.index(stop)]
assert "#ifdef PS5_NATIVE" in method
assert "InvalidateState();" in method
assert "if (!chunk->Record(command)) {" in method
assert "throw std::bad_alloc{};" in method
assert "F07 reject native scheduler second record refusal after rollover" in generator
assert "F07 include bad_alloc declaration for native rejected scheduler rollover" in generator
assert "#include <new>" in header
assert method.index("} catch (...) {") > method.index("(void)chunk->Record(command)")
assert "F07 invalidate native Vulkan binding memo after rejected record" in generator
epoch_begin="    [[nodiscard]] bool RecordedSinceSubmit() const noexcept {"
epoch_end="\n\n    /// Requests to begin a renderpass."
assert header.count(epoch_begin)==1
epoch_method=header[header.index(epoch_begin):header.index(epoch_end,header.index(epoch_begin))]
assert "recorded_command_serial != submitted_command_serial" in epoch_method
assert "deferred_clear.framebuffer != nullptr" in epoch_method
flush_begin=implementation.index("u64 Scheduler::Flush(")
flush_end=implementation.index("\n}\n",flush_begin)
finish_begin=implementation.index("void Scheduler::Finish(")
finish_end=implementation.index("\n}\n",finish_begin)
flush=implementation[flush_begin:flush_end]
finish=implementation[finish_begin:finish_end]
assert flush.count("submitted_command_serial = recorded_command_serial;")==1
assert finish.count("submitted_command_serial = recorded_command_serial;")==1
assert flush.index("SubmitExecution(") < flush.index("submitted_command_serial = recorded_command_serial;")
assert finish.index("SubmitExecution(") < finish.index("submitted_command_serial = recorded_command_serial;")
flush_commands=rasterizer[rasterizer.index("void RasterizerVulkan::FlushCommands() {"):
                          rasterizer.index("\nvoid RasterizerVulkan::TickFrame()",rasterizer.index("void RasterizerVulkan::FlushCommands() {"))]
assert "scheduler.RecordedSinceSubmit()" in flush_commands
assert flush_commands.index("draw_counter = 0;") < flush_commands.index("scheduler.RecordedSinceSubmit()")
clear_begin=buffer_runtime.index("void BufferCacheRuntime::ClearBuffer(")
clear_end=buffer_runtime.index("\nbool BufferCacheRuntime::BindMultiRangeStorageBuffer",clear_begin)
copy_begin=buffer_runtime.index("void BufferCacheRuntime::CopyBuffer(")
copy_end=buffer_runtime.index("\nvoid BufferCacheRuntime::PreCopyBarrier()",copy_begin)
assert "scheduler.Record(" in buffer_runtime[clear_begin:clear_end]
assert "scheduler.Record" in buffer_runtime[copy_begin:copy_end]
assert "FlushWork" not in buffer_runtime[clear_begin:clear_end]
assert "FlushWork" not in buffer_runtime[copy_begin:copy_end]
start=implementation.index("void Scheduler::InvalidateState() {")
invalidate=implementation[start:implementation.index("\n}",start)]
for required in ("state.graphics_pipeline = nullptr;",
                 "state.graphics_pipeline_optimized = false;",
                 "state.rescaling_defined = false;",
                 "state.descriptor_buffer_bound = false;"):
    assert required in invalidate
for path in (".github/workflows/encore-core-fast-gate.yml",
             ".github/workflows/encore-core-preflight.yml"):
    assert "python3 -B tools/check-ps5-f07-scheduler-record-rollback-host.py" in (root/path).read_text()

cpp=r"""
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <new>
#include <stdexcept>
#include <type_traits>
namespace vk { struct CommandBuffer {}; }
struct MockChunk {
    bool refuse_once{};
    bool refuse_always{};
    bool throw_record{};
    unsigned recorded{};
    template<typename T> bool Record(T&) {
        if (throw_record) throw std::bad_alloc{};
        if (refuse_always) return false;
        if (refuse_once) { refuse_once=false; return false; }
        ++recorded;
        return true;
    }
};
struct Scheduler {
    MockChunk storage{};
    MockChunk* chunk=&storage;
    bool throw_dispatch{};
    bool pipeline_memo{true};
    bool rescaling_memo{true};
    bool descriptor_memo{true};
    bool renderpass_active{true};
    unsigned invalidations{};
    unsigned dispatches{};
    std::uint64_t recorded_command_serial{};
    std::uint64_t submitted_command_serial{};
    struct DeferredClear { const void* framebuffer{}; } deferred_clear{};
    bool device_retired{};
    [[nodiscard]] bool RecordedSinceSubmit() const noexcept {
        return recorded_command_serial != submitted_command_serial ||
               deferred_clear.framebuffer != nullptr;
    }
    void DispatchWork() {
        if (throw_dispatch) throw std::bad_alloc{};
        ++dispatches;
    }
    void InvalidateState() {
        pipeline_memo=false;
        rescaling_memo=false;
        descriptor_memo=false;
        ++invalidations;
    }
""" + method + r"""
};
int main() {
    const auto cmd=[](vk::CommandBuffer, vk::CommandBuffer){};
    {
        Scheduler normal;
        normal.RecordWithUploadBuffer(cmd);
        assert(normal.storage.recorded==1 && normal.invalidations==0);
        assert(normal.recorded_command_serial==1);
        assert(normal.RecordedSinceSubmit());
        normal.submitted_command_serial=normal.recorded_command_serial;
        assert(!normal.RecordedSinceSubmit());
        normal.deferred_clear.framebuffer=&normal;
        assert(normal.RecordedSinceSubmit());
        normal.deferred_clear.framebuffer=nullptr;
        assert(!normal.RecordedSinceSubmit());
        assert(normal.pipeline_memo && normal.descriptor_memo);
    }
    {
        Scheduler rollover;
        rollover.storage.refuse_once=true;
        rollover.RecordWithUploadBuffer(cmd);
        assert(rollover.dispatches==1 && rollover.storage.recorded==1);
        assert(rollover.invalidations==0);
        assert(rollover.recorded_command_serial==1);
    }
    {
        // First and second record refuse: native must throw, clear pipeline
        // memos and allow a later draw to bind again. Desktop is unchanged.
        Scheduler denied_twice;
        denied_twice.storage.refuse_always=true;
        bool failed=false;
        try { denied_twice.RecordWithUploadBuffer(cmd); }
        catch(const std::bad_alloc&) { failed=true; }
        assert(denied_twice.dispatches==1 && denied_twice.storage.recorded==0);
        assert(denied_twice.recorded_command_serial==1);
#ifdef PS5_NATIVE
        assert(failed && denied_twice.invalidations==1);
        assert(!denied_twice.pipeline_memo && !denied_twice.descriptor_memo);
#else
        assert(!failed && denied_twice.invalidations==0);
#endif
        assert(denied_twice.renderpass_active);
        denied_twice.storage.refuse_always=false;
        denied_twice.RecordWithUploadBuffer(cmd);
        assert(denied_twice.storage.recorded==1);
        assert(denied_twice.recorded_command_serial==2);
    }
    for (bool fail_record : {true,false}) {
        Scheduler denied;
        denied.storage.throw_record=fail_record;
        denied.storage.refuse_once=!fail_record;
        denied.throw_dispatch=!fail_record;
        bool failed=false;
        try { denied.RecordWithUploadBuffer(cmd); }
        catch(const std::bad_alloc&) { failed=true; }
        assert(failed && denied.storage.recorded==0);
        assert(denied.recorded_command_serial==1);
#ifdef PS5_NATIVE
        assert(denied.invalidations==1);
        assert(!denied.pipeline_memo && !denied.rescaling_memo && !denied.descriptor_memo);
#else
        assert(denied.invalidations==0);
        assert(denied.pipeline_memo && denied.rescaling_memo && denied.descriptor_memo);
#endif
        assert(denied.renderpass_active);
        denied.storage.throw_record=false;
        denied.storage.refuse_once=false;
        denied.throw_dispatch=false;
        denied.RecordWithUploadBuffer(cmd);
        assert(denied.storage.recorded==1);
        assert(denied.recorded_command_serial==2);
    }
}
"""
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="f07-record-memo-") as temp:
    unit=Path(temp)/"test.cpp"
    unit.write_text(cpp)
    for native in (True,False):
        for opt in ("-O0","-O2"):
            output=Path(temp)/(("ps5" if native else "desktop")+opt[1:])
            flags=["-DPS5_NATIVE=1"] if native else []
            built=subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                                  *flags,str(unit),"-o",str(output)],
                                  capture_output=True,text=True,timeout=40)
            assert built.returncode==0,(native,opt,built.stderr[-4000:])
            tested=subprocess.run([str(output)],capture_output=True,text=True,timeout=15)
            assert tested.returncode==0,(native,opt,tested.stderr[-4000:])
print("F07_SCHEDULER_RECORD_ROLLBACK_PASS first_accept=1 rollover=1 reject_record=1 reject_dispatch=1 replay=1 renderpass_preserved=1 dma_epoch_submit=1 deferred_clear=1 O0=1 O2=1 UBSan=1")
