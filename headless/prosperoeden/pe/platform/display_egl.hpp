// ProsperoEden - EGL display and OpenGL 4.6 Core context.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include <EGL/egl.h>

namespace pe::ps5
{

// Owns the EGL display, window surface and GL 4.6 Core context. ps5-opengl
// presents fullscreen; with runtime display modes the size is chosen before
// EGL starts, so changing it means close() and open() again. Every GL object
// dies with the context and must be recreated by its owner.
class Display
{
  public:
    Display() = default;
    Display(const Display &) = delete;
    Display &operator=(const Display &) = delete;
    ~Display();

    // Opens at width x height (1920x1080, 2560x1440 or 3840x2160) when the
    // SDK supports runtime display modes, else at the SDK's fixed profile.
    bool open(int width = 1920, int height = 1080);
    bool swap();
    void close();

    // A Vulkan launch may take tens of seconds in System::Load before it can
    // create its own VideoOut surface. Transfer the existing GL context,
    // display and surface to one bounded loading presenter so the shared scene
    // keeps moving instead of freezing. The next renderer stops/joins that
    // presenter and releases all three at its explicit takeover boundary.
    bool defer_scanout_close(bool reduce_motion);
    static bool close_deferred_scanout();
    static bool has_deferred_scanout();

    // True when the SDK can change the display size at runtime.
    static bool supports_display_modes();

    int width() const
    {
        return width_;
    }
    int height() const
    {
        return height_;
    }
    EGLint last_error() const
    {
        return last_error_;
    }

  private:
    void fail(const char *operation);

    EGLDisplay display_ = EGL_NO_DISPLAY;
    EGLSurface surface_ = EGL_NO_SURFACE;
    EGLContext context_ = EGL_NO_CONTEXT;
    int width_ = 0;
    int height_ = 0;
    EGLint last_error_ = EGL_SUCCESS;
};

const char *egl_error_name(EGLint error);

} // namespace pe::ps5
