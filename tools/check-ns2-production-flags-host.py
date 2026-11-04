#!/usr/bin/env python3
"""Source-only gate for migrating NS2 research switches into the shared engine.

No build, shell activation, or claim of title compatibility. A human must
review every new/removed switch against the roadmap and the real source owner.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
DOC = (ROOT / "docs/NS1_NS2_PRODUCTION_FLAG_MIGRATION.md").read_text()
ROADMAP = (ROOT / "docs/ROADMAP_NS1_NS2_UNIFIED.md").read_text()
README = (ROOT / "README.md").read_text()
OPT = re.compile(
    r'option\(\s*(EDEN_NS2_[A-Z0-9_]*EXPERIMENTAL)\s*"[^"]+"\s+(ON|OFF)\s*\)'
)
declared = OPT.findall(CMAKE)
flags = dict(declared)
all_source_flags = set(re.findall(r'\bEDEN_NS2_[A-Z0-9_]*EXPERIMENTAL\b', CMAKE))
assert len(declared) == len(flags), "Duplicate CMake option owner"
assert len(flags) == 9, ("Unreviewed number of NS2 research gates", len(flags))
assert all_source_flags == set(flags), sorted(all_source_flags - set(flags))
assert set(flags.values()) == {"OFF"}, "Research flags must not be enabled by default"

# Retain an opt-in only when it still owns a concrete, selected
# implementation. Simply listing an old option in the release denylist is
# not evidence of a useful research path.
implementation_proofs = {
    "EDEN_NS2_SPARSE_CACHE_PROBE_EXPERIMENTAL": "EDEN_NS2_SPARSE_CACHE_PROBE=1",
    "EDEN_NS2_EXEFS_EXPERIMENTAL": "EDEN_NS2_NATIVE_SVC_SOURCE",
    "EDEN_NS2_A64_EXPERIMENTAL": "target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_EXPERIMENTAL=1)",
    "EDEN_NS2_CPU6_EXPERIMENTAL": "target_compile_definitions(core PRIVATE EDEN_NS2_CPU6_EXPERIMENTAL=1)",
    "EDEN_NS2_NVDRV_EXPERIMENTAL": "EDEN_NS2_NVDRV_AS_SOURCE",
    "EDEN_NS2_GPU_SESSION_EXPERIMENTAL": "EDEN_NS2_GPU_SESSION_SOURCE",
    "EDEN_NS2_GRAPHICS_SUPERVISOR_EXPERIMENTAL": "EDEN_NS2_SUPERVISOR_ROOT",
    "EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL": "EDEN_NS2_NATIVE_GMMU_CAPTURE",
    "EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL": "EDEN_NS2_NATIVE_GPU_SPIRV_CAPTURE",
}
assert set(implementation_proofs) == set(flags), "Unproved/dead NS2 option was retained"
native_runner = (ROOT / "tools/build-headless-native.sh").read_text()
research_workflow = (ROOT / ".github/workflows/ns2-native-ps5-research.yml").read_text()
for flag, marker in implementation_proofs.items():
    assert marker in CMAKE, ("No compiled source owner for retained research option", flag)
    assert CMAKE.count(flag) >= 2, ("Unused NS2 option", flag)
    assert "    " + flag + "\n" in native_runner, ("Native research build misses option", flag)
    assert flag + ": 'ON'" in research_workflow, ("Research workflow misses option", flag)
assert "EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL" not in CMAKE
assert "graphics_scaling_parameters_functions.cpp" not in CMAKE
assert "EDEN_NS2_SPARSE_QUEUE_EXPERIMENTAL" not in CMAKE
sparse_queue_owner = CMAKE.split("# N72: serialize sparse binds", 1)[1].split(
    "# N60: one shared PS5 Vulkan texture-cache", 1)[0]
assert "if(EDEN_NS2_SPARSE_CACHE_PROBE_EXPERIMENTAL)" in sparse_queue_owner
assert "target_compile_definitions(video_core PRIVATE EDEN_NS2_SPARSE_QUEUE_BRIDGE=1)" in sparse_queue_owner
assert "target_compile_definitions(video_core PRIVATE EDEN_NS2_SPARSE_CACHE_PROBE=1)" in CMAKE

documented = re.findall(r'`(EDEN_NS2_[A-Z0-9_]*EXPERIMENTAL)`', DOC)
assert len(documented) == len(set(documented)) == len(flags), (
    "Missing, duplicated or obsolete migration checklist owners", documented
)
assert set(documented) == set(flags), (
    "Every NS2 research feature needs a migration/removal contract",
    sorted(set(flags) - set(documented)),
    sorted(set(documented) - set(flags)),
)
assert "https://github.com/niakw/ProsperoEden-Encore/issues/15" in README
assert "ROADMAP_NS1_NS2_UNIFIED.md" in README
assert "NS1/NS2" in ROADMAP
assert "if: ${{ false }}" in (
    ROOT / ".github/workflows/build-040-zbic.yml"
).read_text()
assert "if: ${{ false }}" in (
    ROOT / ".github/workflows/ns2-native-ps5-research.yml"
).read_text()
print(f"EDEN_NS1_NS2_RESEARCH_GATE_INVENTORY_PASS reviewed={len(flags)}"
      " defaults_off=1 release_builds_frozen=1 roadmap_linked=1")
