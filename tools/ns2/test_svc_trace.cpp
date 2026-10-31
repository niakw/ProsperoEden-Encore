// SPDX-License-Identifier: GPL-3.0-or-later
// Bounded SVC dispatch tracing. This host test does NOT run production HLE.
#include <cassert>
#include <cstdint>
#include "core/loader/ns2_svc_trace.h"

int main() {
    using namespace Eden::NS2::SvcTrace;
    assert(!Next(7).has_value()); // no active process before actual load
    Register(7);
    assert(!Next(0).has_value() && !Next(8).has_value());
    for (std::uint32_t i = 1; i <= MaxSamples; ++i) {
        const auto sample = Next(7);
        assert(sample.has_value() && *sample == i);
    }
    assert(!Next(7).has_value());
    Register(9);
    assert(!Next(7).has_value());
    assert(Next(9).value() == 1);
    Register(0);
    assert(!Next(0).has_value() && !Next(9).has_value());
}
