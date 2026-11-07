# Eden Encore R09 — montée U-Net (7 novembre 2026)

> **Actualisation du 7 novembre 2026 :** les gains FP16 C64/C128/C256
> ont désormais un chemin de reconstruction exact en source depuis les
> deux régions du modèle. La remontée peut être **préparée avant** tout
> enregistrement GPU, puis les quatre skips sont vérifiés comme réellement
> enregistrés au moment du `Record`. Voir
> [gains](ENCORE_R09_UNET_GAIN_RECOVERY_2026-11-07.md) et
> [préparation](ENCORE_R09_PREPARE_BEFORE_GPU_2026-11-07.md).
> Cela ne prouve pas l'inférence numérique sur un GPU.

**Implémentation source, qualification hôte à établir ; aucun rendu PS5 déclaré.**

`NrRdna2UNetUpSequence` construit quatre étapes apprises `NrRdna2UNetUpsampleLink`, enchaînées par quatre `NrRdna2FSwinChain`, depuis un raster FP8 C512 fourni par un bottleneck distinct jusqu'au raster final FP8 C32 (pas une image RGBA).

Le modèle est lu dans les lignes natives Original ou Compact : chaque bloc `_upsample_fp8` est identifié par son vrai numéro et chaque arête vérifie le bloc producteur de son tenseur bas, son skip de même résolution et les `_outview_fp8` intermédiaires. Les quatre skips sont exposés uniquement après `RecordProducer` réussi sur le même scheduler GPU. L'enregistrement du propriétaire est à usage unique : aucune répétition après un échec partiel.

Contrats hôte : dimensions natives transposées en axes Vulkan, C512→C256→C128→C64→C32, offsets/étendues de buffers, sortie raster de chaque niveau, cohérence des blocs et limites de stockage. Tests Original/Compact GCC/Clang+UBSan et syntaxe C++ réelle via R09.

**Pas encore raccordé :** prébloc réellement appris (downsample 1920×1080), sortie C512 du Split-Swin vers l'entrée de la montée, pondération/gains exacts de tous les modèles, postbloc, compositing, cycle du renderer, acquisition des buffers jeu, écran final et performance PS5. Ne pas présenter la fonctionnalité comme disponible en jeu.
