#!/usr/bin/env python3
"""P1: real NVMap pin-refcount release under malformed/double unpin."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vroot=root/'vendor'
if not (vroot/'encore-active').exists(): vroot=root.parent/'vendor'
owner=(vroot/'encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp').read_text()
start='void NvMap::UnpinHandle(Handle::Id handle) {'
end='\nvoid NvMap::DuplicateHandle('
assert owner.count(start)==owner.count(end)==1
body=owner[owner.index(start):owner.index(end,owner.index(start))]
assert 'if (handle_description->pins <= 0)' in body
assert body.index('if (handle_description->pins <= 0)') < body.index('--handle_description->pins;')
assert 'if (!handle_description->unmap_queue_entry)' in body
assert 'if (--handle_description->pins < 0)' not in body
assert 'if (handle_description->internal_dupes <= 0)' in owner
assert 'if (handle_description->dupes <= 0)' in owner
assert 'return std::nullopt;' in owner
assert 'if (--handle_description->dupes == 0)' in owner

fixture=r'''
#include <cassert>
#include <cstdint>
#include <list>
#include <memory>
#include <mutex>
#include <optional>
#include <unordered_map>
#define LOG_WARNING(...) ((void)0)
struct NvMap {
 struct Handle {
  using Id=std::uint32_t;
  Id id{};
  std::mutex mutex;
  std::int64_t pins{};
  std::optional<std::list<std::shared_ptr<Handle>>::iterator> unmap_queue_entry{};
 };
 std::unordered_map<Handle::Id,std::shared_ptr<Handle>> handles;
 std::list<std::shared_ptr<Handle>> unmap_queue;
 std::mutex unmap_queue_lock;
 std::shared_ptr<Handle> GetHandle(Handle::Id id) {
  auto it=handles.find(id);
  return it!=handles.end()?it->second:nullptr;
 }
 void UnpinHandle(Handle::Id id);
};
__REAL_UNPIN__
int main(){
 NvMap n;
 n.UnpinHandle(44);
 auto h=std::make_shared<NvMap::Handle>();h->id=1;n.handles.emplace(1,h);
 n.UnpinHandle(1);
 assert(h->pins==0 && n.unmap_queue.empty());
 h->pins=2;
 n.UnpinHandle(1);
 assert(h->pins==1 && n.unmap_queue.empty());
 n.UnpinHandle(1);
 assert(h->pins==0 && n.unmap_queue.size()==1 && h->unmap_queue_entry);
 auto iter=*h->unmap_queue_entry;
 n.UnpinHandle(1);
 assert(h->pins==0 && n.unmap_queue.size()==1 && *h->unmap_queue_entry==iter);
 n.unmap_queue.erase(iter);h->unmap_queue_entry.reset();
 h->pins=1;n.UnpinHandle(1);
 assert(h->pins==0 && n.unmap_queue.size()==1);
 n.UnpinHandle(1);
 assert(h->pins==0 && n.unmap_queue.size()==1);
}
'''.replace('__REAL_UNPIN__',body)
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-nvmap-refs-') as folder:
    source=Path(folder)/'refs.cpp';source.write_text(fixture)
    for compiler in compilers:
        for optimization in ('-O0','-O2'):
            exe=Path(folder)/(Path(compiler).name+optimization)
            cmd=[compiler,'-std=c++20',optimization,'-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',str(source),'-o',str(exe)]
            run=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=80)
            assert run.returncode==0,(cmd,run.stderr[-2000:])
            check=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=15)
            assert check.returncode==0,(cmd,check.stderr[-2000:])
            print(Path(compiler).name,optimization,'P1_NVDRV_REAL_UNPIN_REFS_PASS',flush=True)
print('P1_NVDRV_PIN_REFCOUNT_OWNER_PASS unknown=refused double_unpin=preserved queue_once=1 free_refs_guarded=1')
