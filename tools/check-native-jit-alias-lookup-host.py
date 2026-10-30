#!/usr/bin/env python3
"""C++20 ASan/UBSan check for real maintained JIT RX/RW alias lookups."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
source=(root/"headless/jit-allocator.h").read_text()
assert "class AliasPositiveCache" in source
assert "static thread_local ::Eden::Jit::AliasPositiveCache cache{}" in source
assert "cache.Find(pointer, generation)" in source
assert "cache.Remember(pointer, writable, latest)" in source
assert "const std::size_t slot = ((bits >> 12)" not in source
memo = source
assert "std::array<Entry, 8>" in memo
assert "if (generation != current_generation) return nullptr;" in memo
assert source.count("mapping_generation.fetch_add(1, std::memory_order_release);")==4
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler
stub="""
#pragma once
#include <cstdint>
#include <cstddef>
namespace Xbyak {
class Allocator {
public:
 virtual ~Allocator()=default;
 virtual std::uint8_t* alloc(std::size_t)=0;
 virtual void free(std::uint8_t*)=0;
 virtual std::uint8_t* writableAddress(std::uint8_t* p){return p;}
 virtual bool useProtect() const{return true;}
};
}
"""
fixture=r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <thread>
#include "jit-allocator.h"
namespace Common {
void* AllocateMemoryPages(std::size_t n) noexcept {return std::malloc(n);}
void FreeMemoryPages(void* p) noexcept {std::free(p);}
void* MapExecutableAlias(void*, std::size_t) noexcept {return nullptr;}
}
int main(){
 auto* allocator=EdenJitAllocator();
 // PS5's 16 MiB-aligned executable arenas can all hash to the same
 // old single-slot memo entry: eight such keys must coexist, lock-free.
 Eden::Jit::AliasPositiveCache aliases;
 std::uint8_t* rx[8]{}; std::uint8_t* rw[8]{};
 for(unsigned i=0;i<8;++i){
   rx[i]=reinterpret_cast<std::uint8_t*>(0x10000000ULL+i*0x01000000ULL);
   rw[i]=reinterpret_cast<std::uint8_t*>(0x90000000ULL+i*0x01000000ULL);
   const auto bits=reinterpret_cast<std::uintptr_t>(rx[i]);
   assert(((bits>>12)^(bits>>21))%8==0);
   aliases.Remember(rx[i],rw[i],7);
 }
 for(unsigned i=0;i<100000;++i)
   assert(aliases.Find(rx[i%8],7)==rw[i%8]);
 assert(!aliases.Find(rx[0],8)); // trim/release epoch flush
 assert(aliases.Find(rx[3],7)==rw[3]);
 aliases.Remember(rx[0],rw[0],8);
 assert(aliases.Find(rx[0],8)==rw[0]);
 assert(!aliases.Find(rx[3],8));
 constexpr std::size_t size=2u*1024u*1024u;
 auto* a=allocator->alloc(size);auto* b=allocator->alloc(size);
 assert(a && b && a!=b);
 auto* aw=allocator->writableAddress(a);auto* bw=allocator->writableAddress(b);
 assert(aw && bw && aw!=a && bw!=b);
 std::memset(aw,0xA5,size);std::memset(bw,0x5A,size);
 assert(a[0]==0xA5 && a[size-1]==0xA5);
 assert(b[0]==0x5A && b[size-1]==0x5A);
 for(unsigned i=0;i<100000;++i){
  assert(allocator->writableAddress(a)==aw);
  assert(allocator->writableAddress(b)==bw);
 }
 std::thread worker([&]{
  for(unsigned i=0;i<10000;++i){
   assert(allocator->writableAddress(a)==aw);
   assert(allocator->writableAddress(b)==bw);
  }
 });worker.join();
 allocator->free(a);
 assert(allocator->writableAddress(a)==a);
 auto* c=allocator->alloc(size);assert(c);
 auto* cw=allocator->writableAddress(c);assert(cw && cw!=c);
 std::memset(cw,0x3C,size);assert(c[0]==0x3C && c[size-1]==0x3C);
 assert(allocator->writableAddress(b)==bw);
 allocator->free(c);allocator->free(b);
 assert(allocator->writableAddress(c)==c);
 assert(allocator->writableAddress(b)==b);
}
"""
with tempfile.TemporaryDirectory(prefix="eden-jit-alias-") as temp:
 d=Path(temp);(d/"xbyak").mkdir()
 (d/"xbyak/xbyak.h").write_text(stub)
 (d/"witness.cpp").write_text(fixture)
 exe=d/"witness"
 subprocess.run([compiler,"-std=c++20","-O1","-g","-pthread","-Wall","-Wextra",
  "-Werror","-fsanitize=address,undefined","-fno-sanitize-recover=all",
  "-I",str(d),"-I",str(root/"headless"),str(d/"witness.cpp"),"-o",str(exe)],
  check=True,timeout=90)
 subprocess.run([str(exe)],check=True,timeout=90)
print("JIT_ALIAS_LOOKUP_HOST_PASS real_rx_rw=1 alternating=1 collision8=1 epoch=1 retirement=1 sanitizer=1")
