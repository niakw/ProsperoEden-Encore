#!/usr/bin/env python3
"""Host-only Clang C++20 syntax of selected REAL neural Vulkan owners.

No PS5 SDK, device, linking, executable, or frame is involved. Uses the same
maintained source roots/BufferCache overlay as P2.4's real native TU witness.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
ACTIVE=ROOT/"vendor/encore-active/eden-vulkan"
SHADER=ROOT/"vendor/encore-active/eden-shader/src"
CPM=ROOT/"vendor/sources/eden-cpm"
FILES=(
    "nr_rdna2_decoder_tile_to_linear.cpp",
    "nr_rdna2_decoder_fp32_to_fp16.cpp",
    "nr_rdna2_native_decoder_link.cpp",
    "nr_rdna2_neural_bottleneck.cpp",
    "nr_rdna2_split_swin_run.cpp",
    "nr_rdna2_vit_run.cpp",
    "nr_rdna2_image_feature_stage.cpp",
    "nr_rdna2_postblock_mix.cpp",
    "nr_rdna2_postblock_run.cpp",
    "nr_rdna2_preblock_run.cpp",
    "nr_rdna2_preblock_pool.cpp",
    "nr_rdna2_proxy_feature_stage.cpp",
    "nr_rdna2_proxy_lift_link.cpp",
    "nr_rdna2_proxy_fswin_link.cpp",
    "nr_rdna2_fswin_dense.cpp",
    "nr_rdna2_fswin_graph.cpp",
    "nr_rdna2_fswin_descriptors.cpp",
    "nr_rdna2_fswin_layer_runtime.cpp",
    "nr_rdna2_fswin_gpu_tensors.cpp",
    "nr_rdna2_fswin_output_view.cpp",
    "nr_rdna2_fswin_chain.cpp",
    "nr_rdna2_fswin_level_link.cpp",
    "nr_rdna2_unet_skip_cache.cpp",
    "nr_rdna2_unet_down_sequence.cpp",
    "nr_rdna2_unet_bottleneck_link.cpp",
    "nr_rdna2_unet_up_sequence.cpp",
    "nr_rdna2_core_feature_sequence.cpp",
    "nr_rdna2_frame_session.cpp",
    "nr_rdna2_nohistory_compose.cpp",
    "nr_rdna2_temporal_compose.cpp",
    "nr_rdna2_hdr_proxy.cpp",
    "nr_rdna2_nohistory_present.cpp",
    "nr_rdna2_texture_proxy.cpp",
    "nr_rdna2_unet_upsample_link.cpp",
)
INCLUDES=[
    ROOT/"extras/graphics",
    ROOT/"headless",
    SHADER,
    ROOT/"vendor/encore-active/ns2-runtime/ampere",
    ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch",
    ROOT/"vendor/encore-active/ns2-runtime/vulkan_abi",
    ROOT/"vendor/encore-active/ns2-runtime/hle",
    ACTIVE/"include",
    ROOT/"vendor/encore-active/ns2-astc/include",
    ROOT/"vendor/encore-active/ns2-helpers/include",
    ROOT/"vendor/encore-active/ns2-runtime/nvdrv_gpu",
    ROOT/"vendor/sources/eden/src",
    CPM/"vulkanheaders/v1.4.345/include",
    CPM/"vulkanmemoryallocator/v3.3.0/include",
    CPM/"fmt/12.1.0/include",
    CPM/"sirit/v1.0.5/include",
    CPM/"spirv-headers/vulkan-sdk-1.4.341.0/include",
]
boost=CPM/"boost/boost-1.90.0/libs"
INCLUDES.extend(sorted(boost.glob("*/include")))
assert all(x.is_dir() for x in INCLUDES),(    "R09 native source dependency root missing",    [str(x) for x in INCLUDES if not x.is_dir()])
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler,"Clang C++20 required"
assert all((ACTIVE/f).is_file() for f in FILES)
with tempfile.TemporaryDirectory(prefix="encore-r09-native-syntax-") as temporary:
    temp=Path(temporary)
    inc=temp/"include"
    shader_headers=inc/"video_core/host_shaders"
    shader_headers.mkdir(parents=True)
    for tool,header in (
        ("test-rdna2-decoder-tile-linear-spv.py",
         "rdna2_nr_decoder_tile_linear_comp_spv.h"),
        ("test-rdna2-decoder-fp32-to-fp16-spv.py",
         "rdna2_nr_decoder_fp32_to_fp16_comp_spv.h"),
        ("test-rdna2-image-feature-spv.py",
         "rdna2_nr_image_feature_comp_spv.h"),
        ("test-rdna2-postblock-mix-spv.py",
         "rdna2_nr_postblock_mix_comp_spv.h"),
        ("test-rdna2-preblock-pool-spv.py",
         "rdna2_nr_preblock_pool_comp_spv.h"),
        ("test-rdna2-fswin-dense-spv.py",
         "rdna2_nr_fswin_dense_comp_spv.h"),
        ("test-rdna2-proxy-features-spv.py",
         "rdna2_nr_proxy_features_comp_spv.h"),
        ("test-rdna2-nohistory-compose-spv.py",
         "rdna2_nr_nohistory_compose_comp_spv.h"),
        ("test-rdna2-temporal-compose-spv.py",
         "rdna2_nr_temporal_compose_comp_spv.h"),
        ("test-rdna2-hdr-proxy-spv.py",
         "rdna2_nr_hdr_proxy_comp_spv.h"),
        ("test-rdna2-nohistory-present-spv.py",
         "rdna2_nr_nohistory_present_comp_spv.h"),
        ("test-rdna2-texture-proxy-spv.py",
         "rdna2_nr_texture_proxy_comp_spv.h"),
    ):
        subprocess.run([
            "python3",str(ROOT/"tools/graphics"/tool),
            "--vendor",str(ROOT/"vendor"),
            "--header",str(shader_headers/header)
        ],check=True,cwd=ROOT)
    # Match production's versioned presentation Layer overlay exactly,
    # otherwise the host syntax check would use the pristine upstream
    # class and miss integration errors in the live PS5 renderer.
    present_layer=temp/"present-overlay/video_core/renderer_vulkan/present"
    present_layer.mkdir(parents=True)
    shutil.copyfile(ROOT/"headless/vulkan_present_layer_r24.h",
                    present_layer/"layer.h")
    # The maintained BufferCache template is the one the production CMake
    # stages. The pristine Eden header would be the wrong ABI.
    cache=temp/"buffer-pages/video_core/buffer_cache"
    cache.mkdir(parents=True)
    for f in ("buffer_cache.h","buffer_cache_base.h"):
        source=ROOT/"vendor/encore-active/eden-core/src/video_core/buffer_cache"/f
        assert source.is_file(),f
        shutil.copyfile(source,cache/f)
    # Linux lacks the FreeBSD cpu-set header present in PS5-native paths.
    (temp/"cpuset.h").write_text(
        "#pragma once\n#include <sched.h>\n"
        "#define CPU_LEVEL_WHICH 3\n#define CPU_WHICH_TID 4\n"
        "using cpuset_t = cpu_set_t;\n"
        "inline int cpuset_getaffinity(int,int,int,size_t n,cpuset_t* m)"
        "{return sched_getaffinity(0,n,m);}\n",encoding="utf-8")
    cmd=[compiler,"-std=c++20","-O0","-fsyntax-only",
         "-DPS5_NATIVE=1","-DFMT_HEADER_ONLY",
         "-Wno-unused-parameter",
         "-I"+str(inc),"-I"+str(temp/"present-overlay"),
         "-I"+str(temp/"buffer-pages"),
         "-I"+str(temp),
         *["-I"+str(p) for p in INCLUDES]]
    env=os.environ.copy()
    def check(name):
        source=(ROOT/"headless/vulkan_present_layer_r24.cpp"
                if name=="__present_layer_r09__" else ACTIVE/name)
        result=subprocess.run(cmd+[str(source)],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=150)
        return name,result.returncode,result.stderr[-10000:]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(check,(*FILES,"__present_layer_r09__")))
    failures=[]
    for name,rc,diagnostics in results:
        if rc:
            failures.append(name)
            print("R09_NEURAL_NATIVE_CPP_FAIL",name,diagnostics,flush=True)
        else:
            print("R09_NEURAL_NATIVE_CPP_PASS",name,flush=True)
    assert not failures,("R09 selected native C++ syntax failed",failures)
    print("R09_NEURAL_NATIVE_CPP_HOST_PASS owners="+str(len(FILES)),flush=True)
