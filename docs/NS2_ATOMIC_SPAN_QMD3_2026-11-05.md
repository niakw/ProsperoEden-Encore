# P2.3 — SSBO atomiques, plages statiques QMD3 (05/11/2026)

## Problème confirmé
Le code natif possédait déjà un filtre qui authentifiait le slot
StorageAtomic, la banque QMD3, son format et l'existence des capacités
Vulkan. Un **offset immédiat** pouvait néanmoins se situer au-delà de
la **taille réelle** de ce SSBO, et un offset **dynamique** n'avait
aucun test SPIR-V contre les limites de la ressource liée avant
l'instruction atomique.

Le traducteur commun utilise des tableaux SPIR-V à longueur
d'exécution et ne propose actuellement aucun garde atomique
exécutable dans le chemin NS2. Remplacer l'adresse invalide par
l'élément zéro n'est pas sûr : cela écrirait dans le mauvais mot.

## Correction source
- native_atomic_span.h collecte depuis les véritables instructions IR
  les couples (slot aplati, offset, largeur 4/8 octets), après la
  vérification des opcodes et de provenance. Un offset dynamique,
  non aligné ou non représentable est refusé avant tout module SPIR-V.
- NativeSpirvResult transporte les plages sous forme de métadonnées
  **propriétaires** : aucun objet IR, pointeur invité ou contexte
  mutable n'est conservé.
- CompileCapturedNs2QmdComputeSpirvWithResources vérifie toutes
  les plages contre les tailles known_size et bytes du
  vrai NativeQmdResourcePlan, construites depuis les enregistrements
  QMD3 accessibles dans le GMMU sous ticket de session. Aucune plage
  invalide ne produit de plan publiable. Les contrôles d'époque,
  de mapping et d'identité des descripteurs restent exigés au moment
  du dispatch.
- Aucune modification de l'émetteur Maxwell NS1, ni extension
  artificielle de la mémoire invitée, ni changement du moteur Vulkan
  non authentifié.

## Validation
Témoins de la production Opcode, IR::Inst, IR::Program et
NativeQmdStorageBinding, compilés et exécutés avec UBSan en O0/O2
Clang/GCC. Tests : plages valides et au-delà du dernier mot,
U32/U64, floats, buffer marqué lecture seule, 0 octet, taille
inconnue, 32 bits saturés, descripteur absent, mutations de longueur,
offsets dynamiques refusés. Les unités source exactes
renderer_spirv_bridge.cpp et ns2_shader_spirv_compile.cpp
passent leur contrôle syntaxique O0/O2 sur headers épinglés.

**Limitation :** ce n'est pas une implémentation des offsets
atomiques dynamiques ; ils restent non admis sans borne SPIR-V.
Ni le rendu NS2, ni le dispatch atomique sur Vulkan/PS5, ni les
horloges/fences GPU n'ont été validés par ces tests hôte.
