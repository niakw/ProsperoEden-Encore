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
WRAP_MODE = "--wrap-mode=nodownload"
C_ARGS_OLD = "-Dc_args=-Wno-thread-safety-analysis\n"
CPP_ARGS_OLD = "-Dcpp_args=-Wno-thread-safety-analysis\n"
C_ARGS_NEW = (
    "-Dc_args=-Wno-thread-safety-analysis,-Wno-unreachable-code-generic-assoc,"
    "-Wno-unused-parameter\n"
)
CPP_ARGS_NEW = (
    "-Dcpp_args=-Wno-thread-safety-analysis,-Wno-unreachable-code-generic-assoc,"
    "-Wno-unused-parameter\n"
)

def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    present = [flag for flag in FLAGS if flag in text]
    if present:
        if set(present) != set(FLAGS) or any(text.count(flag) != 1 for flag in FLAGS):
            raise RuntimeError(f"partial/duplicate Mesa PS5 feature selection: {present}")
        if text.count(WRAP_MODE) != 1:
            raise RuntimeError("partial/duplicate Mesa PS5 no-download selection")
        if text.count(C_ARGS_NEW) != 1 or text.count(CPP_ARGS_NEW) != 1:
            raise RuntimeError("partial/duplicate Mesa PS5 diagnostic selection")
        if C_ARGS_OLD in text or CPP_ARGS_OLD in text:
            raise RuntimeError("old Mesa PS5 diagnostic flags remained after selection")
        print("PS5_OPENGL_MESA_OPTIONAL_FEATURES_ALREADY_SELECTED")
        return
    if text.count(ANCHOR) != 1:
        raise RuntimeError("Pinned PS5 OpenGL Mesa meson_args anchor changed")
    if text.count(C_ARGS_OLD) != 1 or text.count(CPP_ARGS_OLD) != 1:
        raise RuntimeError("Pinned PS5 OpenGL Mesa diagnostic flags changed")
    replacement = ANCHOR + WRAP_MODE + "\n" + "".join(flag + "\n" for flag in FLAGS)
    text = text.replace(ANCHOR, replacement, 1)
    text = text.replace(C_ARGS_OLD, C_ARGS_NEW, 1)
    text = text.replace(CPP_ARGS_OLD, CPP_ARGS_NEW, 1)
    path.write_text(text, encoding="utf-8")
    print(
        "PS5_OPENGL_MESA_OPTIONAL_FEATURES_PASS "
        + " ".join(FLAGS)
        + " wrap-mode=nodownload diagnostics=SDK-generic-assoc,unused-parameter"
    )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("build_script", type=Path)
    args = ap.parse_args()
    patch(args.build_script)
