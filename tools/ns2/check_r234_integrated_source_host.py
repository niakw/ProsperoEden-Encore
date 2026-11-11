#!/usr/bin/env python3
"""Pin all R2/R3/R4 real combined CMake owners and vendor blobs.

Host source admission only. It does not prove Vulkan queue/fence, full
application link, NS1/NS2 gameplay, hardware pixels, or performance.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VENDOR = "4f08b9c9dd2f34deecc9c9fa0d8196dcd6575c2e"
EXPECTED = {
    ".github/workflows/ns2-r2-upload-batch-host.yml": "fbd0abe08e90c394b029e70dc8b34aa0a8b650f6",
    "encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h": "b2ab2c539ae161fc4a9680d31258f6ea823e2517",
    "encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h": "33e077863e503a956cabf2b99edb73f8967b89a8",
    "encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h": "8905d42732b2d5848aa49b5800340e031cd214c9",
    "encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_verified_upload_batch.h": "b12cc0489ebbb463b4ec9e4c39b2d2be41ab2376",
    "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h": "88485385b530d678c2c4b4f161053569c723e270",
    "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h": "d2d7e8b6cef6ea6ba912d5c7ad41b646527f6f0d",
    "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_staging_buffer_pool.h": "09152820218895c71bbbdf145a30db6d95559e7f",
    "encore-active/eden-vulkan/tests/test_ns2_cache_shutdown_order.cpp": "472860e5ddc853197ec79b63d16800daffa372cc",
    "encore-active/eden-vulkan/tests/test_ns2_gpu_retirement_hold.cpp": "0de5c2e112ce21a9736031879830ff377ba7f307",
    "encore-active/eden-vulkan/tests/test_ns2_verified_upload_batch.cpp": "2bb3d3389565f06c7eb2ea46a57acae06c28c53a",
    "encore-active/eden-vulkan/vk_buffer_cache_cost.cpp": "fd3837717e8d3e3887c958bbd51c0bf91cd35a2f",
    "encore-active/eden-vulkan/vk_staging_buffer_pool.cpp": "87cf07f4522f7225610785f1908337f5eabdeb32",
    "encore-active/eden-vulkan/vulkan_scheduler.cpp": "db83d90460d93c8c50212753e51c54924f4f2e61",
    "tools/ns2/check_r2_scheduler_staging_source_host.py": "3f589e792323579dbbb934e4a36778ebb4f264e8",
    ".github/workflows/ns2-r3-decoder-host.yml": "e99e30342acfc366a1a9e02ededbd627d4a3bdcc",
    "encore-active/eden-core/src/video_core/textures/decoders.cpp": "cc8bb22035f306e45389b6a7efbceeddb45dd6d0",
    "encore-active/eden-core/tests/test_ns2_gob16_decoder_public_api.cpp": "5acd6621bb8f4e240596793e1dd77660865b26a3",
    "encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h": "b48a544156be57b0dfe21bdf3972399a4349941c"
}

def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

def run():
    assert git("rev-parse", "HEAD:vendor") == VENDOR, "research vendor gitlink drift"
    assert git("rev-parse", "HEAD", cwd=ROOT / "vendor") == VENDOR, "submodule checkout drift"
    for path, sha in EXPECTED.items():
        target = ROOT / "vendor" / path
        assert target.is_file(), ("missing reviewed vendor owner", path)
        actual = git("hash-object", str(target))
        assert actual == sha, ("unreviewed R2/R3/R4 vendor bytes", path, actual)
    text = (ROOT / "headless/CMakeLists.txt").read_text()
    for name in ("EDEN_RESEARCH_NS2_STAGE_BACKING", "EDEN_RESEARCH_NS2_GOB16",
                 "EDEN_RESEARCH_NS2_R4_VOLUME"):
        assert text.count("option(" + name + "\n") == 1, ("CMake option drift", name)
        assert text.count("target_compile_definitions(video_core PRIVATE " +
                          name + "=1)") == 1, ("CMake research guard drift", name)
    assert "list(REMOVE_ITEM video_sources \"renderer_vulkan/vk_staging_buffer_pool.cpp\")" in text
    assert 'list(APPEND video_sources "${EDEN_R2_STAGING_CPP}")' in text
    assert "list(REMOVE_ITEM video_sources \"textures/decoders.cpp\")" in text
    assert 'list(APPEND video_sources "${EDEN_NS2_GOB16_DECODER}")' in text
    assert text.count("copy_native_volume_slice") == 2, "real R4 N60 owner admission changed"
    start = text.index("# R4 native research-only:")
    end = text.index("# Sparse native GPU probes were diagnostic paths", start)
    r4 = text[start:end]
    assert 'vk_texture_cache_cost.cpp' in r4 and 'vk_graphics_pipeline_cost.cpp' not in r4
    assert 'TARGET_DIRECTORY video_core' in (ROOT / "headless/vulkan.cmake").read_text(), (
        "do not regress main's MihawkGen/FrameGen native namespaced header wiring")
    r2_owner = (ROOT / "vendor/encore-active/eden-vulkan/vk_staging_buffer_pool.cpp").read_text()
    assert "R2: same-tick staging physical reuse" in r2_owner
    assert "active_staging_requests.clear();" not in r2_owner
    assert "sync_ticks = sync_before;" in r2_owner
    r2_runtime = (ROOT / "vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp").read_text()
    assert "staging_pool.IsCurrentRequest(" in r2_runtime
    r3_decoder = (ROOT / "vendor/encore-active/eden-core/src/video_core/textures/decoders.cpp").read_text()
    assert "Host-reviewed 16-byte GOB unit addresses" in r3_decoder
    r4_owner = (ROOT / "vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h").read_text()
    assert "copy_native_volume_slice" in r4_owner
    assert "runtime.RetireGpuImage(" in r4_owner and "runtime.RetireGpuImageView(" in r4_owner
    print("R234_INTEGRATED_OWNER_PASS files=19 flags=3 gitlink_exact=1 "
          "r2_live_ledger=1 r3_gob16=1 r4_active_n60=1 no_app_build=1")

if __name__ == "__main__":
    run()
