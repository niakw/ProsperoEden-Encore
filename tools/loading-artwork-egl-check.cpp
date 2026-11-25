// SPDX-License-Identifier: GPL-3.0-or-later
// Isolated desktop Mesa test of the actual title-artwork producer/presenter.
#define GL_GLEXT_PROTOTYPES 1
#include <EGL/egl.h>
#include "loading_artwork_gl.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <vector>

extern "C" bool LoadingMockGladDraw(int width, int height, double seconds);

namespace {
constexpr int W = 960, H = 540;
using Pixel = std::array<std::uint8_t, 4>;
constexpr Pixel red{255, 0, 0, 255}, green{0, 255, 0, 255};
constexpr Pixel blue{0, 0, 255, 255}, yellow{255, 255, 0, 255};
constexpr Pixel cyan{0, 255, 255, 255};

void Expect(const Pixel& a, const Pixel& b, int tolerance = 2) {
    for (std::size_t c = 0; c < a.size(); ++c) {
        if (std::abs(int(a[c]) - int(b[c])) > tolerance) {
            std::cerr << "unexpected pixel channel " << c << " actual=" << int(a[c])
                      << " expected=" << int(b[c]) << '\n';
            std::abort();
        }
    }
}

Pixel Read(int x, int y) {
    Pixel pixel{};
    glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel.data());
    assert(glGetError() == GL_NO_ERROR);
    return pixel;
}

void Paint(int w, int h) {
    // Deliberately asymmetric, exact corner colors. OpenGL's origin is at
    // the bottom, but the shared frame and Vulkan upload are top-row-first.
    glEnable(GL_SCISSOR_TEST);
    auto rect = [&](int x, int y, float r, float g, float b) {
        glScissor(x, y, w/2, h/2);
        glClearColor(r, g, b, 1.f);
        glClear(GL_COLOR_BUFFER_BIT);
    };
    rect(0, h/2, 1, 0, 0);
    rect(w/2, h/2, 0, 1, 0);
    rect(0, 0, 0, 0, 1);
    rect(w/2, 0, 1, 1, 0);
}

void PaintAtlas(int w,int h) {
    assert(w==Eden::LoadingCase::kAtlasWidth && h==Eden::LoadingCase::kAtlasHeight);
    glEnable(GL_SCISSOR_TEST);
    auto rect=[&](int x,int width,float r,float g,float b){
        glScissor(x,0,width,h);glClearColor(r,g,b,1.0f);glClear(GL_COLOR_BUFFER_BIT);
    };
    rect(0,960,1,0,1);     // front, magenta
    rect(960,960,0,1,1);   // back, cyan
    rect(1920,128,1,1,1);  // spine, white
}

Eden::LoadingCase::Scene Scene(bool calm=false) {
    using namespace Eden::LoadingCase;
    Eden::LoadingCase::Scene s;
    s.reduce_motion=calm;
    for(unsigned pose=0;pose<4;++pose) {
        const bool back=pose>=2;
        Quad face;
        face.values={381,139,440,704, 1,1,1,1, 1,1,1,1, 0,0,0,0,
                     kTemplateYaw[pose],back?1.0f:0.0f,1,9, 0,0,1,1};
        face.slot=back?2u:1u;
        s.poses[pose].push_back(face);
        Quad side=face;
        side.values[17]=44.0f;
        side.values[18]=0.0f;
        side.values[19]=14.0f;
        side.slot=3;
        s.poses[pose].push_back(side);
    }
    return s;
}

void ExpectCorners() {
    Expect(Read(40,H-40),red);
    Expect(Read(W-40,H-40),green);
    Expect(Read(40,40),blue);
    Expect(Read(W-40,40),yellow);
}

std::vector<std::uint8_t> ReadFrame() {
    std::vector<std::uint8_t> pixels(std::size_t(W)*H*4);
    glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    assert(glGetError() == GL_NO_ERROR);
    return pixels;
}
}
int main() {
    namespace artwork = Eden::LoadingArtwork;
    namespace handoff = Eden::LaunchHandoff;
    const EGLDisplay display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    assert(display != EGL_NO_DISPLAY);
    assert(eglInitialize(display, nullptr, nullptr));
    assert(eglBindAPI(EGL_OPENGL_API));
    const EGLint cfg[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
        EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE
    };
    EGLConfig config{};
    EGLint count = 0;
    assert(eglChooseConfig(display,cfg,&config,1,&count) && count == 1);
    const EGLint pb[] = {EGL_WIDTH,W,EGL_HEIGHT,H,EGL_NONE};
    const EGLSurface surface = eglCreatePbufferSurface(display,config,pb);
    assert(surface != EGL_NO_SURFACE);
    const EGLContext first = eglCreateContext(display,config,EGL_NO_CONTEXT,nullptr);
    assert(first != EGL_NO_CONTEXT);
    assert(eglMakeCurrent(display,surface,surface,first));
    handoff::Clear();
    glViewport(3, 4, W-6, H-8);
    glEnable(GL_SCISSOR_TEST);
    glPixelStorei(GL_PACK_ALIGNMENT, 8);
    glPixelStorei(GL_PACK_ROW_LENGTH, 17);
    glPixelStorei(GL_PACK_SKIP_ROWS, 2);
    glPixelStorei(GL_PACK_SKIP_PIXELS, 3);
    assert(artwork::Capture(Paint));
    assert(artwork::Capture(PaintAtlas,true,Eden::LoadingCase::kAtlasWidth,Eden::LoadingCase::kAtlasHeight));
    handoff::PublishCase(Scene());
    assert(handoff::PeekCase());
    const auto alternate = handoff::PeekAlternate();
    assert(alternate && handoff::Valid(*alternate));
    GLint state[4]{};
    glGetIntegerv(GL_VIEWPORT,state);
    assert(state[0]==3 && state[1]==4 && state[2]==W-6 && state[3]==H-8);
    assert(glIsEnabled(GL_SCISSOR_TEST));
    glGetIntegerv(GL_PACK_ALIGNMENT,state); assert(state[0]==8);
    glGetIntegerv(GL_PACK_ROW_LENGTH,state); assert(state[0]==17);
    glGetIntegerv(GL_PACK_SKIP_ROWS,state); assert(state[0]==2);
    glGetIntegerv(GL_PACK_SKIP_PIXELS,state); assert(state[0]==3);
    assert(glGetError()==GL_NO_ERROR);
    glPixelStorei(GL_PACK_ALIGNMENT,1);
    glPixelStorei(GL_PACK_ROW_LENGTH,0);
    glPixelStorei(GL_PACK_SKIP_ROWS,0);
    glPixelStorei(GL_PACK_SKIP_PIXELS,0);

    const auto frame=handoff::Peek();
    assert(frame && handoff::Valid(*frame));
    assert(frame->width==1920 && frame->height==1080);
    auto at=[&](std::uint32_t x,std::uint32_t y) {
        const auto i=(std::size_t(y)*frame->width+x)*4;
        return Pixel{frame->rgba[i],frame->rgba[i+1],frame->rgba[i+2],frame->rgba[i+3]};
    };
    Expect(at(480,270),red); Expect(at(1440,270),green);
    Expect(at(480,810),blue); Expect(at(1440,810),yellow);

    // Two independent contexts model launcher -> new game GL context.
    artwork::GlPresenter launcher;
    assert(launcher.Draw(W,H,1.0));
    ExpectCorners();
    Expect(Read(300,295),Pixel{255,0,255,255});
    const auto initial = ReadFrame();
    launcher.Release();
    assert(LoadingMockGladDraw(W,H,1.0));
    ExpectCorners();
    assert(ReadFrame()==initial);
    assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT));
    assert(eglDestroyContext(display,first));
    const EGLContext second=eglCreateContext(display,config,EGL_NO_CONTEXT,nullptr);
    assert(second!=EGL_NO_CONTEXT);
    assert(eglMakeCurrent(display,surface,surface,second));
    artwork::GlPresenter game;
    assert(game.Draw(W,H,1.0));
    ExpectCorners();
    assert(ReadFrame()==initial);
    assert(game.Draw(W,H,1.4));
    const auto next=ReadFrame();
    std::size_t animated=0;
    for(int y=0;y<H;++y) for(int x=0;x<W;++x) {
        auto i=(std::size_t(y)*W+x)*4;
        if(!std::equal(initial.begin()+i,initial.begin()+i+4,next.begin()+i)) {
            // Only the three dots may change, not the title artwork.
            assert(x>=673 && x<=707 && y>=177 && y<=187);
            ++animated;
        }
    }
    assert(animated>0);
    // The 3D case changes projection, never the 2D scene. The rear stays
    // readable for the entire original 4.50 second hold.
    assert(game.Draw(W,H,2.55));
    const auto turning=ReadFrame();
    assert(turning!=initial);
    ExpectCorners();
    assert(game.Draw(W,H,3.0));
    Expect(Read(300,295),cyan);
    ExpectCorners();
    assert(game.Draw(W,H,7.35));
    Expect(Read(300,295),cyan);
    ExpectCorners();
    assert(game.Draw(W,H,8.5));
    Expect(Read(300,295),Pixel{255,0,255,255});
    game.Release();
    handoff::PublishCase(Scene(true));
    artwork::GlPresenter calm_game;
    assert(calm_game.Draw(W,H,1001.0));
    const auto calm=ReadFrame();
    assert(calm_game.Draw(W,H,1005.0));
    assert(ReadFrame()==calm);
    calm_game.Release();
    game.Release();
    handoff::Clear();
    assert(!handoff::Peek());
    assert(!handoff::PeekAlternate());
    assert(!handoff::PeekCase());
    artwork::GlPresenter missing;
    assert(missing.Draw(W,H,1.0));
    Expect(Read(W/4,H/4),Pixel{14,19,27,255});
    missing.Release();
    assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT));
    assert(eglDestroyContext(display,second));
    assert(eglDestroySurface(display,surface));
    assert(eglTerminate(display));
    std::cout << "ENCORE_LOADING_ARTWORK_MESA_PIXELS_PASS independent_contexts=2 top_row=1 animated_pixels="
              << animated << " native_3d=1 back_hold=4.5 reduced_motion=1 neutral_fallback=1\n";
}
