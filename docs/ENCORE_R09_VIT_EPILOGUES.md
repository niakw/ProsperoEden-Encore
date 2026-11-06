# R09 — ViT activation et résidu RDNA2 / Vulkan

Le moteur enregistre et génère désormais les deux shaders portables déjà présents dans le vendor : `vit_activation_rdna2.comp` (GEMM FP32 → activation cubique → FP16 → FP8) et `vit_residual_rdna2.comp` (projection FP32 + branche résiduelle FP8 pondérée par coefficients FP16 → E4M3FN).

`rdna2_nr_vit_epilogue_policy.h` valide dimensions, alignements, capacités de buffers et indices 32 bits avant tout dispatch. Il couvre les dimensions ViT (1024/4096 canaux) et la réutilisation future sur les projections résiduelles Split-Swin (512 canaux). Le test hôte `test_rdna2_nr_vit_epilogue_policy` vérifie ces frontières ; `test-rdna2-vit-epilogues-spv.py` compile les deux shaders avec `glslangValidator`, vérifie `spirv-val`, la géométrie 128×1×1, les 2/4 bindings et les 4/6 push constants, puis produit les deux headers SPIR-V pour la compilation native PS5.

Ce code complète la disponibilité des deux primitives. Il **ne raccorde pas encore** l'intégralité des étapes de FFN/ViT, leurs poids résiduels ni l'image finale. Aucune CI Vulkan ni exécution console attestée.
