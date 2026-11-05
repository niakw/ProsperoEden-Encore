#!/usr/bin/env python3
"""Verify real native GPU source selection without a second research profile."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / "headless/CMakeLists.txt").read_text()
start = "# N3m: compile a renderer-callable"
end = "# N50: shared native PS5 device-memory"
assert start in source and end in source
selector = start + source.split(start,1)[1].split(end,1)[0]
target = ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp"
assert target.is_file() and "target_sources(video_core PRIVATE" in selector
# P2.2: production-selected native renderer obtains TIC metadata exclusively
# from the authenticated QMD channel tables, not from fake defaults or a
# second Switch 2 texture cache. This source witness is not PS5 runtime proof.
rasterizer = (ROOT / "vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
native = rasterizer.split("bool RasterizerVulkan::DispatchNativeCompute(", 1)[1].split(
    "void RasterizerVulkan::DispatchCompute(", 1)[0]
assert "class NativeQmdTextureMetadata final : public Shader::Environment" in rasterizer
assert "NativeBufferOnlyMetadata" not in rasterizer
assert "VideoCommon::PixelFormatFromTextureInfo(" in rasterizer
assert "VideoCommon::ReadNs2GpuShader(" in rasterizer
assert "NativeQmdTextureTables" in native
assert "kepler_compute.regs" in native
assert "launch.linked_tsc" in native
assert "if (native_images.size() + native_texels.size() !=" in native
assert "typed_descriptors->size())" in native
assert "native_texels.reserve(typed_descriptors->size());" in native
assert "resources->HasResolvedBufferBindings()" in native
print("NS2_NATIVE_TIC_METADATA_SOURCE_PASS real_tables=1 no_false_vk_images=1")

def main():
    assert shutil.which("cmake"), "CMake needed for a real source-graph check"
    for forbidden in ("EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL",
                      "EDEN_NS2_GPU_SESSION_EXPERIMENTAL",
                      "EDEN_NS2_NVDRV_EXPERIMENTAL",
                      "EDEN_DEV_PROFILE","EDEN_FINAL_RELEASE_PROFILE"):
        assert forbidden not in source, forbidden
    assert "if(EDEN_SHARED_NS2_SPIRV_COMPILER)" in selector
    assert 'configure_file("${EDEN_NS2_RASTERIZER_INTERFACE}"' in selector
    assert 'target_sources(video_core PRIVATE "${EDEN_NS2_VULKAN_SHADER_BRIDGE}")' in selector
    assert 'target_sources(video_core PRIVATE "${EDEN_NS2_NATIVE_GPU_SPIRV_CAPTURE}")' in selector
    # This configures the complete real GPU/renderer owner selector with
    # the PS5 platform gate, not a synthetic flag-enabled shadow program.
    graph = ROOT / "tools/ns2/check_unified_native_gpu_graph_host.py"
    assert graph.is_file()
    proc = subprocess.run(["python3","-B",str(graph)],cwd=ROOT,
                          capture_output=True,text=True,timeout=80)
    assert proc.returncode == 0 and "UNIFIED_NATIVE_GPU_SOURCE_GRAPH_PASS" in proc.stdout, (
        proc.stdout[-2500:],proc.stderr[-2500:])
    print("NS2_RENDERER_UNIFIED_SOURCE_SELECTOR_PASS native_ps5=1 ns1_maxwell=preserved gpu_session=shared")

if __name__=="__main__":
    main()
