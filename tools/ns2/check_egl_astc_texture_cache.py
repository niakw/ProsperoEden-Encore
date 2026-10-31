#!/usr/bin/env python3
"""N60 generation source-owner parity and explicit full fallback guard."""
from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"vendor/sources/eden/src/video_core/texture_cache"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
assert 'EDEN_NS2_ASTC_TEXTURE_CACHE_BRIDGE_EXPERIMENTAL OR' in CMAKE
assert 'NOT EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL OR EDEN_FINAL_RELEASE_PROFILE' in CMAKE
with tempfile.TemporaryDirectory(prefix="n60-astc-") as folder:
    out=Path(folder)
    subprocess.run([sys.executable,str(ROOT/"tools/ns2/prepare_egl_astc_texture_cache.py"),
      "--image",str(SOURCE/"image_base.h"),"--base",str(SOURCE/"texture_cache_base.h"),
      "--texture",str(SOURCE/"texture_cache.h"),"--output",str(out)],check=True)
    image=(out/"video_core/texture_cache/image_base.h").read_text()
    tex=(out/"video_core/texture_cache/texture_cache.h").read_text()
    base=(out/"video_core/texture_cache/texture_cache_base.h").read_text()
    original=(SOURCE/"texture_cache.h").read_text()
    assert "std::optional<Eden::NS2::Eglantine::AstcDirtyLayerPlanner>" in image
    for x in ("Ns2AstcEligible(", "Ns2UploadDirtyLayers("):assert x in base
    for x in ("ns2_astc_dirty->MarkWrite(", "ns2_astc_dirty.reset();",
              "UploadAstcDirtyLayerBatches(", "runtime.AccelerateImageUploadLayers(",
              "image.ns2_astc_dirty.reset(); // all prior layer residency is invalid",
              "if (False(image.flags & ImageFlagBits::Tracked))"):
        assert x in tex,x
    # The original guest memory full-image path is not removed by the adapter.
    needle="runtime.AccelerateImageUpload(image, staging, FixSmallVectorADL(uploads), 0, 0);"
    assert original.count(needle)==1 and tex.count(needle)==1
    assert original.count("UploadImageContents(image, staging);")==tex.count("UploadImageContents(image, staging);")
# Prove that N60 composes with the real, vendor-maintained N54 texture owner.
with tempfile.TemporaryDirectory(prefix="n60-n54-vendor-composed-") as joined:
    root=Path(joined)
    vendor_tex=ROOT/"vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h"
    assert vendor_tex.is_file()
    combo=root/"combined"
    subprocess.run([sys.executable,str(ROOT/"tools/ns2/prepare_egl_astc_texture_cache.py"),
      "--image",str(SOURCE/"image_base.h"),"--base",str(SOURCE/"texture_cache_base.h"),
      "--texture",str(vendor_tex),"--output",str(combo)],check=True)
    content=(combo/"video_core/texture_cache/texture_cache.h").read_text()
    assert "N54ScratchTrimThreshold" in content
    assert "TextureCache<P>::Ns2UploadDirtyLayers(" in content
print("N60_ASTC_TEXTURE_CACHE_OWNER_AND_FULL_FALLBACK_PASS")
