# Eden Encore R457 — audit des artefacts et avertissements CI (11 novembre 2026)

## Périmètre et limites de preuve

- Code de référence : moteur \`ec8b519182532d3864c5a67dd27aa41aa9d43ff3\`, vendor épinglé \`90c9c8a203a27181e23349a889a8f2a7d1cd9dd2\`.
- [Run R457 récupéré #42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990) : SUCCESS (13/13 étapes du job) ; restauration de cache, liaison, signature/staging, deux ZIP, SHA-256 et upload.
- Archives inspectées **localement**, par ouverture ZIP et contrôle CRC des membres, SHA-256 et comparaison byte-for-byte des fichiers communs : bundle Actions (6 entrées), ZIP complet (258), FTP ZIP (78), artifact FTP brut (185). Absence de corruption, doublons et chemin ZIP dangereux sur les deux ZIP de distribution.
- Empreintes du \`dist/SHA256SUMS\` vérifiées : complet \`3b39c603fb97e558e5fe815fb0f77def475ab874adaf43ae9b8bdae488f3df3a\`, FTP minimal \`7b87abb567247cf06cdfc7adc7cd498e7826367d1a5548b8d000a3a19e63f474\`.
- Le ZIP FTP est intentionnellement réduit : \`tools/ci/make-dist.py\` exclut les notices légales et les compagnons \`.txt\` (FTP ASCII auto), mais conserve 31 catalogues \`.po\`. Le bundle complet conserve tout. Ce **n'est pas** un manque de langues dans le ZIP FTP.
- **Limite :** ceci n'est ni une installation réelle sur console, ni une vérification des FPS, de l'audio, de l'image NS1/NS2 ou de la concordance avec un dump PS5 exécuté.

## Anomalies de packaging réellement observées

| Priorité | Diagnostic | Run / effet | Correction préparée |
| --- | --- | --- | --- |
| P0 | \`crash-provenance.json\` référence \`link.map\` (54 464 368 octets), mais l'artefact de symboles ne l'embarque pas | #42942150990 : bundle incomplet pour analyse avancée des crashs | Copier \`build/headless-native/link.map\` sous \`build/symbols/link.map\` et comparer taille et SHA-256 au reçu, bloquer si écart |
| P1 | Fond quotidien optionnel : \`fetch_daily_switch.py\` exige \`magick\` ImageMagick 7, alors que l'Ubuntu runner expose \`convert\` et \`identify\` ImageMagick 6 | #42942150990 : repli sur le fond Encore | Choisir correctement les commandes 6/7, conserver limites mémoire et dimensions, vérification hôte sans réseau |
| P2 | \`iCCP\` : profil ICC RGB incorrect sur une image PNG gris \`switch-rear-footer.png\` | #42942150990 : warning ImageMagick, conversion poursuivie | Recréer/normaliser **l'actif source** sans profil incohérent après vérification visuelle ; ne pas masquer stderr |
| Réglé en CI | ZIP de distribution inexistant / mauvais nom puis \`SHA256SUMS\` vérifié depuis mauvais répertoire | #42938625487, #42941245433 rouges | Correctifs déjà présents dans R457 : fichier attendu contrôlé et \`(cd dist && sha256sum --check --strict SHA256SUMS)\` |

## Journaux natifs lourds et warnings — triage par propriétaire

- [Run #42911552038](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42911552038) (11e tentative environ) : compilation native effective, échec \`libwebp\` avec \`SSE2 register return with SSE2 disabled\` sur \`sharpyuv_gamma.c\`, autres TUs WebP et \`graphics.cpp\`. Défaut bloquant historique ; le run R457 a depuis produit un paquet, sans prouver à lui seul qu'une nouvelle compilation complète aurait réussi avec le même graphe.
- [Run #42924336057](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42924336057) (12e tentative) : les 1 398 étapes avant lien avaient progressé, échec de l'édition de liens sur fonctions Vulkan et émetteurs atomiques du shader (\`vkCmdDispatch\`, \`vkCmdBindDescriptorSets\`, \`EmitStorageAtomicCompareExchange32\`, etc.). Les reconstructions ciblées et le relink de #42942150990 ont résolu l'échec de lien **pour le binaire candidat**.
- **Mesa/NIR/RADV (bibliothèques de préparation tierces)** : très nombreux \`-Wunused-but-set-variable\` à partir de \`nir.h\`, \`radv_shader.c\`, \`radv_postprocess_nir_standalone.c\`, \`psbc_compile.c\`. Ce sont des warnings récurrents de la même famille, pas autant de régressions indépendantes. Ne pas modifier les snapshots externes ni retirer globalement les avertissements.
- **Mesa SPIR-V (priorité haute à qualifier)** : \`-Wreturn-type\` sur plusieurs \`spirv_to_nir.c\`, \`vtn_alu.c\`, \`vtn_variables.c\`, \`vtn_structured_cfg.c\` ; \`-Wmaybe-uninitialized\` (ex. \`vtn_subgroup.c\`, \`vtn_variables.c\`). Examiner macros abort/unreachable, versions de compilateur et préconditions avant de décider si vrai problème de flot ou faux positif.
- **Vendor NS2 Ampere (priorité haute à qualifier)** : conversions signées/non signées et pertes de précision dans \`frontend/ampere/lower_to_maxwell.h\`, \`capture.cpp\` et \`probe.cpp\`. Réserver un audit de domaines des valeurs sur une branche vendor isolée ; des casts pour faire disparaître les warnings peuvent introduire des régressions shader NS1/NS2.
- **CMake/paquets tiers** : Opus \`Could not get package version\` (version affichée 0, source épinglée \`a3f0ec02b3\`) ; SDL3 \`Unable to find the alsa development library\` (sonde ALSA hôte). Qualifier le mode de compilation et les fonctionnalités effectivement activées avant de modifier la configuration. Absence d'ALSA sur un hôte de build PS5 n'est pas automatiquement un défaut audio PS5.
- **UI/i18n** : avertissements de dépassement de libellés en plusieurs langues et glyphes non vérifiés pour certaines polices. Ne pas raccourcir massivement les traductions sans vérifier le sens et les composants UI réels.

## Règles de clôture

1. **Pas de nouveau build PS5 lourd** pour nettoyer des logs. Corriger par propriétaire, utiliser source-preflight et témoins hôtes, puis seulement un nouveau build explicitement approuvé.
2. Garder \`main\` et \`vendor\` inchangés tant que le correctif de packaging et les tests ciblés ne sont pas validés sur branche.
3. **Aucune release publiée** ; le brouillon R2 reste séparé et sans assets.
4. Actualiser ce rapport et les preuves après exécution des CI de branche ; ne pas écrire « tous warnings réglés » avant validation.
