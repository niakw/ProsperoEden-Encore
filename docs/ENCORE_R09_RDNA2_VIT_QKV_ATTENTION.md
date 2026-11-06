# Eden Encore — R09 : ViT GPU QKV + attention RDNA2

6 novembre 2026 — PR #24, hors main — portage fonctionnel **partiel**.

## Nouveau sous-graphe de trois dispatchs

`NrRdna2VitQkvAttentionLink` enregistre sur le **même scheduler Vulkan** :

1. `NrRdna2Projection` : GEMM FP8 [2560,1024] × [3072,1024] → FP32 [2560,3072].
2. Nouveau `NrRdna2VitQkvNorm` : sépare Q/K/V en trois buffers E4M3FN [2560,32,32], normalise Q et K par tête, applique à Q `sqrt(32) × temperature[head]`, conserve V non normalisé.
3. `NrRdna2VitAttention` : attention globale Q/K/V, contexte FP8 [2560,32,32].

Le kernel ViT QKV est en Vulkan 1.1, sans coopérative FP8 ni HIP. Chaque passage possède ses descripteurs `STORAGE_BUFFER`, ses constantes vérifiées, sa barrière GPU compute→compute et ses limites d'adressage. Le raccord lie explicitement les **mêmes buffers** de production et de consommation, sans aller-retour CPU. Il vérifie la présence et la non-identité des 8 buffers physiques ; l'appelant conserve leur propriété jusqu'à la fin GPU. Aucun poids ou modèle propriétaire inclus.

## Validation et limites

- Contrat hôte : dimension 2560 tokens du modèle 1080p, limite 4096 tokens, 32 têtes de 32 dimensions, tailles FP32/FP8, offsets, 256 MiB par buffer, ressources disjointes.
- Test hôte `test_rdna2_nr_vit_qkv_norm_policy` : trois volumes de tensors du chemin, cas de mémoire insuffisante et frontières, référence mathématique normalisation Q/K.
- Shader : `test-rdna2-vit-qkv-norm-spv.py` valide SPIR-V Vulkan 1.1, 5 bindings et 24 octets de push constants. CMake natif enregistre les deux sources GPU et le générateur de shader.
- **Aucune exécution shader GPU, aucune CI, aucun rendu PS5 ne sont encore attestés** au moment de ce commit.

Ce sous-graphe n'est pas encore l'assemblage des **40 opérations ViT de chaque modèle**. Il manque notamment les FFN expand/contract, les projections résiduelles, l'import réel des matrices QKV et des températures FP32 depuis NRMODEL1, les liens interblocs, le Split-Swin et la sortie renderer. Les arrondis FP32→FP16→FP8 et réductions ne prétendent pas être identiques à NVIDIA ; une comparaison numérique hôte/GPU de référence reste requise. Ce code ne rend pas DLSS-NR activable sur PS5.

## Importeur local de poids ViT QKV

Le vendor contient `nr_rdna2_vit_qkv_weight_loader.h`. Il lit un **NRMODEL1 fourni localement**, exactement sous les noms `unpacked/blockN.layerM.layer.{header,q,k,v}.bin` produits par l'extracteur MIT. Les matrices Q, K et V [1024,1024] sont concaténées dans l'ordre row-major [3072,1024], avec conversion E4M3 prévue par le projet. Le header de 128 octets fournit les 32 températures FP32 par tête, refusées si non finies. Tout échec de forme/lecture/poids NaN efface la sortie : pas de réseau partiellement initialisé.

Le test hôte `test_rdna2_nr_vit_qkv_weight_loader` génère un **modèle NRMODEL1 entièrement synthétique** sur le disque temporaire, vérifie l'import Q/K/V, les 32 températures, le rejet d'un header NaN, d'un poids NaN, d'un nom de dossier dangereux et d'une matrice tronquée. Aucun poids commercial n'est conservé dans le dépôt. Le vendor fournit désormais `NrRdna2VitModelBuffers` : deux allocations GPU immuables créées via `NrRdna2GpuWeights`, contenant respectivement les matrices FP8 et les 32 températures FP32. `NrRdna2VitQkvAttentionLink::InitializeWithModel` les importe, les alloue et les lie directement à son sous-graphe de trois dispatchs. L'upload est transactionnel et les buffers sont retenus par l'objet jusqu'à sa destruction ; l'appelant doit respecter les clôtures GPU normales du scheduler. Les autres buffers (activation, FP32 temporaire, Q/K/V, sortie) restent fournis par le renderer. Pas d'activation PS5 ni d'image démontrée.

## Découpage GPU par tokens — correction de couverture

Le chemin ViT n'exige plus un seul GEMM sur la totalité des tokens. `BuildVitQkvBatches` prévalide **toutes** les projections [T,3072] et normalisations avant le premier enregistrement Vulkan, puis exécute des lots successifs avec le **même** buffer FP32 temporaire. Chaque lot lit le décalage correspondant dans l'activation FP8 [T,1024] et écrit Q/K/V à des offsets disjoints ; l'attention globale attend les trois tenseurs **complets**.

Le budget `kMaxProducts` et la taille réelle du temporaire déterminent la taille des lots (16 maximum, pas de débordement caché). Corpus 1080p de 2560 tokens : un lot si FP32 complet disponible. Exemple 4096 tokens : deux lots de 2048 avec un temporaire de 24 Mio. Tests `test_rdna2_nr_vit_qkv_batches_policy` : dimensions natives, 4096, offsets, capacités et rejet atomique d'un programme incomplet. Ce code permet une forme mémoire validée ; il n'atteste pas la rapidité ni la précision de l'exécution sur PS5.

## Allocations Vulkan autonomes du sous-graphe ViT

`NrRdna2VitGpuTensors` alloue via le VMA du moteur cinq buffers GPU : temporaire FP32 réutilisé pour la GEMM, Q, K, V et contexte final, avec limite de 512 Mio combinés et `maxStorageBufferRange` par buffer. `NrRdna2VitQkvSubgraph` raccorde l'entrée E4M3 déjà fournie par l'étape précédente sur GPU, les poids/32 températures importés de NRMODEL1, le plan de batches et l'attention. Il expose le buffer contexte sans recopie CPU.

Le propriétaire du renderer doit garder en vie le buffer d'entrée et attendre la complétion du scheduler avant de libérer les ressources. Cette intégration ne connecte **pas encore** les autres couches ViT ni le pré/post-image ni le renderer PS5. Test hôte `test_rdna2_nr_vit_gpu_tensors_policy` ajouté ; compilation PS5/Vulkan non confirmée.
