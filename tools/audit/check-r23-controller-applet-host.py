#!/usr/bin/env python3
"""R23 #131: verify exact pinned source + extracted real function under mock HID.
No PS5 compile, linked guest service, device test or physical controller proof.
"""
from pathlib import Path
import hashlib, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "vendor/sources/eden/src/core/frontend/applets/controller.cpp"
NEW = ROOT / "headless/r23_controller_applet_ps5.cpp"

def blob(p):
    b = p.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

assert blob(OLD) == "c4292c5a1257dbfb18c3709d4911193caf2ed5b6"
assert blob(NEW) == "e535866855cb3b87b95efdc5369d7fdb5752b235"
old, new = OLD.read_text(), NEW.read_text()
assert "keep_connected[index]" not in old
assert "if (keep_connected[index]) continue;" in new
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
for marker in ('eden_r23_controller_original "frontend/applets/controller.cpp"',
               'r23_controller_applet_ps5.cpp', 'list(FIND eden_r23_controller_sources',
               'list(REMOVE_ITEM eden_r23_controller_sources',
               'set_property(TARGET core PROPERTY SOURCES'):
    assert marker in cmake, marker
marker = "void DefaultControllerApplet::ReconfigureControllers("
assert new.count(marker) == 1
start = new.index(marker)
opening = new.index("{", start)
depth, end = 0, None
for pos in range(opening, len(new)):
    if new[pos] == "{": depth += 1
    if new[pos] == "}":
        depth -= 1
        if depth == 0:
            end = pos + 1
            break
assert end is not None
actual_method = new[start:end]
fixture = r"""
#include <array>
#include <cassert>
#include <cstddef>
#include <functional>
#include <iostream>
#define LOG_INFO(...) ((void)0)
#define ASSERT_MSG(condition, ...) assert(condition)
namespace Settings { bool docked = false; bool IsDockedMode() {return docked;} }
namespace Core::HID {
enum class NpadStyleIndex { Fullkey, JoyconDual, JoyconLeft, JoyconRight, Handheld, GameCube };
enum class NpadIdType { Handheld };
struct Pad {
  bool connected = false;
  NpadStyleIndex style = NpadStyleIndex::Fullkey;
  unsigned disconnects = 0, connects = 0;
  bool IsConnected() const { return connected; }
  NpadStyleIndex GetNpadStyleIndex() const { return style; }
  void Disconnect(){ ++disconnects; connected = false; }
  void SetNpadStyleIndex(NpadStyleIndex s){ style = s; }
  void Connect(bool){ ++connects; connected = true; }
};
struct HIDCore {
  static constexpr std::size_t available_controllers = 10;
  std::array<Pad, available_controllers> pads{};
  Pad* GetEmulatedController(NpadIdType) { return &pads[8]; }
  Pad* GetEmulatedControllerByIndex(std::size_t i) { return &pads.at(i); }
  const Pad* GetEmulatedControllerByIndex(std::size_t i) const { return &pads.at(i); }
};
}
namespace Core::Frontend {
struct ControllerParameters {
  int min_players = 0, max_players = 0;
  bool keep_controllers_connected = false, enable_single_mode = false;
  bool allow_pro_controller = false, allow_handheld = false, allow_dual_joycons = false;
  bool allow_left_joycon = false, allow_right_joycon = false;
  bool allow_gamecube_controller = false;
};
class DefaultControllerApplet {
public:
  HID::HIDCore& hid_core;
  using ReconfigureCallback = std::function<void(bool)>;
  explicit DefaultControllerApplet(HID::HIDCore& h):hid_core(h){}
  void ReconfigureControllers(ReconfigureCallback, const ControllerParameters&) const;
};
"""
fixture += actual_method + "\n}\n"
fixture += r"""
int main() {
  using namespace Core;
  using namespace Core::Frontend;
  using HID::NpadStyleIndex;
  {
    HID::HIDCore h; h.pads[0].connected = h.pads[1].connected = true;
    DefaultControllerApplet a(h); ControllerParameters p;
    p.keep_controllers_connected=true; p.min_players=1; p.max_players=3; p.allow_pro_controller=true;
    bool cb=false; a.ReconfigureControllers([&](bool v){cb=v;},p);
    assert(cb && h.pads[0].connected && h.pads[1].connected);
    assert(h.pads[0].disconnects==0 && h.pads[1].disconnects==0);
  }
  {
    HID::HIDCore h; h.pads[2].connected=true;
    DefaultControllerApplet a(h); ControllerParameters p;
    p.min_players=2; p.max_players=4; p.allow_pro_controller=true;
    a.ReconfigureControllers([](bool v){assert(v);},p);
    assert(h.pads[0].connected && h.pads[1].connected && !h.pads[2].connected);
    assert(h.pads[2].disconnects==1);
  }
  {
    HID::HIDCore h; h.pads[0].connected=true; h.pads[0].style=NpadStyleIndex::JoyconDual;
    DefaultControllerApplet a(h); ControllerParameters p;
    p.keep_controllers_connected=true; p.min_players=1; p.max_players=1; p.allow_pro_controller=true;
    a.ReconfigureControllers([](bool v){assert(v);},p);
    assert(h.pads[0].connected && h.pads[0].style==NpadStyleIndex::Fullkey);
    assert(h.pads[0].disconnects==1 && h.pads[0].connects==1);
  }
  {
    HID::HIDCore h; h.pads[0].connected=h.pads[1].connected=true;
    DefaultControllerApplet a(h); ControllerParameters p;
    p.keep_controllers_connected=true; p.min_players=1; p.max_players=1; p.allow_pro_controller=true;
    a.ReconfigureControllers([](bool v){assert(v);},p);
    assert(h.pads[0].connected && h.pads[0].disconnects==0);
    assert(!h.pads[1].connected && h.pads[1].disconnects==1);
  }
  {
    HID::HIDCore h; h.pads[8].connected=true; h.pads[8].style=NpadStyleIndex::Handheld;
    DefaultControllerApplet a(h); ControllerParameters p;
    p.enable_single_mode=true; p.keep_controllers_connected=true;
    p.min_players=1; p.max_players=1; p.allow_handheld=true;
    a.ReconfigureControllers([](bool v){assert(v);},p);
    assert(h.pads[8].connected && h.pads[8].disconnects==0);
  }
  {
    HID::HIDCore h; h.pads[8].connected=true; h.pads[8].style=NpadStyleIndex::Handheld;
    DefaultControllerApplet a(h); ControllerParameters p;
    p.enable_single_mode=true; p.keep_controllers_connected=true; p.allow_pro_controller=true;
    p.min_players=1; p.max_players=1; p.allow_handheld=true;
    Settings::docked=true;
    a.ReconfigureControllers([](bool v){assert(v);},p);
    assert(!h.pads[8].connected && h.pads[8].disconnects==1);
  }
  std::cout << "R23_CONTROLLER_EXTRACTED_HID_ASAN_PASS\n";
}
"""
with tempfile.TemporaryDirectory(prefix="r23-controller-") as temp:
    path = Path(temp)/"test.cpp"
    exe = Path(temp)/"test"
    path.write_text(fixture)
    subprocess.run(["clang++","-std=c++20","-O1","-g","-Wall","-Wextra",
        "-fsanitize=address,undefined","-fno-omit-frame-pointer",
        str(path),"-o",str(exe)], check=True)
    subprocess.run([str(exe)],check=True)
print("R23_CONTROLLER_FULL_SOURCE_PIN_CMAKE_OWNER_PASS")
