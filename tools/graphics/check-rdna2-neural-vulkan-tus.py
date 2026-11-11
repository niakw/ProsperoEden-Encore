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
import runpy
import re
import struct

ROOT=Path(__file__).resolve().parents[2]
ACTIVE=ROOT/"vendor/encore-active/eden-vulkan"
SHADER=ROOT/"vendor/encore-active/eden-shader/src"
CPM=ROOT/"vendor/sources/eden-cpm"
# Compile every maintained R09 Vulkan C++ owner, not a hand-selected
# subset that can silently miss a renderer/graph/weight source.
# Authoritative production list: do not count abandoned experimental
# sources as linked neural operators.
SHIPPING_CPP=(ROOT/"headless/vulkan.cmake").read_text(encoding="utf-8")
FILES=tuple(sorted(set(re.findall(r"nr_rdna2_[a-z0-9_]+[.]cpp", SHIPPING_CPP))))
REQUIRED={"nr_rdna2_frame_session.cpp","nr_rdna2_frame_readback.cpp",
          "nr_rdna2_core_feature_sequence.cpp","nr_rdna2_fswin_upsample.cpp",
          "nr_rdna2_split_swin_block.cpp","nr_rdna2_vit_block.cpp"}
assert len(FILES)>=72 and REQUIRED.issubset(FILES), (
    "R09 whole-graph C++ owner source inventory incomplete", len(FILES))
# Restricted mode used ONLY by R09 Min's isolated native vendor CI.
# The default whole-graph source inventory above remains mandatory.
R09_MIN_DUAL=os.environ.get("R09_MIN_VIT_NATIVE_TU_DUAL","")
R09_FSWIN_DUAL=os.environ.get("R09_FSWIN_NATIVE_TU_DUAL","")
R09_HOST_720_DUAL=os.environ.get("R09_MIN_720_HOST_RUNNER_DUAL","")
R09_PRESENT_720_DUAL=os.environ.get("R09_MIN_720_PRESENT_TU_DUAL","")
R09_A4K_OWNER_DUAL=os.environ.get("R09_A4K_NATIVE_OUTPUT_DUAL","")
assert all(v in ("","1") for v in
           (R09_MIN_DUAL,R09_FSWIN_DUAL,R09_HOST_720_DUAL,
            R09_PRESENT_720_DUAL,R09_A4K_OWNER_DUAL))
assert sum(v=="1" for v in
           (R09_MIN_DUAL,R09_FSWIN_DUAL,R09_HOST_720_DUAL,
            R09_PRESENT_720_DUAL,R09_A4K_OWNER_DUAL))<=1
if R09_MIN_DUAL=="1":
    chosen={"nr_rdna2_frame_session.cpp","nr_rdna2_vit_run.cpp",
            "nr_rdna2_vit_block.cpp","nr_rdna2_vit_projection_stage.cpp",
            "nr_rdna2_vit_epilogue.cpp","nr_rdna2_vit_qkv_attention_link.cpp"}
    assert chosen.issubset(FILES)
    FILES=tuple(sorted(chosen))
elif R09_FSWIN_DUAL=="1":
    # Only the three authentic C++ translation units modified by the
    # separate vendor scratch-pool PR. Test both compile-time branches.
    chosen={"nr_rdna2_fswin_gpu_tensors.cpp",
            "nr_rdna2_fswin_layer_runtime.cpp",
            "nr_rdna2_fswin_chain.cpp"}
    assert chosen.issubset(FILES)
    FILES=tuple(sorted(chosen))
elif R09_HOST_720_DUAL=="1" or R09_PRESENT_720_DUAL=="1" or R09_A4K_OWNER_DUAL=="1":
    # Compile either the host runner or real PS5 presenter in both macro
    # states: syntax-only, no execution or runtime opt-in.
    FILES=()
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
    if R09_A4K_OWNER_DUAL=="1":
        # Compile real vendor C++ methods, with 13 non-executable SPIR-V
        # header stubs for host SYNTAX ONLY. Never run these shader bytes.
        for stem in (*("anime4k_3d_us_stage_"+str(i) for i in range(4)),
                     *("anime4k_soft_stage_"+str(i) for i in range(4)),
                     *("anime4k_denoise_stage_"+str(i) for i in range(5))):
            symbol=stem.upper()+"_COMP_SPV"
            (shader_headers/(stem+"_comp_spv.h")).write_text(
                "#pragma once\\n#include <array>\\n#include <cstdint>\\n"
                f"inline constexpr std::array<std::uint32_t,4> {symbol}"
                "{0x07230203u,0u,0u,0u};\\n",encoding="utf-8")
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
    # The full R09 host runner must build every neural operator. Generate
    # real, validated Vulkan-1.1 SPIR-V for all maintained production shaders.
    # The 12 explicit ABI generators above remain authoritative for their
    # respective headers. Missing sources and duplicate shader symbols fail.
    neural_shader_root=ACTIVE/"r09_rdna2_nr"
    shaders=sorted(neural_shader_root.glob("*_rdna2.comp"))
    assert len(shaders)>=35, ("R09 production shader inventory incomplete",
                             len(shaders))
    symbols=set()
    for shader in shaders:
        stem=shader.name.removesuffix("_rdna2.comp")
        # The production FFWD3 shader file has a group suffix, but the
        # compiled ABI published to C++ has always been named FFWD3.
        public_name="ffwd3" if stem=="ffwd3_group" else stem
        symbol="RDNA2_NR_"+public_name.upper()+"_COMP_SPV"
        assert symbol not in symbols, ("duplicate R09 shader ABI",symbol)
        symbols.add(symbol)
        header=shader_headers/("rdna2_nr_"+public_name+"_comp_spv.h")
        if header.is_file():
            continue
        spv=temp/(public_name+".spv")
        subprocess.run([
            "glslangValidator","-V","--target-env","vulkan1.1",
            "-S","comp","-o",str(spv),str(shader)
        ],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",
                        str(spv)],check=True,cwd=ROOT)
        raw=spv.read_bytes()
        assert raw and len(raw)%4==0, ("bad R09 SPIR-V",shader)
        words=struct.unpack("<"+"I"*(len(raw)//4),raw)
        output=["// SPDX-License-Identifier: MIT","#pragma once",
                "#include <array>","#include <cstdint>",
                f"inline constexpr std::array<std::uint32_t, {len(words)}> {symbol} = {{"]
        for offset in range(0,len(words),8):
            output.append("    "+", ".join(
                f"0x{word:08x}u" for word in words[offset:offset+8])+",")
        output.append("};")
        header.write_text("\n".join(output)+"\n",encoding="utf-8")
    # Independent completeness check: do not accept unknown or renamed
    # #include <video_core/host_shaders/> references during host compilation.
    for name in FILES:
        contents=(ACTIVE/name).read_text(encoding="utf-8")
        for include in re.findall(
                r'#include\s+["<]video_core/host_shaders/([^">]+)[">]',
                contents):
            assert (shader_headers/include).is_file(), (
                "R09 required compiled shader missing",name,include)
    print("R09_WHOLE_GRAPH_REAL_SPIRV_PASS shaders="+str(len(shaders)),
          "owners="+str(len(FILES)),flush=True)
    # Match production's versioned presentation Layer overlay exactly,
    # otherwise the host syntax check would use the pristine upstream
    # class and miss integration errors in the live PS5 renderer.
    present_layer=temp/"present-overlay/video_core/renderer_vulkan/present"
    present_layer.mkdir(parents=True)
    shutil.copyfile(ROOT/"headless/vulkan_present_layer_r24.h",
                    present_layer/"layer.h")
    shutil.copyfile(ROOT/"headless/vulkan_fxaa_r24.h",
                    present_layer/"fxaa.h")
    # The active PS5 build also stages vk_blit_screen.h, which carries
    # the actual accelerated VkImageView sampled_format for R09.
    # Without this overlay Clang silently includes pristine Eden's
    # FramebufferTextureInfo and misses the production header ABI.
    shutil.copyfile(ROOT/"headless/vk_blit_screen_r08.h",
                    present_layer.parent/"vk_blit_screen.h")
    # Match the exact PS5 graphics enums and display/app-capture flags.
    # The shipping stage verifies BOTH source and audited backport hashes.
    enum_tools=runpy.run_path(str(ROOT/"tools/stage-ps5-graphics-enums.py"))
    _, approved=enum_tools["approved_bytes"]()
    graphics_enums=enum_tools["extend_graphics_enums"](
        approved.decode("utf-8"))
    enum_root=temp/"graphics-enums"
    (enum_root/"common").mkdir(parents=True)
    (enum_root/"common/settings_enums.h").write_text(
        graphics_enums,encoding="utf-8")
    # The 83-source PS5 backport stages settings.h *together* with its
    # audited settings_enums.h. Mixing the old Enum (Accurate) with
    # pristine new settings.h (Strict) is an invalid hybrid ABI.
    reviewed_settings=ROOT/"vendor/encore-active/eden-backports/src/common/settings.h"
    assert reviewed_settings.is_file()
    shutil.copyfile(reviewed_settings,enum_root/"common/settings.h")
    # The same audited 83-file source baseline changes fence_manager.h:
    # pristine upstream calls IsGPUFenceBehaviorStrict, absent in the
    # reviewed GPU fence settings ABI. Never mix those revisions.
    (enum_root/"video_core").mkdir(parents=True)
    shutil.copyfile(
        ROOT/"vendor/encore-active/eden-backports/src/video_core/fence_manager.h",
        enum_root/"video_core/fence_manager.h")
    active_present=ROOT/"vendor/encore-active/eden-vulkan/include/video_core/present.h"
    source_present=ROOT/"vendor/sources/eden/src/video_core/present.h"
    assert active_present.read_bytes()==source_present.read_bytes(),(
        "R09 actual build present.h differs from Eden PresentFilters source")
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
         "-I"+str(enum_root),
         "-I"+str(temp/"buffer-pages"),
         "-I"+str(temp),
         *["-I"+str(p) for p in INCLUDES]]
    env=os.environ.copy()
    if R09_MIN_DUAL=="1":
        # Every real ViT owner with pooling disabled/enabled, plus four
        # independently compiled explicit scratch profiles in the only
        # translation unit which selects them. No production default change.
        tasks=tuple((name,mode) for name in FILES for mode in ("0","1"))+tuple(
            ("nr_rdna2_frame_session.cpp","p"+profile)
            for profile in ("4","5","6","8","12","16"))
    elif R09_FSWIN_DUAL=="1":
        # Run the exact real FSwin C++ owners in default AND scratch-pool
        # mode. This is syntax-only with real emulator/Vulkan headers.
        tasks=tuple((name,"f"+mode)
                    for name in FILES for mode in ("0","1"))
    elif R09_HOST_720_DUAL=="1":
        tasks=(("__r09_full_gpu_host__","h0"),
               ("__r09_full_gpu_host__","h1"))
    elif R09_PRESENT_720_DUAL=="1":
        tasks=(("__present_layer_r09__","r0"),
               ("__present_layer_r09__","r1"))
    elif R09_A4K_OWNER_DUAL=="1":
        # Requires separate vendor PR #40, temporarily checked out in CI.
        tasks=(("__native_a4k_owner__","a0"),
               ("__present_layer_r09__","a0"),
               ("__present_layer_r09__","a1"))
    else:
        tasks=tuple((name,None) for name in
                    (*FILES,"__present_layer_r09__","__r09_full_gpu_host__"))
    def check(task):
        name,mode=task
        source=(ROOT/"vendor/encore-active/eden-vulkan/anime4k_3d.cpp"
                if name=="__native_a4k_owner__" else
                ROOT/"headless/vulkan_present_layer_r24.cpp"
                if name=="__present_layer_r09__" else
                ROOT/"tools/graphics/r09_full_gpu_host.cpp"
                if name=="__r09_full_gpu_host__" else ACTIVE/name)
        flags=(["-DEDEN_R09_A4K_DUAL_IMAGE_RESEARCH="+mode[1:]]
                if mode is not None and mode.startswith("a")
                else ["-DEDEN_R09_MIN_720_PRESENT_RESEARCH="+mode[1:]]
               if mode is not None and mode.startswith("r")
               else ["-DEDEN_R09_MIN_720_HOST_EXPERIMENTAL="+mode[1:]]
               if mode is not None and mode.startswith("h")
               else ["-DEDEN_R09_MIN_FSWIN_SCRATCH_POOL_EXPERIMENTAL="+mode[1:]]
               if mode is not None and mode.startswith("f")
               else ["-DEDEN_R09_MIN_VIT_POOL_EXPERIMENTAL=1",
                     "-DEDEN_R09_MIN_VIT_POOL_SCRATCH_PLANES="+mode[1:]]
               if mode is not None and mode.startswith("p")
               else ["-DEDEN_R09_MIN_VIT_POOL_EXPERIMENTAL="+mode]
               if mode is not None else [])
        result=subprocess.run(cmd+flags+[str(source)],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=150)
        return name+("_macro_"+mode if mode else ""),result.returncode,result.stderr[-10000:]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(check,tasks))
    failures=[]
    for name,rc,diagnostics in results:
        if rc:
            failures.append(name)
            print("R09_NEURAL_NATIVE_CPP_FAIL",name,diagnostics,flush=True)
        else:
            print("R09_NEURAL_NATIVE_CPP_PASS",name,flush=True)
    assert not failures,("R09 selected native C++ syntax failed",failures)
    if R09_MIN_DUAL=="1":
        assert len(results)==18
        print("R09_MIN_VIT_NATIVE_CPP_BOTH_MODES_AND_ALL_SIX_SCRATCH_PROFILES_PASS",flush=True)
    elif R09_FSWIN_DUAL=="1":
        assert len(results)==6
        print("R09_FSWIN_NATIVE_CPP_ALL_THREE_REAL_TUS_BOTH_MACRO_MODES_PASS",flush=True)
    elif R09_HOST_720_DUAL=="1":
        assert len(results)==2
        print("R09_MIN_720_ORIGINAL_REAL_HOST_RUNNER_MACRO_OFF_ON_SYNTAX_PASS",flush=True)
    elif R09_PRESENT_720_DUAL=="1":
        assert len(results)==2
        print("R09_MIN_720_REAL_POST_NEURAL_FSR_PRESENTER_MACRO_OFF_ON_SYNTAX_PASS",flush=True)
    elif R09_A4K_OWNER_DUAL=="1":
        assert len(results)==3
        print("R09_A4K_NATIVE_OWNER_AND_SPATIAL_PRESENTER_BOTH_MACROS_SYNTAX_PASS",flush=True)
    else:
        print("R09_NEURAL_NATIVE_CPP_HOST_PASS owners="+str(len(FILES)),flush=True)
