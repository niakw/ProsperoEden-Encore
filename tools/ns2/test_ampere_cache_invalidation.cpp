// SPDX-License-Identifier: GPL-3.0-or-later
// Deterministic race regression: invalidation during a native shader translation.
#include <array>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <thread>
#include "shader_recompiler/frontend/ampere/translation_cache.h"

namespace {
std::mutex gate_mutex;
std::condition_variable gate;
bool entered = false;
bool release = false;
void Check(bool cond, const char* why) {
    if (!cond) { std::fprintf(stderr, "NS2 cache race FAIL: %s\n", why); std::exit(1); }
}
}
namespace Shader::Ampere {
// Test link replaces real lowering only to make a Clear-vs-translation race deterministic.
MaxwellShaderImage BuildMaxwellShaderImage(std::span<const u8>,std::span<const u8>,u32) {
    {
        std::unique_lock lock{gate_mutex};
        entered = true;
        gate.notify_all();
        gate.wait(lock, [] { return release; });
    }
    MaxwellShaderImage image;
    image.status = MaxwellImageStatus::Ready;
    image.code = {0x50,0x58};
    return image;
}
}
int main() {
    using namespace Shader::Ampere;
    NativeTranslationCache cache{1024*1024,2};
    std::array<u8,0x50> header{};
    std::array<u8,16> native{};
    MaxwellShaderImage stale;
    std::thread worker([&] { stale = cache.GetOrTranslate(header,native,3); });
    {
        std::unique_lock lock{gate_mutex};
        gate.wait(lock, [] { return entered; });
    }
    cache.Clear();
    {
        std::lock_guard lock{gate_mutex};
        release=true;
    }
    gate.notify_all();
    worker.join();
    const auto after=cache.Stats();
    Check(!stale.Ready() && after.entries==0 && after.bytes==0 &&
          after.invalidations==1 && after.invalidated_translations==1,
          "Clear must discard in-flight translation from prior generation");
    auto fresh=cache.GetOrTranslate(header,native,3);
    auto reused=cache.GetOrTranslate(header,native,3);
    const auto final=cache.Stats();
    Check(fresh.Ready() && reused.Ready() && final.entries==1 &&
          final.translations==2 && final.hits==1,
          "fresh generation can translate and reuse cache normally");
    std::puts("NS2 cache generation race: PASS");
}
