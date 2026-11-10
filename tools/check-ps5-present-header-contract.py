#!/usr/bin/env python3
"""Verify the selected native PresentManager ABI against the pinned Vulkan owner.

Runs before toolchain installation: a real source-header ownership check, not
a replacement for C++ syntax, linking or execution on PS5.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
native_header = (root / "headless/vk_present_manager_r08.h").read_text()
owner_header = (root / "vendor/encore-active/eden-vulkan/include/"
                "video_core/renderer_vulkan/vk_present_manager.h").read_text()
owner_cpp = (root / "vendor/encore-active/eden-vulkan/"
             "vulkan_present_manager.cpp").read_text()

# Only compare the shared worker state; Encore legitimately extends the
# public class with non-blocking frame-generation reservation methods.
fields = (
    "std::condition_variable_any frame_cv;",
    "std::condition_variable_any present_ready_cv;",
    "std::condition_variable free_cv;",
    "std::mutex swapchain_mutex;",
    "std::mutex queue_mutex;",
    "std::mutex free_mutex;",
    "std::size_t free_waiters{};",
    "bool present_in_flight{};",
    "std::size_t present_waiters{};",
    "std::exception_ptr present_failure;",
    "std::jthread present_thread;",
)
def statements(text):
    return [line.split("//", 1)[0].strip() for line in text.splitlines()]
for label, text in (("native header", native_header),
                    ("pinned owner header", owner_header)):
    selected = statements(text)
    indexes = []
    for field in fields:
        assert selected.count(field) == 1, f"{label}: missing or duplicated {field}"
        indexes.append(selected.index(field))
    assert indexes == sorted(indexes), f"{label}: synchronization state order drift"

required_source = (
    "++free_waiters;", "--free_waiters;",
    "++present_waiters;", "--present_waiters;",
    "present_ready_cv.notify_one();",
    "present_ready_cv.wait(lock, token,",
    "free_cv.wait(lock,", "frame_cv.wait(queue_lock,",
    "wake_free_waiter = free_waiters != 0;",
    "notify_drainers = present_waiters != 0 && present_queue.empty();",
)
for clause in required_source:
    assert clause in owner_cpp, f"Pinned presenter changed: {clause}"
assert "Frame* TryReserveRenderFrame()" in native_header
assert "void CancelReservedRenderFrame(Frame* frame)" in native_header
assert "void ConfirmReservedRenderFrame(Frame* frame)" in native_header
print("PS5_PRESENT_HEADER_OWNER_PARITY_PASS")
