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
    'Refusing to null unreviewed weak PS5 import:',
):
    assert part in link, f"missing weak-import contract: {part}"
# Execute the production shell case. The R457 ELF has exactly 5,719 weak
# optional dispatch entries under these ten Mesa families, and no others.
# A future missing runtime/CRT/Vulkan export must fail the link, not get NULL.
case_body = link.split('    case "$name" in\n', 1)[1].split('    esac', 1)[0]
def guarded(symbol: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", 'name="$1"; case "$name" in\n'
                           + case_body + 'esac', "_", symbol],
                          capture_output=True, text=True, timeout=5)

for symbol in ("sceKernelUsleep", "sceSystemServiceParamGetInt",
               "sceVideoOutSubmitFlip", "sceAudioOutOutput", "sceNetInit",
               "pthread_create", "pthread_join", "__cxa_throw",
               "__cxa_allocate_exception"):
    test = guarded(symbol)
    assert test.returncode == 2 and 'required PS5 runtime symbol' in test.stderr, (symbol, test)
for symbol in ("vkCmdDraw", "radv_shader_nir_to_asm", "glDrawArrays",
               "__cxa_thread_atexit", "malloc", "foreign_OptionalHook",
               "sceKernelWeakEntry", "radv_missingFallback"):
    test = guarded(symbol)
    assert test.returncode == 2 and test.stderr.strip(), (symbol, test)
for symbol in ("radv_AcquireNextImageKHR", "vk_common_AcquireNextImageKHR",
               "wsi_AllocateCommandBuffers", "ctx_roll_CmdDraw",
               "rmv_CmdDraw", "rra_CmdDraw", "utrace_CmdDraw",
               "sqtt_CmdDraw", "annotate_CmdDraw", "threaded_CmdDraw"):
    test = guarded(symbol)
    assert test.returncode == 0, (symbol, test)
subprocess.run(["bash","-n",str(root/"tools/link-headless-native.sh")],
               check=True,timeout=10)
print("PASS native weak symbol scan/resolution; required PS5 and unknown imports rejected; ten optional Mesa dispatch families only")
