#!/usr/bin/env python3
"""Validate the shipping NS1 X8_D24 <-> ABGR8 Vulkan conversion path."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
CPP = VENDOR / "encore-active/eden-vulkan/blit_image.cpp"
HDR = VENDOR / "encore-active/eden-vulkan/include/video_core/renderer_vulkan/blit_image.h"
TEX = VENDOR / "encore-active/eden-vulkan/vk_texture_cache_cost.cpp"
CACHE = VENDOR / "encore-active/eden/src/video_core/texture_cache/texture_cache.h"
CMAKE = ROOT / "headless/vulkan.cmake"
COMMON = ROOT / "headless/x8d24_conversion.glsl"
SHADERS = (
    (ROOT / "headless/convert_abgr8_to_x8d24.frag", "CONVERT_ABGR8_TO_X8D24_FRAG_SPV"),
    (ROOT / "headless/convert_x8d24_to_abgr8.frag", "CONVERT_X8D24_TO_ABGR8_FRAG_SPV"),
)

def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()

assert git_blob(CPP) == "4ba93afb6594213d5bde82be2693f0e08cb1cd63"
assert git_blob(HDR) == "a38cfcf655adcb8ceebfce955b39a2312a239768"
assert git_blob(TEX) == "e9191238ccddd94aa22570eba501fb05fff5b207"
assert git_blob(CACHE) in {"5c6d015cf207d63de31b577411972606145d9f2e", "27ea4e0e665d3f94e173c1335cb19211efc03646", "45659d2fa8ae336d28e7ccbd02b3104d96229378", "bbb55dc7b1648fa1e6fd730a1b3515f2969221c7", "5fa75d9b6b7b4f9710a6840182dc0de854e62268", "709ee61bc3a620654fa9c66eafa6482aab382d12", "bfd98bca9204d06da8a828c9dba6d8eab7bafb63", "4076fb27d78e6be2893d6a09d3f9d5493e6bab59", "85c2514267ca38fc0b88d1442a464cc0299aa2d8", "ab226987e5e20829d156c8edb917fd4851cf478d", "014b8a25cf34391965f7f465c372e7673596e86b", "655dcfc936c0157a5e5910942d44d1f21ff028d7", "c0312be09d81afb0064479179db794d2648560b9"}

cpp = CPP.read_text()
hdr = HDR.read_text()
tex = TEX.read_text()
cache = CACHE.read_text()
assert "if (!image_id)" in cache and "return ImageViewId{};" in cache
cmake = CMAKE.read_text()
common = COMMON.read_text()
assert "DecodeX8D24" in common and "EncodeX8D24" in common
assert "16777216.0f" in common and "16777215.0f" in common
for token in (
    "CONVERT_ABGR8_TO_X8D24_FRAG_SPV",
    "CONVERT_X8D24_TO_ABGR8_FRAG_SPV",
    "ConvertABGR8ToX8D24",
    "ConvertX8D24ToABGR8",
):
    assert token in cpp or token in hdr or token in tex, token
assert "case PixelFormat::X8_D24_UNORM:" in tex
assert "return blit_image_helper.ConvertX8D24ToABGR8(dst, src_view);" in tex
assert "return blit_image_helper.ConvertABGR8ToX8D24(dst, src_view);" in tex
assert "alias_conversion_format" in cache
assert "other_format == PixelFormat::X8_D24_UNORM" in cache
assert "BytesPerBlock(format) == 4" in cache
assert "const ImageViewInfo src_view_info(ImageViewType::e2D, src_format, src_range);" in cache
assert "eden-ns1-x8d24-spv" in cmake
assert "--target-env spirv1.3" in cmake
assert "EDEN_NS1_ABGR8_TO_X8D24_HEADER" in cmake
assert "EDEN_NS1_X8D24_TO_ABGR8_HEADER" in cmake
# GPU-51 must not mutate the immutable upstream Eden host-shader tree.
assert not (VENDOR / "sources/eden/src/video_core/host_shaders/convert_abgr8_to_x8d24.frag").exists()
assert not (VENDOR / "sources/eden/src/video_core/host_shaders/convert_x8d24_to_abgr8.frag").exists()

parser = argparse.ArgumentParser()
parser.add_argument("--compile", action="store_true")
args = parser.parse_args()
if args.compile:
    glslang = shutil.which("glslangValidator")
    spirv_val = shutil.which("spirv-val")
    assert glslang and spirv_val, "glslangValidator and spirv-val are required"
    with tempfile.TemporaryDirectory(prefix="encore-x8d24-") as td:
        out = Path(td)
        for source, variable in SHADERS:
            spv = out / (source.stem + ".spv")
            header = out / (source.stem + "_spv.h")
            common_args = [glslang, "-V", "--target-env", "spirv1.3", f"-I{COMMON.parent}",
                           "-DUseUniformBlock=1"]
            subprocess.run(common_args + ["-o", str(spv), str(source)], check=True)
            subprocess.run([spirv_val, "--target-env", "spv1.3", str(spv)], check=True)
            subprocess.run(common_args + ["--variable-name", variable,
                                           "-o", str(header), str(source)], check=True)
            assert variable in header.read_text(), variable
print("NS1_X8D24_CONVERSION_HOST_PASS owners=4 shaders=2 color_alias32=1 pinned_eden_immutable=1")
