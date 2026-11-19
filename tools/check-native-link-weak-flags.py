#!/usr/bin/env python3
"""Guard native two-pass weak-symbol linker resolution without ignored -z flags."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
link = (root/"tools/link-headless-native.sh").read_text()
assert "-z nodynamic-undefined-weak" not in "\n".join(
    line for line in link.splitlines() if not line.lstrip().startswith("#")
)
for part in (
    'link_native "$weak_scan" "$weak_map"',
    'weak_flags+=("--defsym=${name}=0")',
    'link_native "$output" "$output.map" "${weak_flags[@]}"',
    'if "$nm_tool" -D --undefined-only "$output"',
    'Native link still contains unresolved weak imports:',
    'Refusing to null required PS5 runtime symbol:',
):
    assert part in link, f"missing weak-import contract: {part}"
# Test the exact linker guard against essential native APIs and optional Mesa slots.
case_body = link.split('    case "$name" in\n', 1)[1].split('    esac', 1)[0]
for symbol in ("sceKernelUsleep", "sceSystemServiceParamGetInt",
               "sceVideoOutSubmitFlip", "sceAudioOutOutput", "sceNetInit",
               "pthread_create", "pthread_join", "__cxa_throw",
               "__cxa_allocate_exception"):
    test = subprocess.run(["bash", "-c", 'name="$1"; case "$name" in\n'
                           + case_body + 'esac', "_", symbol], capture_output=True)
    assert test.returncode == 2, (symbol, test.returncode, test.stderr)
for symbol in ("vkCmdDraw", "radv_shader_nir_to_asm", "glDrawArrays"):
    test = subprocess.run(["bash", "-c", 'name="$1"; case "$name" in\n'
                           + case_body + 'esac', "_", symbol], capture_output=True)
    assert test.returncode == 0, (symbol, test.returncode, test.stderr)
subprocess.run(["bash","-n",str(root/"tools/link-headless-native.sh")],
               check=True,timeout=10)
print("PASS native weak symbol scan/resolution preserved; unsupported linker option removed")
