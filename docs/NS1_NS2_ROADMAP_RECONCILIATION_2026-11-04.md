# Eden Encore — réconciliation des cases ouvertes (4 novembre 2026)

## Méthode
Contrôle des cases de l'issue #15 sur le code local à main 90f3ff0 / vendor 1a6caf4, sans build PS5 ni lancement de CI. Une preuve de source/hôte, une preuve de CI au SHA final et une preuve console sont distinctes. Une case transférée à P5 signifie uniquement que son critère est déplacé, jamais que son comportement est prouvé.

## Cases obsolètes, doublonnées ou exclusivement console

| Case historique | Conclusion vérifiée et décision |
| --- | --- |
| P3.2 (jaquettes) | SOURCE/HÔTE À COCHER : le véritable sélecteur de médias de boîtier passe Clang/GCC/C++ O0/O2 après correction d'un test à pointeur pendant ; déduplication des catégories et index de release validés. Les images réellement chargées sur PS5 restent P5. |
| P3.4d (scan ROM) | OBSOLÈTE : le sous-jalon P3.4d-1 déjà coché prouve un run source-early vert ultérieur. Le contrôle du scanner atomique Clang/GCC O0/O2 vient de passer. Cocher P3.4d pour éviter une contradiction avec sa propre preuve. |
| P2.6b (mesures de hit-rate/stalls) | TRANSFÉRER en P5 : sans scène NS1/NS2 réelle comparable, ce n'est pas un critère de clôture de la sécurité du cache Compute en source. Le LRU borné, l'époque, les identités SPIR-V et les fences sont déjà implémentés et prouvés sur hôte. |
| P3.5 (FC27 micro-saccades, HUD) | TRANSFÉRER en P5 : ces défauts sont visibles seulement sur la console et nécessitent une nouvelle trace avec le build final. Ne pas inventer un correctif FC27 par TitleID. |
| P2.5 (ASTC/sparse et budget VRAM) | SOURCE/HÔTE À COCHER : cache ASTC GPU N60 et stress 2400 frames N61 passent ; autres preuves N54–N61 déjà référencées dans #15. Taille/budget physique GPU réel → P5. |
| P2.7b (comparaison upstream snapshots de commandes) | AUDIT TERMINÉ : absence de submitted_words/submitted_offsets et fetch invité actif prouvés par check_native_gpu_command_fetch_owner.py. En revanche la synchronisation de véritables GPU-writes avant fetch est explicitement NOT_PROVEN et demeure sous P2.7, pas supprimée. |
| P4.1, P2.2c (CI de qualification finale) | PÉRIMÈTRE À RECADRER : la CI du dernier couple SHA ne peut pas être déduite d'anciens runs. Réserver la qualification exhaustive au freeze P5; garder les manques d'interface C++/Vulkan qui sont réellement du code dans P2.2c. |

## Restes réellement techniques (ne pas cocher sur de simples tests de source)

| Case | État |
| --- | --- |
| P0.2 | VRAI BLOCAGE : 11 commutateurs EDEN_NS2_*_EXPERIMENTAL restent présents et OFF par défaut après les promotions de N1 (NPDM 2048/3072 bits partagé), N3b (AM320), N49 (vues Vulkan 2D/3D), N50 (continuité GMMU), N51 (notifications PTE), N52 (démarrage KProcess), N54 (scratch CPU), N56 (cache Vulkan), N57 (ASTC layer decode), N60 (ASTC dirty-layer cache) et N76 (compteur invité NPDM) ; aucune preuve de sélection automatique d'un NS2 de production. |
| P1.1 | Portage formats/ExeFS/NPDM/NUP/firmwares/keys partiel ; les tests de métadonnées existent mais un boot réel / PC invité est P5. Ne pas déclarer tout le boot automatique intégré sans inspection source complète. |
| P1.2 | Source NVMap/GMMU 49 bits, 4 Kio, rollback/sparse et garde d'overflow en place ; résidence GPU réelle, VRAM et pilote en P5, autres cas source encore à inventorier. |
| P1.3 | HLE/IPC/AM/VI2/audio/NCM : services partiellement adaptés ; les appels incomplets ne sont pas une preuve de complétude. |
| P1.4 | Régression complète source/hôte NS1 au SHA figé encore non attestée. |
| P2.2c | Interfaces Vulkan/ASTC natives réelles compilées sous gates PS5 non prouvées par les seuls contrôles de texte. Précondition source/qualification à préserver. |
| P2.3 | Global memory et CBUF indirect ont des chemins sécurisés, mais formes inconnues refusées ; l'exécution de tous les cas sur buffers GPU hôtes ne suit pas de ces gardes. |
| P2.4 | VertexA/B/Fragment/Geometry et paire TessControl+TessEval raccordés en source ; task/mesh, LEPC dynamique et opcodes Ampere non traduits restent réellement manquants. Test console des patches tessellés réservé à P5. |
| P2.7 | GPFIFO, QMD, VI2, clôture temporelle et politiques de fence ont des témoins hôte ; GPU-write → lecture CPU des commandes invités n'est toujours pas prouvé. |
| P3.3 | Snapshot swapchain source validé ; handoff de présentation multithread non qualifié sur cet hôte (libc++ Mac sans std::jthread/stop_token), pas une preuve d'échec du port PS5. |
| P4.2/P4.3 | Qualification finale des régressions et décision d'entrée P5 incomplètes. L'exécution console n'en fait pas partie. |

## Tests effectivement observés pendant cette revue

- PASS : P3.2 sélecteur réel après correction du test, Clang/GCC/C++ O0 et O2 ; classement des médias de release ; P3.4 scan atomique Clang/GCC O0/O2.
- PASS : ASTC cache N60, stress N61 (2400 images), politiques de fence NS1/NS2, publication VI2 après release/timer, provenance du fetch des commandes invitées.
- PASS : snapshot/ownership de swapchain Vulkan R336, handoff Compute F07.
- ENVIRONNEMENT : plusieurs témoins hôte Mac utilisent par défaut un SDK CLT 27 dont les stubs arm64e.x1 ne sont pas supportés par le linker local ; le test sélecteur de boîtier choisit désormais le SDK compatible 15.4 uniquement pour le test. Le témoin std::jthread ne compile pas avec cette libc++ Mac.
- Aucune CI ni compilation native PS5 lancée dans cette revue.

## Règle de fermeture

Cocher la partie source quand les propriétaires réels et les témoins pertinents sont démontrés ; transférer au P5 uniquement les conditions nécessitant la console. Ne jamais cocher les implémentations manquantes ni une CI non exécutée sur le dernier SHA.
