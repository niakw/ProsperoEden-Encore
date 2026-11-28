#!/usr/bin/env python3
"""Exact engine/vendor contract for the FC27 Maxwell PRMT rc/cr candidate.

Upstream reference: zortos293/Lichii f6a8f513249754e2dd69a7f04efe5f8bb34ab756.
Host/source evidence only; no PS5 FC27 text-fix claim.
"""
from pathlib import Path
import hashlib
import subprocess

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
EXPECTED="dcfe3d2384bd800c6139ede672518ea2c66922a6"
SOURCE=V/"encore-active/eden/src/shader_recompiler/frontend/maxwell/translate/impl/not_implemented.cpp"
TEST=V/"tests/fc27_maxwell_prmt_operand_forms_source.py"

selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert selected==checked==EXPECTED,(selected,checked)

def blob(path: Path) -> str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

assert blob(SOURCE)=="b74459a60b7ced666cec19dbc1fdc32a10feb5da"
assert blob(TEST)=="0dd09b9f863778ffef7234c9305a0cbfdf960e48"

src=SOURCE.read_text()
def section(name: str) -> str:
    start=src.index(f"void TranslatorVisitor::{name}(u64 insn)")
    end=src.index("\nvoid TranslatorVisitor::",start+1)
    return src[start:end]

rc=section("PRMT_rc")
cr=section("PRMT_cr")
assert rc.count("ThrowNotImplemented(Opcode::PRMT_rc)") == 1
assert cr.count("ThrowNotImplemented(Opcode::PRMT_cr)") == 1
assert rc.index("if (mode != 0)") < rc.index("ThrowNotImplemented(Opcode::PRMT_rc)")
assert cr.index("if (mode != 0)") < cr.index("ThrowNotImplemented(Opcode::PRMT_cr)")
assert rc.index("ThrowNotImplemented(Opcode::PRMT_rc)") < rc.index("const IR::U32 a{GetReg8(insn)};")
assert cr.index("ThrowNotImplemented(Opcode::PRMT_cr)") < cr.index("const IR::U32 a{GetReg8(insn)};")
assert "const IR::U32 b{GetCbuf(insn)};" in rc
assert "const IR::U32 selector{GetReg39(insn)};" in rc
assert "const IR::U32 b{GetReg39(insn)};" in cr
assert "const IR::U32 selector{GetCbuf(insn)};" in cr
assert "if (mode != 0)" in rc and "if (mode != 0)" in cr
subprocess.run(["python3","-B",str(TEST)],cwd=ROOT,check=True,timeout=120)
print(f"FC27_PRMT_ENGINE_SELECTION_PASS pin={EXPECTED[:8]} forms=rc,cr selectors=65536 ps5=unverified")
