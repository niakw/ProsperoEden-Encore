#!/usr/bin/env python3
"""Host-only: confirm that every new spatial filter selects a real shader."""
import pathlib, shutil, subprocess, tempfile, hashlib
root=pathlib.Path(__file__).resolve().parents[2]
read=lambda name:(root/name).read_text()
settings=read("headless/settings_store.h")
main=read("headless/main.cpp")
cmake=read("headless/vulkan.cmake")
blit=read("headless/vulkan_blit_screen_r08.cpp")
layer=read("headless/vulkan_present_layer_r24.cpp")
sgsr=read("headless/vulkan_sgsr_r07.cpp")
ui=read("headless/prosperoeden/pe/ui/settings.cpp")
game=read("headless/prosperoeden/pe/ui/library.cpp")
switch=read("headless/prosperoeden/pe/ui/switch_theme.cpp")
count=read("headless/prosperoeden/pe/ui/settings.cpp")
assert '"bilinear", "fsr", "bicubic", "nearest", "lanczos", "sgsr", "sgsr_edge"' in settings
assert "Settings::ScalingFilter::Lanczos" in main
assert "Settings::ScalingFilter::Sgsr" in main
assert "Settings::ScalingFilter::SgsrEdge" in main
assert "MakeLanczos" in blit
assert "sr_filter.emplace<SGSR>" in layer
assert "SGSR1_SHADER_MOBILE_FRAG_SPV" in sgsr
assert "SGSR1_SHADER_MOBILE_EDGE_DIRECTION_FRAG_SPV" in sgsr
assert 'vulkan_sgsr_r07.cpp' in cmake
assert 'renderer_vulkan/present/sgsr.cpp' in cmake
assert 'UpscalingFilterSelectable(next,prefs_.renderer)' in ui
assert 'UpscalingFilterSelectable(selected,' in game
assert 'return services_.save_transfer_available() ? 14 : 13;' in count
assert 'const std::array<std::string,14> values' in switch
assert 'if(i<0||i>=14)continue;' in switch
assert 'case 7:value=TextureAnisotropyName' in switch
assert 'case 8:value=prefs_.frame_generation' in switch
assert 'case 9:value=prefs_.refresh' in switch
shader_source=pathlib.Path("/Users/admin/Developer/EdenEncore/vendor/sources/eden/src/video_core/host_shaders")
# Compatible with portable environments: identify the pinned source through
# actual git submodule when the developer's local mirrors are not mounted.
if not shader_source.is_dir():
    shader_source=root/"vendor/sources/eden/src/video_core/host_shaders"
glslang=shutil.which("glslangValidator")
validator=shutil.which("spirv-val")
if not glslang or not validator:raise SystemExit("Need glslangValidator and spirv-val")
names=("sgsr1_shader_mobile.frag",
       "sgsr1_shader_mobile_edge_direction.frag",
       "sgsr1_shader.vert","present_lanczos.frag")
with tempfile.TemporaryDirectory() as tmp:
    hashes=[]
    for name in names:
        src=shader_source/name
        assert src.exists(),f"Missing upstream shader {name}"
        output=pathlib.Path(tmp)/(name.replace(".","_")+".spv")
        subprocess.run([glslang,"-V","--quiet","--target-env","spirv1.3",
                        "-DUseUniformBlock=1","-o",str(output),str(src)],check=True)
        subprocess.run([validator,"--target-env","spv1.3",str(output)],check=True)
        hashes.append(hashlib.sha256(output.read_bytes()).hexdigest())
assert hashes[0]!=hashes[1],"SGSR and SGSR Edge compiled identically"
print("PASS R07: Lanczos + 2 different SGSR shader paths, Vulkan-only guards, user settings and 14 game rows")
for name,digest in zip(names,hashes):print(" ",name,digest[:16])
