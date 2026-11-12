#!/usr/bin/env python3
"""R08: verify the pinned framegen *source* without claiming a PS5 renderer."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import os

root = Path(__file__).resolve().parents[2]
module = root / "vendor/sources/ps5-mihawkgen"
expected_sha = "c57232a9f16bcb6df5fe07c9bb631518f2b1cc0e"
expected_network = "31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b"

def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)

tree_sha = subprocess.check_output(["git", "-C", str(root/"vendor"), "rev-parse", "HEAD:sources/ps5-mihawkgen"], text=True).strip()
check(tree_sha == "aad67f4bd28c040db7aa0d78cfd3d0de85cfba7a", f"Vendored MihawkGen tree mismatch: {tree_sha}")
# Security change: the exact vendor tree differs from official MihawkGen
# only by the reviewed Python training Pillow pin. Do not depend on old
# commit objects being present in GitHub Actions' shallow submodule clone.
requirements=(module / "train/requirements.txt").read_bytes()
check(requirements.count(b"pillow==13.0.0")==1,"MihawkGen Pillow security pin missing")
old_requirements=requirements.replace(b"pillow==13.0.0",b"pillow==12.3.0")
original_git_blob=hashlib.sha1(
    b"blob "+str(len(old_requirements)).encode()+b"\\x00"+old_requirements
).hexdigest()
check(original_git_blob=="0d8325d208ccfb9d1a3abf37d2688ed01787b240",
      "MihawkGen upstream requirements revision not recognized")
check(expected_sha in (root/"vendor/docs/PS5_INTERNAL_DEPENDENCY_ORIGINS_2026-11-10.md").read_text(), "Missing original upstream commit")
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
