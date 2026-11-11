# R23 — GPU readback NCE #88/#57 annulé par #47 : preuve nette sur six sources

**11 novembre 2026, audit PR #45 ; sources publiques exactes, aucune modification runtime ni build PS5.**

### Revue des commits

- [#88 `8e2d26c`](https://github.com/eden-emulator/mirror/commit/8e2d26c272681d6cafe6d5e703dafdc8200c7b65) ajoutait un readback du cache GPU en réponse aux invalidations NCE.
- [#57 `0e11fe8`](https://github.com/eden-emulator/mirror/commit/0e11fe8b5e3d3b563946726ed06cb44b2bf5ccb3) propageait ce chemin au Vulkan et ajoutait des réglages de configuration.
- [#47 `b4d5760`](https://github.com/eden-emulator/mirror/commit/b4d5760014176bfc42b60b7dc5661240c97c8e3b) revenait sur le code de readback GPU.

### Comparaison blob Git, pas jugement à partir des titres

**Avant #88 :** parent `f8b76511041bb54070c52d1d09ea07d8108c592a`. **Après #47 :** `b4d5760014176bfc42b60b7dc5661240c97c8e3b`.

| Code comparé | Résultat |
|---|---|
| `src/core/memory.cpp` | Identique SHA Git : `837016de` |
| `src/video_core/gpu.cpp` | Identique : `9901cf42` |
| `src/video_core/gpu.h` | Identique : `75956ea1` |
| `src/video_core/renderer_vulkan/vk_rasterizer.cpp` | Identique : `f43bea12` |
| `src/video_core/renderer_vulkan/vk_rasterizer.h` | Identique : `7470aa4f` |
| `src/video_core/rasterizer_interface.h` | Différence limitée à une notice Eden SPDX en trois lignes, aucune ligne de code supprimée/ajoutée |

**Décision : #88 et #47 clos au niveau source.** Ne pas porter à nouveau le readback NCE annulé dans le moteur PS5 x64. La revue de **#57 reste ouverte** uniquement sur ses autres chemins de paramètres Android/Qt/`src/common/settings.h`, non conclus par cette comparaison. Les autres commits intervenus entre ces deux SHAs ne sont pas réputés automatiquement annulés. Aucun test de GPU PS5 ni comparaison de performance n'est sous-entendu.

**R23 runtime : 78 → 76 décisions ouvertes.** Les cinq fichiers source strictement identiques et la notice en-tête sont directement vérifiables depuis les deux commits Git ; leur preuve ne dépend pas du récit de la PR.
