#!/usr/bin/env python3
"""Build the descriptor-free Vulkan quick-menu atlas from shipping font faces.

The heavy work is a tiny host C++ utility using the same stb_truetype source as
launcher SystemFonts. Runtime shaping remains HarfBuzz in the application; this
step only rasterizes every glyph in the catalog-bounded font subsets.
"""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument("--output",type=Path,default=ROOT/"headless/vulkan_menu_font.glsl")
parser.add_argument("--map-output",type=Path,default=ROOT/"headless/vulkan_menu_font_map.h")
parser.add_argument("--fallback-dir",type=Path,default=ROOT/"build/generated/noto-fallback")
parser.add_argument("--host-cxx",default=os.environ.get("EDEN_HOST_CXX",""))
args=parser.parse_args()

required=("NotoSans-Greek.ttf","NotoSansArabic.ttf","NotoSansThai.ttf",
          "NotoSansJP.ttf","NotoSansKR.ttf","NotoSansSC.ttf","NotoSansTC.ttf")
if not all((args.fallback_dir/name).is_file() for name in required):
    subprocess.run([
        "python3","-B",str(ROOT/"tools/launcher/build_noto_subsets.py"),
        "--output",str(args.fallback_dir)
    ],check=True)
for name in required:
    if not (args.fallback_dir/name).is_file():
        raise SystemExit(f"missing generated fallback font: {name}")

host_cxx=args.host_cxx or shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
if not host_cxx:
    raise SystemExit("host C++20 compiler not found")
source=ROOT/"tools/launcher/bake_vulkan_menu_font.cpp"
montserrat=ROOT/"third_party/fonts/Montserrat-Medium.ttf"
if not source.is_file() or not montserrat.is_file():
    raise SystemExit("Vulkan menu font source/Montserrat source is missing")
args.output.parent.mkdir(parents=True,exist_ok=True)
args.map_output.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix="encore-vulkan-menu-font-") as tmp:
    binary=Path(tmp)/"bake-vulkan-menu-font"
    subprocess.run([
        host_cxx,"-std=c++20","-O2","-Wall","-Wextra","-Werror","-pedantic",
        "-I",str(ROOT/"tools/launcher/stb"),str(source),"-o",str(binary)
    ],check=True)
    subprocess.run([
        str(binary),str(montserrat),str(args.fallback_dir),
        str(args.output),str(args.map_output)
    ],check=True)
print(f"VULKAN_MENU_FONT_GENERATOR_PASS glsl={args.output} map={args.map_output}")
