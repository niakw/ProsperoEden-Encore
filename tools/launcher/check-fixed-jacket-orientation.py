#!/usr/bin/env python3
"""Compare rendered NS1/NS2 fixed jacket prints to their canonical PNG sources.

Use screenshots made by the REAL C++/OpenGL launcher (not source-string
assertions) and reject a source-raster vertical flip, even if all other
UI elements and frame statistics still look plausible.
"""
import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "build"
SOURCE = ROOT / "headless/prosperoeden/ui/art"

CASE_RATIO = 454.0 / 730.0
SLEEVE_H = 346.0
SLEEVE_W = SLEEVE_H * CASE_RATIO
SLOT_W = (1776.0 - 20.0 * 4) / 5.0
TOP = SLEEVE_H * 13.0 / 730.0
SIDE = SLEEVE_W * 7.0 / 454.0
PAPER_W = SLEEVE_W - SIDE
PAPER_H = SLEEVE_H - 2 * TOP


def fixed(name):
    data = base64.b64decode((SOURCE / f"{name}.png.b64").read_text().strip(),
                            validate=True)
    with Image.open(BytesIO(data)) as art:
        return art.convert("RGB")


def compare(image, name, box):
    # Exclude a few boundary pixels affected by UV filtering and case rims.
    x, y, w, h = box
    w, h = round(w), round(h)
    x, y = round(x), round(y)
    source = fixed(name).resize((w, h), Image.Resampling.LANCZOS)
    margin = 4 if min(w, h) > 45 else 2
    area = (margin, margin, w - margin, h - margin)
    target = image.crop((x, y, x + w, y + h)).convert("RGB").crop(area)
    expected = source.crop(area)
    flipped = ImageOps.flip(source).crop(area)

    def error(ref):
        return sum(ImageStat.Stat(ImageChops.difference(target, ref)).mean) / 3.0

    up = error(expected)
    down = error(flipped)
    print(f"FIXED_PRINT_ORIENTATION {name} upright_error={up:.2f} "
          f"upside_down_error={down:.2f}")
    # Pixel reference must be measurably closer than its vertical reflection.
    # No pass solely on a blank/solid raster or a misplaced background patch.
    assert up + 3.0 < down, (name, "flipped or missing printed asset", up, down)


def shelf_x(slot):
    return 72.0 + slot * (SLOT_W + 20.0) + (SLOT_W - SLEEVE_W) * 0.5


# Fixture title order is sorted. NS1 BotW at index 10 of 12 -> shelf slot 3.
# NS2 Mario Kart World at index 4 of 12 -> shelf slot 2.
ns1_x = shelf_x(3)
ns2_x = shelf_x(2)
paper_y = 204.0 + TOP

with Image.open(OUTPUT / "launch-case-library-fallback/00-library-fallback-front.png") as frame:
    compare(frame, "switch-logo", (
        ns1_x, paper_y, PAPER_W * 0.222,
        PAPER_W * 0.222 * 190.0 / 193.0,
    ))

with Image.open(OUTPUT / "launch-case-ns2-library/00-library-fallback-front.png") as frame:
    compare(frame, "ns2-head", (
        ns2_x, paper_y, PAPER_W,
        PAPER_W * (246.0 / 1164.0),
    ))

# The selected NS1 rear detail is independently drawn at x=280-rear_w,
# y=882-rear_h; its fixed footer is the last 41% of the inner paper.
rear_h = 247.0
rear_w = rear_h * CASE_RATIO
rear_top = rear_h * 13.0 / 730.0
rear_side = rear_w * 7.0 / 454.0
rear_paper_h = rear_h - 2.0 * rear_top
with Image.open(OUTPUT / "launch-case-library-fallback/01-library-fallback-back.png") as frame:
    compare(frame, "switch-rear-footer", (
        280.0 - rear_w + rear_side,
        882.0 - rear_h + rear_top + rear_paper_h * (1.0 - 0.41),
        rear_w - rear_side,
        rear_paper_h * 0.41,
    ))
print("ENCORE_NS1_NS2_FIXED_PRINT_PIXEL_ORIENTATION: PASS")
