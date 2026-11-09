#!/usr/bin/env python3
"""H05: execute the actual maintained Nx2VideoDecoder::Render on a real FFmpeg
encoded/decoded video frame, including guest NV12/RGBA bytes and negative bounds.

No console and no fabricated decoder output. The service/guest-fence lifecycle
still needs a separate executed-owner IPC witness before H05 can close.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/"vendor/encore-active/ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.cpp"
SERVICE=ROOT/"vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp"
original=OWNER.read_text()
begin="bool Nx2VideoDecoder::Render("
end="\n}\n\n} // namespace Tegra::Host1x"
assert original.count(begin)==original.count(end)==1
real=begin+original.split(begin,1)[1].split(end,1)[0]+"\n}"
service=SERVICE.read_text()
assert "m_decoder->Render(frame.picture," in service
assert service.index("m_owner->WriteVideoSurface(next.id, *target, pixels)") < service.index(
    "syncpoints.IncrementGuest(m_syncpoint);")
assert "if (!m_decoder->Render(frame.picture," in service

cpp=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <span>
#include <vector>
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/pixdesc.h>
#include <libswscale/swscale.h>
}
using u8=std::uint8_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
#define LOG_ERROR(...) ((void)0)
constexpr int HW_GPU=0;
namespace FFmpeg {
class Frame {
    AVFrame* frame;
public:
    explicit Frame(AVFrame* p):frame(p) {assert(frame);}
    ~Frame(){av_frame_free(&frame);}
    const AVFrame* GetFrame() const {return frame;}
};
}
namespace Tegra::Host1x {
struct Nx2Picture {
    u32 width{}, height{};
    u64 pts{};
    std::shared_ptr<FFmpeg::Frame> frame;
};
enum class Nx2PictureFormat : u32 {Nv12,Rgba8,Bgra8};
class Nx2VideoDecoder {
    struct Impl {
        SwsContext* scaler{};
        ~Impl(){sws_freeContext(scaler);}
    };
    std::unique_ptr<Impl> impl{std::make_unique<Impl>()};
public:
    bool Render(const Nx2Picture&, Nx2PictureFormat,u32,u32,u64,u64,std::span<u8>);
};
__REAL_OWNER__
} // namespace Tegra::Host1x

// Encode real planar pixels with FFmpeg's in-tree MPEG4 encoder; then decode
// the compressed packet with FFmpeg's genuine decoder. No fake AVFrame.
AVFrame* CodecRoundTrip() {
    const AVCodec* encoder=avcodec_find_encoder(AV_CODEC_ID_MPEG4);
    const AVCodec* decoder=avcodec_find_decoder(AV_CODEC_ID_MPEG4);
    assert(encoder && decoder);
    AVCodecContext* enc=avcodec_alloc_context3(encoder);
    assert(enc);
    enc->width=16; enc->height=16; enc->pix_fmt=AV_PIX_FMT_YUV420P;
    enc->time_base=AVRational{1,30}; enc->gop_size=1; enc->max_b_frames=0;
    assert(avcodec_open2(enc,encoder,nullptr)==0);
    AVFrame* input=av_frame_alloc();
    assert(input);
    input->format=AV_PIX_FMT_YUV420P;input->width=16;input->height=16;input->pts=1;
    assert(av_frame_get_buffer(input,32)==0);
    assert(av_frame_make_writable(input)==0);
    for(int y=0;y<16;++y)
        std::memset(input->data[0]+y*input->linesize[0],82,16);
    for(int y=0;y<8;++y){
        std::memset(input->data[1]+y*input->linesize[1],90,8);
        std::memset(input->data[2]+y*input->linesize[2],240,8);
    }
    assert(avcodec_send_frame(enc,input)==0);
    AVPacket* packet=av_packet_alloc();
    assert(packet);
    int ret=avcodec_receive_packet(enc,packet);
    if(ret==AVERROR(EAGAIN)){
        assert(avcodec_send_frame(enc,nullptr)==0);
        ret=avcodec_receive_packet(enc,packet);
    }
    assert(ret==0 && packet->size>0);
    AVCodecContext* dec=avcodec_alloc_context3(decoder);
    assert(dec && avcodec_open2(dec,decoder,nullptr)==0);
    assert(avcodec_send_packet(dec,packet)==0);
    AVFrame* output=av_frame_alloc();
    assert(output);
    ret=avcodec_receive_frame(dec,output);
    if(ret==AVERROR(EAGAIN)){
        assert(avcodec_send_packet(dec,nullptr)==0);
        ret=avcodec_receive_frame(dec,output);
    }
    assert(ret==0 && output->width==16 && output->height==16);
    assert(output->format==AV_PIX_FMT_YUV420P);
    av_frame_free(&input);
    av_packet_free(&packet);
    avcodec_free_context(&enc);
    avcodec_free_context(&dec);
    return output;
}
int main(){
    using namespace Tegra::Host1x;
    auto frame=std::make_shared<FFmpeg::Frame>(CodecRoundTrip());
    const auto* f=frame->GetFrame();
    const Nx2Picture picture{16,16,123,frame};
    Nx2VideoDecoder dec;
    constexpr std::size_t luma=16*16;
    constexpr std::size_t size=luma+16*8;
    std::vector<u8> nv12(size+16,0xA5);
    assert(dec.Render(picture,Nx2PictureFormat::Nv12,16,16,16,luma,
                      std::span<u8>(nv12.data(),size)));
    for(int y=0;y<16;++y)
        for(int x=0;x<16;++x)
            assert(nv12[y*16+x]==f->data[0][y*f->linesize[0]+x]);
    for(int y=0;y<8;++y)
        for(int x=0;x<8;++x){
            assert(nv12[luma+y*16+x*2]==f->data[1][y*f->linesize[1]+x]);
            assert(nv12[luma+y*16+x*2+1]==f->data[2][y*f->linesize[2]+x]);
        }
    assert(std::all_of(nv12.begin()+size,nv12.end(),[](u8 x){return x==0xA5;}));
    constexpr std::size_t rgba_size=16*16*4;
    std::vector<u8> rgba(rgba_size+16,0xA5);
    assert(dec.Render(picture,Nx2PictureFormat::Rgba8,16,16,64,0,
                      std::span<u8>(rgba.data(),rgba_size)));
    assert(std::any_of(rgba.begin(),rgba.begin()+rgba_size,
                       [](u8 x){return x!=0xA5;}));
    assert(std::all_of(rgba.begin()+rgba_size,rgba.end(),
                       [](u8 x){return x==0xA5;}));
    std::vector<u8> invalid(size+16,0xEE);
    auto reject=[&](Nx2PictureFormat format,u32 width,u32 height,u64 pitch,
                    u64 chroma,std::size_t available){
        std::fill(invalid.begin(),invalid.end(),0xEE);
        assert(!dec.Render(picture,format,width,height,pitch,chroma,
                           std::span<u8>(invalid.data(),available)));
        assert(std::all_of(invalid.begin(),invalid.end(),
                           [](u8 x){return x==0xEE;}));
    };
    reject(Nx2PictureFormat::Nv12,16,16,15,luma,size);
    reject(Nx2PictureFormat::Nv12,16,16,16,luma-1,size);
    reject(Nx2PictureFormat::Nv12,16,16,16,luma,size-1);
    reject(Nx2PictureFormat::Rgba8,16,16,63,0,size);
    reject(Nx2PictureFormat::Nv12,0,16,16,luma,size);
    reject(Nx2PictureFormat::Nv12,16,16,
           static_cast<u64>(std::numeric_limits<int>::max())+1,0,size);
    std::puts("H05_REAL_FFMPEG_DECODED_FRAME_RENDER_PASS "
              "codec=MPEG4 pixels=FFmpeg decoded NV12=exact RGBA=converted "
              "oob_pitch_offset_size=refused guest_fence=not_exercised");
}
""".replace("__REAL_OWNER__",real)
compilers=list(dict.fromkeys(x for x in
    (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h05-ffmpeg-pixels-") as temp:
    src=Path(temp)/"render.cpp"
    src.write_text(cpp)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-Wno-unused-variable","-fsanitize=undefined",
                 "-fno-sanitize-recover=all",str(src),"-o",str(exe),
                 "-lavcodec","-lavutil","-lswscale"]
            built=subprocess.run(cmd,text=True,capture_output=True,
                                 timeout=75,env=os.environ.copy())
            assert built.returncode==0,(cc,built.stderr[-5000:])
            run=subprocess.run([str(exe)],text=True,capture_output=True,
                               timeout=25,env=os.environ.copy())
            assert run.returncode==0,(cc,run.stderr[-5000:])
            print(Path(cc).name,opt,run.stdout.strip(),flush=True)
