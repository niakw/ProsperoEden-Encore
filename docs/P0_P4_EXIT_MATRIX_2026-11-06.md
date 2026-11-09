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


## Contrat de clôture borné P1/P2 — 9 novembre 2026

La [matrice machine à 17 contrats](NS2_P1_P2_EXIT_CONTRACT.json) fige **H01–H07** et **G01–G10**. Elle évite de transformer chaque refus d'opcode ou chaque titre inédit en une nouvelle condition de sortie. Chaque contrat décrit le propriétaire du code, une admission positive requise, un rejet négatif requis et des témoins hôte **déjà appelés dans la CI maintenue**. Ce n'est pas un pourcentage de compatibilité des jeux.

Le validateur [`check_p1_p2_exit_gate.py`](../tools/ns2/check_p1_p2_exit_gate.py) fournit deux décisions **distinctes** :

- `python3 tools/ns2/check_p1_p2_exit_gate.py --json` : **audit de structure** appelé depuis la qualification hôte P4. Un résultat vert signifie que les 17 contrats, propriétaires et chemins de test sont traçables, **pas** que les fonctions sont terminées. Il indique explicitement le nombre de contrats ouverts.
- `python3 tools/ns2/check_p1_p2_exit_gate.py --enforce` : **décision de sortie bloquante**. Refuse tout contrat ouvert ; exige pour chaque contrat vérifié une preuve **positive et négative** réellement exécutée (pas une simple syntaxe), rattachée aux tests exécutés par les workflows GitHub du SHA courant ; contrôle le gitlink vendor, l'arbre propre et les six workflows obligatoires **verts au même SHA**. Les demandes hors périmètre nécessitent une justification SDK/ABI et un témoin de refus réel. Cette commande n'est **pas** appelée comme simple test vert dans la CI normale.

Le dénominateur ne change pas après chaque découverte : **17 contrats fixes**. Tout écart doit être classé dans l'un d'eux avec un comportement attendu/une preuve, ou être reporté explicitement en P5 si son observation exige le matériel, sans prétendre qu'un problème confirmé de source a disparu. L'admission d'une instruction inconnue par un faux succès est toujours éliminatoire. Les tests jeu, le framebuffer et les performances PS5 restent P5.

**État initial du contrat : 17 ouverts, aucun accusé de clôture signé.** Cela ne remet pas en cause les validations fonctionnelles précédentes (sparse H03, refus G10, P4 hôte), mais refuse d'en déduire sans examen une clôture de toute l'ABI. Le dernier résultat de CI et les preuves d'exécution rempliront les champs de clôture, sans fixer un objectif artificiel en heures ou en nombre de correctifs.

**Garde-fou anti-clôture artificielle :** la matrice n'autorise jamais l'exclusion d'une ligne H/G entière. Les 17 contrats demeurent tous obligatoires. Seules des variantes SDK **précises** peuvent être exclues à l'intérieur d'un contrat, avec identifiant, justification ABI et refus hôte exécuté au même SHA. Des tests de mutation du validateur rejettent une ligne supprimée, un témoin absent, une fausse preuve et une exclusion entière. Les formes exclues ne réduisent jamais le dénominateur 17.

**Contrôle anti-boucle SHA (9 novembre) :** l'état d'une ligne est `open` ou `proof_defined`. Les chemins stables des tests positifs/négatifs sont inscrits dans Git, **aucun futur numéro de run CI ne l'est**. Après publication du commit, le contrôle manuel lit les six suites du **SHA exact de son checkout** via l'API GitHub ; aucune écriture de reçu dans Git n'est nécessaire pour sortir. `proof_defined` n'est pas `terminé` : la décision n'est valide que quand `--enforce` réussit.

**H04 — témoin positif/négatif exécutant le véritable propriétaire VI2 :** `tools/ns2/check_native_vi2_output_ipc_host.py` extrait sans réécriture `IVi2Session::MaxResolution`, `Encoding`, `ValidateDisplayStatus`, `Find` et `W` du vendor, puis compile le code extrait sous Clang et GCC en O0/O2. Il contrôle les réponses SDK 1440p docké / 1080p portable, les formats 0x14, et les refus d'identité d'écran, de client, de taille de paquet, d'encodage et de résolution invalide. Ce n'est ni un rendu réel PS5 ni une preuve console. `proof_defined` reste soumis au verdict du job CI final.
