// Native Encore R23 audren:d: complete NS1+NS2 shared audio TU.
// Original active vendor content differs by exactly the registered service class.
// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// SPDX-FileCopyrightText: Copyright 2018 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include "core/core.h"
#include "core/hle/service/audio/audio.h"
#include "core/hle/service/audio/audio_controller.h"
#include "core/hle/service/audio/nx2_audio_user_client.h"
#include "core/hle/service/nx2_streamplay.h"
#include "core/hle/service/audio/audio_in_manager.h"
#include "core/hle/service/audio/audio_out_manager.h"
#include "core/hle/service/audio/audio_renderer_manager.h"
#include "core/hle/service/audio/final_output_recorder_manager.h"
#include "core/hle/service/audio/final_output_recorder_manager_for_applet.h"
#include "core/hle/service/audio/hardware_opus_decoder_manager.h"
#include "core/hle/service/server_manager.h"
#include "core/hle/service/ipc_helpers.h"
#include "core/hle/service/service.h"

namespace Service::Audio {

class IAudioOutManagerForApplet final : public ServiceFramework<IAudioOutManagerForApplet> {
public:
    explicit IAudioOutManagerForApplet(Core::System& system_)
        : ServiceFramework{system_, "audout:a"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioOutManagerForApplet::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IAudioOutManagerForApplet::RejectUnavailableAudioControl, "RequestResume"},
            {2, &IAudioOutManagerForApplet::RejectUnavailableAudioControl, "GetProcessMasterVolume"},
            {3, &IAudioOutManagerForApplet::RejectUnavailableAudioControl, "SetProcessMasterVolume"},
            {4, &IAudioOutManagerForApplet::RejectUnavailableAudioControl, "GetProcessRecordVolume"},
            {5, &IAudioOutManagerForApplet::RejectUnavailableAudioControl, "SetProcessRecordVolume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioSnoopManager final : public ServiceFramework<IAudioSnoopManager> {
public:
    explicit IAudioSnoopManager(Core::System& system_)
        : ServiceFramework{system_, "auddev"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioSnoopManager::RejectUnavailableAudioControl, "GetDspStatistics"},
            {1, &IAudioSnoopManager::RejectUnavailableAudioControl, "GetAppletStateSummaries"},
            {2, &IAudioSnoopManager::RejectUnavailableAudioControl, "SetDspStatisticsParameter"},
            {3, &IAudioSnoopManager::RejectUnavailableAudioControl, "GetDspStatisticsParameter"},
            {6, &IAudioSnoopManager::RejectUnavailableAudioControl, "GetDspUsage"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioInManagerForApplet final : public ServiceFramework<IAudioInManagerForApplet> {
public:
    explicit IAudioInManagerForApplet(Core::System& system_)
        : ServiceFramework{system_, "audin:a"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioInManagerForApplet::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IAudioInManagerForApplet::RejectUnavailableAudioControl, "RequestResume"},
            {2, &IAudioInManagerForApplet::RejectUnavailableAudioControl, "GetProcessMasterVolume"},
            {3, &IAudioInManagerForApplet::RejectUnavailableAudioControl, "SetProcessMasterVolume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioRendererManagerForApplet final : public ServiceFramework<IAudioRendererManagerForApplet> {
public:
    explicit IAudioRendererManagerForApplet(Core::System& system_)
        : ServiceFramework{system_, "audren:a"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "RequestResume"},
            {2, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "GetProcessMasterVolume"},
            {3, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "SetProcessMasterVolume"},
            {4, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "RegisterAppletResourceUserId"},
            {5, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "UnregisterAppletResourceUserId"},
            {6, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "GetProcessRecordVolume"},
            {7, &IAudioRendererManagerForApplet::RejectUnavailableAudioControl, "SetProcessRecordVolume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioOutManagerForDebugger final : public ServiceFramework<IAudioOutManagerForDebugger> {
public:
    explicit IAudioOutManagerForDebugger(Core::System& system_)
        : ServiceFramework{system_, "audout:d"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioOutManagerForDebugger::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IAudioOutManagerForDebugger::RejectUnavailableAudioControl, "RequestResume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioInManagerForDebugger final : public ServiceFramework<IAudioInManagerForDebugger> {
public:
    explicit IAudioInManagerForDebugger(Core::System& system_)
        : ServiceFramework{system_, "audin:d"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioInManagerForDebugger::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IAudioInManagerForDebugger::RejectUnavailableAudioControl, "RequestResume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IFinalOutputRecorderManagerForDebugger final : public ServiceFramework<IFinalOutputRecorderManagerForDebugger> {
public:
    explicit IFinalOutputRecorderManagerForDebugger(Core::System& system_)
        : ServiceFramework{system_, "audrec:d"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IFinalOutputRecorderManagerForDebugger::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IFinalOutputRecorderManagerForDebugger::RejectUnavailableAudioControl, "RequestResume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioRendererManagerForDebugger final : public ServiceFramework<IAudioRendererManagerForDebugger> {
public:
    explicit IAudioRendererManagerForDebugger(Core::System& system_)
        : ServiceFramework{system_, "audren:d"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioRendererManagerForDebugger::RejectUnavailableAudioControl, "RequestSuspend"},
            {1, &IAudioRendererManagerForDebugger::RejectUnavailableAudioControl, "RequestResume"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioSystemManagerForApplet final : public ServiceFramework<IAudioSystemManagerForApplet> {
public:
    explicit IAudioSystemManagerForApplet(Core::System& system_)
        : ServiceFramework{system_, "aud:a"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "RegisterAppletResourceUserId"},
            {1, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "UnregisterAppletResourceUserId"},
            {2, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "RequestSuspendAudio"},
            {3, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "RequestResumeAudio"},
            {4, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "GetAudioOutputProcessMasterVolume"},
            {5, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "SetAudioOutputProcessMasterVolume"},
            {6, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "GetAudioInputProcessMasterVolume"},
            {7, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "SetAudioInputProcessMasterVolume"},
            {8, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "GetAudioOutputProcessRecordVolume"},
            {9, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "SetAudioOutputProcessRecordVolume"},
            {10, &IAudioSystemManagerForApplet::RejectUnavailableAudioControl, "GetAppletStateSummaries"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

class IAudioSystemManagerForDebugger final : public ServiceFramework<IAudioSystemManagerForDebugger> {
public:
    explicit IAudioSystemManagerForDebugger(Core::System& system_)
        : ServiceFramework{system_, "aud:d"} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &IAudioSystemManagerForDebugger::RejectUnavailableAudioControl, "RequestSuspendAudioForDebug"},
            {1, &IAudioSystemManagerForDebugger::RejectUnavailableAudioControl, "RequestResumeAudioForDebug"},
        };
        // clang-format on
        RegisterHandlers(functions);
    }

private:
    void RejectUnavailableAudioControl(HLERequestContext& ctx) {
        // No qualified backend exists for this private/debug audio control surface.
        // Keep audout:u/audin:u/audren:u untouched and fail explicitly.
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(IPC::ResultNotSupported);
    }
};

void LoopProcess(Core::System& system) {
    auto server_manager = std::make_unique<ServerManager>(system);
    // Shared process-owned Sysmix registry: a single 5ms pump feeds the same
    // real host sink for both the virtual-device and mixer services.
    auto sysmix = std::make_shared<Nx2SysmixStreams>(system);

    // Native Switch 2 aud:u delegates to Eden's maintained audout:u and
    // audren:u interfaces, leaving all existing Switch 1 services untouched.
    server_manager->RegisterNamedService("aud:u", std::make_shared<INx2AudioUserClient>(system));
    // Switch 2 virtual audio device discovery is native; stream opening
    // still refuses until the real sysmix ring/audio backend is wired.
    server_manager->RegisterNamedService("auddmg:u",
        std::make_shared<INx2AudioDeviceManagerService>(system, sysmix));
    server_manager->RegisterNamedService("audsmx:u",
        std::make_shared<INx2AudioSoundMixerService>(system, sysmix));
    // The NS2 stream-play user service holds a real guest HID shared memory,
    // not a placeholder event or simulated GameShare stream.
    server_manager->RegisterNamedService("stpl:u", std::make_shared<INx2StreamPlayService>(system));
    server_manager->RegisterNamedService("aud:a", std::make_shared<IAudioSystemManagerForApplet>(system));
    server_manager->RegisterNamedService("aud:d", std::make_shared<IAudioSystemManagerForDebugger>(system));

    server_manager->RegisterNamedService("audout:d", std::make_shared<IAudioOutManagerForDebugger>(system));
    server_manager->RegisterNamedService("audin:d", std::make_shared<IAudioInManagerForDebugger>(system));
    server_manager->RegisterNamedService("audrec:d", std::make_shared<IFinalOutputRecorderManagerForDebugger>(system));
    server_manager->RegisterNamedService("audren:d", std::make_shared<IAudioRendererManagerForDebugger>(system));

    server_manager->RegisterNamedService("audin:u", std::make_shared<IAudioInManager>(system));
    server_manager->RegisterNamedService("audin:a", std::make_shared<IAudioInManagerForApplet>(system));
    server_manager->RegisterNamedService("audout:u", std::make_shared<IAudioOutManager>(system));
    server_manager->RegisterNamedService("audout:a", std::make_shared<IAudioOutManagerForApplet>(system));
    server_manager->RegisterNamedService("auddev", std::make_shared<IAudioSnoopManager>(system));
    // Depends on audout:u and audin:u on ctor!
    server_manager->RegisterNamedService("audctl", std::make_shared<IAudioController>(system));
    server_manager->RegisterNamedService("audrec:a", std::make_shared<IFinalOutputRecorderManagerForApplet>(system));
    server_manager->RegisterNamedService("audrec:u", std::make_shared<IFinalOutputRecorderManager>(system));
    server_manager->RegisterNamedService("audren:u", std::make_shared<IAudioRendererManager>(system));
    server_manager->RegisterNamedService("audren:a", std::make_shared<IAudioRendererManagerForApplet>(system));
    server_manager->RegisterNamedService("hwopus", std::make_shared<IHardwareOpusDecoderManager>(system));
    ServerManager::RunServer(std::move(server_manager));
}

} // namespace Service::Audio
