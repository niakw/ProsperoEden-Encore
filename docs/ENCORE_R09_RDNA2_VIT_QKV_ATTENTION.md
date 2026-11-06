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

Le test hôte `test_rdna2_nr_vit_qkv_weight_loader` génère un **modèle NRMODEL1 entièrement synthétique** sur le disque temporaire, vérifie l'import Q/K/V, les 32 températures, le rejet d'un header NaN, d'un poids NaN, d'un nom de dossier dangereux et d'une matrice tronquée. Aucun poids commercial n'est conservé dans le dépôt. L'envoi de ces matrices vers deux allocations VMA GPU (poids + températures) demeure à câbler pour une initialisation automatique du sous-graphe.
