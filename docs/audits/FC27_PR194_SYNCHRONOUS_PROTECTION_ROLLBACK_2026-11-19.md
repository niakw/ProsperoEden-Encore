# FC27 — sécurité des textures, retrait ciblé de PR #194, 19 novembre 2026

Le binaire PS5 testé sur FC27 était moteur `4a5b8cc05a662130b9033f7d9b97869c8df3310a`, vendor `8e564f61`, et utilisait la publication différée des décomptes de pages mémoire de la [PR #194](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/194). Le test utilisateur `logs19111615.zip` confirme toujours de graves retards HUD, 28,77 FPS moyens et le **retour des textures incorrectes des maillots**. Il ne contient pas de preuve qu'une opération différée précise a détruit une texture : attribution causale encore ouverte.

La comparaison avec [Lichii #1518](https://github.com/zortos293/Lichii/pull/1518) révèle une différence de synchronisation importante : upstream réserve la déférence aux threads non propriétaires du GPU scheduler (`!GpuSplit::OwnsScheduler()`), tandis qu'Encore n'a pas démontré de garde équivalente. L'optimisation n'avait pas été qualifiée sur la console avant son déploiement.

## Retrait de l'optimisation risquée, sans perdre les autres correctifs

Le vendor [`87b5a4d674e2a1616cd19b5234203e80920abcc4`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/87b5a4d674e2a1616cd19b5234203e80920abcc4) restaure les fichiers de production **exactement** dans leur version synchrone pré-#194 :
- `encore-active/eden-vulkan/vulkan_rasterizer.cpp` Git blob `01c6880e5a8836da45601b0a3cb7c0fd6c46cf35`.
- `encore-active/eden-core/overrides/core/device_memory_manager.inc` Git blob `daf493ce6e863397ec44bfae467c4f7533570477`.

Le header de déférence est supprimé (pas de paramètre `EXPERIMENTAL`). Le vrai `ns2-astc` TextureCache conserve `ImagePages::Mark` dense et sparse ; les corrections JIT A64 16 MiB, buffers GPU-dirty, shaders et RomFS NS2 index 0 ne sont pas retirées.

L'ancienne entrée de test `tests/fc27_deferred_page_protection_host.py` est conservée pour compatibilité des workflows, mais vérifie désormais les méthodes synchrones C++ exactes sous Clang/GCC + UBSan, le traitement GPU-modified, le cache texture, shader invalidate et write-ahead. La correction du nombre attendu d'appels dans le harnais est dans vendor `26be71bf` ; le workflow de statut a été corrigé en `87b5a4d6`. Le moteur réépingle ce vendor et qualifie les sources par blobs exacts et test ciblé.

**Limites** : retour source et test hôte seulement. Le correctif du maillot n'est **pas confirmé** avant un vrai build PS5, contrôle de l'ELF/ZIP et un test FC27 du même match, cache comparable, maillots, textes, intro, fluidité, fermeture/réouverture. NS2 reste P0, première frame non validée. Conserver [FC27 #100](https://github.com/niakw/ProsperoEden-Encore/issues/100) et [NS2 #123](https://github.com/niakw/ProsperoEden-Encore/issues/123) ouverts.
