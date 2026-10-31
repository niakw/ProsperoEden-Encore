#!/usr/bin/env python3
"""Native/desktop source-extracted Vulkan sparse bind coalescing, 4 KiB oracle."""
from pathlib import Path
import subprocess
import shutil
import tempfile
import ast

root = Path(__file__).resolve().parents[1]
src = (root / "vendor/encore-active/eden-vulkan/vk_multi_range_buffer_cost.cpp").read_text()
gen = (root / "tools/prepare-vulkan-port.py").read_text()
call = "python3 -B tools/check-ps5-f07-sparse-bind-coalescing-host.py"
for workflow in ("encore-core-fast-gate.yml", "encore-core-preflight.yml"):
    assert call in (root / ".github/workflows" / workflow).read_text()
assert "F07 merge contiguous native Vulkan sparse bindings safely" in gen
ast.parse(gen)
a = src.index("    std::vector<VkSparseMemoryBind> binds;")
b = src.index("    for (const MultiRangeSource& source : sources) {", a)
c = src.index("    const VkSparseBufferMemoryBindInfo buffer_bind{", b)
loop = src[b:c]
assert loop.count("for (const MultiRangeSource& source : sources)") == 1
assert "binds.back().memory == source.memory" in loop
assert "binds.back().memoryOffset + binds.back().size == physical_offset" in loop
assert "binds.back().resourceOffset + binds.back().size == resource_offset" in loop
assert "#ifdef PS5_NATIVE" in loop and "#endif" in loop
cpp = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>
using VkDeviceSize = std::uint64_t;
using VkDeviceMemory = std::uint64_t;
struct MultiRangeSource { VkDeviceMemory memory; VkDeviceSize memory_offset,offset,size; };
struct VkSparseMemoryBind {
    VkDeviceSize resourceOffset{},size{};
    VkDeviceMemory memory{};
    VkDeviceSize memoryOffset{};
    std::uint32_t flags{};
};
using Src = std::vector<MultiRangeSource>;
using Binds = std::vector<VkSparseMemoryBind>;
Binds Actual(const Src& sources) {
    Binds binds;
    binds.reserve(sources.size());
    VkDeviceSize resource_offset = 0;
__EXTRACTED__
    return binds;
}
struct Page {
    VkDeviceMemory memory;
    VkDeviceSize offset;
    bool operator==(const Page&) const = default;
};
std::vector<Page> Reference(const Src& src) {
    std::vector<Page> out;
    for (const auto& s : src)
        for (VkDeviceSize p=0; p<s.size; p+=4096)
            out.push_back({s.memory,s.memory_offset+s.offset+p});
    return out;
}
std::vector<Page> Expanded(const Binds& binds) {
    std::vector<Page> out;
    VkDeviceSize target=0;
    for (const auto& b : binds) {
        assert(b.resourceOffset==target && b.size && b.size%4096==0 && b.flags==0);
        for (VkDeviceSize p=0; p<b.size; p+=4096)
            out.push_back({b.memory,b.memoryOffset+p});
        target+=b.size;
    }
    return out;
}
void Check(const Src& src, [[maybe_unused]] std::size_t native_count) {
    const auto binds=Actual(src);
    assert(Reference(src)==Expanded(binds));
#ifdef PS5_NATIVE
    assert(binds.size()==native_count);
#else
    assert(binds.size()==src.size());
#endif
}
int main(){
    Src contiguous;
    for(std::uint64_t i=0;i<64;++i)contiguous.push_back({7,8192,i*4096,4096});
    Check(contiguous,1);
    Src mixed{{7,4096,0,4096},{7,4096,4096,4096},
              {9,0,0,4096},{9,0,8192,4096},
              {9,0,12288,4096},{9,8192,8192,4096},
              {10,0,0,4096}};
    Check(mixed,4);
    Src split{{5,4096,4096,4096},{5,8192,4096,4096},
              {5,8192,8192,4096}};
    Check(split,1);
    for(std::uint64_t n=1;n<=73;++n){
        Src cases;
        VkDeviceSize physical=0;
        for(std::uint64_t i=0;i<n;++i){
            if(i%17==0)physical=4096;
            else physical+=i%9==0?8192:4096;
            cases.push_back({5+i/17,0,physical,4096});
        }
        const auto binds=Actual(cases);
        assert(Reference(cases)==Expanded(binds) && !binds.empty());
        assert(binds.size()<=cases.size());
#ifndef PS5_NATIVE
        assert(binds.size()==cases.size());
#endif
    }
    std::puts("F07_SPARSE_BIND_PAGE_PARITY_PASS");
}
""".replace("__EXTRACTED__", loop)
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="f07-sparse-merge-") as temp:
    unit = Path(temp) / "binds.cpp"
    unit.write_text(cpp)
    for native in (False, True):
        for opt in ("-O0", "-O2"):
            binary = Path(temp) / (("native" if native else "desktop")+opt)
            command = [compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                       "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                       *(["-DPS5_NATIVE=1"] if native else []),str(unit),"-o",str(binary)]
            built=subprocess.run(command,capture_output=True,text=True,timeout=50)
            assert built.returncode==0,(native,opt,built.stderr[-5000:])
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,(native,opt,run.stdout,run.stderr[-5000:])
            print("F07_SPARSE_BIND_PHYSICAL_PARITY_PASS",int(native),opt)
print("HOST_ONLY: GPU allocation and FPS are not measured")
