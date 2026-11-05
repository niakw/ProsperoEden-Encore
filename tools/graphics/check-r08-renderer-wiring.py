#!/usr/bin/env python3
"""Source integrity of native Vulkan R08 bridge; not a PS5 runtime test."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[2]
read = lambda p: (root / p).read_text()
fork = read("headless/vulkan_renderer_r08.cpp")
header = read("headless/renderer_vulkan_r08.h")
cmake = read("headless/vulkan.cmake")
pack = read("tools/package-headless-native.sh")
ses = read("headless/mihawk_native_session.cpp")
vox = read("headless/mihawk_volk.h")
pkg = root / "third_party/PS5_MihawkGen/framegen/models/network.fgw"

def one(text, token):
    assert text.count(token) == 1, (token, text.count(token))
    return text.index(token)

# One authoritative render path. The app's real frame must still present,
# whether the Mihawk snapshot is possible or not.
real_composite = one(fork, "void RendererVulkan::Composite(")
draw = one(fork, "    blit_swapchain.DrawToFrame(device, rasterizer, frame, framebuffers,")
snapshot = one(fork, "Eden::FeatureLab::RecordOwnedSnapshot(snapshot)")
flush = one(fork, "const u64 r08_submitted_tick = scheduler.Flush(*frame->render_ready);")
present = fork.index("    present_manager.Present(frame);", flush)
assert real_composite < draw < snapshot < flush < present
assert "    ::Eden::FrameMetrics::OnRealQueued();" in fork
assert "scheduler.IsFree(tick)" in fork
assert "mihawk_capture_fences.Commit(r08_capture, r08_submitted_tick)" in fork
assert "ValidateOwnedSnapshotInput(snapshot)" in fork
assert "reinterpret_cast<VkCommandBuffer>(1)" not in fork
assert "scheduler.Finish();" in fork
assert "mihawk_native.reset();" in fork
assert "std::unique_ptr<Eden::FeatureLab::MihawkNativeSession>" in header

# No mutations to the authoritative pinned submodule. Encore builds a
# versioned renderer source + explicit header, not CMake regex substitutions.
assert 'vulkan_renderer_r08.cpp' in cmake
assert 'renderer_vulkan_r08.h' in cmake
assert "target_sources(video_core PRIVATE $<TARGET_OBJECTS:eden-mihawkgen-native>)" in cmake
assert "EDEN_BUILD_MIHAWKGEN_CORE" not in cmake
assert "mihawk_native_session.cpp" in cmake

# Volk pointers live in a private C++ namespace; do not collide with the
# exported RADV vkGetInstanceProcAddr function.
assert "#define VOLK_NAMESPACE 1" in vox
assert "using namespace volk;" in vox
assert "volkInitializeCustom(setup.instance_proc)" in ses
assert "volkLoadDevice(setup.device)" in ses
assert 'Eden::AppResourceFile("mihawkgen/network.fgw")' in fork

# The model on disk is copied into the app *and* carries its licence/credits.
assert '$app/mihawkgen/network.fgw' in pack
assert 'MIHAWKGEN_LICENSE.md' in pack
assert 'MIHAWKGEN_THIRD_PARTY_NOTICES.txt' in pack
assert pkg.is_file()
assert pkg.stat().st_size == 1_757_240
assert hashlib.sha256(pkg.read_bytes()).hexdigest() == (
    "31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b"
)

# Snapshot wiring is not the generation/presentation step.
assert "RecordNativeMihawkPair(" not in fork
print("R08 RENDERER BRIDGE SOURCE PASS: real-frame snapshot and model path present; generated frames not yet queued")
