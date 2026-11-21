#!/usr/bin/env python3
"""Fail-closed NS1 FFmpeg EAGAIN native owner pair receipt.

Original Eden snapshot is immutable; the reviewed source and header MUST
appear together and be selected together in PS5 native CMake. Host-only.
"""
from __future__ import annotations
import hashlib
import shutil
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
    assert blob(CAND_VIC)=="d1ff5e88ad4fb20426393255a6bdd640c50f9d7c"
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
    # Pin the whole selected VIC owner and its reviewed pixel-copy guards.
    for token in ("if (method >= VicRegisters::NUM_REGS)",
                  "output_pixels > MAX_VIC_PIXELS",
                  "slot_width * slot_height * fields > MAX_VIC_PIXELS",
                  "source_left >= source_right || source_top >= source_bottom",
                  "slot_surface.size() / in_surface_width",
                  "continue; // No decoded pixels to blend."):
        assert token in vic_text, token
    assert vic_text.count("for (u32 x = 0; x < work_width; x") == 2
    assert vic_text.count("const size_t src = static_cast<size_t>(y) * in_surface_width + source_left;") == 2
    assert vic_text.count("const size_t dst = static_cast<size_t>(y) * out_surface_width + rect_left;") == 2
    assert vic_text.count("_mm_loadu_si128(") >= 4
    assert vic_text.count("_mm_storeu_si128(") >= 4

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

# GPU-32: compile the scalar color-conversion loop from the REAL selected
# VIC together with its clipping/decoded-buffer admission. This isolates
# the source/destination indexing bug without inventing video pixels.
VIC_TEXT=CAND_VIC.read_text()
BLEND=VIC_TEXT[VIC_TEXT.index("void Vic::Blend("):VIC_TEXT.index("void Vic::WriteY8__V8U8_N420(")]
CLIP=BLEND[BLEND.index("    source_bottom = (std::min)(source_bottom, out_surface_height);"):
           BLEND.index("    // TODO Alpha blending.")]
# The original function returns void; the host witness reports admission.
CLIP=CLIP.replace("        return;", "        return false;")
BEGIN=BLEND.index("            // Colour conversion is enabled")
LOOP_BEGIN=BLEND.index("            for (u32 y = source_top; y < source_bottom; y++) {",BEGIN)
LOOP_END=BLEND.index(chr(10)+"        }"+chr(10)+"    } else {",LOOP_BEGIN)
SCALAR=BLEND[LOOP_BEGIN:LOOP_END]
assert "for (u32 x = 0; x < work_width; x++)" in SCALAR
cpp=r"""
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <tuple>
#include <vector>
using u32=std::uint32_t;
using u16=std::uint16_t;
using s32=std::int32_t;
struct Pixel {u16 r{},g{},b{},a{};};
bool Copy(std::vector<Pixel>& slot_surface, std::vector<Pixel>& output_surface,
          u32 source_left,u32 source_right,u32 source_top,u32 source_bottom,
          u32 rect_left,u32 rect_right,u32 rect_top,u32 rect_bottom,
          u32 in_surface_width,u32 out_surface_width,u32 out_surface_height) {
__CLIP__
    (void)work_height;
    const s32 clamp_min=0,clamp_max=65535;
    const auto MatMul=[](const Pixel& p)->std::tuple<s32,s32,s32,s32> {
        return {p.r,p.g,p.b,p.a};
    };
__SCALAR__
    return true;
}
int main() {
    std::vector<Pixel> src(32),out(32,Pixel{999,999,999,999});
    for(u32 i=0;i<32;++i) src[i]={u16(i+1),u16(i+1),u16(i+1),65535};
    assert(Copy(src,out,8,16,1,2,8,16,1,2,16,16,2));
    for(u32 x=0;x<16;++x) {
        const u16 expected=x>=8?u16(17+x):999;
        assert(out[16+x].r==expected);
    }
    assert(!Copy(src,out,16,8,1,2,8,16,1,2,16,16,2));
    assert(!Copy(src,out,8,16,3,4,8,16,3,4,16,16,2));
    assert(!Copy(src,out,8,16,2,4,8,16,2,4,16,16,4));
    std::fill(out.begin(),out.end(),Pixel{999,999,999,999});
    assert(Copy(src,out,10,14,1,2,8,16,1,2,16,16,2));
    for(u32 x=0;x<16;++x) {
        const u16 expected=(x>=8&&x<12)?u16(17+x+2):999;
        assert(out[16+x].r==expected);
    }
}
""".replace("__CLIP__",CLIP).replace("__SCALAR__",SCALAR)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler, "Clang required for VIC sanitizer witness"
with tempfile.TemporaryDirectory(prefix="encore-vic-blend-") as temp:
    src=Path(temp)/"vic-blend.cpp"
    src.write_text(cpp)
    for opt in ("-O0","-O2"):
        exe=Path(temp)/("vic-blend-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(src),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_VIC_BLEND_BOUNDS_HOST_PASS selected_scalar=1 nonzero_origin=1 "
      "empty_clip=1 decoded_bounds=1 source_vs_dest_offsets=1 O0_O2=2 ASan_UBSan=1")
