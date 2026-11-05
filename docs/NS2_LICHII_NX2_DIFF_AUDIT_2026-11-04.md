# Eden Encore — revue ciblée de Lichii / nx2 (4 novembre 2026)

Source examinée : [zortos293/Lichii, branche nx2](https://github.com/zortos293/Lichii/commits/nx2/),
jusqu'au commit [7daab099](https://github.com/zortos293/Lichii/commit/7daab0992e) du 04/11/2026.
Le commit #82 ne concerne que les releases de Lichii, pas le GPU Encore. Sélection par opcode/mécanisme partagé, jamais par titre.

## Correctifs génériques intégrés à Encore

| Révision Lichii | Composant natif Ampere | Adaptation dans le vendor Encore |
| --- | --- | --- |
| [#84 / 2940d9f](https://github.com/zortos293/Lichii/commit/2940d9fab0) | Horloge GPU Ampere : rapports/calibration CPU et GPU en nanosecondes, Maxwell restant en ticks 614,4 MHz | Le vrai propriétaire Vulkan PS5 GPU::GetTicks prend les nanosecondes uniquement pour la génération NS2 détectée depuis le NPDM via N76 ; NS1 garde exactement sa formule par profil 1/256/512. Même définition N76 transmise à video_core. Source-extrait, compilé/exécuté Clang O0/O2 UBSan pour trois profils, calibration 1s, NS2→NS1 ; ancien oracle G21 conservé hors cette addition. Aucune preuve d'image PS5. |
| [#75 / 4f9b962](https://github.com/zortos293/Lichii/commit/4f9b9624b9dcd12d160e87c6a2aeb4f62a106d74) | Audio Sysmix PCM | Le portage NS2 spécifique dans le vendor Encore est désormais intégré (ring et processus réels, sink Eden partagé, IPC, formats stéréo 48 kHz) depuis main 9a26225 et vendor 97c01069f ; tests hôte uniquement, son PS5 non qualifié. |
| [#58 / 325e0a8](https://github.com/zortos293/Lichii/commit/325e0a867bdc481cedf0d12c54f9996e7d16d012) | `USHF` 0x499, haut immédiat, décalage par registre uniforme | Admis uniquement avec champs prouvés, sélection wrap/clamp, mapping UR et prédication uniforme ; rejet des formes inconnues |
| [#57 / cf1beed](https://github.com/zortos293/Lichii/commit/cf1beed4beaa75317b1ca6770c196c4616d6e518) | `SULD/SUST` 0x998/0x99c utilisant un handle TIC/TSC de registre | Chemin Maxwell bindless commun, dimensions 2D / 2D-array / 3D, masques et limites de registres contrôlés ; pas de faux buffer CBUF |
| [#66 / fe8d0dd](https://github.com/zortos293/Lichii/commit/fe8d0dda897a4b2bedd07dc40d1982e2a5e4151e) | `SURED.ADD` 0x59f buffer ou 2D ; `IMNMX` 0x817 immédiat signé/complet | Réduction à dimensions exactes, admission ISA limitée au mode prouvé, buffer propriétaire existant ; IMNMX négatif court signé, sinon matérialisation 32 bits |
| [#55 / d48f75b](https://github.com/zortos293/Lichii/commit/d48f75bdfb3e54b72be907eb114a49d16379a9) | Branches Ampere `BRA.U` : bits 32–33 du mot relatif indiquent le mode, et non le déplacement | Mode `.U` reconnu uniquement après vérification des champs réservés ; suppression des deux bits de mode avant calcul de cible signée, réutilisation du relocateur Maxwell borné. Tests 133 instructions, branche arrière, prédicats et rejections. |
| [#65 / d9748a5](https://github.com/zortos293/Lichii/commit/d9748a5d5814489a0576e8af46856f36e8270138) (sous-ensemble générique) | Extension de `PrepareRegisterPressure` aux familles d'opcodes déjà traduites et aux sources GPR hautes | Seuls les champs d'opérandes authentifiés sont ajoutés à l'owner Ampere : seize familles, dont FMUL registre 0x220, adresses 64 bits, sources FFMA et tailles vectorielles ; pas de modification de `TexturePass` partagé ni du cache Maxwell NS1. Test des registres originaux, des préfixes/suffixes et d'un LDG capturé Clang/GCC UBSan. |

### Complément 05/11 — CBUF réel, longueur et ordre des slots NVN

L'audit du propriétaire NativeQmdAtomicStorageIRAdmissible
a confirmé qu'un masque de banque CBUF et un bit
nvn_buffer_used peuvent exister sans le record
effectivement lu par l'émetteur. Le garde vérifie
désormais la présence d'un ConstantBufferDescriptor
couvrant l'index, la longueur de réflexion jusqu'à la
fin du descripteur de 16 octets et l'identité
storage.cbuf_offset = nvn_buffer_base + slot*16.
Cela prévient un SSBO déplacé ou un slot atomique
réordonné qui écrirait dans la mauvaise mémoire invitée.
Seul le bridge NS2 est modifié. Tests du véritable IR
avec deux slots valides puis inversés, masques sans
descripteur et tailles absentes. Ce correctif ne prouve
pas le mappage GPU physique en cours de dispatch.

### P2.3 — provenance réelle des pointeurs atomiques SSBO, 04/11

Le backend SPIR-V partagé laisse les GlobalAtomic sans origine
SSBO reconnue en « NotImplemented » et dispose de replis
**non atomiques** pour certaines variantes 64 bits/U32x2. Une
émission NS2 qui rendrait « Ready » pour ces dernières ne
constituerait pas une exécution atomique.

Le bridge QMD3 Compute possède maintenant un garde de l'IR
post-ConvertLegacyToGeneric sur les opcodes atomiques complets.
Les seules formes admises ont un SSBO reflété et activé, inscriptible,
une banque CBUF réelle, une adresse de descripteur alignée et
les fonctions matérielles requises. Les offsets statiques sous-
alignés sont refusés sans les arrondir. Les formes avec pointeur
global non résolu et tout repli non atomique sont refusées avant
SPIR-V. Il ne s'agit pas encore d'une extension vers les atomiques
dynamiques sans preuve de résidence GPU ; NS1 n'est pas modifiée.

### P2.3 — assemblage natif des deux mots U32x2, 04/11

Le seuil de 64 Kio vérifié dans le lot initial ne garantissait pas
la **même paire de mots** sous SPIR-V avec aliasing de
descripteurs : une lecture à 12 octets indexée via offset / 8
chargeait les mots 8 et 12 au lieu de 12 et 16.

Le chemin natif extrait désormais chaque composant de **deux
vecteurs U32x2 successifs**, avec indice de seconde ligne
calculé depuis le déplacement dans un vecteur de 8 octets.
Le chemin de repli sans aliasing utilise déjà deux U32x4 et
une frontière de 16 octets. Les deux représentations produisent
les deux mots authentiques à offsets 4, 12 ou 0xfff4 sans modifier
l'émetteur Maxwell/NS1. La réflexion QMD3 statique compte le
dernier mot et arrondit la taille réelle au rang uniform de
16 octets. Les sous-décalages non alignés sur 4 octets sont
refusés faute de sémantique native démontrée. Les gardes du
backend empêchent la lecture au-delà de la fin 64 Kio,
pour les banques directes comme indirectes.

Preuves exécutées : les deux vrais propriétaires QMD3 et
SPIR-V compilent sur hôte ; tests source-opérationnels des
charges U32x2 le long des 64 Kio, avec/sans aliasing,
O0/O2 UBSan Clang/GCC et accès négatifs. Aucune preuve
d'une image NS2 sur la console.

### P2.3 — seuils de lecture CBUF sur les octets invités, 04/11

Revue du backend commun Ampere→SPIR-V : l'ancienne vérification d'un
CBUF à décalage dynamique utilisait l'index **après** division par la
largeur du vecteur. Une lecture U32x2 à 0xfffc (8 octets requis)
pouvait donc charger la ligne 0xfff8, pourtant invalide comme
plage invitée. Le backend conservé est corrigé sur les vrais
appelants U8/U16/U32/F32/U32x2, y compris repli U32x4 en l'absence
d'aliasing. Ce dernier repli restaure également la lecture du second
mot dans la ligne suivante quand le premier se trouve en composant 3.
Détection native seule, sans modifier l'émetteur Maxwell NS1.

Preuve locale : compilation syntaxique du vrai TU
emit_spirv_context_get_set.cpp en O0/O2 ; oracle C++/UBSan des bornes
de 64 Kio et de traversée 16 octets, assertions de liaison aux appels
de largeur d'origine. Le shader SPIR-V et le GPU Vulkan physiques ne
sont pas exécutés par cet oracle ; ne pas étendre la coche P2.3 à
toutes les formes d'atomiques CBUF.

### Revue complémentaire P2.4 — UISETP/USEL (04/11)

Le bas niveau Ampere de Lichii `nx2` a mis en évidence deux différences
**génériques** du propriétaire Encore :
- `UISETP` utilisait un masque global `0x7f` pour P2R/R2P alors qu'il
  n'agit que sur le prédicat de sortie et éventuellement celui
  d'accumulation ; seuls ces bits sont désormais sauvegardés/restaurés,
  y compris dans la variante immédiate et en cas de `UPT`.
- La fusion de `UISETP` suivi de `USEL` en clamp entier doit être
  limitée aux champs canoniques et à `condition == 0`. Les conditions
  non nulles sont désormais traduites par `USEL` ordinaire, sans
  transformation incorrecte en min/max.

Ces deux changements sont adaptés au lowerer **actuel** d'Encore,
pas un cherry-pick du fichier entier : tests réels O0/O2 + UBSan
des masques émis, comparaison des deux chemins `USEL`, refus de
champs illégaux, `test_lichii_nx2_generic_shader_regressions` et
`test_ampere_gpu_capture` conservés verts. Rien n'a été modifié
dans le frontend Maxwell Switch 1. Aucun rendu PS5/NS2 démontré.

Les régressions hôte utilisent les mots d'instruction capturés dans les commits
en amont, via le **vrai** `LowerToMaxwell` et `ProbeProgram` d'Encore,
pas via un modèle indépendant de compilateur. Tests positifs, négatifs (bits,
dimensions, registres, canaux et chevauchements des registres scratch), prédication, sortie Maxwell et sémantique wrap
sous Clang/GCC et UBSan. Vérification du bridge existant en parallèle.

**Limites :** aucun shader complet, pipeline RADV ou framebuffer invité prouvé ;
P2.4 reste ouvert pour les autres instructions, la LEPC dynamique et task/mesh.
Le correctif ne garantit pas que le cache textures puisse satisfaire tous les
handles natifs ou que tous les kernels Compute aient une traduction complète.

## P2.4 — atomiques globaux à registres élevés, 04/11

La relecture des deux variantes de ATOMG.E.ADD.STRONG.GPU.U32 sur
le lowerer natif Encore a montré une divergence générique :
la forme GPR 0x3a8 nécessitait un enregistrement des **deux** mots
d'adresse et du registre source, mais n'était pas reconnue par le
spilleur de GPR ; la forme uniforme 0x9a8 contenait un registre
données à bit 32 qui échappait à la détection du scratch. Les deux
sont maintenant inscrites dans la copie/restauration des GPR, sans
toucher aux instructions Maxwell classiques. L'alias physique du
registre uniforme U63 a également été refusé lorsqu'un pointeur
virtuel U62 demanderait son mot haut. Détecteur des vecteurs
implicites 64 bits mis en cohérence.

Les tests source-exécutés des vraies unités C++ valident les deux
ATOMG, leurs emprunts et leur restauration à O0/O2, les mots Maxwell
émis et les conditions négatives. Ils n'impliquent **ni** que le
backend SSBO connaît toute provenance de pointeur atomique,
**ni** qu'un Vulkan Compute ou un jeu NS2 rend un framebuffer.

## Correctifs évalués mais non copiés aveuglément

| Lichii | Décision raisonnée |
| --- | --- |
| [#70 / e3d8e9c](https://github.com/zortos293/Lichii/commit/e3d8e9c60587a6c30fbaae23bbf83bb9c492e3a2), [#54 / 9479d8f](https://github.com/zortos293/Lichii/commit/9479d8fa613868bf2d8817e7f20a808a12903e80) | Optimisation de pages GPU-written command et séquencement du front/back `GpuSplit`. Cet ordonnanceur n'existe pas dans le vendor Encore ; faire une transplantation directe introduirait des races dans le renderer partagé NS1/NS2. Gardé comme piste P2.7 (preuve de cohérence lectures de commandes invitées). |
| [#72 / d7fd2f2](https://github.com/zortos293/Lichii/commit/d7fd2f283d436923a6af60096853c3860eb860b5) puis [#73 / a3e94bf](https://github.com/zortos293/Lichii/commit/a3e94bf4e9fd56e7be7a8c2e9a06c6e185607dc7) | La modification de libération de fences a été annulée dans Lichii : explicitement **ne pas reprendre** le commit #72. |
| [#65 / d9748a5](https://github.com/zortos293/Lichii/commit/d9748a5d5814489a0576e8af46856f36e8270138) | Indexation dynamique d'une table TIC avec sampler statique : le **planificateur QMD3 natif** est maintenant corrigé (second CBUF constant sur chaque entrée et test Clang/GCC du vrai lecteur). La détection IR de ces tableaux et le budget final des descripteurs restent non portés : pas de modification du `TexturePass` partagé NS1 sans vérification de ses limites et son propriétaire. |
| [#47 / 448fdae](https://github.com/zortos293/Lichii/commit/448fdaed95517d2c6d5ae7a5e3d3528db41480ef) | Compteurs atomiques derrière un pointeur CBUF non mappé : piste P2.3. Le correctif dépend d'un `global_memory_to_storage_buffer_pass` et de heuristiques natives propres au fork Lichii ; ne pas autoriser d'accès SSBO à une adresse inconnue sans preuve de routage. |
| [#74 / 1ca9f7d](https://github.com/zortos293/Lichii/commit/1ca9f7d5c4b8d92a1189fae3912de017e25fca32) | Gestion des relocalisations/EXIT : Encore utilise déjà des cibles `s64` et un protocole différent d'authentification BRX ; ne pas appliquer aveuglément cette modification. |
| [#77 / 286117c](https://github.com/zortos293/Lichii/commit/286117c7e0d89ab0384e896489128fdd88a424f8) | Mutex protégeant une session de trace de fenêtre de JIT ; aucun propriétaire `window_trace` équivalent dans Encore. Pas de code à recopier. |
| [#62 / d5b2582](https://github.com/zortos293/Lichii/commit/d5b258210436254fc734c8a646bcd60eee96ba1e), [#56 / 546cb67](https://github.com/zortos293/Lichii/commit/546cb67825b886898c974f2773e9426b62e6fdcc) | Lot de correctifs amont et corrections de shaders observés dans plusieurs jeux : audit sélectif seulement, sans merge massif ni règles par TitleID. |

Cette revue **ne vaut pas validation GPU PS5**. NS1 conserve son propriétaire
Maxwell et le profil de release refuse toujours les chemins NS2 expérimentaux.
Aucun build PS5 ni test console avant P5.
