#!/usr/bin/env python3
"""Compile and check the actual FinalHead/ViT GPU boundary shader ABI."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--vendor',type=Path,required=True)
    ap.add_argument('--header',type=Path)
    args=ap.parse_args()
    source=(args.vendor/'encore-active/eden-vulkan/r09_rdna2_nr/vit_boundary_repack_rdna2.comp')
    src=source.read_text()
    for unsafe in ('cooperative_matrix','GL_EXT_shader_8bit_storage','shader_float8','GL_EXT_shader_explicit_arithmetic_types_float16'):
        assert unsafe not in src,unsafe
    with tempfile.TemporaryDirectory(prefix='eden-vit-boundary-') as directory:
        spv=Path(directory)/'vit_boundary.spv'
        subprocess.run(['glslangValidator','-V','--target-env','vulkan1.1','-S','comp','-o',str(spv),str(source)],check=True,capture_output=True)
        subprocess.run(['spirv-val','--target-env','vulkan1.1',str(spv)],check=True,capture_output=True)
        dis=subprocess.check_output(['spirv-dis',str(spv)],text=True)
        assert 'OpExecutionMode %main LocalSize 256 1 1' in dis
        for name,binding in [('source',0),('target',1)]:
            assert f'OpDecorate %{name} DescriptorSet 0' in dis,(name,'set')
            assert f'OpDecorate %{name} Binding {binding}' in dis,(name,'binding')
        for i in range(7):
            assert f'OpMemberDecorate %Params {i} Offset {i*4}' in dis,i
        assert 'OpCapability Shader' in dis
        if args.header:
            blob=spv.read_bytes()
            words=struct.unpack('<'+'I'*(len(blob)//4),blob)
            lines=['// SPDX-License-Identifier: MIT','#pragma once','#include <array>','#include <cstdint>',
                   f'inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_VIT_BOUNDARY_REPACK_COMP_SPV = {{']
            for i in range(0,len(words),8):
                lines.append('    '+', '.join(f'0x{v:08x}u' for v in words[i:i+8])+',')
            lines.append('};')
            args.header.parent.mkdir(parents=True,exist_ok=True)
            args.header.write_text('\n'.join(lines)+'\n')
    print('RDNA2_VIT_BOUNDARY_SPIRV_ABI_PASS')

if __name__=='__main__':
    main()
