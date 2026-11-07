// SPDX-License-Identifier: GPL-3.0-or-later
#include "in_game_overlay_style.h"
#include <cassert>
#include <cstdint>
#include <set>
using namespace Eden::QuickOverlay;
int main() {
    std::set<std::uint32_t> seen;
    for (int palette=0;palette<4;++palette)
      for (int accent=0;accent<5;++accent)
        for (int contrast=0;contrast<2;++contrast) {
            const auto id=StyleId(palette,accent,contrast!=0,false);
            assert(id<40u && seen.insert(id).second);
            for(const auto primitive:{kBackdrop,kRow,kSelectedRow,kWarningRow}){
                const auto tag=StyledMode(primitive,id);
                assert(IsQuickMode(tag));
                assert(((tag>>8u)&63u)==id);
                assert((tag&kKindMask)==(primitive&kKindMask));
            }
        }
    assert(seen.size()==40u);
    assert(StyleId(3,4,false,true)==StyleId(0,4,false,false));
    assert(StyleId(-99,100,false,false)==StyleId(0,4,false,false));
    assert(StyleId(99,-5,true,false)==StyleId(3,0,true,false));
    assert(!IsQuickMode(0u));
    assert(!IsQuickMode(48000u));
    assert(!IsQuickMode(0xfffffff4u));
}
