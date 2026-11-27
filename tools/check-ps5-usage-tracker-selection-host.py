#!/usr/bin/env python3
"""Qualify the current PS5 UsageTracker owner selected from encore-active.

The upstream source stays under vendor/sources; the maintained final header is
vendor/encore-active and must be selected for PS5_NATIVE. No revision hashes
are part of this contract.
"""
from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PORT=ROOT/"headless/CMakeLists.txt"
PINNED=ROOT/"vendor/sources/eden/src/video_core/buffer_cache/usage_tracker.h"
OWNED=ROOT/"vendor/encore-active/eden/src/video_core/buffer_cache/usage_tracker.h"
CMAKE=PORT.read_text()

assert PINNED.is_file(), "upstream UsageTracker baseline missing"
assert OWNED.is_file(), "maintained UsageTracker must live in encore-active"
assert "if(PS5_NATIVE)" in CMAKE
for value in (
    'set(EDEN_PS5_USAGE_TRACKER_ROOT',
    'vendor/encore-active/eden/src',
    'if(EXISTS "${EDEN_PS5_USAGE_TRACKER_HEADER}")',
    'target_include_directories(video_core BEFORE PRIVATE',
    'message(STATUS "PS5 Vulkan: reviewed 64-byte UsageTracker header selected")',
    'message(STATUS "PS5 Vulkan: pinned baseline UsageTracker header selected")',
    'set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS',
):
    assert value in CMAKE, value
begin=CMAKE.index('# Eglantine #462: PS5 Vulkan BufferCache::CanReorderUpload')
# The NVDEC source selector was added AFTER this independent Vulkan
# header selector. Do not inadvertently count its extra native if()/endif().
end=min(CMAKE.index('# The texture-cache small-vector',begin),
        CMAKE.index('# NS1 NVDEC/FFmpeg EAGAIN:',begin))
block=CMAKE[begin:end]
assert block.count('if(PS5_NATIVE)')==1
assert block.count('if(EXISTS "${EDEN_PS5_USAGE_TRACKER_HEADER}")')==1
assert block.count('target_include_directories(video_core BEFORE PRIVATE')==1
assert block.count('endif()')==2
assert 'file(WRITE' not in block and 'file(COPY' not in block
assert CMAKE.index('if(PS5_NATIVE)',begin)<CMAKE.index(
    'target_include_directories(video_core BEFORE PRIVATE',begin)
assert "CanReorderUpload" in (
    ROOT/"vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp").read_text()
source=OWNED.read_text()
assert "last_bit - first_bit + 1" in source
assert "if (first_page == last_page) return false;" in source
assert "set_begin{pages.size()}" in source
assert "set_begin = std::min(set_begin, first_page);" in source
assert "set_end = std::max(set_end, last_page + 1);" in source
assert "if (set_begin == pages.size()) return;" in source
assert "pages.begin() + static_cast<std::ptrdiff_t>(set_begin)" in source
assert "recent.fill({~u64{0}, 0});" in source
assert "recent[recent_cursor++ % recent.size()] = {offset, size};" in source
print("PS5_USAGE_TRACKER_ENGINE_SELECTION_HOST_PASS "
      "candidate=1 upstream_baseline_present=1 "
      "source_owner=video_core BEFORE PRIVATE PS5_only=1 console=unverified")
