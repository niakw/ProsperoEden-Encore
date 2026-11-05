#!/usr/bin/env python3
"""Compare the 11 AMD FSR 3.1.4 SPIR-V descriptor ABIs with Eden C++ layouts.

Checks actual OpVariable/OpTypeImage and Vk descriptor type rather than
merely counting binding numbers or trusting shader source comments.
Requires SPIRV-Tools spirv-dis, and SPV binaries produced by
build-fsr31-amd-shaders.py --keep-spv. Host-only static verification.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import subprocess

PASS_ARRAY={
    "prepare_inputs":"PREPARE_INPUTS",
    "luma_pyramid":"LUMA_PYRAMID",
    "luma_pyramid_nowave":"LUMA_PYRAMID",
    "shading_change_pyramid":"SHADING_CHANGE_PYRAMID",
    "shading_change_pyramid_nowave":"SHADING_CHANGE_PYRAMID",
    "shading_change":"SHADING_CHANGE",
    "prepare_reactivity":"PREPARE_REACTIVITY",
    "luma_instability":"LUMA_INSTABILITY",
    "accumulate":"ACCUMULATE",
    "accumulate_sharpen":"ACCUMULATE",
    "rcas":"RCAS",
}

def expected_layouts(source: str) -> dict[str,list[str]]:
    matches=dict(re.findall(
        r"constexpr std::array\s+([A-Z_]+)\s*\{([^{}]+)\};",source))
    result={}
    for name in set(PASS_ARRAY.values()):
        if name not in matches:
            raise ValueError(f"missing host descriptor layout: {name}")
        kinds=[x.strip() for x in matches[name].split(",")]
        if not kinds or any(x not in ("T","I","U") for x in kinds):
            raise ValueError(f"invalid host layout {name}: {kinds}")
        result[name]=kinds
    return result

def parse_spirv_abi(disassembly: str) -> dict[int,str]:
    lines=disassembly.splitlines()
    bindings={}
    descriptor_sets={}
    pointers={}
    types={}
    vars={}
    for line in lines:
        m=re.search(r"OpDecorate\s+(%\S+)\s+Binding\s+(\d+)",line)
        if m:
            bindings[m[1]]=int(m[2])
        m=re.search(r"OpDecorate\s+(%\S+)\s+DescriptorSet\s+(\d+)",line)
        if m:
            descriptor_sets[m[1]]=int(m[2])
        m=re.match(r"\s*(%\S+)\s*=\s*OpTypePointer\s+(\w+)\s+(%\S+)",line)
        if m:
            pointers[m[1]]=(m[2],m[3])
        m=re.match(r"\s*(%\S+)\s*=\s*OpTypeSampler\b",line)
        if m:
            types[m[1]]="S"
        m=re.match(r"\s*(%\S+)\s*=\s*OpTypeImage\s+(.+)",line)
        if m:
            tokens=m[2].split()
            if len(tokens)<7:
                raise ValueError(f"malformed OpTypeImage: {line}")
            sampled=tokens[5]  # Sampled operand after sampled type/dim/depth/array/MS
            types[m[1]]={"1":"T","2":"I"}.get(sampled,"UNKNOWN_IMAGE")
        m=re.match(r"\s*(%\S+)\s*=\s*OpVariable\s+(%\S+)\s+(\w+)",line)
        if m:
            vars[m[1]]=(m[2],m[3])
    out={}
    for var,bind in bindings.items():
        if var not in vars:
            raise ValueError(f"decorated binding has no variable: {var}")
        if descriptor_sets.get(var)!=0:
            raise ValueError(f"unexpected descriptor set {descriptor_sets.get(var)}")
        if bind in out:
            raise ValueError(f"duplicate SPIR-V binding {bind}")
        ptr,storage=vars[var]
        ptr_storage,pointee=pointers[ptr]
        if ptr_storage!=storage:
            raise ValueError(f"inconsistent storage class {var}")
        if storage=="Uniform":
            actual="U"
        elif storage=="UniformConstant":
            actual=types.get(pointee,"UNKNOWN")
        else:
            raise ValueError(f"unsupported storage class {var}: {storage}")
        if actual not in ("U","T","I","S"):
            raise ValueError(f"unrecognised descriptor type {var}: {actual}")
        out[bind]=actual
    return out

def host_uniform_offsets(source: str) -> dict[str,list[int]]:
    result={}
    for host,spirv in (("Constants","cbFSR3UPSCALER_t"),
                       ("SpdConstants","cbSPD_t"),
                       ("RcasConstants","cbRCAS_t")):
        match=re.search(r"struct\s+"+host+r"\s*\{(.*?)\};",source,re.S)
        if not match:
            raise ValueError(f"host C++ uniform struct missing: {host}")
        fields=re.findall(
            r"^\s*(?:std::array<(?:s32|f32|u32),\s*(\d+)>|(s32|u32|f32))\s+\w+\s*;",
            match[1],re.M)
        if not fields:
            raise ValueError(f"host C++ uniform fields missing: {host}")
        offset=0
        offsets=[]
        for length,scalar in fields:
            offsets.append(offset)
            offset+=4*(int(length) if length else 1)
        result[spirv]=offsets
    if len(result["cbFSR3UPSCALER_t"])!=23 or (
        result["cbFSR3UPSCALER_t"][-1]!=144):
        raise ValueError("FSR3.1 C++ uniform ABI drift")
    return result


def verify_uniform_abi(shader: str, asm: str, offsets: dict[str,list[int]]) -> set[str]:
    seen=set()
    for spirv,expected in offsets.items():
        members={int(i):int(off) for i,off in re.findall(
            r"OpMemberDecorate\s+%"+re.escape(spirv)+r"\s+(\d+)\s+Offset\s+(\d+)",asm)}
        if not members:
            continue
        seen.add(spirv)
        if sorted(members)!=list(range(len(expected))):
            raise ValueError(f"{shader}: {spirv} uniform member count mismatch")
        actual=[members[i] for i in range(len(expected))]
        if actual!=expected:
            raise ValueError(f"{shader}: {spirv} uniform offsets wrong; GPU={actual} CPU={expected}")
    return seen

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--shader-dir",type=Path,required=True)
    parser.add_argument("--backend-source",type=Path,required=True)
    parser.add_argument("--spirv-dis",default=shutil.which("spirv-dis"))
    args=parser.parse_args()
    executable=args.spirv_dis
    if not executable:
        parser.error("spirv-dis is required for host descriptor ABI checks")
    cpp=args.backend_source.read_text()
    expected=expected_layouts(cpp)
    uniform_offsets=host_uniform_offsets(cpp)
    seen_uniforms=set()
    all_bindings=0
    for shader,layout in PASS_ARRAY.items():
        binary=args.shader_dir/f"fsr3_upscaler_{shader}.spv"
        if not binary.is_file():
            raise FileNotFoundError(binary)
        asm=subprocess.run([executable,str(binary)],check=True,
                           capture_output=True,text=True).stdout
        current=parse_spirv_abi(asm)
        seen_uniforms.update(verify_uniform_abi(shader,asm,uniform_offsets))
        host=expected[layout]
        for binding,actual in current.items():
            if binding in (1000,1001):
                want="S"
            elif 0<=binding<len(host):
                want=host[binding]
            else:
                raise ValueError(f"{shader}: out-of-range binding {binding}")
            if actual!=want:
                raise ValueError(f"{shader}: binding {binding} SPIR-V {actual}, C++ {want}")
        if not any(k not in (1000,1001) for k in current):
            raise ValueError(f"{shader}: no GPU resources")
        all_bindings+=len(current)
        print(f"ABI_OK {shader} reflected={len(current)} host={len(host)}")
    if "cbFSR3UPSCALER_t" not in seen_uniforms or "cbSPD_t" not in seen_uniforms:
        raise ValueError("AMD GPU shaders did not expose FSR3.1 / SPD uniforms")
    print(f"FSR31_SPIRV_DESCRIPTOR_ABI_OK passes={len(PASS_ARRAY)} reflected_bindings={all_bindings} uniform_structs={len(seen_uniforms)}")

if __name__=="__main__":
    main()
