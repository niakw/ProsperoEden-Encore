#!/usr/bin/env python3
"""Exact reversible receipt for selected NS2 failed-load KProcess registration.

Only the two reviewed additions in vendor PR #111 are stripped for the
historical owner/source generator checks. Compiled vendor source is untouched.
"""
from __future__ import annotations
import hashlib

ORIGINAL_BLOB = "80d4186339ad6e48e86ec177a8946da67ea164ff"
REVIEWED_BLOB = "be6874e3f0f1ec74fc8f686408b97d9122dad561"
EARLY_ORIGINAL = """    Kernel::KProcess::Register(m_system.Kernel(), process);

"""
EARLY_CANDIDATE = """    // Register only after loader.Load has succeeded. If NPDM/NSO/firmware
    // loading fails before KProcess::Initialize, registering here leaves a
    // dangling intrusive list node when the slab object is destroyed.
    // Upstream Lichii #1574 / Eglantine eb579d2 found this exact failure.

"""
LATE_CANDIDATE = """    // This object is now fully loaded with valid NPDM parameters. A failed
    // load must never enter the global intrusive kernel object list.
    Kernel::KProcess::Register(m_system.Kernel(), process);

"""
LATE_ORIGINAL = ""

def git_blob(source: str) -> str:
    data=source.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()

def normalize_process_receipt(source: str) -> tuple[str,bool]:
    observed=git_blob(source)
    if observed == ORIGINAL_BLOB:
        return source, False
    assert observed == REVIEWED_BLOB, (
        "Unreviewed native KProcess source: no historical SHA exemption", observed)
    assert source.count(EARLY_CANDIDATE)==1
    assert source.count(LATE_CANDIDATE)==1
    assert source.count("Kernel::KProcess::Register(m_system.Kernel(), process);")==1
    original=source.replace(EARLY_CANDIDATE,EARLY_ORIGINAL,1)
    original=original.replace(LATE_CANDIDATE,LATE_ORIGINAL,1)
    assert git_blob(original)==ORIGINAL_BLOB, (
        "PS5 KProcess registration normalized source does not reconstruct original")
    return original, True
