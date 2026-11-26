#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Keep GitHub's native cache genuinely restorable instead of silently rejecting sibling paths."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
workflow = (root / ".github/workflows/build-040-zbic.yml").read_text()
linker = (root / "tools/ci/link-sibling-deps.sh").read_text()
build = (root / "tools/build-headless-native.sh").read_text()
deps = (root / "tools/deps.py").read_text()
makefile = (root / "Makefile").read_text()
deps_target = makefile.split("deps:", 1)[1].split("\n\n", 1)[0]
assert "tools/deps.py fetch" in deps_target
assert "tools/deps.py verify" in deps_target
assert deps_target.index("tools/deps.py fetch") < deps_target.index("tools/deps.py verify")
assert "release dependency verification failed" in deps

for path in (
    "../ps5-native-app-boilerplate",
    "../ps5-opengl-review",
    "../mihawk-vulkan-review",
    "../mihawk-mesa-review",
    "../mihawk-sdk-review",
):
    assert path not in workflow, f"actions/cache still contains unsupported path {path}"

# Native all-on builds must provision the same Boost.Container header as
# the separate host-only core preflight. Four Vulkan host C++ checks consume
# boost/container/small_vector.hpp before PS5-native compilation starts.
host_workflow = (root / ".github/workflows/encore-core-preflight.yml").read_text()
native_toolchain = workflow.split("      - name: Install build toolchain", 1)[1].split(
    "      - name: Upgrade Meson", 1)[0]
# Native source changes now trigger core verification independent of commit
# message suffixes. Narrow push paths avoid unnecessary runs.
# Latest-source host validations supersede obsolete SHA work. This is an
# intentional throughput policy: the current reviewed vendor pin must receive
# a full result, but superseded source revisions should release CI runners.
host_push = host_workflow.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]
host_group = host_workflow.split("concurrency:", 1)[1].split("jobs:", 1)[0]
assert "branches: [main]" in host_push
assert "paths:" in host_push
for selected in (
    "'vendor/encore-active/**'",
    "'headless/**'",
    "'tools/**'",
    "'.github/workflows/encore-core-preflight.yml'",
):
    assert selected in host_push, ("core source path missing", selected)
assert "'docs/**'" not in host_push
assert "'launcher/**'" not in host_push
assert "${{ github.ref }}" in host_group
assert "${{ github.event_name }}" in host_group
assert "${{ github.sha }}" not in host_group, "stale SHA-scoped host validations"
assert "cancel-in-progress: true" in host_group
for host_guard in (
    ".github/workflows/encore-core-fast-gate.yml",
    ".github/workflows/ns2-research-host.yml",
):
    guard = (root / host_guard).read_text()
    group = guard.split("concurrency:", 1)[1].split("jobs:", 1)[0]
    assert "${{ github.ref }}" in group
    assert "${{ github.event_name }}" in group
    assert "${{ github.sha }}" not in group
    assert "cancel-in-progress: true" in group
assert "if: ${{ github.event_name == 'workflow_dispatch' ||" not in host_workflow

assert "libboost-container-dev" in host_workflow
assert "libboost-container-dev" in native_toolchain
assert "clang++-18 -std=c++20 -x c++ -fsyntax-only -" in native_toolchain
assert native_toolchain.index("libboost-container-dev") < native_toolchain.index(
    "clang++-18 -std=c++20 -x c++ -fsyntax-only -"
)
# Ordinary main UI/docs pushes start a *skipped* native workflow.
# They must not cancel a long-running explicitly requested native package.
native_group = workflow.split("concurrency:", 1)[1].split("jobs:", 1)[0]
assert "github.ref == 'refs/heads/main'" in native_group
assert "github.event_name == 'push'" in native_group
assert "!startsWith(github.event.head_commit.message || '', '[full-build]')" in native_group
assert "!startsWith(github.event.head_commit.message || '', '[resume-stage:45087056642]')" in native_group
assert "'skip-only' || 'build-capable'" in native_group
assert "cancel-in-progress: true" in native_group
# Preserve existing one-at-a-time build-capable behavior for explicitly
# requested native pushes; workflow_dispatch has its own event scope.
assert "${{ github.event_name }}" in native_group

assert "PROSPEROEDEN_GIT_DEPS_ROOT: .deps/repos" in workflow
assert "PROSPEROEDEN_GIT_DEPS_ROOT" in deps
assert "item.get('path', '').startswith('../')" in deps
assert "pathlib.Path(item['path']).name" in deps
assert "PROSPEROEDEN_GIT_DEPS_ROOT" in linker

assert workflow.count("            .deps\n") == 2
assert "Prepare cacheable sibling dependency paths" in workflow
assert workflow.index("Prepare cacheable sibling dependency paths") < workflow.index("Prepare native build inputs")
for name in (
    "ps5-native-app-boilerplate",
    "ps5-opengl-review",
    "mihawk-vulkan-review",
    "mihawk-mesa-review",
    "mihawk-sdk-review",
):
    assert name in linker
assert '.deps/repos' in linker

# The native build must not reuse a tracked-dirty OpenGL checkout from a
# previous runner cache as though it were our immutable upstream source.
# Guard ONLY the Actions-owned cache path; preserve the old checkout and
# rehydrate from the pinned vendor pack rather than resetting local work.
for required in (
    'if [[ "${GITHUB_ACTIONS:-}" == "true" && "$store" == "$root/.deps/repos" ]]; then',
    'git -C "$cached_opengl" status --porcelain --untracked-files=no',
    'pinned_opengl=$(python3 - "$root/tools/deps.json"',
    'vendor/objects/opengl-source/chunks.json',
    'quarantine=$(mktemp -d "${RUNNER_TEMP:?}/encore-opengl-cache-XXXXXX")',
    'mv -- "$cached_opengl" "$quarantine/ps5-opengl-review"',
):
    assert required in linker, ("Pinned CI OpenGL cache recovery guard missing", required)
assert "git reset --hard" not in linker
assert "git clean -fd" not in linker


assert "fork-source-stamps.json" in build
assert "sha256(path.read_bytes())" in build
assert "os.utime(path" in build
assert "-exec touch" not in build
# Catch PS5 ABI/source errors before spending time on the native Ninja build.
assert '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON' in build
# The native CMake cache must report the real vendored SDL3 release.
sdl_cmake = (root / "vendor/sources/eden-cpm/sdl3/release-3.4.8/CMakeLists.txt").read_text()
assert 'project(SDL3 LANGUAGES C VERSION "3.4.8")' in sdl_cmake
assert '-DSDL_REVISION=SDL-release-3.4.8' in build
assert 'tools/check-native-source-syntax.py' in build
assert build.index('tools/check-native-source-syntax.py') < build.index('cmake --build "$scratch/native-local"')
syntax_gate = (root / "tools/check-native-source-syntax.py").read_text()
assert 'HUD_GENERATED_CONSUMER = "headless/vulkan_window_adapt_r08.cpp"' in syntax_gate
assert 'HUD_GENERATED_TARGET = "eden-vulkan-hud-shaders"' in syntax_gate
assert '"cmake", "--build", str(native_build_dir.resolve())' in syntax_gate
# Syntax-only Clang bypasses Ninja's OBJECT_DEPENDS; both maintained
# shader producers must be materialized before either native consumer.
assert 'HOST_SHADER_GENERATED_TARGET = "host_shaders"' in syntax_gate
assert 'required.append(HUD_GENERATED_TARGET)' in syntax_gate
assert 'required.append(HOST_SHADER_GENERATED_TARGET)' in syntax_gate
assert '"--target", target' in syntax_gate
assert 'if any(consumer in selected for consumer in HOST_SHADER_CONSUMERS):' in syntax_gate
assert syntax_gate.index("prepare_generated_prerequisites(args.native_build_dir, selected)") < syntax_gate.index("for relative in selected:")
# The tracked French fallback is generated from fr-FR.po. A native build must
# rematerialize it immediately before Ninja and reject any generator/source
# drift instead of compiling a contaminated raw PO payload as C++.
assert 'embedded_fr_rel="headless/prosperoeden/fr_fr_embedded.h"' in build
assert 'tools/launcher/strings.py" embed-fr' in build
assert 'tools/launcher/strings.py" check' in build
assert 'git -C "$root" diff --exit-code -- "$embedded_fr_rel"' in build
assert 'EDEN_EMBEDDED_FR_NATIVE_HEADER_PASS' in build
assert build.index('tools/launcher/strings.py" embed-fr') < build.index('cmake --build "$scratch/native-local"')
assert build.index('git -C "$root" diff --exit-code -- "$embedded_fr_rel"') < build.index('cmake --build "$scratch/native-local"')
# Publish a verified FTP title and release bundle independently of optional
# dependency cache preservation. Do not restore an obsolete dev package path.
assert "EDEN_TEST_ALL_ON" not in workflow
assert "Upload validated native development package" not in workflow
assert "Upload native development debug symbols" not in workflow
assert "bash tools/build-package.sh dev" not in workflow
native_cache_step = "      - name: Save caches after successful native preparation"
assert workflow.count(native_cache_step) == 1
assert workflow.index("Prepare native build inputs") < workflow.index(native_cache_step)
assert workflow.index("Upload FTP-ready title folder") < workflow.index(native_cache_step)
assert workflow.index("Upload compiled release bundle") < workflow.index(native_cache_step)
# Only the verified FTP title archive is presented as the installable package.
# Preserve resumable failed-job state internally; historical downloads are a
# restore fallback, never an additional upload in a new run.
assert "Upload resumable staged app" not in workflow
assert "Verify downloadable staged ZIP root" not in workflow
assert "Reject flattened staged archives" not in workflow
assert workflow.count("name: Prospero.Eden-Encore-staged-app") == 1
assert "Restore internal stage checkpoint" in workflow
assert "Restore historical staged artifact if no checkpoint exists" in workflow
assert "steps.restore_stage.outputs.cache-hit != 'true'" in workflow
assert "encore-internal-stage-v1-${{ runner.os }}-${{ github.run_id }}" in workflow
assert "encore-internal-stage-v1-${{ runner.os }}-${{ env.RESUME_STAGE_RUN_ID }}" in workflow
assert workflow.index("Save compiled stage recovery checkpoint") < workflow.index("Validate freshly built staged app")
assert workflow.index("Validate freshly built staged app") < workflow.index("Save internal stage checkpoint")
assert "encore-compiled-stage-v1-${{ runner.os }}-${{ github.run_id }}" in workflow
assert 'test "$EXACT_CACHE_HIT" = true' in workflow
assert "EDEN_CACHED_NATIVE_RECOVERY_BINARY_IDENTICAL" in workflow
assert workflow.index("Save internal stage checkpoint") < workflow.index("Assemble release files")
assert workflow.index("Upload FTP-ready title folder") < workflow.index("Validate actual downloadable FTP ZIP root")
assert "name: Eden-Encore-PS5-FTP-PPSA99008" in workflow

cache_block = workflow.split(native_cache_step, 1)[1].split("\n  release:", 1)[0]
assert "if: ${{ !cancelled() && steps.prepare_native.outcome == 'success' }}" in cache_block
assert "continue-on-error: true" in cache_block, "optional cache write must not fail artifact delivery"
assert "uses: actions/cache/save@" in cache_block
print("Encore CI incremental-cache and early syntax gate contract PASS")
