#include "settings_store.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <unistd.h>
static std::string Read(const char* path) {
 std::ifstream f(path);
 return {std::istreambuf_iterator<char>(f),{}};
}
int main() {
 char f[]="/tmp/eden-fg-preferences-XXXXXX";
 const int fd=mkstemp(f); assert(fd>=0); close(fd);
 Eden::Preferences p = Eden::LoadPreferences(f);
 assert(p.frame_generation==0);
 p.frame_generation=1;
 assert(Eden::SavePreferences(p,f));
 assert(Eden::LoadPreferences(f).frame_generation==1);
 assert(Read(f).find("\"frame_generation\": \"mihawkgen\"")!=std::string::npos);
 p.frame_generation=2;
 assert(Eden::SavePreferences(p,f));
 assert(Eden::LoadPreferences(f).frame_generation==2);
 p.frame_generation=3;
 assert(Eden::SavePreferences(p,f));
 assert(Eden::LoadPreferences(f).frame_generation==3);
 p.frame_generation=4;
 assert(!Eden::SavePreferences(p,f));
 assert(Eden::LoadPreferences(f).frame_generation==3);
 constexpr auto tid=0x0100000000010000ull;
 Eden::GameSettings g=Eden::LoadGameSettings(tid,f);
 assert(g.frame_generation==-1);
 g.frame_generation=0;
 assert(Eden::SaveGameSettings(tid,g,f));
 assert(Eden::LoadGameSettings(tid,f).frame_generation==0);
 g.frame_generation=1;
 assert(Eden::SaveGameSettings(tid,g,f));
 assert(Eden::LoadGameSettings(tid,f).frame_generation==1);
 g.frame_generation=2;
 assert(Eden::SaveGameSettings(tid,g,f));
 assert(Eden::LoadGameSettings(tid,f).frame_generation==2);
 g.frame_generation=3;
 assert(Eden::SaveGameSettings(tid,g,f));
 assert(Eden::LoadGameSettings(tid,f).frame_generation==3);
 g.frame_generation=4;
 assert(!Eden::SaveGameSettings(tid,g,f));
 g.frame_generation=-1;
 assert(Eden::SaveGameSettings(tid,g,f));
 assert(Eden::LoadGameSettings(tid,f).frame_generation==-1);
 const std::string unknown=std::string(f)+".unknown";
 std::ofstream(unknown)<<R"({"video":{"frame_generation":"bogus"},"games":{"0100000000010000":{"frame_generation":"bogus"}}})";
 assert(Eden::LoadPreferences(unknown).frame_generation==0);
 assert(Eden::LoadGameSettings(tid,unknown).frame_generation==-1);
 std::remove(f);
 std::remove(unknown.c_str());
}
