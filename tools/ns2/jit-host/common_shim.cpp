// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only test shim, never used by Encore release.
#include <cstdlib>
#include "common/logging.h"
void AssertFailSoftImpl(){std::abort();}
void AssertFatalImpl(){std::abort();}
namespace Common::Log {
void FmtLogMessageImpl(Class,Level,const char*,unsigned,const char*,
                       fmt::string_view,const fmt::format_args&){}
}
