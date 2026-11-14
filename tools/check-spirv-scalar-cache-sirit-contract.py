#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prove the exact Sirit v1.0.5 declaration-dedup contract used by the scalar cache."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
stream=V/"sources/eden-cpm/sirit/v1.0.5/src/stream.h"
constant=V/"sources/eden-cpm/sirit/v1.0.5/src/instructions/constant.cpp"
header=V/"encore-active/eden-shader/src/shader_recompiler/backend/spirv/spirv_emit_context.h"
assert blob(stream)=="31c2680c2f2c6977e5368e4a28262d8db611e3f8"
assert blob(constant)=="612049c4f8e54db3e95f43f49e8407158ab0b9ac"
assert blob(header)=="844a118358c874b0666aebda116c1d6a0c9a8ceb"
s=stream.read_text()
c=constant.read_text()
h=header.read_text()
# Sirit creates a declaration candidate, zeroes its result id for lookup,
# returns the first id on duplicates, and rewinds both words and bound.
for needle in (
    "std::vector<u32> declarations(begin + stream.op_index, begin + stream.insert_index);",
    "const u32 id = std::exchange(declarations[id_index], 0);",
    "existing_declarations.emplace(declarations, id)",
    "stream.insert_index = stream.op_index;",
    "--*stream.bound;",
    "return Id{entry->second};",
):
    assert s.count(needle)==1,needle
assert "Id Module::Constant(Id result_type, const Literal& literal)" in c
assert "return *declarations << OpId{spv::Op::OpConstant, result_type} << literal << EndOp{};" in c
for needle in (
    "CachedConstant(u32_constants, U32[1], value)",
    "CachedConstant(f32_constants, F32[1], value)",
    "cache.try_emplace(std::bit_cast<u32>(value))",
):
    assert needle in h
# Because the first call still reaches Sirit and repeated equal-bit/type calls
# return that exact first Id, this optimization preserves Sirit's existing
# duplicate declaration identity. This is not a whole-corpus output oracle.
print("SPIRV_SCALAR_SIRIT_DEDUP_CONTRACT_PASS exact_sirit=1 first_id=preserved duplicate_stream=rewound full_corpus=unverified")
