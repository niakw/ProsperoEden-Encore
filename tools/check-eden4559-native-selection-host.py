#!/usr/bin/env python3
from pathlib import Path
import subprocess, hashlib
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert selected==checked=="42459a7893c51a178ecd0c2f74f3951cc20fa12d",(selected,checked)
cm=(ROOT/"headless/vulkan.cmake").read_text()
for marker in (
    'list(FIND video_sources "renderer_vulkan/blit_image.cpp" EDEN4559_PINNED_BLIT_INDEX)',
    'list(REMOVE_ITEM video_sources renderer_vulkan/blit_image.cpp)',
    'list(APPEND video_sources "${PORT_BUILD_DIR}/blit_image.cpp")',
    'message(FATAL_ERROR "Missing maintained Eden #4559 BlitImageHelper owner")',
):
    assert marker in cm,marker
active=V/"encore-active/eden/src/video_core/renderer_vulkan"
assert (active/"blit_image.cpp").is_file()
assert (active/"blit_image.h").is_file()
assert "const std::optional<VkRect2D>& scissor = std::nullopt" in (
    active/"blit_image.h").read_text()
subprocess.run(["python3","-B",str(V/"tests/eden4559_drawtexture_state_source.py")],
               cwd=ROOT,check=True,timeout=120)
print("EDEN4559_ENGINE_VENDOR_SELECTION_PASS blit_cpp=maintained header=matched ps5=unverified")
