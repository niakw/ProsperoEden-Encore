#!/usr/bin/env python3
"""R08: verify the pinned framegen *source* without claiming a PS5 renderer."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import os

root = Path(__file__).resolve().parents[2]
module = root / "third_party/PS5_MihawkGen"
expected_sha = "c57232a9f16bcb6df5fe07c9bb631518f2b1cc0e"
expected_network = "31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b"

def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)

git_sha = subprocess.check_output(
    ["git", "-C", str(module), "rev-parse", "HEAD"], text=True).strip()
check(git_sha == expected_sha, f"MihawkGen SHA mismatch: {git_sha}")
network = module / "framegen/models/network.fgw"
check(network.stat().st_size == 1757240, "Unexpected MihawkGen model size")
check(hashlib.sha256(network.read_bytes()).hexdigest() == expected_network,
      "Unexpected MihawkGen model hash")
sources = [module / f"framegen/src/fg_{name}.cpp" for name in
           ("common", "neural", "splat", "vulkan")]
for source in sources:
    check(source.is_file(), f"Missing native source: {source}")
shaders = sorted((module / "framegen/shaders").glob("*.spv"))
check(len(shaders) == 21, f"Unexpected SPIR-V count: {len(shaders)}")
if validator := shutil.which("spirv-val"):
    for shader in shaders:
        subprocess.run([validator, "--target-env", "vulkan1.3", str(shader)], check=True)
    print(f"SPIR-V: {len(shaders)} Vulkan 1.3 shaders validated")
else:
    print("SPIR-V: validation unavailable (spirv-val not installed)")
compiler = os.environ.get("CXX") or shutil.which("clang++")
if compiler:
    cmd = [compiler, "-std=c++20", "-fsyntax-only", "-Wno-missing-designated-field-initializers",
           "-DVK_NO_PROTOTYPES", "-I" + str(module / "framegen/include"),
           "-I" + str(module / "framegen/src"),
           "-I" + str(module / "external"), "-include",
           str(module / "ps5/third_party/volk/volk.h")]
    subprocess.run(cmd + [str(src) for src in sources], check=True)
    print("C++: four MihawkGen core sources passed host syntax")
else:
    print("C++: source compilation unavailable (clang++ not installed)")
print("R08 SOURCE PASS: pinned modules and model verified; NO native PS5 execution")
