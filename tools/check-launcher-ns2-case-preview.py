#!/usr/bin/env python3
"""Host-only source and fixture contract for NS2 launcher box presentation."""
from pathlib import Path
import base64
import hashlib
import struct

root = Path(__file__).resolve().parents[1]
def read(path):
    return (root / path).read_text()

case = read("headless/prosperoeden/pe/ui/case_media_selection.hpp")
library = read("headless/prosperoeden/pe/ui/library.cpp")
launcher = read("headless/prosperoeden/pe/ui/launcher.cpp")
textures = read("headless/prosperoeden/pe/ui/textures.cpp")
texture_header = read("headless/prosperoeden/pe/ui/textures.hpp")
fixture = read("headless/prosperoeden/host/fake_services.cpp")
preview = read(".github/workflows/launcher-production-preview.yml")
staging = read("tools/ci/check-staged-app.py")
packaging = read("tools/package-headless-native.sh")

assert "inline constexpr bool IsSwitch2TitleId(" in case
assert "(id & 0xFF00000000000000ULL) == 0x0400000000000000ULL" in case
assert "case_media::IsSwitch2TitleId(game.title_id)" in library
assert "case_media::IsSwitch2TitleId(launch_title_id_)" in launcher

front = library.split("void flat_front_fallback(", 1)[1].split("void flat_back_fallback(", 1)[0]
assert "if (ns2_cover)" in front
assert "if (!ns2_cover)" in front
assert "c.textures.switch2_header()" in front
# Both PS5 and host share the OpenGL source-row convention. A negative V
# rendered the supplied NS2 header upside down in the actual 3D paper.
assert """c.list.image(c.textures.switch2_header(), header,
                         {0.0f, 0.0f, 1.0f, 1.0f}""" in front
assert """c.list.image(c.textures.switch2_header(), header,
                         {0.0f, 1.0f, 1.0f, -1.0f}""" not in front
assert "c.textures.switch_logo()" in front
assert """c.list.image(c.textures.switch_logo(), logo,
                         {0.0f, 0.0f, 1.0f, 1.0f}""" in front
assert """c.list.image(c.textures.switch_logo(), logo,
                         {0.0f, 1.0f, 1.0f, -1.0f}""" not in front
back = library.split("void flat_back_fallback(", 1)[1].split("void flat_composed_ink(", 1)[0]
assert """c.list.image(c.textures.switch_rear_footer(), footer,
                     {0.0f, 0.0f, 1.0f, 1.0f}""" in back
assert """c.list.image(c.textures.switch_rear_footer(), footer,
                     {0.0f, 1.0f, 1.0f, -1.0f}""" not in back
assert "kHeaderAspect = 246.0f / 1164.0f" in front
# Original retail scans retain precedence: no NS2 strip is painted over them.
sleeve = library.split("void flat_retail_sleeve(", 1)[1].split("std::string controller_profile_name(", 1)[0]
assert sleeve.index("if (artwork.texture != 0)") < sleeve.index("flat_composed_ink(c, game, paper, rear)")
assert "ns2_case ? Color::rgb(" in sleeve
assert "const std::string& scan = rear ? game.box_back : game.box_front;" in sleeve
assert "ns2_case ? Color::rgb(" in launcher
assert "launch_box_spine_ = case_art.spine;" in launcher
assert "c.list.case_spine_image(ink.texture, side_strip, angle," in launcher
assert "if (ink.texture != 0)" in launcher
assert "c.list.case_spine_blank(" in launcher
assert "launch_case_game_.title_id = title_id;" in launcher

for path in (texture_header, textures):
    assert "switch2_header_" in path
assert 'load("art/ns2-head.tga", &switch2_header_)' in textures
assert "switch2_header_})" in textures
for path in (packaging, staging, read("tools/launcher/render-art.py")):
    assert "ns2-head" in path

encoded = root / "headless/prosperoeden/ui/art/ns2-head.png.b64"
data = base64.b64decode(encoded.read_text().strip(), validate=True)
assert data[:8] == bytes((137, 80, 78, 71, 13, 10, 26, 10))
assert struct.unpack(">II", data[16:24]) == (660, 140)
assert hashlib.sha256(data).hexdigest() == (
    "4dcd4cb6a4580d31c1174d7a2531fc17232b5e6c2b3c0e03e96ed04d6fdc200e"
), "the attached NS2 header source changed unexpectedly"

assert 'PE_PREVIEW_NS2' in fixture
assert '0x0400C3F00006E000ull' in fixture
assert 'PE_PREVIEW_NS2: "1"' in preview
for folder in ("launch-case-ns2-retail", "launch-case-ns2-fallback",
               "launch-case-ns2-library"):
    assert folder in preview, folder
assert "PE_PREVIEW_NO_BOX_SCANS" in preview
assert "build-launch-case-ns2-fallback.log" in preview
print("NS1/NS2 case art, real spine, red shell and preview coverage: PASS")
