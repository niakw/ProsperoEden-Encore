#!/usr/bin/env python3
"""Verify the single canonical PS5 GPU worker selected from encore-active/eden."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=ROOT/"vendor/encore-active/eden/src"
UPSTREAM=ROOT/"vendor/sources/eden/src"
WORKER=ACTIVE/"video_core/gpu_thread.cpp"
WORKER_HEADER=ACTIVE/"video_core/gpu_thread.h"
QUEUE_HEADER=ACTIVE/"common/bounded_threadsafe_queue.h"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

for path in (WORKER,WORKER_HEADER,QUEUE_HEADER):
    assert path.is_file(),path
for path in (
    UPSTREAM/"video_core/gpu_thread.cpp",
    UPSTREAM/"video_core/gpu_thread.h",
    UPSTREAM/"common/bounded_threadsafe_queue.h",
):
    assert path.is_file(),path

worker=WORKER.read_text()
header=WORKER_HEADER.read_text()
queue=QUEUE_HEADER.read_text()
assert "SPSCQueue<CommandDataContainer, 256>" in header
assert "EmplaceWaitWithStopToken" in queue
assert "union Slot {" in queue
assert "std::array<Slot, Capacity> m_data;" in queue
assert queue.count("std::construct_at(std::addressof(m_data[pos].value)")==2
assert "std::destroy_at(std::addressof(m_data[pos].value));" in queue
assert "std::destroy_at(std::addressof(m_data[cursor % Capacity].value));" in queue
for marker in (
    "void ThreadManager::StartThread(",
    "void ThreadManager::Stop()",
    "pthread_join(thread, nullptr)",
    "scheduler.HasPendingNativeChannels()",
    "scheduler.ResumePendingNative(system.GPU());",
    "state.signaled_fence.store(next.fence, std::memory_order_release);",
    "Eden::RecordGpuFailure(std::current_exception());",
):
    assert marker in worker,marker
for marker in (
    'set(EDEN_ACTIVE_EDEN "${PORT_ROOT}/vendor/encore-active/eden")',
    'set(EDEN_GPU_WORKER "${EDEN_ACTIVE_EDEN}/src/video_core/gpu_thread.cpp")',
    'set(EDEN_GPU_WORKER_HEADER "${EDEN_ACTIVE_EDEN}/src/video_core/gpu_thread.h")',
    'set(EDEN_GPU_QUEUE_HEADER "${EDEN_ACTIVE_EDEN}/src/common/bounded_threadsafe_queue.h")',
    'list(APPEND video_sources "${EDEN_GPU_WORKER}")',
):
    assert marker in CMAKE,marker
for forbidden in ("gpu_thread_quiet.cpp","gpu_thread_dev.cpp","EDEN_GPU_WORKER_VARIANT"):
    assert forbidden not in CMAKE,forbidden
entry=subprocess.check_output(["git","ls-tree","HEAD","vendor"],cwd=ROOT,text=True).split()
vendor_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT/"vendor",text=True).strip()
assert len(entry)==4 and entry[0]=="160000" and entry[1]=="commit" and entry[2]==vendor_head
print("CANONICAL_GPU_WORKER_SOURCE_PASS single_owner=1 direct_cmake=1 legacy_variants=0")
