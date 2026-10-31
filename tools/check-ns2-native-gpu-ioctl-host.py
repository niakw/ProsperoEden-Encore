#!/usr/bin/env python3
"""Validate exact native GPU characteristic reply helper against synthetic ioctl fixtures."""
from pathlib import Path
import subprocess,shutil,sys,tempfile

ROOT=Path(__file__).resolve().parent.parent
NVDRV=ROOT/"vendor/encore-active/ns2-runtime/nvdrv"
EDEN=ROOT/"vendor/sources/eden/src"
SOURCE=ROOT/"tools/ns2/test_native_gpu_ioctl.cpp"
OWNER=NVDRV/"core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp"
def main():
    if not OWNER.is_file() or "WriteNativeCharacteristicsIoctlReply(" not in OWNER.read_text():
        print("NVDRV research owner not wired to tested helper",file=sys.stderr)
        return 2
    cc=shutil.which("clang++") or shutil.which("g++")
    if not cc:
        print("Missing C++20 compiler",file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="encore-ns2-gpu-ioctl-") as tmp:
        for opt in ("-O0","-O2"):
            executable=Path(tmp)/("test"+opt)
            subprocess.run([cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                            "-pedantic","-fsanitize=undefined","-fno-sanitize-recover=all",
                            "-I",str(NVDRV),"-I",str(EDEN),str(SOURCE),
                            "-o",str(executable)],check=True)
            subprocess.run([str(executable)],check=True)
            print("Native NVDRV reply "+opt+": PASS")
    print("No device capabilities, Ampere execution or PS5 runtime validated.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
