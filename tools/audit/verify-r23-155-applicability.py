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
        "runtime-semantic-review-pending": 59,
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
        "verified-relevant-source-gap-awaiting-native-proof": 11,
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
            or any(by_index[i]["classification"] != "runtime-semantic-review-pending"
                   for i in (30,))):
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
    for i in (30,):
        if by_index[i]["classification"] != "runtime-semantic-review-pending":
            raise ValueError(f"R23 common/native semantic case #{i} was closed without proof")
    # Exact upstream source reversion receipts were reviewed separately.
    # Do not accidentally reactivate either giant HLE pair or the NCE GPU
    # writeback sequence because the frozen class totals happen to match.
    for i in (69, 74):
        if by_index[i]["classification"] != "source-equivalent-hle-handler-revert-cosmetic-only":
            raise ValueError(f"R23 HLE handler undo pair #{i} lost source proof")
    for i in (47, 88):
        if by_index[i]["classification"] != "source-equivalent-GPU-NCE-readback-reverted":
            raise ValueError(f"R23 NCE GPU reverted pair #{i} lost source proof")
    for i in (45, 60, 92):
        if by_index[i]["classification"] not in (
            "source-implemented-native-PS5-NCZBLOCK-NSZ-XCZ",
            "source-implemented-native-PS5-ZBIC-NSO",
            "runtime-semantic-review-pending",
        ):
            raise ValueError(f"R23 compressed-content case #{i} changed silently")
    for i in (117, 122, 125):
        if by_index[i]["classification"] != "source-equivalent-declared-native-x64-lookup":
            raise ValueError(f"R23 x64 page-table lookup #${i} lost E1 parity proof")
    if by_index[136]["classification"] != "runtime-semantic-review-pending":
        raise ValueError("R23 A32 sign-extension divergence #136 still requires JIT tests")
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
    assert validate(root)["runtime_semantic_cases_pending"] == 59
    bad = copy.deepcopy(current)
    bad["individual_commits"][4]["classification"] = "runtime-semantic-review-pending"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("incorrect source classification was accepted")
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
