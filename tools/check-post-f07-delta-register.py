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
assert len(entries)==40  # reviewed post-F07 successors, including fail-closed stop watchdog
assert len({e["path"] for e in entries})==len(entries)
stop_entry=next(e for e in entries if e["path"]=="headless/stop_limit.cpp")
assert stop_entry["post_snapshot_git_blob"]=="a8124257c1a3a068973d6b1e98970f717ac40559"
assert stop_entry["required_source_fragment"]=="game stop exceeded 10s; exiting app without automatic restart"
# Nov15 launcher successors merged by engine #207/#209. Preserve each prior
# register blob and admit only the exact currently selected reviewed successor;
# #209's size worker changes eden_services.cpp but does not rewrite the frozen
# historical register or widen acceptance to arbitrary drift.
successors={
    "headless/prosperoeden/eden_services.cpp": (
        "4e9159c716e7eb6759ba3aef7d200ef869d069aa",
        "964a3a490948aa01149ade2b47dd95ea2b57628b",
    ),
    "headless/prosperoeden/eden_services.h": (
        "604a9d15118390b7f9b7e1265d38a91ff97c4a23",
        "f3d2ca33cc2e42eeafef26207784bd43b6da918b",
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
    if entry["path"] in successors:
        prior, successor=successors[entry["path"]]
        assert expected==prior,(entry["path"],expected,prior)
        assert actual==successor,("Unreviewed Nov15 launcher successor",entry["path"],actual)
        successor_hits.add(entry["path"])
    elif actual!=expected:
        drifts.append((entry["path"],expected,actual))
assert successor_hits==set(successors)
assert not drifts,("Unreviewed post-F07 source change",drifts)
print(f"POST_F07_SHA_PREFLIGHT_PASS files={len(entries)} historical_snapshot=immutable")
