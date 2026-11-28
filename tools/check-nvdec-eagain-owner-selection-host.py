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
CAND_SOURCE=V/"encore-active/eden/src/video_core/host1x/ffmpeg.cpp"
CAND_HEADER=V/"encore-active/eden/src/video_core/host1x/ffmpeg.h"
ORIG_VIC=V/"sources/eden/src/video_core/host1x/vic.cpp"
CAND_VIC=V/"encore-active/eden/src/video_core/host1x/vic.cpp"
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
    assert blob(CAND_VIC)=="178d361bc3b5e9a0bf6ca9fa579d49df7ab72935"
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
    # A guest FFmpeg frame's NV12 plane, odd-width decoded Pixel row or
    # mapped output address is not guaranteed to be 16-byte aligned.
    # All VIC SIMD byte accesses must use the unaligned SSE intrinsics.
    assert "_mm_load_si128(" not in vic_text
    assert "_mm_store_si128(" not in vic_text
    assert vic_text.count("_mm_loadu_si128(") == 21
    assert vic_text.count("_mm_storeu_si128(") == 18
    assert vic_text.count("CheckedVicPlane(") == 4
    assert "out_chroma_stride < (static_cast<u64>(surface_width) + 1) / 2 * 2" in vic_text
    assert "out_chroma_height < (static_cast<u64>(surface_height) + 1) / 2" in vic_text
    assert "for (; x + 1 < surface_width; x += 2)" in vic_text
    assert "if (x < surface_width) {" in vic_text
    assert "out_chroma_width, out_chroma_height, 1, block_height, 0, 3" in vic_text
    assert "out_luma_width, out_luma_height, 1, block_height, 0, 4" in vic_text
    assert "out_luma_width, out_luma_height, 1, block_height, 0, 2" in vic_text
    assert "block_height == 1 && (out_luma_height & 1) == 0" in vic_text

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
        active=root/"vendor/encore-active/eden"
        ff=active/"src/video_core/host1x/ffmpeg.cpp"
        vic=ff.with_name("vic.cpp")
        hdr=active/"src/video_core/host1x/ffmpeg.h"
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

# The historical fallback intentionally has no maintained FFmpeg/VIC pair.
# Its original hashes, CMake fallback and graph failure cases are already
# qualified above. Candidate-only GPU/VIC fixtures start below.
if not CAND_VIC.exists():
    print("NVDEC_HISTORICAL_FALLBACK_PASS maintained_pair=0 original_pristine=1")
    raise SystemExit(0)

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

# GPU-33: run the real production VIC's u64 GOB/pitch admission and its
# exact YUV420 scalar loop. Do not mistake this for a PS5 TU compilation.
NATIVE_VIC=CAND_VIC.read_text()
PLANE=NATIVE_VIC[
    NATIVE_VIC.index("bool CheckedVicPlane("):
    NATIVE_VIC.index("void SwizzleSurface(")]
YU=NATIVE_VIC[NATIVE_VIC.index("void Vic::WriteY8__V8U8_N420("):
              NATIVE_VIC.index("void Vic::WriteABGR(")]
YBEGIN=YU.index("        } else {"+chr(10)+"            for (size_t y = 0; y < surface_height; ++y) {")
YEND=YU.index(chr(10)+"        }"+chr(10)+"    };",YBEGIN)
ODD_LOOP=YU[YBEGIN+len("        } else {"+chr(10)):YEND]
assert "if (x < surface_width)" in ODD_LOOP
cpp=r"""
#include <cassert>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>
using u8=std::uint8_t;
using u16=std::uint16_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
namespace Texture {
std::size_t CalculateSize(bool tiled,u32 bpp,u32 w,u32 h,u32 depth,u32 bh,u32 bd){
    if(!tiled) return u32(w*h*depth*bpp);
    const u32 aw=((u32(w*bpp)+63u)/64u)*64u;
    const u32 block_h=8u<<bh;
    const u32 ah=((h+block_h-1u)/block_h)*block_h;
    const u32 ad=((depth+(1u<<bd)-1u)/(1u<<bd))*(1u<<bd);
    return u32(aw*ah*ad);
}
}
__PLANE__
struct Pixel {u16 r{},g{},b{},a{};};
void Decode(const std::vector<Pixel>& output_surface,std::vector<u8>& luma,
            std::vector<u8>& chroma,u32 surface_width,u32 surface_height,
            u32 surface_stride,u32 out_luma_stride,u32 out_chroma_stride) {
    auto* out_luma=luma.data();
    auto* out_chroma=chroma.data();
__ODD_LOOP__
}
int main() {
    assert(CheckedVicPlane(1920,1080,4,true,1));
    assert(CheckedVicPlane(1920,1080,1,true,1));
    assert(CheckedVicPlane(960,540,2,true,1));
    assert(CheckedVicPlane(1,3,2,true,1));
    assert(CheckedVicPlane(16384,16384,4,false,0)==false);
    assert(CheckedVicPlane(16384,16384,4,true,5)==false);
    assert(CheckedVicPlane(16384,16384,2,true,5)==false);
    assert(!CheckedVicPlane(1920,1080,1,true,6));
    assert(!CheckedVicPlane(0,1080,1,true,1));
    assert(!CheckedVicPlane(1080,0,1,true,1));
    assert(!CheckedVicPlane(1920,1080,0,true,1));
    assert(CheckedVicPlane(4096,2160,4,true,2));
    std::vector<Pixel> pixels{{4,40,80,0},{8,44,84,0},
                              {12,48,88,0},{16,52,92,0},
                              {20,56,96,0},{24,60,100,0}};
    // 3x2 pixels, two luma bytes/rows? 16B-strided luma, one UV row.
    // Host ASan would catch the old x+1 luma pixel on the last row.
    std::vector<u8> luma(32,0xea), chroma(16,0xe9);
    Decode(pixels,luma,chroma,3,2,3,16,16);
    for(u32 y=0;y<2;++y)for(u32 x=0;x<3;++x)
        assert(luma[y*16+x] == pixels[y*3+x].r / 4);
    assert(luma[19] == 0xea && luma[3] == 0xea);
    assert(chroma[0] == pixels[3].g/4 && chroma[1] == pixels[3].b/4);
    assert(chroma[2] == pixels[5].g/4 && chroma[3] == pixels[5].b/4);
    assert(chroma[4] == 0xe9);
    // A one-pixel-wide decoded surface still writes a full UV pair safely.
    std::vector<Pixel> single{{100,120,140,0}};
    std::vector<u8> luma1(16,0),uv1(16,0);
    Decode(single,luma1,uv1,1,1,1,16,16);
    assert(luma1[0]==25 && uv1[0]==30 && uv1[1]==35);
}
""".replace("__PLANE__",PLANE).replace("__ODD_LOOP__",ODD_LOOP)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler,"Need host Clang for VIC u64 plane witness"
with tempfile.TemporaryDirectory(prefix="encore-vic-planes-") as folder:
    source=Path(folder)/"vic-planes.cpp"
    source.write_text(cpp)
    for opt in ("-O0","-O2"):
        exe=Path(folder)/("planes-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_VIC_PLANE_HOST_PASS native_geometry=1 oversized_rejected=1 "
      "bad_gob_rejected=1 valid_4k=1 odd_width_UV=1 last_row=1 O0_O2=2 ASan_UBSan=1")

# GPU-52: the native VIC scratch buffer is not zero-initialized on reuse.
# Both partial progressive and partial Bob-decoded surfaces must be scrubbed.
vic_gpu52=CAND_VIC.read_text()
vic_gpu52_guard="if (in_luma_width < s32(out_luma_width) || in_luma_height < s32(out_luma_height)) {"
vic_prog=vic_gpu52[vic_gpu52.index("void Vic::ReadProgressiveY8__V8U8_N420"):vic_gpu52.index("void Vic::ReadInterlacedY8__V8U8_N420")]
vic_bob=vic_gpu52[vic_gpu52.index("void Vic::ReadInterlacedY8__V8U8_N420"):vic_gpu52.index("void Vic::ReadY8__V8U8_N420")]
assert vic_prog.count(vic_gpu52_guard)==1
assert vic_bob.count(vic_gpu52_guard)==1
for path in (vic_prog,vic_bob):
    assert "std::fill(slot_surface.begin(), slot_surface.end(), Pixel{});" in path

# GPU-42: compile the exact maintained VIC bob-field loop, not a hand-written
# proxy. The inherited loop used chroma_height*2 as a luma row limit and
# read one row past odd-height decoded frames for the bottom field.
vic_interlaced_source=CAND_VIC.read_text()
vic_interlaced_old=ORIG_VIC.read_text()
bob_sig="        auto DecodeBobField = [&]() {"
def extract_bob(source):
    start=source.index(bob_sig,source.index("void Vic::ReadInterlacedY8__V8U8_N420"))
    end=source.index("\n        };",start)+len("\n        };")
    return source[start:end]
native_bob=extract_bob(vic_interlaced_source)
old_bob=extract_bob(vic_interlaced_old)
partial_guard_start=vic_bob.index("        "+vic_gpu52_guard)
partial_guard_end=vic_bob.index("\n        }",partial_guard_start)+len("\n        }")
partial_guard_code=vic_bob[partial_guard_start:partial_guard_end]
assert "y < in_chroma_height * 2" in old_bob
assert "y < in_luma_height" in native_bob
assert "y < in_chroma_height * 2" not in native_bob
assert "auto const in_luma_height = (std::min)(frame->GetHeight(), s32(out_luma_height));" in vic_interlaced_source
assert native_bob.count("slot.config.planar_alpha.Value()")==1
# Only adapt the alpha register accessor to a literal in the isolated C++
# fixture. All actual indexing and memcpy statements stay byte-for-byte.
native_bob=native_bob.replace("slot.config.planar_alpha.Value()","255")
bob_fixture=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <tuple>
#include <vector>
using s32=std::int32_t; using u16=std::uint16_t;
struct Pixel { u16 r{},g{},b{},a{}; };
int main() {
  for(auto [decoded_h,out_h,top_field]:
      std::array<std::tuple<s32,s32,bool>,6>{{{5,6,false},{5,6,true},
                                                {4,6,false},{9,6,false},{1,6,false},
                                                {6,6,false}}}) {
    s32 in_luma_width=4,out_luma_width=4,out_luma_stride=4,out_luma_height=out_h;
    s32 in_luma_stride=4,in_chroma_stride=4;
    s32 in_luma_height=std::min(decoded_h,out_h);
    std::vector<std::uint8_t> luma(decoded_h*in_luma_stride,77);
    std::vector<std::uint8_t> chroma_u(((decoded_h+1)/2)*in_chroma_stride,12);
    std::vector<std::uint8_t> chroma_v(((decoded_h+1)/2)*in_chroma_stride,23);
    auto const* luma_buffer=luma.data();
    auto const* chroma_u_buffer=chroma_u.data();
    auto const* chroma_v_buffer=chroma_v.data();
    std::vector<Pixel> slot_surface(out_h*out_luma_width, Pixel{65000,65000,65000,65000});
 __PARTIAL_CLEAR__
    assert(slot_surface.back().r == (in_luma_height < out_luma_height ? 0 : 65000));
    bool planar=true;
__NATIVE_BOB__
    DecodeBobField();
    s32 first=top_field?0:1;
    if(first<in_luma_height) {
       assert(slot_surface[first*out_luma_width].r==308);
       assert(slot_surface[(top_field?first+1:first-1)*out_luma_width].r==308);
    }
  }
}
""".replace("__NATIVE_BOB__",native_bob).replace("__PARTIAL_CLEAR__",partial_guard_code)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler, "Clang required for real VIC interlaced ASan/UBSan witness"
with tempfile.TemporaryDirectory(prefix="encore-vic-bob-gpu42-") as folder:
    source=Path(folder)/"vic-bob.cpp"
    source.write_text(bob_fixture)
    for opt in ("-O0","-O2"):
        binary=Path(folder)/("vic-bob-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra",
                        "-Werror","-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all",str(source),"-o",str(binary)],
                       check=True,timeout=50)
        subprocess.run([str(binary)],check=True,timeout=20)
print("NS1_VIC_PARTIAL_SLOT_CLEAR_PASS native_guard=1 partial=1 full_unchanged=1 O0_O2=2 ASan_UBSan=1")
print("NS1_VIC_INTERLACED_BOB_BOUNDS_PASS actual_lambda=1 odd_bottom=1 "
      "odd_top=1 even_bottom=1 slot_clamp=1 empty_bottom=1 ASan_UBSan=1 O0_O2=2")

# GPU-34: compile the exact four reviewed intrinsics from the maintained
# VIC on deliberately 8-byte/1-byte-offset memory, with SSE4.1 + ASan.
# The previous _mm_load/store_si128 assumed 16-byte alignment not supplied
# by odd decoded Pixel row strides or guest NV12/luma destinations.
VIC_SSE=CAND_VIC.read_text()
tested_statements=(
    "auto pixel01 = _mm_loadu_si128((__m128i*)&inp[src + x + 0]);",
    "_mm_storeu_si128((__m128i*)&slot_surface[dst + x + 0], yuv01);",
    "chroma = _mm_loadu_si128((__m128i*)&chroma_u_buffer[src_chroma + x]);",
    "_mm_storeu_si128((__m128i*)&out[dst + x * 4 + 0], pixels0_lo);",
)
for statement in tested_statements:
    assert VIC_SSE.count(statement)==1, statement
sse_cpp=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <immintrin.h>
using u8=std::uint8_t;
using u16=std::uint16_t;
struct Pixel {u16 r{},g{},b{},a{};};
int main() {
    alignas(16) std::array<Pixel,10> input{};
    for(std::size_t i=0;i<input.size();++i) input[i].r=u16(i+1);
    const Pixel* inp=input.data();
    std::size_t src=1,x=0;
    assert((reinterpret_cast<std::uintptr_t>(&inp[src]) & 15)==8);
__LOAD__
    alignas(16) std::array<Pixel,10> slot_surface{};
    const std::size_t dst=1;
    const auto yuv01=pixel01;
    assert((reinterpret_cast<std::uintptr_t>(&slot_surface[dst]) & 15)==8);
__STORE__
    assert(slot_surface[dst].r==input[src].r);
    alignas(16) std::array<u8,32> nv12{};
    for(std::size_t i=0;i<nv12.size();++i) nv12[i]=u8(i);
    const u8* chroma_u_buffer=nv12.data();
    const std::size_t src_chroma=1;
    __m128i chroma{};
__NV12__
    alignas(16) std::array<u8,80> output{};
    u8* out=output.data();
    const std::size_t dst_bytes=1;
    const auto pixels0_lo=chroma;
    assert((reinterpret_cast<std::uintptr_t>(&out[dst_bytes]) & 15)==1);
__ABGR__
    assert(output[dst_bytes]==nv12[src_chroma]);
}
""".replace("__LOAD__",tested_statements[0]).replace("__STORE__",tested_statements[1])
# The scalar source expression uses a dst index shared with the Pixel
# fixture; the ABGR byte stream uses its own byte-index value.
sse_cpp=sse_cpp.replace("__NV12__",tested_statements[2])
sse_cpp=sse_cpp.replace("__ABGR__",tested_statements[3].replace("out[dst + x * 4", "out[dst_bytes + x * 4"))
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-vic-sse-") as folder:
    source=Path(folder)/"vic-sse.cpp"
    source.write_text(sse_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(folder)/("sse-"+opt[1:])
        subprocess.run([compiler,"-std=c++20","-msse4.1",opt,
                        "-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_VIC_SSE_UNALIGNED_HOST_PASS NV12_unaligned=1 Pixel_stride8=1 "
      "ABGR_byte_offset=1 ASan_UBSan=1 O0_O2=2")


# GPU-35: exact C++ Host1x signed FD device-array guard, maintained owner.
H1_CPP=V/"encore-active/eden/src/video_core/host1x/host1x.cpp"
H1_HDR=V/"encore-active/eden/src/video_core/host1x/host1x.h"
H1_ORIG_CPP=V/"sources/eden/src/video_core/host1x/host1x.cpp"
H1_ORIG_HDR=V/"sources/eden/src/video_core/host1x/host1x.h"
assert blob(H1_CPP)=="1815363b19282be07bb4217dd01f369a38e53272"
assert blob(H1_HDR)=="d716ee97dd8be807d2f29219c4b0c7072ed6b028"
assert blob(H1_ORIG_CPP)=="590b0e0ff2f7d5f9f3771b07659afcbb49814863"
assert blob(H1_ORIG_HDR)=="3b886a59d59763278d1c44b8b993d25f7260656d"
HS=H1_CPP.read_text();HH=H1_HDR.read_text()
OS=H1_ORIG_CPP.read_text();OH=H1_ORIG_HDR.read_text()
guard="fd < 0 || static_cast<std::size_t>(fd) >= devices.size()"
assert HS.count(guard)==3 and HH.count(guard)==0
assert HS.count("devices[fd]")==4 and "devices[fd]" not in HH
assert "std::array<std::mutex, 1024> device_dispatch_mutexes;" in HS
assert HS.count("std::scoped_lock lk{device_dispatch_mutexes[static_cast<std::size_t>(fd)]};")==3
assert "void Host1x::PushEntries(" in HS
assert "void PushEntries(s32 fd, ChCommandHeaderList&& entries);" in HH
assert "std::array<std::mutex, 1024> device_dispatch_mutexes" not in HH # no Host1x class size / ABI change
# Two dispatches and two guarded re-open probes; both happen after the FD preflight.
# The two StartDevice dispatches are reached only after the signed range guard.
start="void Host1x::StartDevice("
stop="void Host1x::StopDevice("
# All five reviewed Host1x methods are pinned by the whole source blob.
# The separate synchronization is intentionally in the TU, preserving the
# existing C++ type layout. The historical Eden source remains immutable.
assert "void Host1x::PushEntries(s32 fd, ChCommandHeaderList&& entries)" in HS
assert "std::array<std::mutex, 1024> device_dispatch_mutexes;" not in OS
assert "std::scoped_lock lk{device_dispatch_mutexes[static_cast<std::size_t>(fd)]};" not in OS
push="    void PushEntries(s32 fd,"
limit="\n    Core::System& system;"
new_push=HH[HH.index(push):HH.index(limit)]
old_push=OH[OH.index(push):OH.index(limit)]
assert HH.replace(
    "    // Submission and FD close/reopen can originate from different NVDRV\n"
    "    // service threads. Dispatch must not race with device variant teardown.\n",""
).replace(new_push,old_push,1).replace(
    "#include <variant>\n#include <cstddef>","#include <variant>")==OH
cm_fragment=CMAKE[CMAKE.index("# Native Host1x FD safety:"):CMAKE.index("# N54: shared PS5 texture-cache")]
for item in ("if(PS5_NATIVE)","list(FIND video_sources",
             "list(REMOVE_ITEM video_sources host1x/host1x.cpp)",
             "list(APPEND video_sources","configure_file(",
             "target_include_directories(video_core BEFORE PUBLIC",
             "target_include_directories(core BEFORE PUBLIC"):
    assert item in cm_fragment,item
assert cm_fragment.count("list(REMOVE_ITEM video_sources host1x/host1x.cpp)")==1
source_methods=HS[HS.index("Host1x::~Host1x()"):HS.index("} // namespace Tegra::Host1x")]
cpp=r"""
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <atomic>
#include <mutex>
#include <thread>
#include <utility>
#include <variant>
#include <vector>
using s32=std::int32_t;
using u32=std::uint32_t;
#define LOG_ERROR(...) ((void)0)
namespace Tegra::Host1x {
std::array<std::mutex, 1024> device_dispatch_mutexes;
std::atomic<bool> submit_entered{false};
std::atomic<bool> submit_release{false};
std::atomic<bool> close_finished{false};
using ChCommandHeaderList=std::vector<int>;
enum class ChannelType:u32 {MsEnc=0,VIC=1,GPU=2,NvDec=3};
struct Host1x;
struct Nvdec {
    s32 fd;
    unsigned submits=0;
    Nvdec(Host1x&,s32 n,u32):fd(n){}
    void PushEntries(ChCommandHeaderList&& a) {
        if(fd==7){
            submit_entered.store(true,std::memory_order_release);
            while(!submit_release.load(std::memory_order_acquire)) std::this_thread::yield();
        }
        submits+=unsigned(a.size());
    }
    void Shutdown(){if(fd==7)assert(submit_release.load(std::memory_order_acquire));}
};
struct Vic {
    s32 fd;
    unsigned submits=0;
    Vic(Host1x&,s32 n,u32):fd(n){}
    void PushEntries(ChCommandHeaderList&& a) {submits+=unsigned(a.size());}
    void Shutdown(){}
};
struct Host1x {
    std::array<std::variant<std::monostate,Nvdec,Vic>,1024> devices{};
    ~Host1x();
    void StartDevice(s32,ChannelType,u32);
    void StopDevice(s32,ChannelType);
__PUSH__
};
__METHODS__
}
int main() {
    using namespace Tegra::Host1x;
    Host1x h{};
    h.StartDevice(-1,ChannelType::NvDec,0);
    h.StartDevice(1024,ChannelType::VIC,0);
    assert(std::holds_alternative<std::monostate>(h.devices[0]));
    h.StartDevice(0,ChannelType::NvDec,7);
    h.StartDevice(1023,ChannelType::VIC,8);
    assert(std::get<Nvdec>(h.devices[0]).fd==0);
    assert(std::get<Vic>(h.devices[1023]).fd==1023);
    h.PushEntries(-1,{1,2,3});
    h.PushEntries(1024,{4,5});
    assert(std::get<Nvdec>(h.devices[0]).submits==0);
    assert(std::get<Vic>(h.devices[1023]).submits==0);
    h.PushEntries(0,{1,2,3});
    h.PushEntries(1023,{4,5});
    assert(std::get<Nvdec>(h.devices[0]).submits==3);
    assert(std::get<Vic>(h.devices[1023]).submits==2);
    h.StopDevice(-1,ChannelType::NvDec);
    h.StopDevice(1024,ChannelType::VIC);
    assert(std::holds_alternative<Nvdec>(h.devices[0]));
    assert(std::holds_alternative<Vic>(h.devices[1023]));
    h.StopDevice(0,ChannelType::NvDec);
    h.StopDevice(1023,ChannelType::VIC);
    assert(std::holds_alternative<std::monostate>(h.devices[0]));
    assert(std::holds_alternative<std::monostate>(h.devices[1023]));
    // Deterministic race witness: PushEntries is paused INSIDE the device
    // method while StopDevice attempts to replace that same variant.
    // Without the shared dispatch lock, Shutdown occurs before release.
    h.StartDevice(7,ChannelType::NvDec,0);
    std::thread submitter([&]{h.PushEntries(7,{1,2,3});});
    for(int i=0;i<200000&&!submit_entered.load(std::memory_order_acquire);++i)
        std::this_thread::yield();
    assert(submit_entered.load(std::memory_order_acquire));
    std::thread closer([&]{
        h.StopDevice(7,ChannelType::NvDec);
        close_finished.store(true,std::memory_order_release);
    });
    for(int i=0;i<20000;++i)std::this_thread::yield();
    assert(!close_finished.load(std::memory_order_acquire));
    // GPU-41: closing FD 7 must not hold up unrelated VIC traffic on FD 8.
    // The same-FD close still waits for the in-progress enqueue above.
    std::atomic<bool> unrelated_done{false};
    std::thread unrelated([&] {
        h.StartDevice(8,ChannelType::VIC,0);
        h.PushEntries(8,{6,7});
        unrelated_done.store(true,std::memory_order_release);
    });
    for(int i=0;i<200000&&!unrelated_done.load(std::memory_order_acquire);++i)
        std::this_thread::yield();
    const bool separate_fd_progress = unrelated_done.load(std::memory_order_acquire);
    submit_release.store(true,std::memory_order_release);
    submitter.join();closer.join();unrelated.join();
    assert(separate_fd_progress);
    assert(close_finished.load(std::memory_order_acquire));
    assert(std::holds_alternative<std::monostate>(h.devices[7]));
}
""".replace("__PUSH__",new_push).replace("__METHODS__",source_methods)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-host1x-device-fd-") as tmp:
    source=Path(tmp)/"host1x-fd.cpp"
    source.write_text(cpp)
    for opt in ("-O0","-O2"):
        exe=Path(tmp)/("fd-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-Wno-unused-parameter","-pthread", # Real close/submit interleaving.
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_HOST1X_DEVICE_FD_HOST_PASS active_source=1 ABI_unchanged=1 concurrent_close=1 independent_fd_progress=1 "
      "negative_fd=1 above_1023=1 NVDEC_VIC_dispatch=1 teardown=1 "
      "ASan_UBSan=1 O0_O2=2")


# GPU-36: actual native NVDEC submit preflight code, compiled in a focused
# Clang sanitizer harness to reject untrusted ioctl sizes before allocation.
NVD_PATH=V/"encore-active/eden/src/core/hle/service/nvdrv/devices/nvhost_nvdec_common.cpp"
assert NVD_PATH.is_file(), "Missing canonical native NVDEC owner"
NVD=NVD_PATH.read_text()
assert "submit_timeout = timeout;" in NVD
assert 'LOG_DEBUG(Service_NVDRV, "SetSubmitTimeout timeout={}", timeout);' in NVD
assert "core.GetSession(sessions[fd])" not in NVD
assert "params.syncpoint_count > params.fence_count" in NVD
assert "cmd.word_count < 0" in NVD
assert "syncpoint_manager.IsSyncpointAllocated(increment.id)" in NVD
assert 'list(REMOVE_ITEM core_sources "hle/service/nvdrv/devices/nvhost_nvdec_common.cpp")' in CMAKE
S=NVD[NVD.index("NvResult nvhost_nvdec_common::Submit("):
      NVD.index("NvResult nvhost_nvdec_common::GetSyncpoint(")]
packet=S[S.index("    constexpr std::size_t MAX_NVDEC_SUBMIT_BYTES"):
         S.index("    // Instantiate param buffers")]
sync_guard=S[S.index("    // The NVDRV syncpoint table has 192 entries."):S.index("    // Preflight command handles and word counts")]
commands=S[S.index("    constexpr u64 MAX_NVDEC_CMD_BYTES"):
           S.index("    for (std::size_t i = 0; i < syncpt_increments.size(); i++)")]
assert "sessions.find(fd)" in packet
assert "nvmap.GetHandle(cmd.memory_id)" in commands
fixture=r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <span>
#include <unordered_map>
#include <vector>
using u8=std::uint8_t;using u32=std::uint32_t;
using u64=std::uint64_t;using s32=std::int32_t;
using DeviceFD=s32;
enum class NvResult{InvalidState,Success};
struct IoctlSubmit{u32 cmd_buffer_count{},relocation_count{},syncpoint_count{},fence_count{};};
struct CommandBuffer{s32 memory_id{};u32 offset{};s32 word_count{};};
struct Reloc{s32 a{},b{},c{},d{};};
struct SyncptIncr{u32 id{},b{},c{},d{},e{};};
namespace Tegra{struct ChCommandHeader{u32 value;};}
struct Session{int* process{};};
struct CoreMock{Session* current{};Session* GetSession(int){return current;}};
struct Handle{u64 size{},address{};};
struct NvmapMock{
 std::shared_ptr<Handle> handle{};
 std::shared_ptr<Handle> GetHandle(s32 id){return id==1?handle:nullptr;}
};
struct SyncpointMock{bool IsSyncpointAllocated(u32 id) const{return id==1;}};
struct Owner{
 CoreMock core;
 NvmapMock nvmap;
 SyncpointMock syncpoint_manager;
 std::unordered_map<DeviceFD,int> sessions;
 NvResult Packet(IoctlSubmit params,std::span<u8> data,DeviceFD fd){
__PACKET__
 return NvResult::Success;
 }
 NvResult Commands(std::vector<CommandBuffer> command_buffers){
__COMMANDS__
 return NvResult::Success;
 }
 NvResult Syncpoints(std::vector<SyncptIncr> syncpt_increments){
__SYNCPOINT__
 return NvResult::Success;
 }
};
int main(){
 int process=3; Session session{&process};
 Owner owner{};owner.core.current=&session;owner.sessions[10]=1;
 std::vector<u8> bytes(56);IoctlSubmit good{1,1,1,1};
 assert(owner.Packet(good,bytes,10)==NvResult::Success);
 assert(owner.Packet(good,std::span<u8>(bytes).first(55),10)==NvResult::InvalidState);
 assert(owner.Packet(IoctlSubmit{0,0,2,1},bytes,10)==NvResult::InvalidState);
 assert(owner.Packet(IoctlSubmit{0xffffffffu,0,0,0},bytes,10)==NvResult::InvalidState);
 assert(owner.Packet(good,bytes,-1)==NvResult::InvalidState);
 assert(owner.sessions.size()==1);
 owner.core.current=nullptr;
 assert(owner.Packet(good,bytes,10)==NvResult::InvalidState);
 Session invalid{};owner.core.current=&invalid;
 assert(owner.Packet(good,bytes,10)==NvResult::InvalidState);
 owner.nvmap.handle=std::make_shared<Handle>(Handle{4096,0x10000});
 assert(owner.Commands({CommandBuffer{1,128,4}})==NvResult::Success);
 assert(owner.Syncpoints({SyncptIncr{1,1,0,0,0}})==NvResult::Success);
 assert(owner.Syncpoints({SyncptIncr{0,1,0,0,0}})==NvResult::InvalidState);
 assert(owner.Syncpoints({SyncptIncr{192,1,0,0,0}})==NvResult::InvalidState);
 assert(owner.Commands({CommandBuffer{1,128,-1}})==NvResult::InvalidState);
 assert(owner.Commands({CommandBuffer{1,128,0x7fffffff}})==NvResult::InvalidState);
 assert(owner.Commands({CommandBuffer{99,128,4}})==NvResult::InvalidState);
 assert(owner.Commands({CommandBuffer{1,4095,4}})==NvResult::InvalidState);
 assert(owner.Commands({CommandBuffer{1,4097,1}})==NvResult::InvalidState);
 owner.nvmap.handle->address=std::numeric_limits<u64>::max()-1;
 assert(owner.Commands({CommandBuffer{1,0,4}})==NvResult::InvalidState);
}
""".replace("__PACKET__",packet).replace("__COMMANDS__",commands).replace("__SYNCPOINT__",sync_guard)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-nvdec-submit-") as temp:
    path=Path(temp)/"nvdec-submit.cpp"
    path.write_text(fixture)
    for opt in ("-O0","-O2"):
        exe=Path(temp)/("nvdec-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(path),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_NVDEC_SUBMIT_PREFLIGHT_HOST_PASS packet=1 command=1 truncated=1 "
      "huge_counts=1 session=1 signed_words=1 handle_bounds=1 invalid_syncpoints=1 "
      "ASan_UBSan=1 O0_O2=2")


# GPU-37/38: source-verified worker teardown and register method bounds.
CDMA_CPP=V/"encore-active/eden/src/video_core/cdma_pusher.cpp"
CDMA_HDR=V/"encore-active/eden/src/video_core/cdma_pusher.h"
NVDEC_CPP=V/"encore-active/eden/src/video_core/host1x/nvdec.cpp"
assert blob(CDMA_CPP)=="91ace41154430a718cd163ceacd45b9607b63d43"
assert blob(CDMA_HDR)=="72338d9e2c07f2ebe019450c8b608df802738449"
assert blob(NVDEC_CPP)=="c83ac98215fcf196ec8b2927ec9a421ddf95c9f7"
assert blob(V/"sources/eden/src/video_core/cdma_pusher.cpp")=="d04b73877936b207fd5b8bd8b49ce41bbce67b0a"
assert blob(V/"sources/eden/src/video_core/cdma_pusher.h")=="2ce827cdfec9b6c81f7cd6b91549895a67749d01"
assert blob(V/"sources/eden/src/video_core/host1x/nvdec.cpp")=="5dbc6a417eaf34623101238d2a7ce014f097aee0"
CDMA=CDMA_CPP.read_text()
CDMA_HEADER=CDMA_HDR.read_text()
NVDEC=NVDEC_CPP.read_text()
VIC=CAND_VIC.read_text()
HOST=H1_CPP.read_text()
graph=CMAKE[CMAKE.index("# Native NS1 Host1x GPU-37/38:"):
            CMAKE.index("# Native N04: avoid invoking")]
for fragment in ("if(PS5_NATIVE)", "list(FIND video_sources",
                 "list(REMOVE_ITEM video_sources", "list(APPEND video_sources",
                 "configure_file(", "target_include_directories(video_core BEFORE PUBLIC"):
    assert fragment in graph,fragment
assert "cdma_pusher.cpp" in graph and "host1x/nvdec.cpp" in graph
assert "void Shutdown();" in CDMA_HEADER
assert "thread.get_stop_token().stop_requested()" in CDMA_HEADER
assert "if (stop_token.stop_requested())" in CDMA
assert "method >= ThiRegisters::NUM_REGS" in CDMA
assert "method >= NvdecCommon::NvdecRegisters::NUM_REGS" in NVDEC
assert "Shutdown();" in NVDEC[NVDEC.index("Nvdec::~Nvdec()"):NVDEC.index("void Nvdec::ProcessMethod")]
assert "Shutdown();" in VIC[VIC.index("Vic::~Vic()"):VIC.index("void Vic::ProcessMethod")]
assert HOST.count("->Shutdown();")==6
assert CDMA.index("thread.request_stop();") < CDMA.index("command_cv.notify_all();") < CDMA.index("thread.join();")


# Execute the native Shutdown and the two authentic derived destructors
# with a live stop-token worker. FrameQueue::Close asserts the worker was
# joined before decoder resources were touched. Also compile the exact
# guard branches of CDMAPusher and NVDEC into independently bounded arrays.
native_shutdown=CDMA[CDMA.index("CDmaPusher::~CDmaPusher() {"):
                     CDMA.index("void CDmaPusher::ExecuteCommand(")]
nvdec_dtor=NVDEC[NVDEC.index("Nvdec::~Nvdec() {"):
                 NVDEC.index("void Nvdec::ProcessMethod(")]
vic_dtor=VIC[VIC.index("Vic::~Vic() noexcept {"):
            VIC.index("void Vic::ProcessMethod(")]
thi_guard=CDMA[CDMA.index("        if (method >= ThiRegisters::NUM_REGS) {"):
               CDMA.index("        thi_regs.reg_array[method] = arg;")]
nvdec_guard=NVDEC[NVDEC.index("    if (method >= NvdecCommon::NvdecRegisters::NUM_REGS) {"):
                   NVDEC.index("    regs.reg_array[method] = argument;")]
cpp=r"""
#include <array>
#include <atomic>
#include <cassert>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <thread>
#define LOG_INFO(...) ((void)0)
#define LOG_WARNING(...) ((void)0)
using u32=std::uint32_t;
struct FrameQueue {
    std::atomic<bool> worker_stopped{false};
    unsigned closes=0;
    void Close(int) {
        assert(worker_stopped.load(std::memory_order_acquire));
        ++closes;
    }
};
struct Host1x{ FrameQueue frame_queue; };
class CDmaPusher {
public:
    explicit CDmaPusher(Host1x& h) {
        thread=std::jthread([this,&h](std::stop_token tok) {
            std::unique_lock lock{mutex};
            command_cv.wait(lock,tok,[]{return false;});
            h.frame_queue.worker_stopped.store(true,std::memory_order_release);
        });
    }
    virtual ~CDmaPusher();
    void Shutdown();
protected:
    std::mutex mutex{};
    std::condition_variable_any command_cv{};
    std::jthread thread{};
};
__BASE_DTOR_SHUTDOWN__
struct Nvdec:CDmaPusher {
    Host1x& host1x;
    int id;
    explicit Nvdec(Host1x& h):CDmaPusher(h),host1x(h),id(3){}
    ~Nvdec();
};
__NVDEC_DTOR__
struct Vic:CDmaPusher {
    Host1x& host1x;
    int id;
    explicit Vic(Host1x& h):CDmaPusher(h),host1x(h),id(4){}
    ~Vic() noexcept;
};
__VIC_DTOR__
struct ThiRegisters {
    static constexpr std::size_t NUM_REGS=0x20;
    std::array<u32,NUM_REGS> reg_array{};
};
struct NvdecCommon {
    struct NvdecRegisters {
        static constexpr std::size_t NUM_REGS=0x178;
        std::array<u32,NUM_REGS> reg_array{};
    };
};
struct MethodWitness {
    ThiRegisters thi_regs{};
    NvdecCommon::NvdecRegisters regs{};
    void THI(u32 method,u32 arg) {
__THI_GUARD__
        thi_regs.reg_array[method]=arg;
    }
    void NVDEC(u32 method,u32 argument) {
__NVDEC_GUARD__
        regs.reg_array[method]=argument;
    }
};
int main() {
    for(int i=0;i<40;++i) {
        Host1x n{};
        { Nvdec decoder(n); decoder.Shutdown(); decoder.Shutdown(); }
        assert(n.frame_queue.closes==1);
        Host1x v{};
        { Vic vic(v); }
        assert(v.frame_queue.closes==1);
    }
    MethodWitness m{};
    m.THI(0,17);m.THI(0x1f,41);m.THI(0x20,42);m.THI(0xfff,43);
    assert(m.thi_regs.reg_array[0]==17);
    assert(m.thi_regs.reg_array[0x1f]==41);
    m.NVDEC(0,17);m.NVDEC(0x177,52);m.NVDEC(0x178,53);m.NVDEC(0xfff,54);
    assert(m.regs.reg_array[0]==17);
    assert(m.regs.reg_array[0x177]==52);
}
""".replace("__BASE_DTOR_SHUTDOWN__",native_shutdown)
cpp=cpp.replace("__NVDEC_DTOR__",nvdec_dtor).replace("__VIC_DTOR__",vic_dtor)
cpp=cpp.replace("__THI_GUARD__",thi_guard).replace("__NVDEC_GUARD__",nvdec_guard)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-host1x-worker-") as temp:
    source=Path(temp)/"host1x-worker.cpp"
    source.write_text(cpp)
    for opt in ("-O0","-O2"):
        exe=Path(temp)/("worker-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-pthread","-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all",str(source),"-o",str(exe)],
                       check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=30)
print("NS1_HOST1X_CDMA_WORKER_HOST_PASS authentic_stop=1 derived_dtor=2 "
      "join_before_frameclose=1 repeated_shutdown=1 threads=80 "
      "THI_bounds_0x20=1 NVDEC_bounds_0x178=1 ASan_UBSan_O0_O2=1")


# GPU-39: the Host1x join-before-release patch must interrupt an
# unsignalled Control syncpoint wait when its device closes. Execute
# the selected SyncpointManager/Control methods with std::stop_token.
SYNC_CPP=V/"encore-active/eden/src/video_core/host1x/syncpoint_manager.cpp"
SYNC_HDR=V/"encore-active/eden/src/video_core/host1x/syncpoint_manager.h"
CTRL_CPP=V/"encore-active/eden/src/video_core/host1x/control.cpp"
CTRL_HDR=V/"encore-active/eden/src/video_core/host1x/control.h"
sync_blob=blob(SYNC_CPP)
assert sync_blob in {"eb5e2ea63652f020b6e14497080ba3339a9c983c", "59ac07af5eab89e78b7089d1db58918f2506aafe", "abe89b570a18508123a5c14c49cf5a43935f620c"}
SYNC_SOURCE=SYNC_CPP.read_text()
sync_receipt_source=SYNC_SOURCE
if sync_blob=="abe89b570a18508123a5c14c49cf5a43935f620c":
    # Reverse the strict host-completion delta on the audit copy only.
    # The stop-aware wait below is still extracted from the current owner.
    for newer,older in (
        ("    // Legacy guest/max-like progress is visible as soon as the command\n    // processor reaches the increment. Native NS2 completion must not be\n    // published here: the Vulkan work preceding this increment may still be\n    // in flight, and OunceVK treats an reached producer counter with a stale\n    // GPU marker as a fatal completion mismatch.\n    Increment(syncpoints_guest[id], wait_guest_cv, guest_action_storage[id]);", "    Increment(syncpoints_guest[id], wait_guest_cv, guest_action_storage[id], id);"),
        ("    // The host counter retires only behind the renderer fence. Drive the\n    // native 64-bit producer count, transfer-memory mirror and GSV actions\n    // from this completed value so producer target + GPU marker stay ordered.\n    Increment(syncpoints_host[id], wait_host_cv, host_action_storage[id], id);", "    Increment(syncpoints_host[id], wait_host_cv, host_action_storage[id]);"),
    ):
        assert sync_receipt_source.count(newer)==1
        sync_receipt_source=sync_receipt_source.replace(newer,older,1)
    raw=sync_receipt_source.encode()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()=="59ac07af5eab89e78b7089d1db58918f2506aafe"
    sync_blob="59ac07af5eab89e78b7089d1db58918f2506aafe"
if sync_blob == "59ac07af5eab89e78b7089d1db58918f2506aafe":
    # Reverse only the native NS2 counter/queue delta on the audit copy.
    # Execute the current selected stop-aware WaitHost below.
    native_added="SyncpointManager::ActionHandle SyncpointManager::RegisterNativeGuestAction(\n    u32 id, u64 target, bool wide, std::function<void()>&& action) {\n    if (id >= NUM_MAX_SYNCPOINTS) return {};\n    {\n        std::scoped_lock lk(guard);\n        if (!IsNativeGuestActionReady(native_guest_counts[id].load(std::memory_order_relaxed),\n                                      target, wide)) {\n            do { ++last_action_id; } while (last_action_id == 0);\n            auto& entry = native_guest_actions[id].emplace_back(0, last_action_id, std::move(action));\n            entry.native_target = target;\n            entry.native_wide = wide;\n            return entry.id;\n        }\n    }\n    action();\n    return {};\n}\n\nvoid SyncpointManager::DeregisterNativeGuestAction(u32 id, const ActionHandle& handle) {\n    if (id < NUM_MAX_SYNCPOINTS) DeregisterAction(native_guest_actions[id], handle);\n}\n\n"
    native_increment="void SyncpointManager::Increment(std::atomic<u32>& syncpoint, std::condition_variable& wait_cv,\n                                 std::list<RegisteredAction>& action_storage,\n                                 std::optional<u32> mirrored_id) {\n    std::unique_lock lk(guard);\n    u64 native_value{};\n    if (mirrored_id) {\n        native_value = native_guest_counts[*mirrored_id].load(std::memory_order_relaxed) + 1;\n        if (guest_mirror) guest_mirror(*mirrored_id, native_value);\n    }\n    const u32 new_value{syncpoint.fetch_add(1, std::memory_order_acq_rel) + 1};\n    if (mirrored_id)\n        native_guest_counts[*mirrored_id].store(native_value, std::memory_order_release);\n    wait_cv.notify_all();\n    auto end = action_storage.begin();\n    while (end != action_storage.end() && end->expected_value <= new_value) ++end;\n    if (end == action_storage.begin() &&\n        (!mirrored_id || native_guest_actions[*mirrored_id].empty())) return;\n\n    DueActions due;\n    due.pending.splice(due.pending.end(), action_storage, action_storage.begin(), end);\n    if (mirrored_id) {\n        auto& native = native_guest_actions[*mirrored_id];\n        for (auto it = native.begin(); it != native.end();) {\n            auto candidate = it++;\n            if (IsNativeGuestActionReady(native_value, candidate->native_target,\n                                         candidate->native_wide))\n                due.pending.splice(due.pending.end(), native, candidate);\n        }\n    }\n    if (due.pending.empty()) return;\n"
    legacy_increment="void SyncpointManager::Increment(std::atomic<u32>& syncpoint, std::condition_variable& wait_cv,\n                                 std::list<RegisteredAction>& action_storage,\n                                 std::optional<u32> mirrored_id) {\n    std::unique_lock lk(guard);\n    if (mirrored_id && guest_mirror) {\n        guest_mirror(*mirrored_id, syncpoint.load(std::memory_order_relaxed) + 1);\n    }\n    const u32 new_value{syncpoint.fetch_add(1, std::memory_order_acq_rel) + 1};\n    wait_cv.notify_all();\n    auto end = action_storage.begin();\n    while (end != action_storage.end() && end->expected_value <= new_value) ++end;\n    if (end == action_storage.begin()) return;\n\n    DueActions due;\n    due.pending.splice(due.pending.end(), action_storage, action_storage.begin(), end);\n"
    assert sync_receipt_source.count(native_added)==1
    assert sync_receipt_source.count(native_increment)==1
    sync_receipt_source=sync_receipt_source.replace(native_added,"",1).replace(native_increment,legacy_increment,1)
    raw=sync_receipt_source.encode()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()=="eb5e2ea63652f020b6e14497080ba3339a9c983c"
_sync_new='''        lk.unlock();
        try {
            action();
        } catch (...) {
            // DeregisterAction may already be waiting for this running handle.
            // Restore the guarded state before propagating the fatal callback:
            // otherwise due points to this stack object forever and teardown
            // can block on action_done_cv after the GPU/Host1x worker failed.
            lk.lock();
            due.running = 0;
            action_done_cv.notify_all();
            std::erase(due_actions, &due);
            throw;
        }
        action = nullptr;
        lk.lock();
        due.running = 0;
        action_done_cv.notify_all();'''
_sync_old='''        lk.unlock();
        action();
        action = nullptr;
        lk.lock();
        due.running = 0;
        action_done_cv.notify_all();'''
assert sync_receipt_source.count(_sync_new)==1
_sync_prior=sync_receipt_source.replace(_sync_new,_sync_old,1).encode()
assert hashlib.sha1(b"blob "+str(len(_sync_prior)).encode()+bytes([0])+_sync_prior).hexdigest()==\
       "103ed91c68bae0238f2a2ce181e3e292845c19c1"
print("NS1_HOST1X_THROWING_ACTION_EXACT_REVERSE_PASS prior_blob=103ed91c running_cleanup=1")
assert blob(SYNC_HDR)==("a62b9a9e8019c2df085fc9d393fcbd4207cd78d7" if sync_blob=="59ac07af5eab89e78b7089d1db58918f2506aafe" else "4f45e7ca10bef7fadf94b4d08a310dea953e7315")
assert blob(CTRL_CPP)=="fcbf4e092f054724b9fd4731c8dfec9917cea27a"
assert blob(CTRL_HDR)=="fc1c4e3d47bdcf8ef282da02410940432051fcca"
SYNC_HEADER=SYNC_HDR.read_text()
CTRL_SOURCE=CTRL_CPP.read_text()
CTRL_HEADER=CTRL_HDR.read_text()
assert "void WaitHost(u32 syncpoint_id, u32 expected_value, std::stop_token stop);" in SYNC_HEADER
assert "void WaitHost(u32 syncpoint_id, u32 expected_value);" in SYNC_HEADER
assert "void ProcessMethod(Host1x& host1x, Method method, u32 argument," in CTRL_HEADER
assert "thread.get_stop_token()" in CDMA
assert "EDEN_HOST1X_CONTROL_HEADER" in CMAKE and "host1x/control.cpp" in CMAKE
assert 'list(REMOVE_ITEM video_sources host1x/syncpoint_manager.cpp)' in CMAKE
assert 'list(REMOVE_ITEM video_sources "' in CMAKE
assert 'encore-active/eden/src/video_core/host1x/syncpoint_manager.h' in CMAKE
start=SYNC_SOURCE.index("void SyncpointManager::WaitHost(u32 id, u32 expected, std::stop_token stop) {")
end=SYNC_SOURCE.index("\nvoid SyncpointManager::Increment(",start)
native_wait=SYNC_SOURCE[start:end]
ctrl_start=CTRL_SOURCE.index("void Control::ProcessMethod(")
ctrl_end=CTRL_SOURCE.index("\n} // namespace Tegra::Host1x",ctrl_start)
native_control=CTRL_SOURCE[ctrl_start:ctrl_end]
assert "std::stop_callback on_stop(stop," in native_wait
assert "std::scoped_lock lock(guard)" in native_wait
assert "stop.stop_requested() ||" in native_wait
assert "WaitHost(data, syncpoint_value, stop)" in native_control
fixture=r"""
#include <array>
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <stop_token>
#include <thread>
#define LOG_TRACE(...) ((void)0)
#define UNIMPLEMENTED_MSG(...) ((void)0)
using u32=std::uint32_t;
namespace Tegra::Host1x {
struct SyncpointManager {
    static constexpr std::size_t NUM_MAX_SYNCPOINTS=192;
    std::array<std::atomic<u32>,NUM_MAX_SYNCPOINTS> syncpoints_host{};
    std::condition_variable wait_host_cv{};
    std::mutex guard{};
    void WaitHost(u32,u32,std::stop_token);
    void IncrementHost(u32 id) {
        std::scoped_lock lock(guard);
        syncpoints_host[id].fetch_add(1,std::memory_order_release);
        wait_host_cv.notify_all();
    }
};
struct Host1x {
    SyncpointManager syncpoint{};
    SyncpointManager& GetSyncpointManager(){return syncpoint;}
};
struct Control {
    enum class Method:u32{WaitSyncpt=0x8,LoadSyncptPayload32=0x4e,WaitSyncpt32=0x50};
    u32 syncpoint_value{};
    void ProcessMethod(Host1x&,Method,u32,std::stop_token);
    void Execute(Host1x&,u32,std::stop_token);
};
__WAIT__
__CONTROL__
}
int main() {
    using namespace Tegra::Host1x;
    for(int i=0;i<50;++i) {
        Host1x host{};
        Control control{};
        control.ProcessMethod(host,Control::Method::LoadSyncptPayload32,100000,{});
        std::atomic<bool> exited{false};
        std::jthread worker([&](std::stop_token stop) {
            control.ProcessMethod(host,Control::Method::WaitSyncpt32,1,stop);
            exited.store(true,std::memory_order_release);
        });
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        assert(!exited.load(std::memory_order_acquire));
        worker.request_stop();
        worker.join();
        assert(exited.load(std::memory_order_acquire));
        assert(host.syncpoint.syncpoints_host[1].load()==0);
    }
    for(int i=0;i<50;++i) {
        Host1x host{};
        Control control{};
        control.ProcessMethod(host,Control::Method::LoadSyncptPayload32,1,{});
        std::atomic<bool> exited{false};
        std::jthread worker([&](std::stop_token stop) {
            control.ProcessMethod(host,Control::Method::WaitSyncpt,1,stop);
            exited.store(true,std::memory_order_release);
        });
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        assert(!exited.load(std::memory_order_acquire));
        host.syncpoint.IncrementHost(1);
        worker.join();
        assert(exited.load(std::memory_order_acquire));
        assert(host.syncpoint.syncpoints_host[1].load()==1);
    }
    Host1x immediate{};
    Control c{};
    c.ProcessMethod(immediate,Control::Method::LoadSyncptPayload32,1,{});
    immediate.syncpoint.IncrementHost(1);
    c.ProcessMethod(immediate,Control::Method::WaitSyncpt,1,{});
}
""".replace("__WAIT__",native_wait).replace("__CONTROL__",native_control)
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-host1x-stopwait-") as temp:
    source=Path(temp)/"stopwait.cpp"
    source.write_text(fixture)
    for opt in ("-O0","-O2"):
        exe=Path(temp)/("stopwait-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-pthread","-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all",str(source),"-o",str(exe)],
                       check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_HOST1X_STOP_AWARE_WAIT_HOST_PASS native_syncpoint=1 native_control=1 "
      "stop_while_waiting=1 valid_fence_signal=1 immediate_ready=1 "
      "threads=200 O0_O2=2 ASan_UBSan=1")
