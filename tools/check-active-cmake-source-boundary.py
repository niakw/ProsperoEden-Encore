#!/usr/bin/env python3
"""Audit the single vendor source-of-truth contract used by main.

Unmodified upstream inputs stay under vendor/sources. Every maintained Encore
override lives under vendor/encore-active and CMake selects those tracked bytes
directly; build-time C++ fabrication/patching is forbidden. The vendor checkout
must match the engine gitlink, with no historical revision allowlist.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
ACTIVE = VENDOR / "encore-active"
SOURCES = VENDOR / "sources"

gitlink = subprocess.check_output(
    ["git", "ls-tree", "HEAD", "vendor"], cwd=ROOT, text=True
).split()
assert len(gitlink) == 4 and gitlink[0] == "160000" and gitlink[1] == "commit"
vendor_head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=VENDOR, text=True
).strip()
assert vendor_head == gitlink[2], ("vendor checkout differs from engine gitlink", vendor_head, gitlink[2])
assert ACTIVE.is_dir() and SOURCES.is_dir()
assert not subprocess.check_output(
    ["git", "status", "--porcelain", "--untracked-files=no"], cwd=VENDOR, text=True
).strip(), "tracked vendor source is dirty"

# One layout contract, no per-revision SHA catalogue. sources/ is the frozen
# dependency mirror; encore-active/ is the only maintained override tree.
sources_readme = (SOURCES / "README.md").read_text(encoding="utf-8")
active_readme = (ACTIVE / "README.md").read_text(encoding="utf-8")
for marker in (
    "sources/ = dépendances upstream figées",
    "encore-active/ = code maintenu par Eden Encore",
):
    assert marker in sources_readme, ("sources contract drift", marker)
for marker in (
    "override pur Eden Encore",
    "même nom de dépendance, même chemin relatif",
    "sources/ est la dépendance ; encore-active/ est notre code final",
):
    assert marker in active_readme, ("encore-active contract drift", marker)

# Functional roots that duplicated the Eden dependency are retired. A future
# override must use encore-active/eden/<same upstream-relative path>, not
# recreate a second family tree.
retired_eden_roots = ("eden-gpu", "eden-sync", "eden-threading", "eden-shader")
for legacy in retired_eden_roots:
    assert not (ACTIVE / legacy).exists(), ("retired Encore root reintroduced", legacy)

root_cmake = (ROOT/"headless/CMakeLists.txt").read_text(encoding="utf-8")
assert "vendor/encore-active" in root_cmake
# P5: CMake defers only target wiring, never creating a subdirectory.
# The actual project(yuzu) hook registers the immutable source before DEFER.
native_inject = (ROOT/"headless/inject.cmake").read_text(encoding="utf-8")
assert native_inject.count("cmake_language(DEFER CALL add_eden_headless)") == 1
assert native_inject.count('add_subdirectory("${EDEN_WEBP_ROOT}"') == 1
assert 'add_subdirectory("${EDEN_WEBP_ROOT}"' not in root_cmake
assert 'if(NOT TARGET webp OR NOT EXISTS "${EDEN_WEBP_ROOT}/CMakeLists.txt")' in root_cmake
assert 'target_link_libraries(eden-headless PRIVATE webp)' in root_cmake
assert native_inject.index('add_subdirectory("${EDEN_WEBP_ROOT}"') > (
    native_inject.index("cmake_language(DEFER CALL add_eden_headless)"))
# The existing maintained threading module selects absolute HLE sources.
# Compare their canonical names before replacing the single Wait64 owner;
# the unnormalised PORT_ROOT spelling may include /headless/...
assert 'foreach(eden_wait64_candidate IN LISTS eden_wait64_sources)' in root_cmake
assert 'get_filename_component(eden_wait64_reviewed_real' in root_cmake
assert 'get_filename_component(eden_wait64_candidate_real' in root_cmake
assert 'if(eden_wait64_candidate_real STREQUAL eden_wait64_reviewed_real)' in root_cmake
assert root_cmake.count('message(FATAL_ERROR "Missing unified address arbiter owner:') == 1

generator_sites = re.findall(
    r'^\s*write_derived\(\s*"([^"]+)"', root_cmake, re.M)
assert generator_sites == ["${PORT_BUILD_DIR}/include/loading_scene_glsl.h"], generator_sites
assert root_cmake.count("function(write_derived path content)") == 1
assert root_cmake.count('file(WRITE "${path}.in" "${content}")') == 1
assert len(re.findall(r"^\s*string\(REPLACE", root_cmake, re.M)) == 2
assert 'write_derived("${derived}"' not in root_cmake
assert 'write_derived("${PORT_BUILD_DIR}/kernel.cpp"' not in root_cmake
assert 'write_derived("${PORT_BUILD_DIR}/gpu.cpp"' not in root_cmake

# Discover modules recursively so a newly introduced indirect CMake owner
# cannot hide outside today's documented top-level module list.
module_paths = {
    ROOT/"tools/ps5.cmake",
    *(ROOT/"headless").rglob("*.cmake"),
    *(ROOT/"vendor/encore-active").rglob("*.cmake"),
    *(ROOT/"vendor/encore-active").rglob("CMakeLists.txt"),
}
module_paths.discard(ROOT/"headless/CMakeLists.txt")

for path in [ROOT/"headless/CMakeLists.txt", *sorted(module_paths)]:
    source = path.read_text(encoding="utf-8")
    for legacy in retired_eden_roots:
        forbidden = f"vendor/encore-active/{legacy}"
        assert forbidden not in source, (
            "active CMake references retired Encore root",
            str(path.relative_to(ROOT)), forbidden)

# All original upstream source CMake files live under vendor/sources/:
# they are not maintained Encore CMake mutation owners. Every active
# override under vendor/encore-active remains in module_paths and is checked.
pinned_upstream_roots = tuple(
    ROOT / "vendor/sources" / name
    for name in ("ps5-mihawkgen", "ps5-fsr3-optical-flow", "libwebp")
)
assert all(path.is_dir() and not (path / ".git").exists()
           for path in pinned_upstream_roots)
for stale in ("PS5_MihawkGen", "PS5_FSR3OpticalFlow", "libwebp"):
    assert not (ROOT / "vendor/encore-active" / stale).exists(), stale
excluded_upstream_modules = 0
assert not any(any(upstream in p.parents for upstream in pinned_upstream_roots)
               for p in module_paths)

# Exclude source-pin SDK manifests: the checked Encore CMake layer above
# is the only location allowed to mutate included dependency sources.
active_mutation = re.compile(
    r'^\s*(?:file\s*\(\s*(?:WRITE|APPEND|GENERATE)\b'
    r'|string\s*\(\s*REPLACE\b'
    r'|write_derived\s*\('
    r'|execute_process\s*\()', re.I | re.M)
# The unified NUP owner selector tokenizes two audited source-owner names, not C++
# source text. Permit that ONE exact list-parsing invocation only. Do not
# exempt the module, a generic string(REPLACE), or future source transforms.
nup_gate_path = ROOT/"headless/nup_v1_runtime.cmake"
nup_pair_split = 'string(REPLACE "|" ";" eden_nup_parts "${eden_nup_pair}")'
assert nup_gate_path.read_text(encoding="utf-8").count(nup_pair_split) == 1

def permitted_source_owner_split(path: Path, source: str, match: re.Match) -> bool:
    return (path == nup_gate_path and
            source[match.start():].splitlines()[0].strip() == nup_pair_split)

# A newly introduced CMake string replacement in this very module must still
# fail, including one that creates a .cpp output or changes the selected list.
assert permitted_source_owner_split(
    nup_gate_path, nup_pair_split, active_mutation.search(nup_pair_split))
assert not permitted_source_owner_split(
    ROOT/"headless/other.cmake", nup_pair_split,
    active_mutation.search(nup_pair_split))
for negative in (
    'string(REPLACE "old" "new" cpp_text "${source}")',
    'string(REPLACE "|" ";" eden_nup_parts "${other}")',
):
    assert not permitted_source_owner_split(
        nup_gate_path, negative, active_mutation.search(negative))

checked = 0
approved_splits = 0
for path in sorted(module_paths):
    assert path.is_file(), path
    text = path.read_text(encoding="utf-8")
    violations = []
    for match in active_mutation.finditer(text):
        if permitted_source_owner_split(path, text, match):
            approved_splits += 1
            continue
        violations.append((text.count("\n", 0, match.start()) + 1,
                           match.group(0).strip()))
    assert not violations, (
        f"Active CMake module must not generate or rewrite C++: "
        f"{path.relative_to(ROOT)} {violations}")
    checked += 1
assert approved_splits == 1, approved_splits

native_build = (ROOT/"tools/build-headless-native.sh").read_text()
vulkan = (ROOT/"headless/vulkan.cmake").read_text()
assert 'file(COPY "${EDEN_ACTIVE_VULKAN}/"' in vulkan
assert 'vendor/encore-active' in vulkan or 'EDEN_ACTIVE_VULKAN' in vulkan
for path, code in (("native build", native_build),
                   ("CMake root", root_cmake), ("Vulkan selector", vulkan)):
    assert "prepare-vulkan-port.py" not in code, (
        f"Historical Vulkan source transformation invoked by {path}")
assert 'shutil.copyfile(maintained, tmp)' in (
    ROOT/"tools/install-active-core-backports.py").read_text()
# SVC cache coherency is a real core TU replacement, not a no-op IPC stub.
svc_cache = ROOT / "vendor/encore-active/eden-core/src/core/hle/kernel/svc/svc_cache.cpp"
assert svc_cache.is_file()
svc_code = svc_cache.read_text(encoding="utf-8")
assert 'list(FIND core_sources "hle/kernel/svc/svc_cache.cpp" eden_ns1_svc_cache_index)' in root_cmake
assert 'list(APPEND core_sources "${EDEN_NS1_SVC_CACHE}")' in root_cmake
assert 'process->GetMemory().InvalidateDataCache(address, size)' in svc_code
assert 'process->GetMemory().StoreDataCache(address, size)' in svc_code
assert 'process->GetMemory().FlushDataCache(address, size)' in svc_code
assert 'GetCurrentMemory(system.Kernel()).FlushDataCache(address, size)' in svc_code
assert svc_code.count('R_UNLESS(address < address + size, ResultInvalidCurrentMemory);') == 4
# Native CMake CAS selection is order-sensitive: the early NS1 replacement
# already holds the maintained absolute global-atomic source when P5 runs.
# Configure ONLY these two verbatim blocks with a synthetic target to prove
# that the final target keeps one maintained owner for each CAS TU. No PS5
# compilation is triggered; the original vendor sources remain untouched.
def cmake_block(start: str, end: str) -> str:
    assert root_cmake.count(start) == root_cmake.count(end) == 1
    return start + root_cmake.split(start, 1)[1].split(end, 1)[0]

ns1_cas_block = cmake_block("# NS1 Maxwell ATOM.CAS:", "# NS1 Maxwell FP64")
p5_cas_block = cmake_block("# P5 link parity:", "# R457 NS2 sparse")
for enable_gl in (False, True):
    sources = [
        "backend/spirv/emit_spirv_atomic.cpp",
        "frontend/maxwell/translate/impl/atomic_operations_shared_memory.cpp",
        "frontend/maxwell/translate/impl/atomic_operations_global_memory.cpp",
    ]
    if enable_gl:
        sources.extend([
            "backend/glasm/emit_glasm_memory.cpp",
            "backend/glsl/emit_glsl_atomic.cpp",
        ])
    with tempfile.TemporaryDirectory(prefix="encore-ns1-cas-cmake-") as scratch:
        tmp = Path(scratch)
        project = f"""cmake_minimum_required(VERSION 3.21)
project(EncoreNs1CASSelection LANGUAGES CXX)
set(PORT_ROOT "{ROOT.as_posix()}")
set(PS5_NATIVE ON)
set(ENABLE_OPENGL {"ON" if enable_gl else "OFF"})
add_library(shader_recompiler STATIC
{chr(10).join("    " + item for item in sources)}
)
{ns1_cas_block}
{p5_cas_block}
get_target_property(confirmed_sources shader_recompiler SOURCES)
foreach(relative_path IN LISTS eden_native_cas_paths)
    set(selected "${{EDEN_MAINTAINED_SHADER_CAS_ROOT}}/${{relative_path}}")
    set(found 0)
    foreach(candidate IN LISTS confirmed_sources)
        if(candidate STREQUAL selected)
            math(EXPR found "${{found}} + 1")
        endif()
    endforeach()
    if(NOT found EQUAL 1)
        message(FATAL_ERROR "CAS owner not selected exactly once: ${{relative_path}} => ${{found}}")
    endif()
endforeach()
list(LENGTH confirmed_sources total_sources)
list(LENGTH eden_native_cas_paths expected_sources)
if(NOT total_sources EQUAL expected_sources)
    message(FATAL_ERROR "CAS selection kept stale/duplicate sources")
endif()
"""
        (tmp / "CMakeLists.txt").write_text(project, encoding="utf-8")
        run = subprocess.run(
            ["cmake", "-S", str(tmp), "-B", str(tmp / "build")],
            text=True, capture_output=True, timeout=60, check=False,
        )
        assert run.returncode == 0, (
            f"NS1 CAS native source CMake failed ENABLE_OPENGL={enable_gl}: "
            f"{run.stdout[-3000:]} {run.stderr[-3000:]}"
        )
print("ENCORE_NS1_CAS_SOURCE_SELECTION_PASS native=1 maintained=1 unique=1 profiles=2")

print(f"ENCORE_ACTIVE_CMAKE_SOURCE_BOUNDARY_PASS modules={checked} "
      f"pinned_upstream_modules={excluded_upstream_modules} "
      "vendor_gitlink_match=1 active_source_of_truth=1 "
      "cpp_generators=0 resource_generators=1 nup_source_pair_split=1")
