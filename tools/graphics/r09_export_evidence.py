# SPDX-License-Identifier: MIT
"""PNG images of the actual R09 Vulkan before/after framebuffer smoke.
Synthetic fixture, NOT game footage and NOT complete neural inference.
No third-party packages; PNG uses the Python standard library.
"""
import base64
from pathlib import Path
import struct
import zlib

BASE=Path(".build-r09-gpu")
W,H=80,45

def png_from_gpu_ppm(name):
    ppm=(BASE/name).read_bytes()
    header=f"P6\n{W} {H}\n255\n".encode("ascii")
    if not ppm.startswith(header):
        raise ValueError("GPU evidence must be P6 in exact expected geometry")
    rgb=ppm[len(header):]
    if len(rgb)!=W*H*3:
        raise ValueError("Readback PPM length mismatch")
    scanlines=b"".join(
        b"\0"+rgb[row*W*3:(row+1)*W*3] for row in range(H))
    def chunk(tag,payload):
        return (struct.pack(">I",len(payload))+tag+payload+
                struct.pack(">I",zlib.crc32(tag+payload)&0xffffffff))
    png=(b"\x89PNG\r\n\x1a\n"+
         chunk(b"IHDR",struct.pack(">IIBBBBB",W,H,8,2,0,0,0))+
         chunk(b"IDAT",zlib.compress(scanlines,9))+
         chunk(b"IEND",b""))
    out=BASE/(name.replace(".ppm",".png"))
    if not png.startswith(bytes.fromhex("89504e470d0a1a0a")):
        raise ValueError("PNG signature invalid")
    out.write_bytes(png)
    return out,png

def main():
    for name,label in [
        ("r09_before.ppm","BEFORE"),
        ("r09_after_gpu.ppm","AFTER_REAL_GPU")]:
        path,png=png_from_gpu_ppm(name)
        print(f"R09_EVIDENCE_FILE_{label}: {path}")
        print(f"R09_EVIDENCE_PNG_{label}={base64.b64encode(png).decode('ascii')}")
if __name__=="__main__":
    main()
