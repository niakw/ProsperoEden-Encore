// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only test shim, never used by Encore release.
#include <cstdlib>
#include <cstdio>
#include "common/logging.h"
void AssertFailSoftImpl(){std::fputs("NS2 shim AssertFailSoftImpl\n",stderr);std::abort();}
void AssertFatalImpl(){std::fputs("NS2 shim AssertFatalImpl\n",stderr);std::abort();}
namespace Common::Log {
void FmtLogMessageImpl(Class,Level,const char*,unsigned,const char*,
                       fmt::string_view message,const fmt::format_args&){
    std::fprintf(stderr,"NS2 shim log: %.*s\n",(int)message.size(),message.data());
}
}
