// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include "video_core/renderer_vulkan/ns2_view_type_guard.h"
enum class MockView { OneD, TwoD, TwoDArray, Cube, ThreeD };
int main() {
    using Eden::NS2::Vulkan::CrossDimensionView;
    for (auto actual : {MockView::OneD, MockView::TwoD, MockView::TwoDArray, MockView::Cube}) {
        if (!CrossDimensionView(actual, MockView::ThreeD, MockView::ThreeD)) std::abort();
        if (CrossDimensionView(actual, MockView::TwoD, MockView::ThreeD)) std::abort();
    }
    if (!CrossDimensionView(MockView::ThreeD, MockView::TwoD, MockView::ThreeD)) std::abort();
    if (CrossDimensionView(MockView::ThreeD, MockView::ThreeD, MockView::ThreeD)) std::abort();
    std::puts("N49_EGLANTINE_VIEW_DIMENSION_PASS (host-only)");
}
