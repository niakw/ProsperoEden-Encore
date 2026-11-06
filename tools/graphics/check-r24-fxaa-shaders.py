#!/usr/bin/env python3
"""R24 shader/selected-source audit. Only host tools, no PS5 build."""
import hashlib
import pathlib
import shutil
import subprocess
import tempfile

root=pathlib.Path(__file__).resolve().parents[2]
source=(root/"headless/fxaa_quality.frag").read_text()
native=(root/"headless/vulkan_fxaa_r24.cpp").read_text()
cmake=(root/"headless/vulkan.cmake").read_text()
present=(root/"headless/vulkan_present_layer_r24.cpp").read_text()
launch=(root/"headless/main.cpp").read_text()
prefs=(root/"headless/settings_store.h").read_text()

mapping={
    "const float FXAA_SPAN_MAX = 12.0;":
        "const float FXAA_SPAN_MAX = 8.0;",
    "const float FXAA_REDUCE_MUL = 1.0 / 16.0;":
        "const float FXAA_REDUCE_MUL = 1.0 / 8.0;",
    "const float FXAA_REDUCE_MIN = 1.0 / 256.0;":
        "const float FXAA_REDUCE_MIN = 1.0 / 128.0;",
}
for high,base in mapping.items():
    assert source.count(high)==1,(high,source.count(high))
    assert base not in source
assert "FXAA_QUALITY_FRAG_SPV" in native
assert "FXAA_FRAG_SPV" in native
assert "if (m_enhanced)" in native
assert "anti_alias.emplace<FXAA>(device, memory_allocator, image_count, render_area, enhanced)" in present
assert "fxaa_enhanced_setting == enhanced" in present
assert "scheduler.Finish()" in present and "WaitIdle()" in present
assert "vulkan_fxaa_r24.cpp" in cmake and "fxaa_quality_select.cpp" in cmake
assert "eden-r24-fxaa-quality-spv" in cmake
assert 'SetEnhancedFxaa(' in launch and 'anti_aliasing == 3 && profile_renderer == 1' in launch
assert '{"none", "fxaa", "smaa", "fxaa_quality"}' in prefs
assert '"FXAA+"' in prefs

glslang=shutil.which("glslangValidator")
spirv_val=shutil.which("spirv-val")
if not glslang or not spirv_val:
    raise SystemExit("Host shader tools glslangValidator and spirv-val required")
with tempfile.TemporaryDirectory() as tmp:
    work=pathlib.Path(tmp)
    std=source
    for high,base in mapping.items():
        std=std.replace(high,base)
    (work/"fxaa_regular.frag").write_text(std)
    inputs=[work/"fxaa_regular.frag",root/"headless/fxaa_quality.frag"]
    binaries=[]
    for idx,input_path in enumerate(inputs):
        output=work/f"fxaa_{idx}.spv"
        cmd=[glslang,"-V","-DUseUniformBlock=1",
             "--target-env","spirv1.3","-o",str(output),str(input_path)]
        subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                       text=True,check=True)
        subprocess.run([spirv_val,"--target-env","spv1.3",str(output)],
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        binaries.append(output.read_bytes())
assert binaries[0]!=binaries[1],"Quality SPIR-V silently identical to standard"
print("PASS R24: two different valid SPIR-V shaders, native selection, resize/lifetime, UI persistence and Vulkan host-only guard")
print(" regular",hashlib.sha256(binaries[0]).hexdigest()[:16])
print(" enhanced",hashlib.sha256(binaries[1]).hexdigest()[:16])
