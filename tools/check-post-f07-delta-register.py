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
drifts=[]
for entry in entries:
    path=ROOT/entry["path"]
    assert path.is_file(),("Missing reviewed source",entry["path"])
    expected=entry["post_snapshot_git_blob"]
    assert expected!=entry["historical_reviewed_git_blob"]
    actual=subprocess.check_output(
        ["git","hash-object",str(path)],cwd=ROOT,text=True
    ).strip()
    if actual!=expected:
        drifts.append((entry["path"],expected,actual))
assert not drifts,("Unreviewed post-F07 source change",drifts)
print(f"POST_F07_SHA_PREFLIGHT_PASS files={len(entries)} historical_snapshot=immutable")
