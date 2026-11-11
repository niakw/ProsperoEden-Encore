#!/usr/bin/env python3
"""R23 AM #84/#109: exact full-source proof and mock-compiled Exit() semantics.
Only E1 and host-sanitizer evidence, not native PS5 core or game execution.
"""
from pathlib import Path
import hashlib, os, subprocess, tempfile
root=Path(__file__).resolve().parents[2]
base=root/"vendor/sources/eden/src/core/hle/service/am"
orig_front=base/"frontend/applets.cpp"
orig_creator=base/"service/library_applet_creator.cpp"
new_front=root/"headless/r23_am_frontend_applets_ps5.cpp"
new_creator=root/"vendor/encore-active/eden-backports/src/core/hle/service/am/service/library_applet_creator.cpp"
def gitblob(path):
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
assert gitblob(orig_front)=="407ca10602a1fe9107d13aa8393f4145ac7d715a"
assert gitblob(orig_creator)=="c20a77f8c40c7fbf023411fd47a299662b798cb3"
old=orig_front.read_text()
new=new_front.read_text()
old_exit="""void FrontendApplet::Exit() {
    auto applet_ = applet.lock();

    std::scoped_lock lk{applet_->lock};
    applet_->is_completed = true;
    applet_->state_changed_event.Signal(system.Kernel());
}"""
new_exit="""void FrontendApplet::Exit() {
    auto applet_ = applet.lock();
    {
        std::scoped_lock lk{applet_->lock};
        applet_->is_completed = true;
        applet_->state_changed_event.Signal(system.Kernel());
    }
    if (auto caller_applet = applet_->caller_applet.lock()) {
        std::scoped_lock lk{caller_applet->lock};
        std::erase(caller_applet->child_applets, applet_);
    }
    if (auto* window_system = system.GetAppletManager().GetWindowSystem()) window_system->RequestUpdate();
}"""
assert old.count(old_exit)==1
assert new.count(new_exit)==1
expected=old.replace('#include "core/hle/service/am/service/storage.h"\n',
                     '#include "core/hle/service/am/service/storage.h"\n#include "core/hle/service/am/window_system.h"\n')
expected=expected.replace(old_exit,new_exit)
expected=expected.replace("    default:\n        LOG_ERROR(Service_AM,",
                          "    case AppletId::None:\n        return nullptr;\n    default:\n        LOG_ERROR(Service_AM,")
assert expected==new, "AM frontend full TU differs beyond #84/#109"
assert new.count("case AppletId::None:\n        return nullptr;")==1
assert "return std::make_shared<StubApplet>(system, applet, id, mode);" in new
target=new_creator.read_text()
assert gitblob(new_creator)=="4ee92908b539c2ee1aad04b38523a297689ce016"
assert '#include "core/hle/api_version.h"' in target
assert "CreateProcess(system, program_id, 1, HLE::ApiVersion::HOS_VERSION_MAJOR)" in target
assert target.count("std::scoped_lock lk{caller_applet->lock};")==2
cm=(root/"headless/CMakeLists.txt").read_text()
assert "r23_am_frontend_applets_ps5.cpp" in cm
assert "r23_am_library_applet_creator_ps5.cpp" not in cm
assert 'src/core/hle/service/am/service/library_applet_creator.cpp' in cm
assert 'R23 #84 frontend core owner moved' in cm
print("R23_AM_ONE_FRONTEND_PLUS_SHIPPING_FW23_CREATOR_PASS")
cpp=r"""
#include <algorithm>
#include <cassert>
#include <memory>
#include <mutex>
#include <vector>
namespace Core {
struct KernelCore {};
struct WindowSystem {unsigned calls=0; void RequestUpdate(){++calls;}};
struct AppletManager {
 WindowSystem* ws{};
 WindowSystem* GetWindowSystem(){return ws;}
};
struct System {
 KernelCore kernel;
 AppletManager app;
 KernelCore& Kernel(){return kernel;}
 AppletManager& GetAppletManager(){return app;}
};
}
namespace Service::AM::Frontend {
struct Applet {
 std::mutex lock;
 bool is_completed{};
 std::weak_ptr<Applet> caller_applet;
 std::vector<std::shared_ptr<Applet>> child_applets;
 struct Event {unsigned signals=0;void Signal(Core::KernelCore&){++signals;}} state_changed_event;
};
struct FrontendApplet {
 Core::System& system;
 std::weak_ptr<Applet> applet;
 FrontendApplet(Core::System& s,std::shared_ptr<Applet> a):system(s),applet(a){}
 void Exit();
};
""" + new_exit + r"""
}
int main(){
 using namespace Service::AM::Frontend;
 Core::System sys;
 Core::WindowSystem ws; sys.app.ws=&ws;
 auto parent=std::make_shared<Applet>();
 for(int i=0;i<50;++i){
  auto child=std::make_shared<Applet>();
  child->caller_applet=parent;
  {std::scoped_lock lk(parent->lock);parent->child_applets.push_back(child);}
  FrontendApplet f(sys,child);
  f.Exit();
  assert(child->is_completed&&child->state_changed_event.signals==1);
  assert(parent->child_applets.empty());
 }
 assert(ws.calls==50);
 sys.app.ws=nullptr;
 auto detached=std::make_shared<Applet>();
 FrontendApplet f(sys,detached);
 f.Exit();
 assert(detached->is_completed&&detached->state_changed_event.signals==1);
 assert(ws.calls==50);
}
"""
with tempfile.TemporaryDirectory(prefix="r23-am-") as td:
    path=Path(td)/"case.cpp"
    binary=Path(td)/"case"
    path.write_text(cpp)
    subprocess.run(["clang++","-std=c++20","-O1","-g","-Wall","-Wextra","-Werror",
                    "-fsanitize=address,undefined","-fno-omit-frame-pointer",
                    str(path),"-o",str(binary)],check=True)
    subprocess.run([str(binary)],check=True,env={**os.environ,"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})
print("R23_AM_EXTRACTED_EXIT_ASAN_UBSAN_PASS 50_cycles guest_not_tested=1")
