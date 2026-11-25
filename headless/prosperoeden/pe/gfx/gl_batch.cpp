// ProsperoEden - OpenGL backend for the 2D draw list.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#include "pe/gfx/gl_batch.hpp"

#include "pe/gfx/gl_program.hpp"
#include "../../../loading_case_shader_source.hpp"

#include <algorithm>
#include <cmath>

namespace pe::gfx
{

namespace
{

using Eden::LoadingCase::kVertex;
using Eden::LoadingCase::kFragment;

} // namespace

GlBatch::~GlBatch()
{
    release();
}

void GlBatch::release()
{
    glDeleteBuffers(static_cast<GLsizei>(buffers_.size()), buffers_.data());
    glDeleteVertexArrays(static_cast<GLsizei>(vaos_.size()), vaos_.data());
    if (program_ != 0)
        glDeleteProgram(program_);
    buffers_.fill(0);
    vaos_.fill(0);
    capacities_.fill(0);
    next_slot_ = 0;
    program_ = 0;
}

bool GlBatch::init()
{
    program_ = build_program("batch2d", kVertex, kFragment);
    if (program_ == 0)
        return false;
    glGenVertexArrays(static_cast<GLsizei>(vaos_.size()), vaos_.data());
    glGenBuffers(static_cast<GLsizei>(buffers_.size()), buffers_.data());
    constexpr GLsizei stride = sizeof(Instance);
    // Each VAO remembers its own VBO. Rotating both prevents a stalled
    // read of the previous frame's same-size storage in the PS5 GL driver.
    for (std::size_t slot = 0; slot < buffers_.size(); ++slot)
    {
        glBindVertexArray(vaos_[slot]);
        glBindBuffer(GL_ARRAY_BUFFER, buffers_[slot]);
        for (GLuint attribute = 0; attribute < 6; ++attribute)
        {
            glEnableVertexAttribArray(attribute);
            glVertexAttribPointer(
                attribute, 4, GL_FLOAT, GL_FALSE, stride,
                reinterpret_cast<const void *>(static_cast<std::uintptr_t>(attribute * 16)));
            glVertexAttribDivisor(attribute, 1);
        }
    }
    glBindVertexArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    return true;
}

std::uint32_t GlBatch::create_font_texture(const Font &font)
{
    GLuint texture = 0;
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, font.atlas_width(), font.atlas_height(), 0, GL_RED,
                 GL_UNSIGNED_BYTE, font.atlas().data());
    // One level only: mip chains leave ps5-opengl's batched fast path.
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    return texture;
}

void GlBatch::sync_font_texture(std::uint32_t texture, const Font &font)
{
    int first = 0;
    int last = 0;
    if (texture == 0 || !font.take_changed_rows(&first, &last))
        return;
    glBindTexture(GL_TEXTURE_2D, texture);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, first, font.atlas_width(), last - first, GL_RED, GL_UNSIGNED_BYTE,
                    font.atlas().data() + static_cast<std::size_t>(first) * font.atlas_width());
}

std::uint32_t GlBatch::create_texture(int width, int height, const std::uint8_t *rgba)
{
    GLuint texture = 0;
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 4);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    return texture;
}

void GlBatch::delete_texture(std::uint32_t texture)
{
    if (texture != 0)
        glDeleteTextures(1, &texture);
}

void GlBatch::draw(const DrawList &list, const Viewport &viewport, int surface_width,
                   int surface_height)
{
    draw_calls_ = 0;
    const auto &instances = list.instances();
    if (instances.empty())
        return;
    // The old path orphaned the SAME GL store every frame. PS5 OpenGL can
    // drain on that operation, making held-D-pad navigation stutter.
    // Rotate three VBOs, and resize a store only when it actually grows.
    const std::size_t slot = next_slot_++ % kStreamBufferSlots;
    glBindBuffer(GL_ARRAY_BUFFER, buffers_[slot]);
    const auto capacity = StreamCapacity(capacities_[slot], instances.size());
    if (capacity != capacities_[slot])
    {
        glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(capacity * sizeof(Instance)), nullptr,
                     GL_STREAM_DRAW);
        capacities_[slot] = capacity;
    }
    glBufferSubData(GL_ARRAY_BUFFER, 0,
                    static_cast<GLsizeiptr>(instances.size() * sizeof(Instance)),
                    instances.data());

    glViewport(0, 0, surface_width, surface_height);
    glEnable(GL_BLEND);
    glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
    glUseProgram(program_);
    glUniform4f(0, viewport.scale, viewport.offset_x, viewport.offset_y, 0.0f);
    glUniform2f(1, static_cast<float>(surface_width), static_cast<float>(surface_height));
    glUniform1i(2, 0);
    glActiveTexture(GL_TEXTURE0);

    GLuint bound_texture = 0;
    bool scissor = false;
    Rect last_scissor_clip{};
    glBindVertexArray(vaos_[slot]);
    for (const Run &run : list.runs())
    {
        if (run.count == 0)
            continue;
        if (run.texture != 0 && run.texture != bound_texture)
        {
            glBindTexture(GL_TEXTURE_2D, run.texture);
            bound_texture = run.texture;
        }
        if (run.clipped)
        {
            // Runs with different textures often share the same clip. Keep
            // the actual last GL scissor and avoid recomputing/submitting it
            // for every image/text run in a clipped library panel.
            const bool new_scissor =
                !scissor || run.clip.x != last_scissor_clip.x ||
                run.clip.y != last_scissor_clip.y ||
                run.clip.w != last_scissor_clip.w ||
                run.clip.h != last_scissor_clip.h;
            if (!scissor)
                glEnable(GL_SCISSOR_TEST);
            scissor = true;
            if (new_scissor)
            {
                const float x0 = std::floor(run.clip.x * viewport.scale + viewport.offset_x);
                const float y0 = std::floor(run.clip.y * viewport.scale + viewport.offset_y);
                const float x1 =
                    std::ceil((run.clip.x + run.clip.w) * viewport.scale + viewport.offset_x);
                const float y1 =
                    std::ceil((run.clip.y + run.clip.h) * viewport.scale + viewport.offset_y);
                glScissor(static_cast<GLint>(x0), surface_height - static_cast<GLint>(y1),
                          static_cast<GLsizei>(std::max(0.0f, x1 - x0)),
                          static_cast<GLsizei>(std::max(0.0f, y1 - y0)));
                last_scissor_clip = run.clip;
            }
        }
        else if (scissor)
        {
            glDisable(GL_SCISSOR_TEST);
            scissor = false;
        }
        glDrawArraysInstancedBaseInstance(GL_TRIANGLES, 0, 6, static_cast<GLsizei>(run.count),
                                          run.first);
        ++draw_calls_;
    }
    if (scissor)
        glDisable(GL_SCISSOR_TEST);
    glBindVertexArray(0);
}

} // namespace pe::gfx
