#!/usr/bin/env python3
"""Exercise the real native PS5 NS2 selector gate without compiling the SDK."""
from pathlib import Path
import os
import re
import subprocess

root = Path(__file__).resolve().parents[2]
cmake = (root / "headless/CMakeLists.txt").read_text()
native_script = root / "tools/build-headless-native.sh"
script = native_script.read_text()

declared = re.findall(r"option\\((EDEN_NS2_[A-Z0-9_]+)\\s", cmake)
assert declared and len(declared) == len(set(declared)), "missing/duplicate NS2 CMake options"
start = script.index("# The shipping PS5 package must never silently acquire")
end = script.index('cmake -S "$scratch/source"', start)
gate = script[start:end]
forwarded = re.findall(r"^    (EDEN_NS2_[A-Z0-9_]+)$", gate, re.MULTILINE)
assert set(forwarded) == set(declared), (
    "Native CMake options drifted", sorted(set(declared) - set(forwarded)),
    sorted(set(forwarded) - set(declared))
)
assert '"${ns2_cmake_args[@]}"' in script, "native CMake does not receive selector array"
assert 'EDEN_FINAL_RELEASE_PROFILE=ON' in gate
assert 'EDEN_NS2_NATIVE_EXPERIMENTAL=ON' in gate

subprocess.run(["bash", "-n", str(native_script)], check=True)
test_code = "set -euo pipefail\\n" + gate + '\\nprintf "%s\\n" "${ns2_cmake_args[@]}"\\n'

def verify(overrides, expected_exit):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    env.update(overrides)
    run = subprocess.run(["bash", "-c", test_code], env=env, text=True,
                         capture_output=True, timeout=10)
    assert (run.returncode == 0) == (expected_exit == 0), (
        overrides, run.returncode, run.stderr
    )
    return run

normal = verify({}, 0)
assert len(normal.stdout.splitlines()) == len(declared)
assert set(normal.stdout.splitlines()) == {f"-D{name}=OFF" for name in declared}
research = verify({"EDEN_NS2_NATIVE_EXPERIMENTAL": "ON",
                   "EDEN_NS2_METADATA_EXPERIMENTAL": "ON"}, 0)
assert "-DEDEN_NS2_METADATA_EXPERIMENTAL=ON" in research.stdout.splitlines()
verify({"EDEN_NS2_METADATA_EXPERIMENTAL": "ON"}, 2)
verify({"EDEN_NS2_NATIVE_EXPERIMENTAL": "ON",
        "EDEN_FINAL_RELEASE_PROFILE": "ON"}, 2)
verify({"EDEN_NS2_NATIVE_EXPERIMENTAL": "maybe"}, 2)
verify({"EDEN_NS2_NATIVE_EXPERIMENTAL": "ON",
        "EDEN_NS2_A64_EXPERIMENTAL": "maybe"}, 2)
print(f"PASS: {len(declared)} native NS2 CMake selectors; opt-in research; release fail-closed")
