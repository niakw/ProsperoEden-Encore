# R09 — sortie standard FP16 et intensité 65 %

Date : 7 novembre 2026, modèle neuronal Original/Compact.

Le shader `nohistory_compose_rdna2.comp` décode les trois premiers
canaux appris du head FP16 et produit le résultat colorimétrique
`clamp(proxy + residual × 0,25, 0, 1)`.

Le résultat RGB est désormais **tronqué vers zéro à la précision FP16**
avant publication, conformément à la frontière native de sortie.
L'intensité utilisateur est appliquée entre proxy et résultat neuronal
avant cette troncature. L'alpha est conservé séparément.

Le test R09 sur Vulkan logiciel exerce une **intensité de 65 %** :
capture de la texture, composition avec résidus FP16 contrôlés et
publication vers une `VkImage`, puis lecture de pixels et
comparaison à un oracle C++ FP16 indépendant. Ce test n'emploie pas
les poids propriétaires NVIDIA et ne démontre pas la parité du
réseau complet Original/Compact.

Référence mathématique indépendante :
https://github.com/maanHimself/OpenDLSS-NR/blob/main/demo/shaders/nr_composite.comp

Aucune optimisation, aucun build PS5 global.
