# Eden Encore — revue ciblée de Lichii / nx2 (4 novembre 2026)

Source examinée : [zortos293/Lichii, branche nx2](https://github.com/zortos293/Lichii/commits/nx2/),
jusqu'au commit [286117c](https://github.com/zortos293/Lichii/commit/286117c7e0d89ab0384e896489128fdd88a424f8)
du 04/11/2026 13:53 UTC. Sélection par opcode/mécanisme partagé, jamais par titre.

## Correctifs génériques intégrés à Encore

| Révision Lichii | Composant natif Ampere | Adaptation dans le vendor Encore |
| --- | --- | --- |
| [#58 / 325e0a8](https://github.com/zortos293/Lichii/commit/325e0a867bdc481cedf0d12c54f9996e7d16d012) | `USHF` 0x499, haut immédiat, décalage par registre uniforme | Admis uniquement avec champs prouvés, sélection wrap/clamp, mapping UR et prédication uniforme ; rejet des formes inconnues |
| [#57 / cf1beed](https://github.com/zortos293/Lichii/commit/cf1beed4beaa75317b1ca6770c196c4616d6e518) | `SULD/SUST` 0x998/0x99c utilisant un handle TIC/TSC de registre | Chemin Maxwell bindless commun, dimensions 2D / 2D-array / 3D, masques et limites de registres contrôlés ; pas de faux buffer CBUF |
| [#66 / fe8d0dd](https://github.com/zortos293/Lichii/commit/fe8d0dda897a4b2bedd07dc40d1982e2a5e4151e) | `SURED.ADD` 0x59f buffer ou 2D ; `IMNMX` 0x817 immédiat signé/complet | Réduction à dimensions exactes, admission ISA limitée au mode prouvé, buffer propriétaire existant ; IMNMX négatif court signé, sinon matérialisation 32 bits |
| [#55 / d48f75b](https://github.com/zortos293/Lichii/commit/d48f75bdfb3e54b72be907eb114a49d16379a9) | Branches Ampere `BRA.U` : bits 32–33 du mot relatif indiquent le mode, et non le déplacement | Mode `.U` reconnu uniquement après vérification des champs réservés ; suppression des deux bits de mode avant calcul de cible signée, réutilisation du relocateur Maxwell borné. Tests 133 instructions, branche arrière, prédicats et rejections. |
| [#65 / d9748a5](https://github.com/zortos293/Lichii/commit/d9748a5d5814489a0576e8af46856f36e8270138) (sous-ensemble générique) | Extension de `PrepareRegisterPressure` aux familles d'opcodes déjà traduites et aux sources GPR hautes | Seuls les champs d'opérandes authentifiés sont ajoutés à l'owner Ampere : quinze familles, adresses 64 bits, sources FFMA et tailles vectorielles ; pas de modification de `TexturePass` partagé ni du cache Maxwell NS1. Test des registres originaux, des préfixes/suffixes et d'un LDG capturé Clang/GCC UBSan. |

Les régressions hôte utilisent les mots d'instruction capturés dans les commits
en amont, via le **vrai** `LowerToMaxwell` et `ProbeProgram` d'Encore,
pas via un modèle indépendant de compilateur. Tests positifs, négatifs (bits,
dimensions, registres, canaux et chevauchements des registres scratch), prédication, sortie Maxwell et sémantique wrap
sous Clang/GCC et UBSan. Vérification du bridge existant en parallèle.

**Limites :** aucun shader complet, pipeline RADV ou framebuffer invité prouvé ;
P2.4 reste ouvert pour les autres instructions, la LEPC dynamique et task/mesh.
Le correctif ne garantit pas que le cache textures puisse satisfaire tous les
handles natifs ou que tous les kernels Compute aient une traduction complète.

## Correctifs évalués mais non copiés aveuglément

| Lichii | Décision raisonnée |
| --- | --- |
| [#70 / e3d8e9c](https://github.com/zortos293/Lichii/commit/e3d8e9c60587a6c30fbaae23bbf83bb9c492e3a2), [#54 / 9479d8f](https://github.com/zortos293/Lichii/commit/9479d8fa613868bf2d8817e7f20a808a12903e80) | Optimisation de pages GPU-written command et séquencement du front/back `GpuSplit`. Cet ordonnanceur n'existe pas dans le vendor Encore ; faire une transplantation directe introduirait des races dans le renderer partagé NS1/NS2. Gardé comme piste P2.7 (preuve de cohérence lectures de commandes invitées). |
| [#72 / d7fd2f2](https://github.com/zortos293/Lichii/commit/d7fd2f283d436923a6af60096853c3860eb860b5) puis [#73 / a3e94bf](https://github.com/zortos293/Lichii/commit/a3e94bf4e9fd56e7be7a8c2e9a06c6e185607dc7) | La modification de libération de fences a été annulée dans Lichii : explicitement **ne pas reprendre** le commit #72. |
| [#65 / d9748a5](https://github.com/zortos293/Lichii/commit/d9748a5d5814489a0576e8af46856f36e8270138) | Indexation dynamique d'une table TIC avec sampler statique : le **planificateur QMD3 natif** est maintenant corrigé (second CBUF constant sur chaque entrée et test Clang/GCC du vrai lecteur). La détection IR de ces tableaux et le budget final des descripteurs restent non portés : pas de modification du `TexturePass` partagé NS1 sans vérification de ses limites et son propriétaire. |
| [#47 / 448fdae](https://github.com/zortos293/Lichii/commit/448fdaed95517d2c6d5ae7a5e3d3528db41480ef) | Compteurs atomiques derrière un pointeur CBUF non mappé : piste P2.3. Le correctif dépend d'un `global_memory_to_storage_buffer_pass` et de heuristiques natives propres au fork Lichii ; ne pas autoriser d'accès SSBO à une adresse inconnue sans preuve de routage. |
| [#74 / 1ca9f7d](https://github.com/zortos293/Lichii/commit/1ca9f7d5c4b8d92a1189fae3912de017e25fca32) | Gestion des relocalisations/EXIT : Encore utilise déjà des cibles `s64` et un protocole différent d'authentification BRX ; ne pas appliquer aveuglément cette modification. |
| [#75 / 4f9b962](https://github.com/zortos293/Lichii/commit/4f9b9624b9dcd12d160e87c6a2aeb4f62a106d74) | Sortie audio mixer système S16 48 kHz : utile en P1.3, mais Encore fournit `aud:u` et `stpl:u`, pas encore le sysmix de Lichii. Ajouter l'IPC et le ring réel avant d'importer une conversion PCM isolée. |
| [#77 / 286117c](https://github.com/zortos293/Lichii/commit/286117c7e0d89ab0384e896489128fdd88a424f8) | Mutex protégeant une session de trace de fenêtre de JIT ; aucun propriétaire `window_trace` équivalent dans Encore. Pas de code à recopier. |
| [#62 / d5b2582](https://github.com/zortos293/Lichii/commit/d5b258210436254fc734c8a646bcd60eee96ba1e), [#56 / 546cb67](https://github.com/zortos293/Lichii/commit/546cb67825b886898c974f2773e9426b62e6fdcc) | Lot de correctifs amont et corrections de shaders observés dans plusieurs jeux : audit sélectif seulement, sans merge massif ni règles par TitleID. |

Cette revue **ne vaut pas validation GPU PS5**. NS1 conserve son propriétaire
Maxwell et le profil de release refuse toujours les chemins NS2 expérimentaux.
Aucun build PS5 ni test console avant P5.
