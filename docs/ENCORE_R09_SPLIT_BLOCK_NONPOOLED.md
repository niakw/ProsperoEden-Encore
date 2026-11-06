# Eden Encore — R09 : bloc GPU Split-Swin — étape initiale et extension ProjPool (06/11/2026)

## Portage fonctionnel au niveau d'un bloc

Le vendor possède maintenant `NrRdna2SplitSwinBlock`, qui importe les quatre couches d'un **même bloc 16 têtes** depuis le NRMODEL1 local, et enregistre les dispatchs Vulkan dans l'ordre suivant :

1. `CCSplitSwin16HFfwd` : `NrRdna2SplitFfwdLayer`, trois jeux de poids W1/W2/W3 reconstruits exactement depuis les deux fichiers canoniques `ffwd_a/ffwd_b`, sortie FP8 512 canaux.
2. `CCSplitSwin16HFfwdProj` : GEMM FP8→FP32 puis résidu FP16 pondéré par la branche d'entrée, résultat FP8.
3. `CCSplitSwin16HQKVAttn` : Q/K/V normalisés sur 16 têtes, attention 64×64 biaisée, contexte FP8.
4. Réagencement GPU `[window][head][token][channel]` → `[window][token][head][channel]`, via `NrRdna2SplitContextRepack`, indispensable avant la dernière projection.
5. `CCSplitSwin16HProj` : GEMM puis résidu avec la sortie de `FFWDProj`.

Les modèles sont référencés via `unpacked-splitswin/blockN.layer{0,1,2,3}.layer` ; chaque sous-composant conserve ses poids GPU et jeux de descripteurs sur le même scheduler. Le scratch FP32 peut être réutilisé entre les deux GEMM grâce aux barrières de commandes, tandis que les flux intermédiaires FP8 sont distincts. La construction est transactionnelle : en cas d'échec de l'une des importations, **aucun bloc partiellement initialisé n'est publié**.

`CanSplitBlock` prévalide la totalité des dimensions et des capacités des dix buffers ; `test_rdna2_nr_split_block_policy` vérifie les 40 fenêtres du modèle 1080p, la borne, les tailles insuffisantes et le refus de `ProjPool`. Les 10 buffers physiques doivent être non aliasants et rester détenus par le renderer jusqu'à la fin des travaux GPU.

## Limites réelles

- Ce raccord n'est valide que pour les **blocs dont la dernière couche est une projection simple**, pas `CCSplitSwin16HProjPool`. Cette dernière produit une deuxième sortie de sous-échantillonnage, encore absente : elle est **explicitement refusée**, jamais silencieusement ignorée.
- L'entrée GPU doit déjà être en format row-major FP8 avec valeurs correctes et padding initialisé. La conversion/validation depuis les tenseurs FSwin amont et la preuve des halos de tuiles ne sont pas intégrées ici.
- Les dépendances entre blocs, le décodage de toutes les étapes Original/Compact et la sortie image finale restent ouvertes.
- **Le code est publié, mais l'exécution d'un bloc sur GPU, la compilation PS5 et la correspondance numérique de sortie ne sont pas encore démontrées.** Pas d'activation NR en jeu ni de branche expérimentale.


## Extension native ProjPool publiée après cette étape

Le refus originel de `ProjPool` est remplacé par une prise en charge **conditionnelle à la fourniture de la géométrie réelle et de la seconde sortie GPU**. La projection standard ne suffit toujours pas seule : `NrRdna2SplitProjectionPool` lit le GEMM FP32 et les coefficients FP16 pour produire le vrai second résultat half-precision→FP8, y compris padding/tail à zéro. Le plan continue de refuser les dimensions ou capacités manquantes. Voir `docs/ENCORE_R09_SPLIT_PROJECTION_POOL.md`. Les limitations historiques ci-dessus décrivent le lot initial, et non le périmètre courant du bloc.


## Raccord du dernier étage FinalHead

Pour le bloc terminal du modèle, le même `NrRdna2SplitSwinBlock` peut maintenant appeler directement la dernière couche `FinalHead` après la seconde sortie `ProjPool`. Le plan indique explicitement `final_head_tokens` (0 pour les blocs sans FinalHead), et le renderer fournit `final_fp32` + `final_output` non aliasants ; si ces ressources manquent, l'initialisation du bloc **échoue sans exécuter une chaîne partielle**. Le test hôte `test_rdna2_nr_split_block_policy` vérifie le contrat complet 60×33 et 1920 tokens, les buffers insuffisants, et le refus de `FinalHead` hors `ProjPool`. L'implémentation effectue les trois dernières dépendances GPU dans le même scheduler : projection résiduelle → pooling half-precision → GEMM 512→1024 et quantification E4M3FN. Les buffers restent externes et l'ensemble du graphe n'est pas encore terminé.
