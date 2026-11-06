#!/usr/bin/env python3
"""Pinned PS5 optical-flow FSR3 shader/host/source gate, no PS5 build."""
from pathlib import Path
import re
import struct
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
src=root/"third_party/PS5_FSR3OpticalFlow"
if not (src/"src/ps5_framegen.cpp").is_file():
    raise SystemExit("Missing third_party/PS5_FSR3OpticalFlow submodule")
commit=subprocess.check_output(["git","-C",str(src),"rev-parse","HEAD"],text=True).strip()
assert commit=="64362101757cdd6f7df9eeb984cb53f03f1fbfca",commit
inc=(src/"src/framegen/fg_shaders.inc").read_text()
arrays=re.findall(r"static const u32 k_fg_spv_(\w+)\[(\d+)\]\s*=\s*\{(.*?)\};",inc,re.S)
assert len(arrays)==10,f"expected 10 optical-flow shader arrays, got {len(arrays)}"
with tempfile.TemporaryDirectory() as temp:
    for label,count,contents in arrays:
        words=[int(x,16) for x in re.findall(r"0x[0-9a-fA-F]+",contents)]
        assert len(words)==int(count),(label,len(words),count)
        assert words[0]==0x07230203,label
        path=Path(temp)/(label+".spv")
        path.write_bytes(struct.pack(f"<{len(words)}I",*words))
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(path)],
                       check=True,stdout=subprocess.DEVNULL)
        print("PASS SPIR-V",label,len(words),"words")
header=(src/"src/ps5_framegen.h").read_text()
for token in ["VkPhysicalDevice physical", "VkDevice device",
              "bool record(VkCommandBuffer cmd, bool reset)",
              "VkImage output_image() const", "void advance()",
              "VK_FORMAT_R8G8B8A8_UNORM", "PS5_FRAMEGEN_VULKAN_HEADER"]:
    assert token in header,token
assert "lossless" not in header.lower()
assert "GNU GENERAL PUBLIC LICENSE" in (src/"COPYING").read_text()
print("PASS pinned optical-flow source, 10 validated SPIR-V shaders, GPL-3/MIT")

settings = (root/"headless/settings_store.h").read_text()
assert '{"off", "mihawkgen", "fsr3", "lsfg"}' in settings
assert "Lossless Scaling LAST" in settings
renderer = (root/"headless/vulkan_renderer_r08.cpp").read_text()
assert "fsr3_optical->Create(" in renderer
assert "fsr3_optical->Ready()" in renderer
assert "fsr3_last_capture_tick" in renderer
assert "present_manager.Present(fsr3_synthetic)" in renderer
assert "present_manager.Present(frame)" in renderer
assert "TryReserveRenderFrame()" in renderer
assert "Fsr3OpticalSession" in (root/"headless/renderer_vulkan_r08.h").read_text()
print("PASS 3 methods in persistent order: MihawkGen, FSR3 optical flow, LSFG last")
