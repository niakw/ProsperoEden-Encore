#!/usr/bin/env python3
"""Select only the Mesa 26.2 optional features used by the PS5 OpenGL build."""
from pathlib import Path
import argparse

FLAGS = (
    "-Ddisplay-info=disabled",
    "-Dspirv-tools=disabled",
    "-Dlmsensors=disabled",
)
ANCHOR = "-Dplatforms=\n"

def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    present = [flag for flag in FLAGS if flag in text]
    if present:
        if set(present) != set(FLAGS) or any(text.count(flag) != 1 for flag in FLAGS):
            raise RuntimeError(f"partial/duplicate Mesa PS5 feature selection: {present}")
        print("PS5_OPENGL_MESA_OPTIONAL_FEATURES_ALREADY_SELECTED")
        return
    if text.count(ANCHOR) != 1:
        raise RuntimeError("Pinned PS5 OpenGL Mesa meson_args anchor changed")
    replacement = ANCHOR + "".join(flag + "\n" for flag in FLAGS)
    path.write_text(text.replace(ANCHOR, replacement, 1), encoding="utf-8")
    print("PS5_OPENGL_MESA_OPTIONAL_FEATURES_PASS " + " ".join(FLAGS))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("build_script", type=Path)
    args = ap.parse_args()
    patch(args.build_script)
