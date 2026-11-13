// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Short, option-specific guidance shared by global and per-game settings.
// The highlighted help panel is separate from small secondary footer text.
#include "pe/ui/widgets.hpp"
#include "neural_video_policy.h"
#include "pe/core/strings.hpp"
#include <string_view>

namespace pe::ui {
inline const char* UpscalingGuide(int filter) {
    switch (filter) {
    case 0: return tr(TR("Bilinear: fast and soft. Best when the game already renders near the TV resolution."));
    case 1: return tr(TR("AMD FSR 1: EASU enlarges the picture; RCAS adds sharpness. Most useful below the TV output resolution."));
    case 2: return tr(TR("Bicubic: sharper than bilinear, but may create bright edges. The sharpness slider does not apply."));
    case 3: return tr(TR("Nearest: keeps hard pixel edges, with visible stair-steps. Best for pixel art, not most 3D games."));
    case 4: return tr(TR("Lanczos: sharp reconstruction of a scaled image. Fine detail may look clearer, but edges can form bright halos."));
    case 5: return tr(TR("SGSR: Qualcomm spatial upscale using a separate Vulkan shader. Try it when FSR 1 looks soft."));
    case 6: return tr(TR("SGSR Edge: edge-directed Qualcomm upscale with a different Vulkan shader. Compare fine detail and halos."));
    case 7: return tr(TR("A4K — Détails améliorés : réseau neuronal pour améliorer les contours et les détails de l’image en 3D. Nécessite Vulkan et un agrandissement x2."));
    case 8: return tr(TR("A4K — Image adoucie : restauration douce avant amélioration des détails. Utile si les contours sont trop durs. Plus coûteux pour le GPU."));
    case 9: return tr(TR("A4K — Image nettoyée : reconstruction neurale avec débruitage. Utile si l’image présente du grain ou des artefacts, avec agrandissement x2."));
    default: return tr(TR("Bilinear: fast and soft. Best when the game already renders near the TV resolution."));
    }
}
inline const char* AntiAliasingGuide(int aa) {
    switch (aa) {
    case 0: return tr(TR("Off: no edge smoothing. Fastest, but diagonal lines may look jagged."));
    case 1: return tr(TR("FXAA: lightweight edge smoothing in one pass. It can slightly soften text and fine details."));
    case 3: return tr(TR("FXAA+: extended edge search. Can smooth more jagged edges but may soften textures. Compare with SMAA Ultra."));
    // Do not describe MSAA as SMAA. The per-title forced-MSAA Vulkan
    // compositor is not yet console-qualified; exact mode labels are
    // already translatable via the shared settings catalog.
    case 4: return tr(TR("MSAA 2x"));
    case 5: return tr(TR("MSAA 4x"));
    case 6: return tr(TR("MSAA 8x"));
    case 7: return tr(TR("MSAA 16x"));
    default: return tr(TR("SMAA Ultra: high-quality multi-pass edge smoothing. Clearer contours but more GPU work than FXAA."));
    }
}
inline const char* SharpnessGuide(int filter,bool renderer_compatible) {
    if (!renderer_compatible || (filter != 1 && filter != 5 && filter != 6))
        return tr(TR("Inactive: this upscale method does not support the sharpness slider. Use FSR 1 or SGSR with Vulkan."));
    if (filter == 1)
        return tr(TR("Only AMD FSR 1 uses this percentage. Start at 50%. Increase gently for detail; reduce if edges shimmer or show halos."));
    return tr(TR("SGSR edge sharpness: 0% disables extra edge intensity, 50% is balanced, 100% is strongest. Reduce halos if needed."));
}
inline const char* UpscalingUnsupportedGuide() {
    return tr(TR("Ce traitement nécessite Vulkan. Choisis Vulkan ou un autre agrandissement d’image pour éviter un retour automatique au bilinéaire."));
}
inline const char* FxaaUnsupportedGuide() {
    return tr(TR("FXAA+ requires Vulkan. Choose Vulkan or another anti-aliasing method."));
}
inline const char* FramegenUnsupportedGuide() {
    return tr(TR("This option needs Vulkan. OpenGL cannot generate extra frames; changing it would have no effect."));
}
// The six choices are directly visible in NR; there is no separate
// A4K/DLSS family selector or duplicate model submenu.
inline const char* NeuralModeName(int mode) {
    using namespace Eden::NeuralVideo;
    switch(mode) {
    case kA4kDetail: return tr(TR("A4K — Détails améliorés"));
    case kA4kSoft: return tr(TR("A4K — Image adoucie"));
    case kA4kDenoise: return tr(TR("A4K — Image nettoyée"));
    case kDlssOriginal: return tr(TR("DLSS-NR — Original"));
    case kDlssCompact: return tr(TR("DLSS-NR — Compact"));
    default: return tr(TR("Désactivé"));
    }
}
inline const char* NeuralModeGuide(int mode) {
    using namespace Eden::NeuralVideo;
    switch(mode) {
    case kA4kDetail:
        return tr(TR("A4K Détails améliorés : réseau de traitement de l'image privilégiant la définition des contours. Un seul moteur NR peut être sélectionné."));
    case kA4kSoft:
        return tr(TR("A4K Image adoucie : réseau de traitement de l'image privilégiant la douceur du rendu et la stabilité des contours."));
    case kA4kDenoise:
        return tr(TR("A4K Image nettoyée : réseau de traitement visant les parasites visuels et le bruit de l'image."));
    case kDlssOriginal:
        return tr(TR("DLSS-NR Original : réseau neuronal complet. Son intensité est configurable par jeu. Le rendu PS5 complet reste à valider."));
    case kDlssCompact:
        return tr(TR("DLSS-NR Compact : réseau neuronal réduit. Son intensité est configurable par jeu. Le rendu PS5 complet reste à valider."));
    default:
        return tr(TR("Neural Rendering est désactivé par défaut. Choisis directement l'un des trois A4K ou l'un des deux DLSS-NR."));
    }
}
inline const char* NeuralStrengthGuide(int mode) {
    if(!Eden::NeuralVideo::IsDlss(mode))
        return tr(TR("L'intensité est propre au DLSS-NR Original/Compact ; elle est inactive en mode A4K ou Désactivé. Le réglage enregistré est conservé."));
    return tr(TR("Intensité du DLSS-NR de 0 à 100 %. Ce réglage ne modifie ni la netteté FSR, ni l'anticrénelage, ni le Frame Generation."));
}
inline const char* NeuralCompatibilityGuide(Eden::NeuralVideo::Reason why) {
    using R=Eden::NeuralVideo::Reason;
    switch(why) {
    case R::RequiresVulkan:
        return tr(TR("Ce Neural Rendering nécessite Vulkan ; OpenGL n'est pas compatible."));
    case R::NeedsExclusiveUpscaler:
        return tr(TR("Pour ce Neural Rendering, choisis Bilinéaire dans Upscaling : les compositions avec les autres méthodes ne sont pas encore validées sur PS5."));
    case R::MsaaUnverified:
        return tr(TR("Le MSAA forcé n'est pas encore validé avec Neural Rendering. Utilise Aucun, FXAA ou SMAA."));
    case R::FrameGenerationUnverified:
        return tr(TR("Neural Rendering et Frame Generation ne sont pas encore validés ensemble. Désactive Frame Generation."));
    case R::EngineIncomplete:
        return tr(TR("Ce moteur n'est pas encore raccordé au rendu complet du jeu."));
    case R::Disabled: return NeuralModeGuide(0);
    case R::Available: return NeuralModeGuide(1);
    }
    return NeuralModeGuide(0);
}
inline const char* TextureGuide() {
    return tr(TR("Texture filtering sharpens roads, floors and walls viewed at an angle. Start at 4x; 8x/16x use more GPU bandwidth. Unlike image sharpness, it does not sharpen the whole picture."));
}
inline void DrawVideoGuide(Canvas& c, std::string_view label,
                           std::string_view explanation,
                           bool inactive = false, bool light_theme = false) {
    constexpr Rect panel{592.0f, 724.0f, 736.0f, 112.0f};
    const Color background = light_theme
        ? Color::rgb(inactive ? 0xfff4e6 : 0xeaf5ff, 0.99f)
        : Color::rgb(inactive ? 0x332617 : 0x101e30, 0.99f);
    const Color ink = light_theme ? Color::rgb(0x172c40) : Color::rgb(0xf2f7ff);
    const Color accent = light_theme
        ? Color::rgb(inactive ? 0x925100 : 0x087a80)
        : Color::rgb(inactive ? 0xffc26e : 0x8cf5d4);
    c.list.rounded_rect(panel, 14.0f, background);
    c.list.rounded_rect({panel.x, panel.y + 8.0f, 5.0f, panel.h - 16.0f},
                        2.5f, accent);
    text_shrink(c, label, panel.x + 18.0f, panel.y + 25.0f,
                17.0f, accent, panel.w - 36.0f);
    // Real measured word wrapping: up to 3 lines, not a single squeezed
    // sentence or an ellipsis that hides the actual instructions.
    text_block(c, explanation, panel.x + 18.0f, panel.y + 51.0f,
               18.0f, 22.0f, ink, panel.w - 38.0f, 3, 0.86f);
}
} // namespace pe::ui
