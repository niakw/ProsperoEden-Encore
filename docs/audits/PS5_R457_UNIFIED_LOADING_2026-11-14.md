# R457 — unified GL/Vulkan loading candidate, 2026-11-14

## Symptom

PS5 R457 (engine cbfab557e1c8cd459d67c6afae7353ca20000ab3) shows a black interval after launcher selection, then a static jacket with only the lower portion of the Vulkan loading scene visible. NS2 core loading measured about 14.8 s for Bananza and 40.5 s for Mario Kart World before game_loaded; neither produced a first guest frame.

This change addresses native presentation continuity only. It does not manufacture a guest frame or claim to fix NS2 execution.

## Root cause in selected source

1. RunApp destroyed the launcher EGL surface and called eglTerminate before returning the selected game.
2. The pinned PS5 OpenGL runtime eglTerminate calls ps5_agc_gate2_shutdown_present, which drains and closes its VideoOut handle.
3. System::Load can then run for many seconds before the Vulkan renderer exists.
4. The later workaround read the final launcher picture back with glReadPixels, uploaded it to Vulkan, and clipped loading_scene.glsl to the lower fifth. This explains the static jacket plus purple band.

## Upstream / related evidence

- PS5 Vulkan tools R53 (vendor/sources/ps5-vulkan-tools/jobs/r53-output-retention/README.md) documents the same class of blank handover: close/reopen VideoOut produced roughly 0.3–0.76 s black gaps in RetroArch; retaining the output yielded zero black presents in those tests. This supports the ownership strategy but is not Encore console proof.
- Active PS5 Mesa WSI already retains one VideoOut across Vulkan swapchain/device recreation. The missing bridge is OpenGL launcher to Vulkan WSI.
- EglantinePS5 uses the shared loading shader on its OpenGL path; Encore had regressed to a solid dark fragment while Vulkan still compiled loading_scene.glsl.

## Candidate design

- Present one full-screen loading_scene.glsl frame before launch.
- Destroy launcher GL context/surface but defer eglTerminate, retaining the last scanout through System::Load.
- OpenGL games release the deferred launcher display before their own display-mode setup.
- Vulkan releases it immediately before CreateSurface.
- Vulkan presents the same loading_scene.glsl fullscreen from t=1 s.
- Retire active jacket readback/upload, transfer barriers, high-bit marker and lower-fifth scissor.
- Keep bounded 10 s / 30 s no-guest-frame diagnostics.

## Validation

Host/source contracts assert selected ownership, vendor eglTerminate/VideoOut close behavior, shared shader identity, fullscreen Vulkan scissor and absence of the jacket upload path.

Not yet proven: physical PS5 continuity at takeover, native package build, Bananza/MKW first frame, FC27 intro/text/frame pacing. Console acceptance must pin exact engine/vendor SHAs.