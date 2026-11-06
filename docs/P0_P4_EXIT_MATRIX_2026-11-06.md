# Eden Encore — critères de sortie P0–P4 et frontière P5

**Référence : 6 novembre 2026.** Source de vérité des cases : [issue #15](https://github.com/niakw/ProsperoEden-Encore/issues/15). Ce tableau est une photographie des **critères**, et non une preuve de réussite au SHA le plus récent. Ne pas assimiler une commande Vulkan présente à une image console; ne pas assimiler une absence de trace console à une lacune de code.

**Règle impérative : aucune validation, installation ou capture PS5 n'est exigée pour clôturer P0–P4.** Le build console, les jeux FC27/BOTW/MKW/Bananza, le premier framebuffer et les mesures GPU/VRAM/performances sont uniquement **P5**. Les contrôles source/ABI, tests C++ hôte, CI Linux, modules SPIR-V validés et preuves de provenance restent des critères P0–P4. Ne pas bloquer la clôture du code en attendant une PS5.

| Jalon | État source/hôte au 06/11 | Critères de sortie vérifiables AVANT P5 |
| --- | --- | --- |
| **P0.2 : architecture unique** | **Fermé côté code/hôte** dans #15; choix du moteur PS5 sans options de recherche/release dans CMake final, `vendor` épinglé et NUP conservé | Garder la sélection automatique et les contrats de provenance; la clôture globale P0 demande encore des CI vertes sur le **dernier** SHA |
| **P0 global** | **Ouvert : CI du SHA courant** | Core fast gate, source preflight, NS2 host guards et contrôles obligatoires verts sur le même `main` + gitlink `vendor` |
| **P1.1** | **Ouvert** | Contrats source pour ExeFS/NSO/NPDM, clés/firmwares, formats et CPU6; les observations du PC invité sur PS5 sont **P5**, pas un motif d'ouverture à elles seules |
| **P1.2** | **Ouvert** | GMMU 49 bits/4 KiB, NVMap, GPU-only, rollback OOM, sparse et synchronisation : source et tests négatifs hôte, sans exiger la résidence VRAM réelle PS5 |
| **P1.3** | **Ouvert** | IPC/TIPC, HOS, AM, NVDRV, VI2, audio et décodage vidéo : commandes réellement implémentées, rejets explicites, réponses et handles corrects en source/hôte |
| **P1.4** | **Ouvert** | Matrice de régression NS1 source/ABI/JIT/HLE et mémoire/Vulkan communs sur hôte, sans FC27/BOTW console |
| **P2.2c / P2.3** | **Ouverts** | Interactions TIC/TSC, images et buffers; preuves des CBUF indirects, tableaux de descripteurs, global memory, atomiques, longueurs/permissions/alias et barrières, sur la vraie chaîne QMD3→Vulkan, avec `spirv-val` quand applicable |
| **P2.4** | **Ouvert** | ISA Ampere et pipeline graphics/compute (VertexA/B, Fragment, Geometry, Tessellation, MME/branches) et task/mesh **selon capacités réellement prises en charge** ; aucune instruction inconnue silencieusement acceptée; tests hôte pertinents |
| **P3 : UI/launcher** | **15/15 sous-points code/hôte fermés** dans #15 | Les comportements UI et la preview hôte sont déjà couverts; les jaquettes/transitions réelles sur PS5 relèvent de P5 |
| **P4.1–P4.2** | **Ouverts** | Recette hôte P0–P3 complète, tests positifs/négatifs Clang/GCC + CI, absence de dettes sources, sans GPU physique |
| **P4.3** | **Ouvert** | Dossier de décision référençant **une seule paire** `main` / `vendor`, les tests et CI verts, et les manques de code P0–P4 réellement résolus |
| **P5** | **Non commencé** | Build natif autorisé explicitement, jeux, framebuffer, fidélité graphique, performances et régressions console. **Jamais prérequis aux cases ci-dessus.** |

## Ordre de traitement des restes

1. **Ne pas ajouter de nouvelles abstractions P5 dans le code.** Corriger les échecs réels du dernier SHA, y compris le compilateur SPIR-V Ampere, tout en conservant NS1 et le sous-module `vendor`.
2. **Fermer les vrais manques P1 / P2** : services/gestion mémoire encore incomplets, CBUF/SSBO et pointeurs dynamiques non prouvés, instructions/stages GPU non pris en charge. Refus conservateur lorsque la sémantique n'est pas implémentée; aucun correctif lié à un TitleID.
3. **Qualifier P4 sur la paire finale** et cocher les cases de #15 avec leurs preuves. **C'est seulement après cela que P0–P4 sont terminés**, sans condition de console.
4. **Ouvrir P5 séparément**, avec l'autorisation explicite de build ; ne pas mettre « pas de framebuffer PS5 » dans les raisons de garder P1/P2/P4 ouverts.

### Ce que signifie « terminé »

Une CI verte **ne ferme pas automatiquement** un critère de fonctionnalité dont le code manque encore. À l'inverse, une fonction source/hôte complète **ne doit pas attendre un essai console**. Ne pas annoncer de pourcentage d'avancement fictif ou de délai à partir du seul nombre de tests réussis. Les descriptions anciennes de #15 et de la roadmap sont un journal historique : les lignes « P5 verrouille le build » ou les neuf flags expérimentaux OFF sont obsolètes lorsqu'elles contredisent les sources intégrées récentes.
