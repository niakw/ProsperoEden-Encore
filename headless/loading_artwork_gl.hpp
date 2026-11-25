// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Native UI-only GL helpers. No guest graphics state or file/network access.
#include "loading_artwork_transfer.hpp"
#include "loading_scene_glsl.h"
#include "loading_case_shader_source.hpp"
#include <GL/glcorearb.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>

namespace Eden::LoadingArtwork {
// The launcher uses direct GL exports; the game renderer uses GLAD macros.
// These helpers must have translation-unit-local linkage: otherwise weak ODR
// definitions may resolve to the other dispatch implementation before GLAD
// is initialized (native crash 0x97698, run 43877460207).
namespace {
// The caller supplies the already composed Encore draw list. Render once at
// a bounded resolution using an explicit FBO, not the transient scanout.
template<class Draw>
bool Capture(Draw&& draw,bool alternate=false,int width=1920,int height=1080){
    if(width<=0||height<=0||width>4096||height>2160)return false;
    LaunchHandoff::Frame frame;
    frame.width = width;
    frame.height = height;
    const std::size_t stride = std::size_t(width) * 4;
    try {
        frame.rgba.resize(stride * height);
    } catch (...) {
        return false;
    }
    GLint old_read = 0, old_draw = 0, old_texture = 0, old_viewport[4]{};
    GLint old_active_texture = GL_TEXTURE0;
    GLint old_pack = 0, old_unpack = 0, old_alignment = 4, old_row = 0;
    GLint old_rows = 0, old_pixels = 0;
    GLfloat old_clear[4]{};
    const GLboolean scissor = glIsEnabled(GL_SCISSOR_TEST);
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &old_read);
    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &old_draw);
    glGetIntegerv(GL_VIEWPORT, old_viewport);
    glGetIntegerv(GL_ACTIVE_TEXTURE, &old_active_texture);
    glGetIntegerv(GL_TEXTURE_BINDING_2D, &old_texture);
    glGetIntegerv(GL_PIXEL_PACK_BUFFER_BINDING, &old_pack);
    glGetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING, &old_unpack);
    glGetIntegerv(GL_PACK_ALIGNMENT, &old_alignment);
    glGetIntegerv(GL_PACK_ROW_LENGTH, &old_row);
    glGetIntegerv(GL_PACK_SKIP_ROWS, &old_rows);
    glGetIntegerv(GL_PACK_SKIP_PIXELS, &old_pixels);
    glGetFloatv(GL_COLOR_CLEAR_VALUE, old_clear);

    // Isolate earlier errors from this transaction without an unbounded loop.
    int stale_errors = 0;
    for (; stale_errors < 8 && glGetError() != GL_NO_ERROR; ++stale_errors) {}
    if (stale_errors) std::fprintf(stderr, "EDEN_LOADING_ARTWORK prior_gl_errors=%d\n", stale_errors);
    GLuint texture = 0, fbo = 0;
    glGenTextures(1, &texture);
    glGenFramebuffers(1, &fbo);
    bool ok = false;
    if (texture && fbo) {
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                               GL_TEXTURE_2D, texture, 0);
        if (glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE) {
            glDisable(GL_SCISSOR_TEST);
            glViewport(0, 0, width, height);
            glClearColor(0.055f, 0.075f, 0.105f, 1.0f);
            glClear(GL_COLOR_BUFFER_BIT);
            bool composed = true;
            try { draw(width, height); } catch (...) { composed = false; }
            glBindFramebuffer(GL_READ_FRAMEBUFFER, fbo);
            glReadBuffer(GL_COLOR_ATTACHMENT0);
            glBindBuffer(GL_PIXEL_PACK_BUFFER, 0);
            glPixelStorei(GL_PACK_ALIGNMENT, 1);
            glPixelStorei(GL_PACK_ROW_LENGTH, 0);
            glPixelStorei(GL_PACK_SKIP_ROWS, 0);
            glPixelStorei(GL_PACK_SKIP_PIXELS, 0);
            if (composed) {
                glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, frame.rgba.data());
                ok = glGetError() == GL_NO_ERROR;
            }
        }
    }
    glBindFramebuffer(GL_READ_FRAMEBUFFER, static_cast<GLuint>(old_read));
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, static_cast<GLuint>(old_draw));
    glActiveTexture(static_cast<GLenum>(old_active_texture));
    glBindTexture(GL_TEXTURE_2D, static_cast<GLuint>(old_texture));
    glBindBuffer(GL_PIXEL_PACK_BUFFER, static_cast<GLuint>(old_pack));
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER, static_cast<GLuint>(old_unpack));
    glPixelStorei(GL_PACK_ALIGNMENT, old_alignment);
    glPixelStorei(GL_PACK_ROW_LENGTH, old_row);
    glPixelStorei(GL_PACK_SKIP_ROWS, old_rows);
    glPixelStorei(GL_PACK_SKIP_PIXELS, old_pixels);
    glViewport(old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3]);
    glClearColor(old_clear[0], old_clear[1], old_clear[2], old_clear[3]);
    if (scissor) glEnable(GL_SCISSOR_TEST); else glDisable(GL_SCISSOR_TEST);
    glDeleteFramebuffers(1, &fbo);
    glDeleteTextures(1, &texture);
    if (!ok) return false;
    // Standardize to top-row-first without another full-image allocation.
    for (int y = 0; y < height / 2; ++y) {
        auto top = frame.rgba.begin() + y * stride;
        std::swap_ranges(top, top + stride,
                         frame.rgba.begin() + (height - y - 1) * stride);
    }
    try {
        LaunchHandoff::Publish(std::move(frame), alternate);
    } catch (...) {
        return false;
    }
    return true;
}

// All GL loading stages use the exact same shader, CPU artwork and epoch.
// The object must be released on the thread where its GL context is current.
class GlPresenter {
public:
    GlPresenter() = default;
    GlPresenter(const GlPresenter&) = delete;
    GlPresenter& operator=(const GlPresenter&) = delete;
    void Release() {
        glDeleteTextures(1, &texture_);
        glDeleteTextures(1, &alternate_texture_);
        glDeleteVertexArrays(1, &vao_);
        glDeleteProgram(program_);
        glDeleteProgram(case_program_);
        texture_=alternate_texture_=vao_=program_=case_program_=0;
        scene_.reset();
        width_ = height_ = 0;
        attempted_ = false;
    }
    bool Draw(int width, int height, double seconds) {
        if (width <= 0 || height <= 0) return false;
        if (!program_ && !Build()) return false;
        if (!attempted_) {
            attempted_ = true;
            const auto upload = [&](const std::shared_ptr<const LaunchHandoff::Frame>& artwork,
                                    GLuint* out) {
                if (!artwork || !LaunchHandoff::Valid(*artwork)) return;
                glActiveTexture(GL_TEXTURE0);
                glGenTextures(1, out);
                glBindTexture(GL_TEXTURE_2D, *out);
                glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
                glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
                glPixelStorei(GL_UNPACK_SKIP_ROWS, 0);
                glPixelStorei(GL_UNPACK_SKIP_PIXELS, 0);
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, artwork->width, artwork->height,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, artwork->rgba.data());
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
                if (!*out || glGetError() != GL_NO_ERROR) {
                    glDeleteTextures(1, out);
                    *out = 0;
                }
            };
            const auto artwork = LaunchHandoff::Peek();
            upload(artwork, &texture_);
            if (texture_ && artwork) {
                width_ = artwork->width;
                height_ = artwork->height;
                const auto alternate = LaunchHandoff::PeekAlternate();
                scene_=LaunchHandoff::PeekCase();
                if(scene_&&alternate&&alternate->width==LoadingCase::kAtlasWidth&&
                   alternate->height==LoadingCase::kAtlasHeight)upload(alternate,&alternate_texture_);
            }
        }
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glDisable(GL_BLEND);
        glDisable(GL_SCISSOR_TEST);
        glDisable(GL_DEPTH_TEST);
        glUseProgram(program_);
        glBindVertexArray(vao_);
        glViewport(0, 0, width, height);
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, texture_);
        glUniform1i(glGetUniformLocation(program_, "art"), 0);
        glUniform1i(glGetUniformLocation(program_,"has_art"),texture_?1:0);
        const auto fit = Fit(width_, height_, width, height);
        glUniform4f(glGetUniformLocation(program_, "fit_rect"), float(fit.x), float(fit.y),
                    float(std::max(1u, fit.width)), float(std::max(1u, fit.height)));
        glUniform2f(glGetUniformLocation(program_, "size"), float(width), float(height));
        glUniform1f(glGetUniformLocation(program_, "seconds"), float(seconds));
        glDrawArrays(GL_TRIANGLES, 0, 3);
        if(scene_ && (!alternate_texture_ || (!case_program_ && !BuildCase())))
            return false;
        if(scene_ && alternate_texture_){
            const auto draw=LoadingCase::MakeBatch(*scene_,seconds,float(width),float(height));
            glUseProgram(case_program_);
            glEnable(GL_BLEND);
            glBlendFuncSeparate(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA,GL_ONE,GL_ONE_MINUS_SRC_ALPHA);
            glDisable(GL_CULL_FACE);
            glBindTexture(GL_TEXTURE_2D,alternate_texture_);
            glUniform1i(glGetUniformLocation(case_program_,"u_texture"),0);
            const float scale=std::min(float(width)/1920.0f,float(height)/1080.0f);
            glUniform4f(glGetUniformLocation(case_program_,"u_viewport"),scale,
                (width-1920.0f*scale)*0.5f,(height-1080.0f*scale)*0.5f,0.0f);
            glUniform2f(glGetUniformLocation(case_program_,"u_surface"),float(width),float(height));
            const char* names[]={"a_rect","a_top","a_bottom","a_border","a_params","a_extra"};
            GLint loc[6]{};
            for(int i=0;i<6;++i)loc[i]=glGetUniformLocation(case_program_,names[i]);
            const GLint slot=glGetUniformLocation(case_program_,"u_slot");
            for(std::size_t n=0;n<draw.count;++n){
                const auto& q=draw.quads[n];
                for(int i=0;i<6;++i) {
                    const auto* value=q.values.data()+4*i;
                    glUniform4f(loc[i],value[0],value[1],value[2],value[3]);
                }
                glUniform1i(slot,int(q.output[2]));glDrawArrays(GL_TRIANGLES,0,6);
            }
            glDisable(GL_BLEND);
        }
        glFlush();
        return glGetError() == GL_NO_ERROR;
    }
private:
    bool Build() {
        const char* vertex = "#version 330 core\n"
            "void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);"
            "gl_Position=vec4(p*2.0-1.0,0.0,1.0);}";
        const std::string fragment = std::string{"#version 330 core\n"} + kLoadingSceneGlsl +
            "uniform sampler2D art; uniform int has_art; uniform vec4 fit_rect;"
            "uniform vec2 size; uniform float seconds; out vec4 color;\n"
            "void main(){vec2 p=vec2(gl_FragCoord.x,size.y-gl_FragCoord.y);"
            "vec2 uv=clamp((p-fit_rect.xy)/fit_rect.zw,vec2(0),vec2(1));"
            "vec3 base=has_art!=0?texture(art,uv).rgb:vec3(0.055,0.075,0.105);"
            "vec4 dots=loading_artwork_indicator(gl_FragCoord.xy,size,seconds);"
            "color=vec4(mix(base,dots.rgb,dots.a),1.0);}";
        GLuint program = glCreateProgram();
        if (!program) return false;
        bool ok = true;
        for (unsigned i = 0; i < 2 && ok; ++i) {
            GLuint shader = glCreateShader(i ? GL_FRAGMENT_SHADER : GL_VERTEX_SHADER);
            if (!shader) { ok = false; break; }
            const char* code = i ? fragment.c_str() : vertex;
            glShaderSource(shader, 1, &code, nullptr);
            glCompileShader(shader);
            GLint compiled = 0;
            glGetShaderiv(shader, GL_COMPILE_STATUS, &compiled);
            if (compiled) glAttachShader(program, shader);
            glDeleteShader(shader);
            ok = compiled != 0;
        }
        if (ok) {
            glLinkProgram(program);
            GLint linked = 0;
            glGetProgramiv(program, GL_LINK_STATUS, &linked);
            ok = linked != 0;
        }
        if (ok) glGenVertexArrays(1, &vao_);
        if (!ok || !vao_) { glDeleteProgram(program); return false; }
        program_ = program;
        return true;
    }
    bool BuildCase(){
        const std::string prefix="#version 330 core\n#define EDEN_CASE_HANDOFF_GL 1\n";
        const std::string vertex=prefix+LoadingCase::kVertex,fragment=prefix+LoadingCase::kFragment;
        const GLuint program=glCreateProgram();if(!program)return false;
        bool ok=true;
        for(unsigned i=0;i<2&&ok;++i){
            GLuint shader=glCreateShader(i?GL_FRAGMENT_SHADER:GL_VERTEX_SHADER);
            if(!shader){ok=false;break;}
            const char* code=i?fragment.c_str():vertex.c_str();
            glShaderSource(shader,1,&code,nullptr);glCompileShader(shader);
            GLint compiled=0;glGetShaderiv(shader,GL_COMPILE_STATUS,&compiled);
            if(compiled)glAttachShader(program,shader);
            else{char info[1024]{};glGetShaderInfoLog(shader,sizeof(info),nullptr,info);
                 std::fprintf(stderr,"EDEN_LOADING_CASE_SHADER %s\n",info);}
            glDeleteShader(shader);ok=compiled!=0;
        }
        if(ok){glLinkProgram(program);GLint linked=0;glGetProgramiv(program,GL_LINK_STATUS,&linked);ok=linked!=0;}
        if(!ok){glDeleteProgram(program);return false;}
        case_program_=program;return true;
    }
    GLuint program_{},vao_{},texture_{},alternate_texture_{},case_program_{};
    std::shared_ptr<const LoadingCase::Scene> scene_;
    std::uint32_t width_{}, height_{};
    bool attempted_{};
};
} // anonymous namespace (GL dispatch is local to each translation unit)
} // namespace Eden::LoadingArtwork
