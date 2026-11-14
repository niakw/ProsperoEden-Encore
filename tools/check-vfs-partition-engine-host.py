#!/usr/bin/env python3
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/"headless/CMakeLists.txt").read_text()
begin = "foreach(eden_vfs_relative IN ITEMS"
assert source.count(begin)==1
segment = begin + source.split(begin,1)[1].split("# NSZ/XCZ:",1)[0]
paths = ["file_sys/vfs/vfs.cpp","file_sys/vfs/vfs_vector.cpp","file_sys/partition_filesystem.cpp",
         "file_sys/fssystem/fssystem_integrity_verification_storage.cpp",
         "file_sys/fssystem/fssystem_nca_file_system_driver.cpp"]
for name in paths:
    assert '"' + name + '"' in segment
    assert (ROOT/"vendor/encore-active/eden-core/src/core"/name).is_file()
ncz = source.split("# NSZ/XCZ:",1)[1].split("# Extracted AOC:",1)[0]
assert '"file_sys/card_image.cpp"' in ncz
# Evaluate the actual CMake selection loop with the original source list.
with tempfile.TemporaryDirectory(prefix="vfs-selection-") as tmp:
    p = Path(tmp)/"check.cmake"
    p.write_text('set(PORT_ROOT "'+str(ROOT)+'")\nset(core_sources '+ ' '.join(paths) +' file_sys/card_image.cpp)\n'+segment+'''
list(LENGTH core_sources len)
if(NOT len EQUAL 6)
    message(FATAL_ERROR "VFS duplicate or missing selected owner")
endif()
foreach(relative IN ITEMS '''+' '.join(paths)+''')
    if(relative IN_LIST core_sources)
       message(FATAL_ERROR "Original VFS owner retained")
    endif()
    if(NOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/${relative}" IN_LIST core_sources)
       message(FATAL_ERROR "Maintained owner missing")
    endif()
endforeach()
''')
    # IN_LIST policy enabled by minimum version; script mode has no project.
    p.write_text("cmake_minimum_required(VERSION 3.20)\n"+p.read_text())
    subprocess.run(["cmake","-P",str(p)],check=True,timeout=30)
print("VFS_ENGINE_SELECTED_OWNER_HOST_PASS replacements=5 nca_owners=2 xci_existing_owner=1 actual_cmake_loop=1 full_native_graph=unverified")
