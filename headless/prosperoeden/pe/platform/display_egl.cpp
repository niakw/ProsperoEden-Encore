// ProsperoEden - EGL display and OpenGL 4.6 Core context.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later
//
// The launcher needs colour only (no depth or stencil): the same surface
// configuration the game window asks for.

#include "pe/platform/display_egl.hpp"

#include "pe/core/log.hpp"

#include <EGL/eglext.h>
#include <GL/glcorearb.h>
#include <mutex>
#include <utility>
#include <ps5_opengl_display.h>
#if __has_include(<ps5_opengl_display_modes.h>)
#include <ps5_opengl_display_modes.h> // runtime display modes (one SDK for every TV)
#endif

namespace pe::ps5
{

namespace
{

constexpr EGLint kConfigAttributes[] = {
    EGL_SURFACE_TYPE,
    EGL_WINDOW_BIT,
    EGL_RENDERABLE_TYPE,
    EGL_OPENGL_BIT,
    EGL_RED_SIZE,
    8,
    EGL_GREEN_SIZE,
    8,
    EGL_BLUE_SIZE,
    8,
    EGL_ALPHA_SIZE,
    8,
    EGL_NONE,
};

constexpr EGLint kContextAttributes[] = {
    EGL_CONTEXT_MAJOR_VERSION_KHR,
    4,
    EGL_CONTEXT_MINOR_VERSION_KHR,
    6,
    EGL_CONTEXT_OPENGL_PROFILE_MASK_KHR,
    EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT_KHR,
    EGL_NONE,
};

const char *gl_string(GLenum name)
{
    const auto *value = reinterpret_cast<const char *>(glGetString(name));
    return value != nullptr ? value : "(null)";
}

// Exactly one fullscreen VideoOut owner is handed from the launcher to a
// game at a time. Keeping EGL initialized leaves its last registered buffer
// scanning out; the Vulkan renderer explicitly terminates it immediately
// before creating its own surface.
std::mutex deferred_display_mutex;
EGLDisplay deferred_display = EGL_NO_DISPLAY;
EGLSurface deferred_surface = EGL_NO_SURFACE;

} // namespace

Display::~Display()
{
    close();
}

void Display::fail(const char *operation)
{
    last_error_ = eglGetError();
    sys::log("egl %s failed: %s (0x%04x)", operation, egl_error_name(last_error_),
             static_cast<unsigned>(last_error_));
}

bool Display::supports_display_modes()
{
#ifdef PS5_OPENGL_DYNAMIC_DISPLAY
    return true;
#else
    return false;
#endif
}

bool Display::open(int width, int height)
{
    EGLint major = 0;
    EGLint minor = 0;
    EGLint count = 0;
    EGLConfig config = nullptr;

    display_ = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (display_ == EGL_NO_DISPLAY)
    {
        fail("eglGetDisplay");
        return false;
    }
#ifdef PS5_OPENGL_DYNAMIC_DISPLAY
    // The mode is fixed while EGL runs: select it before eglInitialize.
    if (!eglSetDisplayModePS5(display_, width, height))
    {
        fail("eglSetDisplayModePS5");
        if (!eglSetDisplayModePS5(display_, PS5_OPENGL_NATIVE_WIDTH, PS5_OPENGL_NATIVE_HEIGHT))
            fail("eglSetDisplayModePS5 default");
    }
    // The menu runs at 60 Hz. A game on the OpenGL renderer may have asked for 120 Hz, and the
    // rate stays as it was last set.
    if (!eglSetDisplayRefreshPS5(display_, 60))
        fail("eglSetDisplayRefreshPS5");
#else
    (void)width;
    (void)height;
#endif
    if (!eglInitialize(display_, &major, &minor))
    {
        fail("eglInitialize");
        close();
        return false;
    }
    if (!eglBindAPI(EGL_OPENGL_API))
    {
        fail("eglBindAPI");
        close();
        return false;
    }
    if (!eglChooseConfig(display_, kConfigAttributes, &config, 1, &count) || count != 1)
    {
        fail("eglChooseConfig");
        close();
        return false;
    }
    // The PS5 backend owns the window: native handle 0 and NULL attributes.
    surface_ =
        eglCreateWindowSurface(display_, config, static_cast<EGLNativeWindowType>(0), nullptr);
    if (surface_ == EGL_NO_SURFACE)
    {
        fail("eglCreateWindowSurface");
        close();
        return false;
    }
    context_ = eglCreateContext(display_, config, EGL_NO_CONTEXT, kContextAttributes);
    if (context_ == EGL_NO_CONTEXT)
    {
        fail("eglCreateContext");
        close();
        return false;
    }
    if (!eglMakeCurrent(display_, surface_, surface_, context_))
    {
        fail("eglMakeCurrent");
        close();
        return false;
    }
    if (!eglQuerySurface(display_, surface_, EGL_WIDTH, &width_) ||
        !eglQuerySurface(display_, surface_, EGL_HEIGHT, &height_) || width_ <= 0 || height_ <= 0)
    {
        fail("eglQuerySurface");
        close();
        return false;
    }
    // Vsync: the swap paces the frame loop. ps5-opengl accepts only 0 or 1.
    if (!eglSwapInterval(display_, 1))
    {
        fail("eglSwapInterval");
        close();
        return false;
    }

    GLint gl_major = 0;
    GLint gl_minor = 0;
    glGetIntegerv(GL_MAJOR_VERSION, &gl_major);
    glGetIntegerv(GL_MINOR_VERSION, &gl_minor);
    sys::log("egl %d.%d surface %dx%d profile %dx%d@%d", major, minor, width_, height_,
             PS5_OPENGL_NATIVE_WIDTH, PS5_OPENGL_NATIVE_HEIGHT, PS5_OPENGL_NATIVE_FPS);
    sys::log("gl %d.%d version=\"%s\" renderer=\"%s\" glsl=\"%s\"", gl_major, gl_minor,
             gl_string(GL_VERSION), gl_string(GL_RENDERER), gl_string(GL_SHADING_LANGUAGE_VERSION));
    if (gl_major < 4 || (gl_major == 4 && gl_minor < 6))
    {
        sys::log("gl context below 4.6");
        close();
        return false;
    }
#ifndef PS5_OPENGL_DYNAMIC_DISPLAY
    if (width_ != PS5_OPENGL_NATIVE_WIDTH || height_ != PS5_OPENGL_NATIVE_HEIGHT)
        sys::log("warning: surface differs from the SDK display profile");
#else
    if (width_ != width || height_ != height)
        sys::log("warning: surface differs from the requested %dx%d", width, height);
#endif
    return true;
}

bool Display::swap()
{
    if (display_ == EGL_NO_DISPLAY || surface_ == EGL_NO_SURFACE)
        return false;
    if (!eglSwapBuffers(display_, surface_))
    {
        fail("eglSwapBuffers");
        return false;
    }
    return true;
}

bool Display::defer_scanout_close()
{
    if (display_ == EGL_NO_DISPLAY || surface_ == EGL_NO_SURFACE)
        return false;
    {
        std::lock_guard lock{deferred_display_mutex};
        if (deferred_display != EGL_NO_DISPLAY)
        {
            sys::log("egl scanout defer refused: previous owner still pending");
            return false;
        }
    }

    // Detach and destroy only the GL context. On this PS5 EGL runtime,
    // eglDestroySurface itself calls ps5_agc_gate2_shutdown_present(), which
    // drains and closes VideoOut. The window surface therefore MUST remain
    // alive with the display until the next renderer reaches its takeover
    // boundary.
    if (context_ != EGL_NO_CONTEXT)
    {
        if (!eglMakeCurrent(display_, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT))
        {
            fail("defer scanout release current");
            return false;
        }
        if (!eglDestroyContext(display_, context_))
        {
            fail("defer scanout context");
            return false;
        }
    }

    {
        std::lock_guard lock{deferred_display_mutex};
        deferred_display = display_;
        deferred_surface = surface_;
    }
    display_ = EGL_NO_DISPLAY;
    surface_ = EGL_NO_SURFACE;
    context_ = EGL_NO_CONTEXT;
    width_ = 0;
    height_ = 0;
    sys::log("egl launcher display+surface deferred for renderer handoff");
    return true;
}

bool Display::close_deferred_scanout()
{
    EGLDisplay display = EGL_NO_DISPLAY;
    EGLSurface surface = EGL_NO_SURFACE;
    {
        std::lock_guard lock{deferred_display_mutex};
        display = std::exchange(deferred_display, EGL_NO_DISPLAY);
        surface = std::exchange(deferred_surface, EGL_NO_SURFACE);
    }
    if (display == EGL_NO_DISPLAY)
        return true;

    // Destroying the retained window surface is the intentional VideoOut
    // handoff point on the pinned PS5 EGL implementation.
    if (surface != EGL_NO_SURFACE && !eglDestroySurface(display, surface))
    {
        const EGLint error = eglGetError();
        sys::log("egl deferred launcher surface release failed: %s (0x%04x)",
                 egl_error_name(error), static_cast<unsigned>(error));
        std::lock_guard lock{deferred_display_mutex};
        if (deferred_display == EGL_NO_DISPLAY)
        {
            deferred_display = display;
            deferred_surface = surface;
        }
        return false;
    }

    if (eglTerminate(display))
    {
        sys::log("egl deferred launcher scanout released");
        return true;
    }

    const EGLint error = eglGetError();
    sys::log("egl deferred launcher terminate failed: %s (0x%04x)",
             egl_error_name(error), static_cast<unsigned>(error));
    // Surface teardown already transferred VideoOut ownership. Retain only
    // the initialized display for a later cleanup retry.
    {
        std::lock_guard lock{deferred_display_mutex};
        if (deferred_display == EGL_NO_DISPLAY)
        {
            deferred_display = display;
            deferred_surface = EGL_NO_SURFACE;
        }
    }
    return false;
}

bool Display::has_deferred_scanout()
{
    std::lock_guard lock{deferred_display_mutex};
    return deferred_display != EGL_NO_DISPLAY;
}

void Display::close()
{
    if (display_ == EGL_NO_DISPLAY)
        return;
    if (context_ != EGL_NO_CONTEXT)
    {
        eglMakeCurrent(display_, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        eglDestroyContext(display_, context_);
    }
    if (surface_ != EGL_NO_SURFACE)
        eglDestroySurface(display_, surface_);
    if (!eglTerminate(display_))
        fail("eglTerminate");
    display_ = EGL_NO_DISPLAY;
    surface_ = EGL_NO_SURFACE;
    context_ = EGL_NO_CONTEXT;
    width_ = 0;
    height_ = 0;
}

const char *egl_error_name(EGLint error)
{
    switch (error)
    {
    case EGL_SUCCESS:
        return "EGL_SUCCESS";
    case EGL_NOT_INITIALIZED:
        return "EGL_NOT_INITIALIZED";
    case EGL_BAD_ACCESS:
        return "EGL_BAD_ACCESS";
    case EGL_BAD_ALLOC:
        return "EGL_BAD_ALLOC";
    case EGL_BAD_ATTRIBUTE:
        return "EGL_BAD_ATTRIBUTE";
    case EGL_BAD_CONFIG:
        return "EGL_BAD_CONFIG";
    case EGL_BAD_CONTEXT:
        return "EGL_BAD_CONTEXT";
    case EGL_BAD_CURRENT_SURFACE:
        return "EGL_BAD_CURRENT_SURFACE";
    case EGL_BAD_DISPLAY:
        return "EGL_BAD_DISPLAY";
    case EGL_BAD_MATCH:
        return "EGL_BAD_MATCH";
    case EGL_BAD_NATIVE_PIXMAP:
        return "EGL_BAD_NATIVE_PIXMAP";
    case EGL_BAD_NATIVE_WINDOW:
        return "EGL_BAD_NATIVE_WINDOW";
    case EGL_BAD_PARAMETER:
        return "EGL_BAD_PARAMETER";
    case EGL_BAD_SURFACE:
        return "EGL_BAD_SURFACE";
    case EGL_CONTEXT_LOST:
        return "EGL_CONTEXT_LOST";
    default:
        return "EGL_UNKNOWN_ERROR";
    }
}

} // namespace pe::ps5
