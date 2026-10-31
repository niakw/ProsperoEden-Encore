#!/usr/bin/env python3
"""N58: verified native Vulkan device owner; exercise its actual feature predicate."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'vendor/sources/eden/src/video_core/vulkan_common/vulkan_device.h'
new='''    bool IsSparseBindingSupported() const {
        return features.features.sparseBinding && graphics_family_sparse_binding;
    }

    // N58: image sparse residency requires a stronger Vulkan feature than
    // sparse resource binding. Never treat the two as interchangeable.
    [[nodiscard]] bool IsSparseResidencyImage2DSupported() const {
        return IsSparseBindingSupported() && features.features.sparseResidencyImage2D;
    }'''
source=ORIGINAL.read_text()
assert source.count(new)==1, 'Canonical vendor Device method drift'
with tempfile.TemporaryDirectory(prefix='n58-vendor-') as td:
    folder=Path(td)
    method=new[new.index('    bool IsSparseBindingSupported()'):]
    cpp=r'''#include <cassert>
struct FakeVkFeatures {
    bool sparseBinding{};
    bool sparseResidencyImage2D{};
};
struct FakeFeatures { FakeVkFeatures features; };
struct Device {
    FakeFeatures features{};
    bool graphics_family_sparse_binding{};
''' +method+'''
};
int main() {
    for(int b=0;b<=1;b++)
    for(int r=0;r<=1;r++)
    for(int q=0;q<=1;q++) {
        Device device{{{b!=0,r!=0}},q!=0};
        assert(device.IsSparseBindingSupported() == (b!=0&&q!=0));
        assert(device.IsSparseResidencyImage2DSupported() == (b!=0&&r!=0&&q!=0));
    }
}
'''
    src=folder/'test.cpp';src.write_text(cpp)
    for cxx in ('clang++','g++'):
        exe=folder/('n58-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-Wall','-Wextra','-Werror','-O2',
                        '-fsanitize=undefined','-fno-sanitize-recover=all',
                        str(src),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N58_NATIVE_VULKAN_SPARSE_RESIDENCY_GATE_PASS')
