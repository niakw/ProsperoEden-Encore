#!/usr/bin/env python3
"""Fail early when the post-F07 reviewed source register drifts.

Historical F07 receipts are immutable. A changed source must be individually
reviewed and pinned in the separate post-F07 register before a native build.
"""
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
register=ROOT/"docs/EDEN_POST_F07_CHANGED_SOURCE_REGISTER_2026-11-08.json"
data=json.loads(register.read_text())
assert data["schema_version"]==1
assert data["historical_f07_source_snapshots_preserved"] is True
entries=data["files"]
assert len(entries)==42  # 41 previous successors + reviewed NS2 program-index-zero RomFS owner
# The additional vendor entry is a documented source-interface successor,
# not a relaxation of historical F07 provenance or a console performance claim.
thread_entry=next(e for e in entries if e["path"]==
    "vendor/encore-active/eden-threading/src/core/hle/kernel/k_thread.h")
assert thread_entry["historical_reviewed_git_blob"]=="e2f359a54cb6b879bdd41f092cf1ea19fb03e4e6"
assert thread_entry["post_snapshot_git_blob"]=="89bbcbd2b0d3627210a980496d00f30a45c7d944"
assert thread_entry["required_source_fragment"]=="std::vector<KThread*>& GetPendingStartedThreads()"
assert thread_entry["review_kind"]=="source_interface"
assert len({e["path"] for e in entries})==len(entries)
romfs=next(e for e in entries if e["path"] ==
    "vendor/encore-active/eden-core/src/core/file_sys/romfs_factory.cpp")
assert romfs["historical_reviewed_git_blob"] == "cd11cb32429efcceaf6b3e1144d495cce1569383"
assert romfs["post_snapshot_git_blob"] == "4775cf98c3bfbc587402928bad424dcb471047a0"
assert romfs["original_disposition"] == "new_source_issue_corrected"
assert romfs["required_source_fragment"] == "program_index == 0 && type == ContentRecordType::Program"
assert romfs["review_kind"] == "source_contract"
stop_entry=next(e for e in entries if e["path"]=="headless/stop_limit.cpp")
assert stop_entry["post_snapshot_git_blob"]=="a8124257c1a3a068973d6b1e98970f717ac40559"
assert stop_entry["required_source_fragment"]=="game stop exceeded 10s; exiting app without automatic restart"
# Nov15-Nov16 launcher/service successors. Preserve each prior
# register blob and admit only the exact currently selected reviewed successor;
# Later reviewed ExeFS/media/diagnostics changes do not rewrite the frozen
# historical register or widen acceptance to arbitrary drift.
successors={
    # Nov22 shipping NS2 completed-HLE receipt: exact graphics source blob,
    # 10s/30s hooks only. Preserve the original historical F07 hash.
    "headless/graphics.cpp": (
        "ca3107c8745af36d6faf0196cf9692e628d52540",
        "b498ee4307ffb0b7f6ae18333177687607a297d7",
    ),
    "headless/hud.h": (
        "0ef8bf75efabf61628b44b91011eb461abcbde81",
        "a506f5dca7efc289f47a172a353bff4f04d9f4e4",
    ),
    "headless/prosperoeden/frontend.cpp": (
        "25884807fdf7759834cb232548184ffefca715d4",
        "1de983352dad85e4dd6c1520a0c9e9aec26d052d",
    ),
    "headless/prosperoeden/eden_services.cpp": (
        "4e9159c716e7eb6759ba3aef7d200ef869d069aa",
        "6efc431641ace097b7216748e1e232c8cc9f1ae1",
    ),
    "headless/prosperoeden/eden_services.h": (
        "604a9d15118390b7f9b7e1265d38a91ff97c4a23",
        "7c4133b4e2f0340aa1e0e182ae469619d5a8c687",
    ),
    "headless/prosperoeden/pe/ui/launcher.cpp": (
        "1e488a05689b29baf8c4318d98be52506816cfaa",
        "255b110f1e1d021ed92511e64c2f8f67ee62a66d",
    ),
    "headless/prosperoeden/pe/ui/launcher.hpp": (
        "f0e8db4791e79d3e173387d2288886bba52ac015",
        "fb3a0037cfb86328f398a3059c5dd95faa9d950b",
    ),
    "headless/prosperoeden/pe/ui/services.hpp": (
        "868cecd138d9b57486d1e9ce3b7b775848bcc0a3",
        "300fa56ad3d8932e25a898c53ed8052f4d69841f",
    ),
    "headless/prosperoeden/pe/ui/switch_theme.cpp": (
        "819f2c96a35a34035da68b487abda3fd08ed1cda",
        "8b59abca5e756f6be6e5da70aec9c477c7e0e1ab",
    ),
}
# Nov23 launcher/media consolidation changed five additional reviewed owners
# in one commit. Each is accepted only at its exact full Git blob, then the
# exact pre-consolidation bytes are loaded from the immutable parent commit so
# the existing Nov15 successor receipts remain authoritative.
launcher_consolidation = {
    "headless/prosperoeden/frontend.cpp":
        ("5433ebd155a504084d84cc1d74a3cbb0eb11b229",
         "1de983352dad85e4dd6c1520a0c9e9aec26d052d"),
    "headless/prosperoeden/eden_services.h":
        ("8c6248417cb3ec25b327661e410960a3e2a738de",
         "7c4133b4e2f0340aa1e0e182ae469619d5a8c687"),
    "headless/prosperoeden/pe/ui/launcher.cpp":
        ("1d7822b025dd5b8927baa7ddb23d6c78e5a22276",
         "255b110f1e1d021ed92511e64c2f8f67ee62a66d"),
    "headless/prosperoeden/pe/ui/launcher.hpp":
        ("4f82cc58396bb3f45aeadc4fb7638e3565d56d03",
         "fb3a0037cfb86328f398a3059c5dd95faa9d950b"),
    "headless/prosperoeden/pe/ui/services.hpp":
        ("2509658b7e8fb888c10e6bede6ba9ce12a124a7d",
         "300fa56ad3d8932e25a898c53ed8052f4d69841f"),
    "headless/prosperoeden/pe/ui/home.cpp":
        ("5fe7795275f7f7561f9a79354ac84197b404f3d3",
         "c4a835b5cfb3033342e6575ef3ccb2606bab0eae"),
    "headless/prosperoeden/pe/platform/display_egl.cpp":
        ("e9484e8e433b1199d30bd80826a6b0f8864ada51",
         "190a885cc2e50e440234b79a8b69f10b8aa84d18"),
}
drifts=[]
successor_hits=set()
for entry in entries:
    path=ROOT/entry["path"]
    assert path.is_file(),("Missing reviewed source",entry["path"])
    expected=entry["post_snapshot_git_blob"]
    assert expected!=entry["historical_reviewed_git_blob"]
    actual=subprocess.check_output(
        ["git","hash-object",str(path)],cwd=ROOT,text=True
    ).strip()
    if entry["path"] in launcher_consolidation:
        current_blob, predecessor_blob = launcher_consolidation[entry["path"]]
        if actual == current_blob:
            predecessor = subprocess.check_output(
                ["git", "show",
                 "e0080f38204bab4cb596a3bed38ba9a625762c86:" + entry["path"]],
                cwd=ROOT, text=True)
            recovered = subprocess.run(
                ["git", "hash-object", "--stdin"],
                input=predecessor.encode("utf-8"),
                stdout=subprocess.PIPE, check=True
            ).stdout.decode().strip()
            assert recovered == predecessor_blob, (
                "Reviewed Nov23 launcher predecessor changed",
                entry["path"], recovered)
            actual = recovered
    if entry["path"] in successors:
        prior, successor=successors[entry["path"]]
        assert expected==prior,(entry["path"],expected,prior)
        if entry["path"] == "headless/prosperoeden/eden_services.cpp":
            # R457 logging retention is a strict successor to the reviewed
            # Nov15/16 service owner. Reconstruct the exact predecessor before
            # checking its immutable Git blob; do not widen the source list.
            # Exact additive PS5 boottrace OFF->ON resume after log retention.
            # Audit the two independent successors without changing F07 baselines.
            # DNSP/DXCI changes only the library format list. Reconstruct
            # the reviewed R457 owner on an audit copy, preserving the real
            # shipping extension list and both prior source receipts.
            service_audit_source = path.read_text(encoding="utf-8")
            # Nov23 launcher/media consolidation is a large reviewed successor
            # of this service owner. Do not replay hundreds of UI/media hunks
            # inline here: admit only its exact full blob, then recover the
            # exact pre-launcher owner from the immutable parent commit before
            # continuing the existing NX/DNSP/R457 historical chain.
            if actual == "c80d171b9177987f4f29cf675c41a75771c62685":
                service_audit_source = subprocess.check_output(
                    ["git", "show",
                     "e0080f38204bab4cb596a3bed38ba9a625762c86:headless/prosperoeden/eden_services.cpp"],
                    cwd=ROOT, text=True)
                actual = subprocess.run(
                    ["git", "hash-object", "--stdin"],
                    input=service_audit_source.encode("utf-8"),
                    stdout=subprocess.PIPE, check=True
                ).stdout.decode().strip()
                assert actual == "f850b77e7b2a366f2e7cb16a0be9efb57679fef9", (
                    "Reviewed Nov23 launcher predecessor changed", actual)
            new_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".dnsp", ".dxci",
                                   ".nro", ".nso", ".nca", ".nax", ".kip", ".nup"}'''
            old_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".nro", ".nso",
                                   ".nca", ".nax", ".kip"}'''
            # The subsequent NX archive registration only appends ".nx" to
            # the same shipping format set. Replay exactly that one hunk
            # before the existing immutable DNSP/DXCI and R457 receipts.
            if actual == "f850b77e7b2a366f2e7cb16a0be9efb57679fef9":
                nx_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".dnsp", ".dxci",
                                   ".nro", ".nso", ".nca", ".nax", ".kip", ".nup", ".nx"}'''
                assert service_audit_source.count(nx_formats) == 1
                service_audit_source = service_audit_source.replace(
                    nx_formats, new_formats, 1)
                actual = subprocess.run(
                    ["git", "hash-object", "--stdin"],
                    input=service_audit_source.encode("utf-8"),
                    stdout=subprocess.PIPE, check=True
                ).stdout.decode().strip()
                assert actual == "01d025544ac3544ab58779884f6fee10dcbe3209", actual
            if actual == "01d025544ac3544ab58779884f6fee10dcbe3209":
                assert service_audit_source.count(new_formats) == 1
                service_audit_source = service_audit_source.replace(new_formats, old_formats, 1)
                prior_raw = service_audit_source.encode("utf-8")
                recovered = subprocess.run(
                    ["git", "hash-object", "--stdin"], input=prior_raw,
                    stdout=subprocess.PIPE, check=True).stdout.decode().strip()
                assert recovered == "90f1f4fb2d239d71d0a856943cc4328704e2058b", recovered
                actual = recovered
            assert actual == "90f1f4fb2d239d71d0a856943cc4328704e2058b", (
                "Unreviewed R457 bootstrap-resume owner", actual)
            restored = service_audit_source
            resume_block = """        } else if (!Eden::BootTrace::Resume(Eden::LogsDir())) {
            // Normal stderr/stdout and fatal crash reports remain independent.
            // A failed bootstrap reopen must not truncate prior traces or
            // misrepresent this additional trace as available.
            Eden::Report("logs", "Early trace unavailable after logging was enabled");
        }"""
            assert restored.count(resume_block) == 1
            restored = restored.replace(resume_block, "        }", 1)
            restored_blob = subprocess.run(
                ["git", "hash-object", "--stdin"], input=restored.encode("utf-8"),
                stdout=subprocess.PIPE, check=True
            ).stdout.decode().strip()
            assert restored_blob == "be163317ca482765f31ddf3b7d1dbe24be041294", (
                "Exact reviewed R457 log retention predecessor changed", restored_blob)
            before = """        if (!value.detailed_logging) {
            // Stop recording, but never erase earlier sessions simply by
            // toggling this option. A user may need those files after a hang.
            Eden::BootTrace::Quiet(Eden::LogsDir());
        }"""
            after = """        if (!value.detailed_logging) {
            Eden::BootTrace::Quiet(Eden::LogsDir());
            for (const char* name : {
                    "eden_log.txt", "eden_log.txt.first.txt", "eden_log.txt.old.txt"})
                (void)std::remove((Eden::UserDir() + "/log/" + name).c_str());
        }"""
            reviewed = restored
            assert reviewed.count(before) == 1, "Unexpected log-retention source delta"
            prior_bytes = reviewed.replace(before, after, 1).encode("utf-8")
            prior_blob = subprocess.run(
                ["git", "hash-object", "--stdin"], input=prior_bytes,
                stdout=subprocess.PIPE, check=True
            ).stdout.decode().strip()
            assert prior_blob == successor, ("Historical launcher service receipt changed", prior_blob)
        else:
            assert actual==successor,("Unreviewed Nov15 launcher successor",entry["path"],actual)
        successor_hits.add(entry["path"])
    elif actual!=expected:
        drifts.append((entry["path"],expected,actual))
assert successor_hits==set(successors)
assert not drifts,("Unreviewed post-F07 source change",drifts)
print(f"POST_F07_SHA_PREFLIGHT_PASS files={len(entries)} historical_snapshot=immutable")
