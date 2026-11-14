#!/usr/bin/env python3
"""Qualify PS5 native UsageTracker include selected from exact paired vendor.

Historical Eden header remains untouched and the original engine vendor
gitlink should still resolve to that header. A reviewed vendor supplies a
separate include overlay, automatically selected only for PS5_NATIVE.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PORT=ROOT/"headless/CMakeLists.txt"
PINNED=ROOT/"vendor/sources/eden/src/video_core/buffer_cache/usage_tracker.h"
OWNED=ROOT/"vendor/encore-active/eden-core/overrides/usage-tracker/video_core/buffer_cache/usage_tracker.h"
CMAKE=PORT.read_text()

def gitblob(path:Path)->str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
assert gitblob(PINNED)=="6f84e463e32b3e839e200e79dfb93f14f2b14aef", "pinned Eden header moved"
assert "if(PS5_NATIVE)" in CMAKE
for value in (
    'set(EDEN_PS5_USAGE_TRACKER_ROOT',
    'vendor/encore-active/eden-core/overrides/usage-tracker',
    'if(EXISTS "${EDEN_PS5_USAGE_TRACKER_HEADER}")',
    'target_include_directories(video_core BEFORE PRIVATE',
    'message(STATUS "PS5 Vulkan: reviewed 64-byte UsageTracker header selected")',
    'message(STATUS "PS5 Vulkan: pinned baseline UsageTracker header selected")',
    'set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS',
):
    assert value in CMAKE,value
begin=CMAKE.index('# Eglantine #462: PS5 Vulkan BufferCache::CanReorderUpload')
end=CMAKE.index('# The texture-cache small-vector',begin)
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
if OWNED.exists():
    assert gitblob(OWNED)=="28d2f4f215b68a00de32e49ba0bfc87de139827e", (
        "unreviewed PS5 UsageTracker override")
    source=OWNED.read_text()
    assert "last_bit - first_bit + 1" in source
    assert "if (first_page == last_page) return false;" in source
else:
    assert not OWNED.exists()
print("PS5_USAGE_TRACKER_ENGINE_SELECTION_HOST_PASS "
      f"candidate={int(OWNED.exists())} original_header_pinned=1 "
      "source_owner=video_core BEFORE PRIVATE PS5_only=1 console=unverified")
