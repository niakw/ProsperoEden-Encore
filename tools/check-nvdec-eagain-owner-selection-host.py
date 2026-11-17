#!/usr/bin/env python3
"""Fail-closed NS1 FFmpeg EAGAIN native owner pair receipt.

Original Eden snapshot is immutable; the reviewed source and header MUST
appear together and be selected together in PS5 native CMake. Host-only.
"""
from __future__ import annotations
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
ORIG_SOURCE=V/"sources/eden/src/video_core/host1x/ffmpeg.cpp"
ORIG_HEADER=V/"sources/eden/src/video_core/host1x/ffmpeg.h"
CAND_SOURCE=V/"encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp"
CAND_HEADER=V/"encore-active/eden-core/overrides/video_core/host1x/ffmpeg.h"
ORIG_VIC=V/"sources/eden/src/video_core/host1x/vic.cpp"
CAND_VIC=V/"encore-active/eden-core/src/video_core/host1x/vic.cpp"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

assert blob(ORIG_SOURCE)=="676e5820a592b194d0c72ee61bfa67a0fa29f45a"
assert blob(ORIG_HEADER)=="00cd3f5d4d9571b4c8de944e3aec8988d11ccda5"
assert CAND_SOURCE.is_file()==CAND_HEADER.is_file(), "Half-selected NVDEC source/header ABI"
if CAND_SOURCE.exists():
    expected_ff="2eadc437cec5559560e5aaf849dd3b6446782e99" if CAND_VIC.is_file() else "4f12f3cc625b5d74f72272b9ac156c8be7a839e0"
    assert blob(CAND_SOURCE)==expected_ff
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
    'set(EDEN_NVDEC_HEADER_DIR "${PORT_BUILD_DIR}/nvdec-eagain")',
    'configure_file("${EDEN_NVDEC_MAINTAINED_HEADER}"',
    '"${EDEN_NVDEC_HEADER_DIR}/video_core/host1x/ffmpeg.h" COPYONLY)',
    'message(FATAL_ERROR "NVDEC maintained FFmpeg source/header pair incomplete")',
):
    assert marker in CMAKE,marker
part=CMAKE.split("# NS1 NVDEC/FFmpeg EAGAIN:",1)[1].split(
    "# NS1 VIC bounded surface witness:",1)[0]
assert part.count("if(PS5_NATIVE)")==1
assert part.count("\n    if(EXISTS ")==1
assert part.count("\n    elseif(EXISTS ")==1
assert part.count('list(APPEND eden_nvdec_video_sources')==1
assert part.count('target_include_directories(video_core BEFORE PUBLIC')==1
active_cmake = "\n".join(
    line for line in part.splitlines()
    if not line.lstrip().startswith("#")
)
assert "vendor/sources/eden" not in active_cmake
assert '"${EDEN_NVDEC_OWNER_ROOT}/overrides"' not in part, (
    "Broad FFmpeg header include root could shadow unrelated core headers")
assert part.count('configure_file("${EDEN_NVDEC_MAINTAINED_HEADER}"')==1
# configure_file owns the configure-time dependency for the copied header.
# A second explicit registration made Ninja reject the native build graph.
assert "CMAKE_CONFIGURE_DEPENDS" not in active_cmake, (
    "NVDEC configure_file input must not also be listed in configure dependencies")
print("NVDEC_EAGAIN_NATIVE_SELECTED_SOURCE_RECEIPT_PASS",
      "original_Eden_pristine=1",
      f"reviewed_vendor_candidate={int(CAND_SOURCE.is_file())}",
      "matched_ABI=1 PS5_NATIVE_only=1 console_unverified=1")


# The VIC witness and FFmpeg decode witness are an exact reviewed pair.
# Reject silent activation of only one side and retain pristine original.
assert blob(ORIG_VIC)=="1a89f3de06981f95be9e5dc743a7c36b8ab6c4cf"
if CAND_VIC.exists():
    assert CAND_SOURCE.is_file() and CAND_HEADER.is_file()
    assert blob(CAND_VIC)=="48008fc5f3b05c3e95432827c03e20b815cce21c"
    vic_text=CAND_VIC.read_text()
    ff_text=CAND_SOURCE.read_text()
    assert vic_text.count("EDEN_NVDEC_STAGE stage=vic_input")==2
    assert vic_text.count("EDEN_NVDEC_STAGE stage=vic_output")==2
    assert ff_text.count("EDEN_NVDEC_STAGE stage=decode")==2
    # Current PS5 diagnostic mirrors only the first bounded decode/VIC receipts
    # to the standard console trace, so ordinary user logs can separate decode,
    # VIC input and VIC output without enabling expensive detailed logging.
    assert "EncoreDetailedVideoLogEnabled()" not in ff_text
    assert "EncoreDetailedVideoLogEnabled()" not in vic_text
    assert "eden_native_detailed_logging" not in ff_text
    assert "eden_native_detailed_logging" not in vic_text
    assert ff_text.count("std::fprintf(stderr") >= 1
    assert vic_text.count("std::fprintf(stderr") >= 2

# Exercise the actual CMake source-list branch in a no-compiler fixture.
# This tests selection and failure modes, not real native VIC compilation.
vic_part=CMAKE.split("# NS1 VIC bounded surface witness:",1)[1].split(
    "# The texture-cache small-vector",1)[0]
vic_part=vic_part[vic_part.index("if(PS5_NATIVE)"):]
assert vic_part.count('list(REMOVE_ITEM eden_vic_video_sources "host1x/vic.cpp")')==1
assert vic_part.count('list(APPEND eden_vic_video_sources "${EDEN_VIC_MAINTAINED_SOURCE}")')==1

def check_vic_graph(native, maintained, pair, original_count=1, duplicate=False,
                    failure=None):
    with tempfile.TemporaryDirectory(prefix="encore-vic-owner-") as folder:
        root=Path(folder)
        (root/"host1x").mkdir()
        (root/"host1x/vic.cpp").touch()
        (root/"other.cpp").touch()
        active=root/"vendor/encore-active/eden-core"
        ff=active/"src/video_core/host1x/ffmpeg.cpp"
        vic=ff.with_name("vic.cpp")
        hdr=active/"overrides/video_core/host1x/ffmpeg.h"
        if maintained:
            vic.parent.mkdir(parents=True,exist_ok=True)
            vic.touch()
        if pair:
            for p in (ff,hdr):
                p.parent.mkdir(parents=True,exist_ok=True)
                p.touch()
        sources=["host1x/vic.cpp"]*original_count+["other.cpp"]
        if duplicate:
            sources.append(str(vic))
        preamble=(
            "cmake_minimum_required(VERSION 3.20)\nproject(vic NONE)\n"
            +f"set(PS5_NATIVE {'ON' if native else 'OFF'})\n"
            +"set(PORT_ROOT \"${CMAKE_CURRENT_SOURCE_DIR}\")\n"
            +f'set(EDEN_NVDEC_MAINTAINED_SOURCE "{ff.as_posix()}")\n'
            +f'set(EDEN_NVDEC_MAINTAINED_HEADER "{hdr.as_posix()}")\n'
            +"add_custom_target(video_core SOURCES "
            +" ".join(f'"{p}"' for p in sources)+")\n"
        )
        (root/"CMakeLists.txt").write_text(preamble+vic_part+
            '\nget_target_property(actual video_core SOURCES)\n'
            'file(WRITE "${CMAKE_BINARY_DIR}/owners.txt" "${actual}")\n')
        proc=subprocess.run(["cmake","-S",str(root),"-B",str(root/"build")],
                            text=True,capture_output=True,timeout=30)
        if failure:
            assert proc.returncode!=0 and failure in proc.stderr,proc.stdout+proc.stderr
            return
        assert proc.returncode==0,proc.stdout+proc.stderr
        owners=(root/"build/owners.txt").read_text().split(";")
        expected=(["other.cpp",str(vic)] if native and maintained else sources)
        assert owners==expected,(owners,expected)

check_vic_graph(True,False,True)
check_vic_graph(True,False,False)
check_vic_graph(False,True,True)
check_vic_graph(True,True,True)
check_vic_graph(True,True,False,failure="requires the FFmpeg source/header pair")
check_vic_graph(True,True,True,original_count=0,failure="Expected exactly one original VIC")
check_vic_graph(True,True,True,original_count=2,failure="Expected exactly one original VIC")
check_vic_graph(True,True,True,duplicate=True,failure="already selected")
print("NS1_VIC_NATIVE_GRAPH_HOST_PASS fallback=2 host_unchanged=1 selected=1 failure_cases=4 console_unverified=1")
