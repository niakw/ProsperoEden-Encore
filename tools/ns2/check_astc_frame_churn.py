#!/usr/bin/env python3
"""N61: synthetic 2400-frame ASTC layer freshness / race / failure stress."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='n61-astc-stress-') as folder:
    for cxx in ('clang++','g++'):
        binary=Path(folder)/('astc-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
           '-fsanitize=undefined','-fno-sanitize-recover=all',
           '-I',str(ROOT/'vendor/encore-active/ns2-helpers/include'),
           str(ROOT/'tools/ns2/test_astc_frame_churn.cpp'),
           '-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
print('N61_ASTC_FRAME_CHURN_HOST_UBSAN_ORACLE_PASS')
