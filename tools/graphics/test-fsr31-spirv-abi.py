#!/usr/bin/env python3
"""Host regression tests for the FSR3.1 SPIR-V/C++ interface gate.

Only synthetic shader reflection is used: no PS5 build, GPU or AMD SDK required.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("check-fsr31-spirv-abi.py")
spec = importlib.util.spec_from_file_location("fsr31_spirv_abi", SCRIPT)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def must_reject(operation, reason: str):
    try:
        operation()
    except (ValueError, KeyError, IndexError) as error:
        assert reason in str(error), (reason, str(error))
    else:
        raise AssertionError("FSR3.1 ABI checker accepted malformed data: " + reason)


BASE = """
%float = OpTypeFloat 32
%image = OpTypeImage %float 2D 0 0 0 1 Unknown
%ptr = OpTypePointer UniformConstant %image
%var = OpVariable %ptr UniformConstant
OpDecorate %var DescriptorSet 0
OpDecorate %var Binding 0
"""
assert gate.parse_spirv_abi(BASE) == {0: "T"}
must_reject(lambda: gate.parse_spirv_abi(BASE.replace("DescriptorSet 0", "DescriptorSet 1")), "unexpected descriptor set")
must_reject(lambda: gate.parse_spirv_abi(BASE + """
%var2 = OpVariable %ptr UniformConstant
OpDecorate %var2 DescriptorSet 0
OpDecorate %var2 Binding 0
"""), "duplicate SPIR-V binding")
must_reject(lambda: gate.parse_spirv_abi(BASE.replace("OpTypePointer UniformConstant", "OpTypePointer Uniform")), "inconsistent storage class")
must_reject(lambda: gate.parse_spirv_abi(BASE.replace("OpVariable %ptr UniformConstant", "OpVariable %ptr Function")), "inconsistent storage class")
must_reject(lambda: gate.parse_spirv_abi(BASE.replace("OpTypeImage %float 2D 0 0 0 1", "OpTypeImage %float 2D 0 0 0 0")), "unrecognised descriptor type")

uniform_good = """
OpMemberDecorate %cbFSR3UPSCALER_t 0 Offset 0
OpMemberDecorate %cbFSR3UPSCALER_t 1 Offset 4
"""
offsets = {"cbFSR3UPSCALER_t": [0, 4]}
assert gate.verify_uniform_abi("synthetic", uniform_good, offsets) == {"cbFSR3UPSCALER_t"}
must_reject(lambda: gate.verify_uniform_abi("synthetic", uniform_good.replace("1 Offset 4", "1 Offset 8"), offsets), "uniform offsets wrong")
must_reject(lambda: gate.verify_uniform_abi("synthetic", uniform_good.replace("1 Offset 4", "2 Offset 4"), offsets), "uniform member count mismatch")

hosts = "\n".join("constexpr std::array " + k + "{T,I,U};" for k in set(gate.PASS_ARRAY.values()))
assert all(v == ["T", "I", "U"] for v in gate.expected_layouts(hosts).values())
must_reject(lambda: gate.expected_layouts(hosts.replace("PREPARE_INPUTS{T,I,U}", "PREPARE_INPUTS{T,I,S}")), "invalid host layout")

print("PASS FSR31 ABI parser rejects descriptor set/binding/storage/image/uniform drift")
