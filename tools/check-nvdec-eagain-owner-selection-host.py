#!/usr/bin/env python3
"""Fail-closed NS1 FFmpeg EAGAIN native owner pair receipt.

Original Eden snapshot is immutable; the reviewed source and header MUST
appear together and be selected together in PS5 native CMake. Host-only.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
ORIG_SOURCE=V/"sources/eden/src/video_core/host1x/ffmpeg.cpp"
ORIG_HEADER=V/"sources/eden/src/video_core/host1x/ffmpeg.h"
CAND_SOURCE=V/"encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp"
CAND_HEADER=V/"encore-active/eden-core/overrides/video_core/host1x/ffmpeg.h"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

assert blob(ORIG_SOURCE)=="676e5820a592b194d0c72ee61bfa67a0fa29f45a"
assert blob(ORIG_HEADER)=="00cd3f5d4d9571b4c8de944e3aec8988d11ccda5"
assert CAND_SOURCE.is_file()==CAND_HEADER.is_file(), "Half-selected NVDEC source/header ABI"
if CAND_SOURCE.exists():
    assert blob(CAND_SOURCE)=="4f12f3cc625b5d74f72272b9ac156c8be7a839e0"
    assert blob(CAND_HEADER)=="4bca3f84dbc224e925e18c28001286ee0e337448"
    src=CAND_SOURCE.read_text()
    h=CAND_HEADER.read_text()
    for marker in ("constexpr int kMaxDrainRetries = 16",
                   "ret != AVERROR(EAGAIN)",
                   "m_decoder_context->ReceiveFrame()",
                   "m_ready_frames.push(std::move(drained))",
                   "m_pending_offsets.push(offsets)",
                   "++m_next_pts;"):
        assert marker in src,("NVDEC EAGAIN candidate source drift",marker)
    assert "int SendPacket(const Packet& packet);" in h
    assert "std::queue<std::shared_ptr<Frame>> m_ready_frames;" in h
for marker in (
    "if(PS5_NATIVE)",
    "EDEN_NVDEC_MAINTAINED_SOURCE",
    "EDEN_NVDEC_MAINTAINED_HEADER",
    'get_target_property(eden_nvdec_video_sources video_core SOURCES)',
    'list(FIND eden_nvdec_video_sources "host1x/ffmpeg.cpp" eden_nvdec_old_source)',
    'list(REMOVE_ITEM eden_nvdec_video_sources "host1x/ffmpeg.cpp")',
    'list(APPEND eden_nvdec_video_sources "${EDEN_NVDEC_MAINTAINED_SOURCE}")',
    'set_property(TARGET video_core PROPERTY SOURCES "${eden_nvdec_video_sources}")',
    'target_include_directories(video_core BEFORE PUBLIC',
    'message(FATAL_ERROR "NVDEC maintained FFmpeg source/header pair incomplete")',
):
    assert marker in CMAKE,marker
part=CMAKE.split("# NS1 NVDEC/FFmpeg EAGAIN:",1)[1].split(
    "# The texture-cache small-vector",1)[0]
assert part.count("if(PS5_NATIVE)")==1
assert part.count("\n    if(EXISTS ")==1
assert part.count("\n    elseif(EXISTS ")==1
assert part.count('list(APPEND eden_nvdec_video_sources')==1
assert part.count('target_include_directories(video_core BEFORE PUBLIC')==1
assert "vendor/sources/eden" not in part
print("NVDEC_EAGAIN_NATIVE_SELECTED_SOURCE_RECEIPT_PASS",
      "original_Eden_pristine=1",
      f"reviewed_vendor_candidate={int(CAND_SOURCE.is_file())}",
      "matched_ABI=1 PS5_NATIVE_only=1 console_unverified=1")
