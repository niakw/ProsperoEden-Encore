#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
patch = (root / 'headless/backports/eden-sm-host-wait.patch').read_text()
audio = (root / 'vendor/encore-active/eden-backports/src/core/hle/service/audio/audio_controller.cpp').read_text()
audio_h = (root / 'vendor/encore-active/eden-backports/src/core/hle/service/audio/audio_controller.h').read_text()

for needle in (
    'Kernel::GetCurrentThread(kernel).IsDummyThread()',
    'std::this_thread::sleep_for(1ms)',
    'SessionRequestHandlerFactory factory',
    'std::scoped_lock',
):
    assert needle in patch, needle
assert 'kernel.IsShuttingDown()' not in patch
assert 'GetCurrentEmuThread' not in patch
assert 'audio/audio_controller.cpp' not in patch
assert 'audio/audio_controller.h' not in patch

assert 'm_set_sys =\n        system.ServiceManager().GetService' not in audio
for needle in (
    'IAudioController::GetSetSys()',
    'std::call_once(m_set_sys_once',
    'GetSetSys()->GetAudioOutputMode',
    'GetSetSys()->SetAudioOutputMode',
    'system.AudioCore().SetInputTargetForceEnabled(enabled)',
):
    assert needle in audio, needle
for needle in ('std::once_flag m_set_sys_once', 'GetSetSys();'):
    assert needle in audio_h, needle

print('Host-thread-safe blocking services + final-owner lazy audctl PASS')
