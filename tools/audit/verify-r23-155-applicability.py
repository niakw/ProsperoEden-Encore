#!/usr/bin/env python3
"""Fail-closed 155-commit R23 applicability register validator.

Checks exact immutable commit/changed-file receipts and all action categories.
Does NOT infer compiled PS5 source, semantic equivalence, ELF or runtime.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = "docs/audits/R23_EDEN_ALL_155_COMMITS_2026-11-10.json"
PATHS = "docs/audits/r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json"
APP = "docs/audits/r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json"

def validate(root: Path, app: dict | None = None) -> dict:
    original = json.loads((root / SRC).read_text())
    receipt = json.loads((root / PATHS).read_text())
    if app is None:
        app = json.loads((root / APP).read_text())
    expected = {item["index"]: item for item in original["items"]}
    paths = {item["index"]: item for item in receipt["rows"]}
    rows = app["individual_commits"]
    if (original["commit_count"] != 155 or receipt["commits"] != 155 or
            app["exact_commit_count"] != 155 or not app["complete_file_lists"] or
            len(rows) != 155 or set(expected) != set(range(1, 156)) or
            set(paths) != set(expected)):
        raise ValueError("155-commit source inventory is incomplete")
    seen = set()
    categories = Counter()
    for item in rows:
        number = item["index"]
        if number in seen or number not in expected:
            raise ValueError(f"bad or duplicate commit index {number}")
        seen.add(number)
        original_item, path_item = expected[number], paths[number]
        if (item["sha"] != original_item["sha"] or
                item["title"] != original_item["title"] or
                item["sha"] != path_item["sha"] or
                item["file_count"] != path_item["file_count"] or
                item["paths"] != [p["path"] for p in path_item["files"]]):
            raise ValueError(f"R23 entry #{number}: upstream source proof drift")
        label = item["classification"]
        if not label or item.get("scope", "") == "" or item.get("action", "") == "":
            raise ValueError(f"R23 entry #{number}: missing explicit disposition")
        categories[label] += 1
    if set(seen) != set(expected):
        raise ValueError("one or more upstream commits are not categorized")
    if dict(categories) != app["classification_counts"] or sum(categories.values()) != 155:
        raise ValueError("inconsistent applicability class totals")
    # This dated pin is a frozen audit decision, not permission to silently
    # drop pending counts without exact source and owner proof.
    # Reviewed 2026-11-11 E1 freeze: future semantic decisions must update
    # this explicit expected distribution and add case-specific provenance.
    mandatory = {
        "runtime-semantic-review-pending": 29,
        "reviewed-PS5-Vulkan-presenter-maintained-defaults-policy-deferred": 1,
        "reviewed-NCE-settings-toggle-no-PS5-x64-port": 1,
        "reviewed-native-mmap-IOFile-experimental-policy-deferred": 1,
        "reviewed-upstream-NCZBLOCK-optimization-module-not-current-native-owner": 1,
        "reviewed-std-overwrite-coallocation-refactor-deferred": 1,
        "reviewed-lock-contention-policy-deferred-native": 1,
        "reviewed-depth-sampler-fallback-preserved-test-open": 1,
        "reviewed-NCE-only-runtime-NRO-patch-not-PS5-x64": 1,
        "reviewed-Android-only-LA-EOW-SPIRV-bloom-option": 1,
        "reviewed-ReShade-applet-postprocess-not-native-selected": 1,
        "source-equivalent-native-GPU-worker-stop-lifecycle": 1,
        "reviewed-nonAndroid-optimized-vertex-branch-only": 1,
        "reviewed-Qualcomm-driver-flag-outside-PS5-RADV": 1,
        "source-equivalent-selected-Vulkan-TFB-end-buffer-order": 1,
        "reviewed-current-PS5-native-ifaddrs-Mac-route-not-selected": 1,
        "reviewed-current-Boost190-ADL-compat-wrapper-retained": 1,
        "reviewed-UTF-conversion-non-equivalence-deferred-host-differential": 1,
        "reviewed-PS5-Vulkan-early-return-GL-depth-policy-open": 1,
        "reviewed-frontend-cli-only-no-current-headless-PS5-port": 1,
        "MSVC-portability-only-no-current-PS5-runtime-port": 1,
        "constexpr-atomic-page-methods-build-compat-only": 1,
        "staged-native-IPS-longline-awaiting-current-host-proof": 1,
        "MSVC-constexpr-only-no-current-PS5-runtime-port": 1,
        "source-equivalent-declared-native-x64-lookup": 3,
        "not-applicable-to-PS5-native-packaging-assets": 8,
        "not-applicable-to-native-runtime-source": 27,
        "staged-host-source-fix": 5,
        "not-applicable-PS5-x64-execution": 6,
        "reviewed-native-glslang-argv-no-space-current-build": 1,
        "reviewed-clang23-only-glsl-backend-no-current-PS5-port": 1,
        "reviewed-native-pad-not-SDL-vibration-path": 1,
        "reviewed-mouse-Qt-SDL-frontend-timer-not-native": 1,
        "reviewed-Qt-applet-picker-no-current-headless-port": 1,
        "reviewed-upstream-NS-async-result-pure-rename": 1,
        "reviewed-upstream-Boost-repin-deferred-native-dependency": 1,
        "reviewed-inactive-native-static-LZ4-option": 2,
        "test-only-upstream": 1,
        "verified-native-GPU-thread-affinity-review-needs-PS5-trace": 1,
        "source-equivalent-GPU-NCE-readback-reverted": 2,
        "verified-relevant-source-gap-awaiting-native-proof": 22,
        "reviewed-observability-only-no-NS1-behavioral-port": 2,
        "source-implemented-native-PS5-NCZBLOCK-NSZ-XCZ": 1,
        "upstream-runtime-then-reverted-equivalent": 2,
        "source-equivalent-hle-handler-revert-cosmetic-only": 2,
        "source-implemented-native-PS5-ZBIC-NSO": 1,
        "source-equivalent-native-PS5-sparse-commit-failstop": 1,
        "source-equivalent-pinned-savedata-post-revert": 1,
        "source-equivalent-PS5-semaphore-lock-lifecycle": 1,
        "source-equivalent-current-openssl-native-build": 1,
        "upstream-opus-ffmpeg-migration-reverted": 2,
        "source-equivalent-native-PS5-sink-volume-lifetime": 1,
        "verified-absent-GPU-null-initialization-candidate": 1,
        "reviewed-include-only-no-native-behavioral-port": 1,
        "ci-only-ffmpeg-artifact-not-selected-native": 1,
        "source-verified-shared-FS-root-preservation-awaiting-PS5-decision": 1,
    }
    if dict(categories) != mandatory:
        raise ValueError("R23 dated classification changed without reviewed baseline bump")
    # Exact E1 source receipts for newly classified firmware NS/OLSC and
    # two conditional native build-only upstream differences. Neither means
    # the tested PS5 application implements the new command/interface.
    detail = (root / "docs/audits/ENCORE_AB_R23_FW23_NS_OLSC_SOURCE_GAPS_2026-11-11.md").read_text()
    build = (root / "docs/audits/ENCORE_AB_R23_FINAL_TWO_BUILD_CASES_2026-11-11.md").read_text()
    expected_new = {
        1: "verified-relevant-source-gap-awaiting-native-proof",
        132: "verified-relevant-source-gap-awaiting-native-proof",
        137: "verified-relevant-source-gap-awaiting-native-proof",
        13: "reviewed-native-glslang-argv-no-space-current-build",
        101: "reviewed-clang23-only-glsl-backend-no-current-PS5-port",
    }
    if by_index_82 := next((item for item in rows if item["index"] == 82), None):
        if by_index_82["classification"] != "reviewed-NCE-settings-toggle-no-PS5-x64-port":
            raise ValueError("R23 #82 native x64 settings-toggle disposition changed")
        evidence = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS18_2026-11-11.md").read_text()
        for token in ("#82", "10bcd2d849", "8b068b85b4de2a2a04fbf32875a79b4304c52294", "#68", "#6", "#149"):
            if token not in evidence:
                raise ValueError(f"R23 #82 audit evidence missing {token}")
    else:
        raise ValueError("R23 #82 missing from 155-commit register")
    selected_81 = next((item for item in rows if item["index"] == 81), None)
    if selected_81 is None or selected_81["classification"] != "reviewed-PS5-Vulkan-presenter-maintained-defaults-policy-deferred":
        raise ValueError("R23 #81 PS5 Vulkan presenter/default-policy disposition lost")
    present_evidence = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS19_2026-11-11.md").read_text()
    for token in ("#81", "3cdd2ce141", "5194b6b183cba24f7ab966c16437884ac75d284f", "d45f0b7bbca982f133dcabcd0621e40cff4f74e5", "29"):
        if token not in present_evidence:
            raise ValueError(f"R23 #81 source proof missing {token}")
    for number, category in expected_new.items():
        if next(x for x in rows if x["index"] == number)["classification"] != category:
            raise ValueError(f"R23 new source-level proof #{number} lost")
        if str(number) not in (detail if number in (1, 132, 137) else build):
            raise ValueError(f"R23 source evidence document missing #{number}")
    for blob in ("c3b2aee8a8e7b87b9dd0c6952538e0ffad9e0424",
                 "f09ccf7b8180af08a501f295b3c7ce3dc4831ff2",
                 "0f9042bf0189e8f7eb4dd305b7e38a2dc24a2f1f"):
        if blob not in detail:
            raise ValueError("R23 NS/OLSC pinned source Git blob receipts changed")
    if "Clang 18.1.3" not in build or "glslangValidator" not in build:
        raise ValueError("R23 #13/#101 current toolchain proof missing")
    # Native frontend selection (not proof the files are unlinked).
    native_note = (root / "docs/audits/ENCORE_AB_R23_NATIVE_PAD_MOUSE_FRONTEND_EXCLUSIONS_2026-11-11.md").read_text()
    for index, classification in ((71, "reviewed-native-pad-not-SDL-vibration-path"),
                                  (143, "reviewed-mouse-Qt-SDL-frontend-timer-not-native")):
        entry = next(row for row in rows if row["index"] == index)
        if entry["classification"] != classification or f"#{index}" not in native_note:
            raise ValueError(f"R23 native frontend proof #{index} missing")
    for sha in ("91589063b50548f3142ffdc36dbad2b090238fc5",
                "4444f0ac3b34ab36bb651f25088dc35e03c79de3",
                "b6fa427d84f6c8af25a35f4787923d79ab891d67"):
        if sha not in native_note:
            raise ValueError("R23 native pad/input source blob proof missing")
    by_index = {item["index"]: item for item in rows}
    if (by_index[53]["classification"] != "reviewed-observability-only-no-NS1-behavioral-port"
            or by_index[5]["classification"] != "not-applicable-to-native-runtime-source"
            or by_index[30]["classification"] != "reviewed-current-PS5-native-ifaddrs-Mac-route-not-selected"):
        raise ValueError("semantically guarded source cases silently reclassified")
    # R23 pass 6: preserve three exact source-only dispositions.
    pass6 = {
        91: ("reviewed-Qt-applet-picker-no-current-headless-port",
             ["src/common/settings_enums.h",
              "src/qt_common/config/shared_translation.cpp",
              "src/qt_common/config/uisettings.h",
              "src/yuzu/configuration/configure_applets.h",
              "src/yuzu/configuration/shared_widget.cpp",
              "src/yuzu/main_window.cpp"]),
        129: ("reviewed-upstream-NS-async-result-pure-rename",
              ["src/core/CMakeLists.txt",
               "src/core/hle/service/ns/application_manager_interface.h",
               "src/core/hle/service/ns/async_result.cpp",
               "src/core/hle/service/ns/async_result.h"]),
        134: ("reviewed-upstream-Boost-repin-deferred-native-dependency",
              [".patch/boost/0001-clang-cl.patch",
               "CMakeLists.txt", "cpmfile.json"]),
    }
    for i, (klass, exact_paths) in pass6.items():
        if by_index[i]["classification"] != klass or by_index[i]["paths"] != exact_paths:
            raise ValueError(f"R23 pass6 exact source decision #{i} changed")
        if by_index[i].get("source_evidence_level", "").startswith("E1") is False:
            raise ValueError(f"R23 pass6 #{i} has no E1-only evidence limit")
    pass6_doc = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS6_2026-11-11.md").read_text()
    for i in (91, 129, 134):
        if f"## #{i}" not in pass6_doc:
            raise ValueError(f"Missing reviewed source proof for R23 #{i}")
    # #100 only unifies Qt/SDL CLI parsing. In the frozen PS5 profile,
    # neither frontend is selected, the upstream new core TU does not exist
    # in the pinned original, and native headless main has its own entry.
    cli_paths = [
        "docs/user/CommandLine.md",
        "src/core/CMakeLists.txt",
        "src/core/launch_params.cpp",
        "src/core/launch_params.h",
        "src/yuzu/main_window.cpp",
        "src/yuzu_cmd/CMakeLists.txt",
        "src/yuzu_cmd/yuzu.cpp",
    ]
    cli = by_index[100]
    if (cli["classification"] != "reviewed-frontend-cli-only-no-current-headless-PS5-port"
            or cli["paths"] != cli_paths
            or not cli.get("source_evidence_level", "").startswith("E1")
            or "ParseLaunchParams" in
                (root / "headless/main.cpp").read_text()
            or "## #100" not in
                (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS7_2026-11-11.md").read_text()):
        raise ValueError("R23 #100 headless CLI exclusion lost exact E1 proof")
    # #52: current PS5 Vulkan policy returns the pipeline BEFORE the desktop
    # async/depth branch, while OpenGL remains selectable and unqualified.
    # E1 closed semantic triage != compiled OpenGL renderer correctness.
    async_case = by_index[52]
    if (async_case["classification"] != "reviewed-PS5-Vulkan-early-return-GL-depth-policy-open"
            or async_case["paths"] != [
                "src/video_core/renderer_opengl/gl_shader_cache.cpp",
                "src/video_core/renderer_vulkan/vk_pipeline_cache.cpp"]
            or not async_case.get("source_evidence_level", "").startswith("E1")):
        raise ValueError("R23 #52 source-level Vulkan/GL policy decision changed")
    from subprocess import check_output, CalledProcessError
    try:
        gitlink = check_output(
            ["git", "-C", str(root), "ls-tree", "HEAD", "vendor"],
            text=True).strip()
    except (OSError, CalledProcessError) as err:
        raise ValueError("R23 #52 cannot attest frozen vendor gitlink") from err
    if gitlink != ("160000 commit 22b69d6053db41b74edac2633c012f925b84f69e\\tvendor".replace("\\t", "\t")):
        raise ValueError("R23 #52 pinned active Vulkan/GL source owner changed")
    vkcmake = (root / "headless/vulkan.cmake").read_text()
    active_selection = (
        'list(REMOVE_ITEM video_sources renderer_vulkan/${name}.cpp)',
        'list(APPEND video_sources "${PORT_BUILD_DIR}/${name}_cost.cpp")',
        'vk_pipeline_cache'
    )
    if any(fragment not in vkcmake for fragment in active_selection):
        raise ValueError("R23 #52 active Vulkan pipeline source selection changed")
    hcmake = (root / "headless/CMakeLists.txt").read_text()
    entry = (root / "headless/main.cpp").read_text()
    if ('if(EDEN_PS5_OPENGL)' not in hcmake
            or 'renderer_opengl/gl_shader_cache.cpp' in hcmake
            or 'recovery_opengl = true' not in entry
            or 'Settings::RendererBackend::OpenGL_GLSL' not in entry):
        raise ValueError("R23 #52 OpenGL fallback selection changed")
    async_note = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS8_2026-11-11.md").read_text()
    for frozen_receipt in (
        "9358b81ab6b8d43e1ae524a159fd5082d4a8cab2",
        "df69eb97f5fc8f440465d698123ea00e274ee671",
        "642b9fa2236f9d66ba0b9144edab6a15b87fc4d6",
        "26a03d2473787abf3223b2d0e65b291eee00c1e1",
        "OpenGL remains open",
    ):
        if frozen_receipt not in async_note:
            raise ValueError("R23 #52 exact source receipt/reopen contract missing")
    # #147: NS cmd23 is missing in the frozen selected core HLE dispatcher,
    # but cmd19 already names the required GetApplicationControlData3 handler.
    # The unrelated AM/overlay edits and ARM64-only JIT code MUST NOT be
    # considered qualified by that one-line IPC table difference.
    fw23 = by_index[147]
    if (fw23["classification"] != "verified-relevant-source-gap-awaiting-native-proof"
            or fw23["paths"] != [
                "src/android/app/src/main/java/org/yuzu/yuzu_emu/model/Game.kt",
                "src/core/hle/service/am/display_layer_manager.cpp",
                "src/core/hle/service/ns/read_only_application_control_data_interface.cpp",
                "src/dynarmic/src/dynarmic/backend/arm64/emit_arm64_memory.cpp"]
            or not fw23.get("source_evidence_level", "").startswith("E1")):
        raise ValueError("R23 #147 FW23 NS+AM semantic gap/source split lost")
    ns_readme = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS9_2026-11-11.md").read_text()
    for frozen_ns in (
        "c7606a83bf771c9251ef8a44add72b72a2589870",
        "494e8a132b30962c5d13f20155eb00725652207a",
        "508ace350173f5068bd7531f37e70199134fde3a",
        "5d150cac5c6624fa6a0e94266846b75d91a6a5d0",
        "cmd 19",
        "cmd 23",
    ):
        if frozen_ns not in ns_readme:
            raise ValueError("R23 #147 exact pinned NS/AM source proof missing")
    # #29 is not a safe codegen modernization to port blindly: malformed
    # Unicode has a reproducible source-derived host behavior difference.
    utf = by_index[29]
    if (utf["classification"] != "reviewed-UTF-conversion-non-equivalence-deferred-host-differential"
            or utf["paths"] != ["src/common/string_util.cpp"]
            or not utf.get("source_evidence_level", "").startswith("E1")):
        raise ValueError("R23 #29 UTF source-level non-equivalence disposition lost")
    utf_doc = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS10_2026-11-11.md").read_text()
    utf_test = (root / "tests/audit_r23_utf_conversion_host.cpp").read_text()
    for witness in (
        "9543a6234376dc4e85ce035a653b41805b8aa072",
        "c6fa5c1f77ba40bcb091b1a53492230f40d97ded",
        "R23_UTF_EXTRACTED_HOST_DIVERGENCE_PASS",
    ):
        if witness not in utf_doc + utf_test:
            raise ValueError("R23 #29 source-tested Unicode evidence missing")
    if ("PinnedUtf8ToUtf16" not in utf_test
            or "UpstreamUtf8ToUtf16" not in utf_test):
        raise ValueError("R23 #29 source-extracted host input shapes absent")
    # #131: controller fallback must not be called equivalent merely because
    # a PS5 pad frontend exists; exact applet owner disconnects all controllers.
    ctl = by_index[131]
    if (ctl["classification"] != "verified-relevant-source-gap-awaiting-native-proof"
            or ctl["paths"] != ["src/core/frontend/applets/controller.cpp"]
            or not ctl.get("source_evidence_level", "").startswith("E1")):
        raise ValueError("R23 #131 keep_connected behavioral gap lost")
    # #75: Boost 1.90 preserves the original high-version vector wrapper
    # type, but this is only an E1 current-version disposition.
    adl = by_index[75]
    if (adl["classification"] != "reviewed-current-Boost190-ADL-compat-wrapper-retained"
            or len(adl["paths"]) != 7
            or "src/video_core/texture_cache/util.h" not in adl["paths"]
            or not adl.get("source_evidence_level", "").startswith("E1")):
        raise ValueError("R23 #75 Boost version-conditional ADL source review lost")
    evidence = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS11_2026-11-11.md").read_text()
    for token in (
        "c4292c5a1257dbfb18c3709d4911193caf2ed5b6",
        "b77308ced62abe890428955dba687c95e4d93aba",
        "4dc69c06f764a235bccd01afbfc765d9ddbebc9f",
        "boost-1.90.0",
        "keep_controllers_connected",
        "13 source gaps",
    ):
        if token not in evidence:
            raise ValueError("R23 #75/#131 pin/semantic evidence missing")
    # #30: selected native FreeBSD interface enumerator is our maintained
    # getifaddrs owner; upstream Darwin/legacy route change is not its runtime.
    # Keep the network gateway/device proof separate from source-only review.
    net = by_index[30]
    if (net["classification"] != "reviewed-current-PS5-native-ifaddrs-Mac-route-not-selected"
            or net["paths"] != ["src/core/internal_network/network_interface.cpp"]
            or not net.get("source_evidence_level", "").startswith("E1")):
        raise ValueError("R23 #30 scoped native network owner decision lost")
    netcm = (root / "headless/CMakeLists.txt").read_text()
    if ('list(REMOVE_ITEM core_sources internal_network/network_interface.cpp)' not in netcm
            or 'encore-active/eden-core/src/core/internal_network/network_interface.cpp' not in netcm):
        raise ValueError("R23 #30 selected native interface owner changed")
    netdoc = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS12_2026-11-11.md").read_text()
    for receipt in ("2c40328a23630353f4dd20778eb587e586cd83a5",
                    "8ea8093bf09c20ede50cab1993e7cfaebe645816",
                    "f68d4617ebb7a665f270052889d4262f83b07641",
                    "__FreeBSD__", "getifaddrs"):
        if receipt not in netdoc:
            raise ValueError("R23 #30 native network evidence missing")
    # Four reviewed, pinned-source cases. Driver/Android exclusions are
    # scoped to current PS5 configuration, not general upstream parity.
    pass13_expected = {
        55: ("reviewed-nonAndroid-optimized-vertex-branch-only",
             ["src/video_core/buffer_cache/buffer_cache.h"]),
        59: ("reviewed-Qualcomm-driver-flag-outside-PS5-RADV",
             ["src/video_core/renderer_vulkan/vk_pipeline_cache.cpp"]),
        77: ("source-equivalent-selected-Vulkan-TFB-end-buffer-order",
             ["src/video_core/renderer_vulkan/vk_query_cache.cpp"]),
        84: ("verified-relevant-source-gap-awaiting-native-proof",
             ["src/core/hle/service/am/frontend/applets.cpp"]),
    }
    for case_id, (klass, paths) in pass13_expected.items():
        entry = by_index[case_id]
        if (entry["classification"] != klass or entry["paths"] != paths
                or not entry.get("source_evidence_level", "").startswith("E1")):
            raise ValueError(f"R23 pass13 source owner #${case_id} lost")
    pass13_doc = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS13_2026-11-11.md").read_text()
    for blob in ("3d1cba92005617c96a15af481133513ff3feef1b",
                 "9358b81ab6b8d43e1ae524a159fd5082d4a8cab2",
                 "ed5655c70176ee85c90c7cd0a26ae947b3689bdd",
                 "407ca10602a1fe9107d13aa8393f4145ac7d715a"):
        if blob not in pass13_doc:
            raise ValueError("R23 pass13 pinned source receipts missing")
    current_vk = (root / "headless/vulkan.cmake").read_text()
    if ('"${PORT_BUILD_DIR}/vulkan_query_cache.cpp"' not in current_vk
            or '"${PORT_BUILD_DIR}/${name}_cost.cpp"' not in current_vk):
        raise ValueError("R23 native Vulkan source selection drifted")
    # Pass 14: Android-only bloom, native HWC lifecycle, ReShade-only layer
    # and native GPU worker stop are four distinct source-owner cases.
    pass14 = {
        50: ("reviewed-Android-only-LA-EOW-SPIRV-bloom-option", 2),
        64: ("verified-relevant-source-gap-awaiting-native-proof", 1),
        99: ("reviewed-ReShade-applet-postprocess-not-native-selected", 2),
        151: ("source-equivalent-native-GPU-worker-stop-lifecycle", 3),
    }
    for i, (classification, files) in pass14.items():
        item = by_index[i]
        if (item["classification"] != classification or len(item["paths"]) != files
                or not item.get("source_evidence_level", "").startswith("E1")):
            raise ValueError(f"R23 pass14 source owner #${i} changed")
    pass14_doc = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS14_2026-11-11.md").read_text()
    for evidence in ("5d4983b9f7be52e607029239cb0f85ff1db066f0",
                     "5decb791e1bb1ab2420f386e3fdbdd2b8628a324",
                     "dea657ef3911828b9437aced16ec9863aeb3b30a",
                     "51e21613c1e23b0f5aefef0dd78ed9d9b13806e7",
                     "28eab249dc8eefdcadb27ccfdb308743a95580ad"):
        if evidence not in pass14_doc:
            raise ValueError("R23 pass14 exact source receipts missing")
    native_cmake = (root / "headless/CMakeLists.txt").read_text()
    native_vulkan = (root / "headless/vulkan.cmake").read_text()
    if ('gpu_gl_native.cpp' not in native_cmake
            or 'gpu_thread_quiet.cpp' not in native_cmake
            or 'vulkan_present_layer_r24.cpp' not in native_vulkan):
        raise ValueError("R23 pass14 PS5 selected owner changed")
    # Pass 15: NCE-only runtime NRO vs x64 ConstPool, applet release and
    # x64 page-table sign extension source gaps are all E1 and distinct.
    cases15 = {
        90: "reviewed-NCE-only-runtime-NRO-patch-not-PS5-x64",
        33: "verified-relevant-source-gap-awaiting-native-proof",
        109: "verified-relevant-source-gap-awaiting-native-proof",
        136: "verified-relevant-source-gap-awaiting-native-proof",
    }
    for idx, klass in cases15.items():
        r = by_index[idx]
        if r["classification"] != klass or not r.get("source_evidence_level", "").startswith("E1"):
            raise ValueError(f"R23 pass15 #${idx} source gap/policy was lost")
    doc15 = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS15_2026-11-11.md").read_text()
    for source_pin in ("922fc10440bad898f392b1f290ec18fd2e3cc5e7",
                       "8782ab0c73e9defb4f7744063c6691806147effb",
                       "407ca10602a1fe9107d13aa8393f4145ac7d715a",
                       "9686e4fc047f78d0863df3ccb5149c8ecc9dc484"):
        if source_pin not in doc15:
            raise ValueError("R23 pass15 pinned source proof missing")
    # R23 pass16: deliberately separate actual runtime gaps from optional
    # allocation / scheduler / depth sampler policy refactors.
    pass16 = {
        17: "verified-relevant-source-gap-awaiting-native-proof",
        48: "verified-relevant-source-gap-awaiting-native-proof",
        96: "reviewed-std-overwrite-coallocation-refactor-deferred",
        103: "verified-relevant-source-gap-awaiting-native-proof",
        119: "verified-relevant-source-gap-awaiting-native-proof",
        124: "reviewed-lock-contention-policy-deferred-native",
        130: "reviewed-depth-sampler-fallback-preserved-test-open",
    }
    for idx, category in pass16.items():
        item = by_index[idx]
        if item["classification"] != category or not item.get("source_evidence_level", "").startswith("E1"):
            raise ValueError(f"R23 pass16 source decision #${idx} drifted")
    pass16_doc = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS16_2026-11-11.md").read_text()
    for receipt in (
        "1588eca6168bdcaf04229d6aa4115c3acb624081",
        "dcc6261e5c79d30f083426d39251d417aa65b017",
        "8c1f566301495d7c05b674b20771a04755072b8f",
        "827944fb08c02cd0d3ebec9f253c23c7a5cdbd96",
        "0af4a7bd0ee5b31af7c9cc49eb613352c4ab74b6",
        "97c11bebf775b2139f87f3a8d22e4d06446df14e",
    ):
        if receipt not in pass16_doc:
            raise ValueError("R23 pass16 pinned owner evidence missing")
    # Source-only policy/compiled owner decisions: mmap IOFile and upstream
    # NCZ decoder are not presumed equivalent or mandatory on current PS5.
    for idx, klass in {
        31: "reviewed-native-mmap-IOFile-experimental-policy-deferred",
        45: "reviewed-upstream-NCZBLOCK-optimization-module-not-current-native-owner",
    }.items():
        if (by_index[idx]["classification"] != klass or
                not by_index[idx].get("source_evidence_level", "").startswith("E1")):
            raise ValueError(f"R23 pass17 #${idx} native IO/NCZ owner decision changed")
    pass17 = (root / "docs/audits/ENCORE_AB_R23_SEMANTIC_SOURCE_PASS17_2026-11-11.md").read_text()
    for pin in ("461a5eee352dcc95025667f9e02d625fe00c52e5",
                "b1ccfbd18a38f65dfa452d4632a66d3b5b55c308",
                "508ace350173f5068bd7531f37e70199134fde3a",
                "ncz_decompressor.cpp"):
        if pin not in pass17:
            raise ValueError("R23 pass17 pinned native files/owner absence not attested")
    # #79 exact upstream diff is include/copyright-only; #86 is the CI-only
    # FFmpeg artifact. Neither alters the PS5 native runtime contract.
    if (by_index[79]["classification"] != "reviewed-include-only-no-native-behavioral-port"
            or by_index[79]["paths"] != [
                "src/core/hle/service/bcat/backend/backend.h",
                "src/hid_core/resources/npad/npad_types.h",
                "src/input_common/helpers/joycon_protocol/joycon_types.h",
                "src/input_common/helpers/joycon_protocol/poller.cpp"]):
        raise ValueError("R23 #79 includes-only upstream source proof changed")
    if (by_index[86]["classification"] != "ci-only-ffmpeg-artifact-not-selected-native"
            or by_index[86]["paths"] != ["cpmfile.json"]):
        raise ValueError("R23 #86 FFmpeg CI package path changed")
    source_deps = json.loads((root / "tools/deps.json").read_text())
    native_ffmpeg = [i for i in source_deps["items"] if i["name"] == "ffmpeg"]
    if (len(native_ffmpeg) != 1 or
            "FFmpeg/FFmpeg/archive/c7b5f1537d" not in native_ffmpeg[0]["url"]):
        raise ValueError("Native FFmpeg source provenance changed; reopen R23 #86")
    # Android-marketed #144 modifies shared Vulkan/frame-generation code;
    # it must NOT be misclassified as Android-only without source comparison.
    if (by_index[144]["classification"] != "runtime-semantic-review-pending"
            or "src/video_core/frame_gen/lossless_dll.cpp" not in by_index[144]["paths"]
            or "src/video_core/renderer_vulkan/vk_present_manager.cpp" not in by_index[144]["paths"]):
        raise ValueError("R23 #144 native framegen change falsely excluded")
    # #123 keeps its tested root-preservation E1 disposition; its PS5 behavior still requires validation.
    if by_index[123]["classification"] != "source-verified-shared-FS-root-preservation-awaiting-PS5-decision":
        raise ValueError("R23 #123 exact source-root-difference lost, missing native behavior proof")
    path_test = (root / "tests/audit_r23_path_sanitizer_host.cpp").read_text()
    if (by_index[123]["paths"] != [
            "src/common/fs/path_util.cpp", "src/common/fs/path_util.h"]
            or "namespace Pinned" not in path_test
            or "namespace Upstream" not in path_test
            or 'R23_PS5_COMMON_FS_SANITIZE_EXACT_SOURCE_DIVERGENCE_PASS' not in path_test):
        raise ValueError("R23 #123 exact source-tested path-API receipt missing")
    # #93: selected PS5 sparse physical memory commits fail-stop rather than
    # upstream mprotect; source equivalence is not a PS5 device test.
    if by_index[93]["classification"] != "source-equivalent-native-PS5-sparse-commit-failstop":
        raise ValueError("R23 #93 selected native sparse allocator proof changed")
    # Additional reviewed source-level regressions and de-duplication decisions.
    for i in (142, 148):
        if by_index[i]["classification"] != "upstream-opus-ffmpeg-migration-reverted":
            raise ValueError(f"R23 upstream Opus migration pair #{i} was silently reintroduced")
    if by_index[138]["classification"] != "source-equivalent-current-openssl-native-build":
        raise ValueError("R23 SSL platform source decision changed without review")
    if by_index[146]["classification"] != "verified-absent-GPU-null-initialization-candidate":
        raise ValueError("R23 GPU init candidate proof changed without review")
    # The earlier FreeBSD-ifaddrs unresolved guard was superseded by the
    # exact selected native owner and preprocessor decision in pass 12.
    if by_index[30]["classification"] != "reviewed-current-PS5-native-ifaddrs-Mac-route-not-selected":
        raise ValueError("R23 #30 reviewed native network scope was changed")
    # Exact upstream source reversion receipts were reviewed separately.
    # Do not accidentally reactivate either giant HLE pair or the NCE GPU
    # writeback sequence because the frozen class totals happen to match.
    for i in (69, 74):
        if by_index[i]["classification"] != "source-equivalent-hle-handler-revert-cosmetic-only":
            raise ValueError(f"R23 HLE handler undo pair #{i} lost source proof")
    for i in (47, 88):
        if by_index[i]["classification"] != "source-equivalent-GPU-NCE-readback-reverted":
            raise ValueError(f"R23 NCE GPU reverted pair #{i} lost source proof")
    # #45 moved to reviewed missing-native-TU disposition in pass17;
    # retain the exact older implementation guards for #60 and #92.
    for i in (60, 92):
        if by_index[i]["classification"] not in (
            "source-implemented-native-PS5-NCZBLOCK-NSZ-XCZ",
            "source-implemented-native-PS5-ZBIC-NSO",
            "runtime-semantic-review-pending",
        ):
            raise ValueError(f"R23 compressed-content case #{i} changed silently")
    for i in (117, 122, 125):
        if by_index[i]["classification"] != "source-equivalent-declared-native-x64-lookup":
            raise ValueError(f"R23 x64 page-table lookup #${i} lost E1 parity proof")
    if by_index[136]["classification"] != "verified-relevant-source-gap-awaiting-native-proof":
        raise ValueError("R23 x64 sign-extension divergence #136 must remain an unqualified source gap until JIT tests")
    if by_index[116]["classification"] != "staged-native-IPS-longline-awaiting-current-host-proof":
        raise ValueError("R23 IPS >256B source is staged, NOT tested at exact corrective HEAD")
    if by_index[141]["classification"] != "MSVC-constexpr-only-no-current-PS5-runtime-port":
        raise ValueError("R23 MSVC-only constexpr constructor source decision changed")
    if by_index[115]["classification"] != "MSVC-portability-only-no-current-PS5-runtime-port":
        raise ValueError("R23 #115 MSVC-only source review disposition changed")
    if by_index[118]["classification"] != "constexpr-atomic-page-methods-build-compat-only":
        raise ValueError("R23 #118 atomic constexpr-only source review disposition changed")
    # All eight upstream UI/translation commits are outside the actual PS5 package:
    # the separate launcher embeds its own ui/*.po, branded assets and artwork.
    native_pkg = (root / "tools/package-headless-native.sh").read_text()
    if ('cp -a "$root/headless/prosperoeden/ui" "$app/ui"' not in native_pkg
            or 'for catalog in "$app/ui/lang/"*.po; do' not in native_pkg
            or any(s in native_pkg for s in (
                "dist/languages", "dist/icons", "src/android/app/src/main/res",
                "tools/optimize-assets.sh"))):
        raise ValueError("PS5 package source selection changed: re-open R23 assets")
    for i in (4, 26, 34, 76, 83, 89, 105, 140):
        row = by_index[i]
        if row["classification"] != "not-applicable-to-PS5-native-packaging-assets":
            raise ValueError(f"R23 launcher asset source #{i} was silently reclassified")
        if not all(p.startswith(("dist/", "src/android/app/src/main/res/", "docs/"))
                   or p == "tools/optimize-assets.sh" for p in row["paths"]):
            raise ValueError(f"R23 asset source #{i} touches an unreviewed native path")
    native_build = (root / "tools/build-headless-native.sh").read_text()
    if "-DENABLE_QT=OFF -DYUZU_CMD=OFF" not in native_build:
        raise ValueError("PS5 native Qt frontend exclusion changed")
    if by_index[24]["classification"] != "not-applicable-to-native-runtime-source":
        raise ValueError("Qt-only commit was reclassified without native-build proof")
    if not all(p in ("CMakeLists.txt", "docs/Deps.md") or
               p.startswith(("src/qt_common/", "src/yuzu/"))
               for p in by_index[24]["paths"]):
        raise ValueError("Qt commit has an unexpected compiled source")
    if by_index[110]["classification"] != "reviewed-observability-only-no-NS1-behavioral-port":
        raise ValueError("XSI strerror_r semantic parity was reclassified")
    if by_index[110]["paths"] != ["src/common/error.cpp"]:
        raise ValueError("strerror_r diagnostics commit contains another source")
    # Confirm source-proven real deficiencies are never silently counted fixed:
    # clock RDTSC >1GHz, NS ListApplicationIcon null, Opus 24/25 decoder limits.
    for i in (114, 128, 153):
        if by_index[i]["classification"] != "verified-relevant-source-gap-awaiting-native-proof":
            raise ValueError(f"R23 confirmed source gap #{i} silently changed")
    # #95 changes HID Connect() branch decisions despite the cleanup title.
    if (by_index[95]["classification"] != "verified-relevant-source-gap-awaiting-native-proof"
            or by_index[95]["paths"] != [
                "src/hid_core/frontend/emulated_controller.cpp",
                "src/hid_core/frontend/emulated_controller.h"]
            or "R23_HID_CONNECT_BRANCH_SOURCE_DIFFERENCE_PASS" not in
                (root / "tools/audit/check-r23-hid-button-connection-host.py").read_text()):
        raise ValueError("R23 #95 HID connection source-policy proof missing")
    # R23 #20/#66 are conditional native-static LZ4 paths. The historical
    # ninth-run CMakeCache (read-only audit run 43012467528) recorded OFF.
    # This disposition does not certify latest main or linker state.
    if any(by_index[i]["classification"] != "reviewed-inactive-native-static-LZ4-option"
           for i in (20, 66)):
        raise ValueError("R23 #20/#66 native-static cache provenance changed")
    if (by_index[20]["paths"] != ["CMakeLists.txt"] or
        by_index[66]["paths"] != ["CMakeModules/find/Findlz4.cmake"] or
        "R23_NATIVE_LZ4_STATIC_MODE_PARSER_SELFTEST_PASS" not in
        (root / "tools/audit/attest-r23-native-lz4-static-mode.py").read_text()):
        raise ValueError("R23 #20/#66 static-mode source receipts missing")
    # Source-reviewed batches: do not label a missing feature as already shipped.
    new_cases = {
        42: "verified-native-GPU-thread-affinity-review-needs-PS5-trace",
        49: "verified-relevant-source-gap-awaiting-native-proof",
        107: "source-equivalent-pinned-savedata-post-revert",
        126: "verified-relevant-source-gap-awaiting-native-proof",
        139: "verified-relevant-source-gap-awaiting-native-proof",
    }
    for i, classification in new_cases.items():
        if by_index[i]["classification"] != classification:
            raise ValueError(f"R23 source-reviewed case #{i} silently changed")
    native_cmake = (root / "headless/CMakeLists.txt").read_text()
    if ('EDEN_GPU_WORKER_VARIANT "gpu_thread_quiet.cpp"' not in native_cmake
            or '"${PORT_BUILD_DIR}/gpu_thread.cpp"' not in native_cmake):
        raise ValueError("Native GPU worker selection changed; re-review #42")
    if by_index[139]["paths"] != ["src/core/hle/service/nfp/nfp.cpp"]:
        raise ValueError("NFP register source proof changed")
    if by_index[107]["paths"] != [
            "src/core/file_sys/savedata_factory.cpp",
            "src/core/file_sys/savedata_factory.h"]:
        raise ValueError("SaveDataFactory revert source paths changed")
    if by_index[44]["classification"] != "staged-host-source-fix":
        raise ValueError("viewport is a proposed host fix, not tested native behavior")
    return {
        "immutable_commit_sha_file_receipts": 155,
        "classified_commits": 155,
        "class_counts": dict(sorted(categories.items())),
        "runtime_semantic_cases_pending": categories["runtime-semantic-review-pending"],
        "asset_and_dependency_cases_pending":
            categories["asset-and-translation-package-review"] +
            categories["native-build-or-dependency-review"],
        "five_staged_fixes_native_PS5_qualified": False,
        "header_include_provenance_qualified": False,
        "native_ELF_or_console_qualified": False,
    }

def self_test(root: Path) -> None:
    current = json.loads((root / APP).read_text())
    assert validate(root)["runtime_semantic_cases_pending"] == 29
    bad = copy.deepcopy(current)
    bad["individual_commits"][4]["classification"] = "runtime-semantic-review-pending"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("incorrect source classification was accepted")
    for case in (16, 29, 30, 32, 44, 47, 49, 54, 58, 63, 74, 76, 83, 89, 95, 98, 102, 108, 118, 123, 129, 130, 135, 150):
        bad = copy.deepcopy(current)
        bad["individual_commits"][case]["classification"] = "runtime-semantic-review-pending"
        try:
            validate(root, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"R23 source-specific disposition case {case + 1} was reset")
    bad = copy.deepcopy(current)
    bad["individual_commits"][28]["classification"] = "runtime-semantic-review-pending"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("R23 #29 unsafe Unicode migration accepted without provenance")
    bad = copy.deepcopy(current)
    bad["individual_commits"][146]["classification"] = "runtime-semantic-review-pending"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("R23 #147 missing cmd23 semantic gap was accepted as closed")
    bad = copy.deepcopy(current)
    bad["individual_commits"][51]["classification"] = "runtime-semantic-review-pending"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("R23 #52 unproved Vulkan/OpenGL port accepted")
    bad = copy.deepcopy(current)
    bad["individual_commits"][0]["paths"][0] = "forged/source.cpp"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("forged changed-file provenance was accepted")
    print("R23_155_APPLICABILITY_SELFTEST_OK")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(args.root)
    else:
        print(json.dumps(validate(args.root), indent=2, sort_keys=True))
