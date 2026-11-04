# Switch 2 native bootstrap — HLE/core integration (2026-11-01)

## Consolidated shared PS5 release source

- **Process + kernel:** detect NS2 from parsed ExeFS main.npdm before kernel initialization. Select 12 GiB guest layout per NS2 title, bound SetHeapSize by intended guest RAM and extend only the 12 GiB profile's *virtual* heap range to 16 GiB. These changes do not eagerly allocate 16 GiB of PS5 RAM.
- **Audio:** additive aud:u commands 1 and 2 return actual maintained IAudioOutManager and IAudioRendererManager interfaces. Existing audout:u, audren:u, audin:u, audctl and hwopus registrations are retained for NS1.
- **Stream play:** le service NS2 \`stpl:u\` renvoie un objet par la commande 0 ; sa commande 300 fournit désormais une **mémoire partagée HID invitée de 0x9b000 octets (lecture côté invité)**, accompagnée de sa structure taille/décalage et d'un copy handle. L'ancien événement supposé, faux succès sans données HID, a été retiré. L'instance garde un propriétaire unique jusqu'à sa fermeture ; échecs d'allocation et d'initialisation refusent l'appel sans fournir de handle. Le partage distant et les autres commandes GameShare restent non implémentés.
- **GPU characteristics:** exact native NVDRV IOCTL adapters are additive. Full GPU session, worker, GMMU/GPFIFO, Ampere shader, VI2 presentation and GPU budget adaptations remain research only.
- **Loader diagnostics:** bounded 10s/30s Vulkan loading notices are distinct from an actual game frame.

Provenance: Djihads80/Eglantine nx2 and 0x2593/Eden-NS2, selectively adapted to the maintained Encore PS5 vendor source. Do not apply broad upstream patches without source/ABI review.

## Verification limits

Host source tests guard source selection, ABI intent, event lifetime, NS1 service preservation and historical F07 inventory separation. A green native build proves compilation only. The recorded Donkey Kong Bananza console state is guest CPU bootstrap with persistent black screen; **first rendered game frame is still unproven**. No NS2 gameplay compatibility claim follows from these integrations.

This one `[full-build]` candidate tests consolidated source buildability. Do not request separate PS5 installations for each fix.


## Consolidated GPU-memory correctness and NS1 handoff

- NS2 `SVC 0x80` is no longer a success-only admission stub: it validates the exact registered NS2 PID, address/size, GPU attribute mask and real guest page-table range before setting or clearing bit `0x20` with `KPageTableBase::SetMemoryAttribute`.
- The shared maintained kernel headers expose `GpuAccessible` identically to the SVC dispatcher, kernel page table, and memory queries; NS1 SVC IDs and existing user permissions are unchanged.
- The NS2 12 GiB guest profile is temporary: after kernel shutdown or an NS2-to-NS1 title transition, the original memory layout and global/custom setting selection are restored.
- The host source gate checks real mutation, cross-unit header selection, invalid input statuses, and memory profile restoration. Full native compilation must still confirm ABI and linkage.
- This candidate intentionally **does not** enable the experimental 4 KiB NVDRV GMMU path or native Ampere GPU worker, so a black-screen NS2 game remains possible.

The validated initial native HLE/memory bootstrap build was run #41273218088 at revision 32433db9. This follow-up full-build marker requests a single newer native build including the fixed GPU attribute persistence and NS1 restoration, not a PS5 gameplay pass.


## P1.3 du 4 novembre — vrai Sysmix PCM partagé et IPC NS2

Le propriétaire NS2 sélectionné via `EDEN_SHARED_NS2_AUDIO` raccorde
maintenant les services `auddmg:u` **et** `audsmx:u` au même registre de
flux `Nx2SysmixStreams` ; `aud:u` et tous les managers audio historiques
NS1 conservent leurs propriétaires Eden. Le service virtuel expose les
commandes de découverte 0/100, les propriétés 401 (nom,
stéréo 48 kHz, latence **inconnue**, conservée à zéro), vérifie la prise en
charge des formats PCM16 et PCM float sur 300, et attache/détache les
flux **existants et appartenant au même processus** sur 700/800. Les
noms, fonctions et identifiants incorrects renvoient des erreurs, sans
flux fantôme ni événement de changement d'appareil imaginé.

La session `audsmx:u` exige le véritable KProcess fourni par un copy
handle IPC, compare son propriétaire au thread appelant et valide la
région utilisateur avant toute création. Chaque flux possède des
événements réels, un identifiant stable, une entrée dans le registre
partagé et un `SinkStream` ouvert sur le sink Eden déjà existant.
L'anneau invité aux offsets lus de l'implémentation amont (index de lecture
`+0x44`, écriture `+0x1004`, échantillons `+0x1040`) est converti
vers le PCM16 stéréo du sink, avec lecture/validation de l'adresse
du processus, gestion de deux segments en cas de bouclage, NaN/Inf,
gain et saturation. L'horloge de flux utilise un propriétaire
`CoreTiming` périodique de 5 ms. Le sink reçoit au plus 240 frames
par pompe ; la pression de sa file (capacité paramétrée à 8, admission
maximum 4) empêche l'appel bloquant quand l'hôte est saturé. Le pointeur
de lecture invité n'est avancé qu'après l'admission, par
`WriteExclusive32` et vérification de lecture. Les échecs IO/CAS
marquent le flux en faute et stoppent le sink. Le registre refuse une
33e session active et l'épuisement des IDs, au lieu de les recycler.

**Pas de succès IPC artificiel :** les fonctions non implémentées
(clock/prime/purge et renommage) retournent `ResultNotSupported`. Une
incompatibilité audio réelle doit être diagnostiquée à P5 et ne peut
être masquée par une réponse zéro. Le changement est borné au
propriétaire audio NS2 ; aucun source de lecture NS1 n'est remplacé.

**Preuves exécutées sur hôte :** compilation syntaxique C++20 des
deux vraies unités de service et mixeur (O0/O2) avec leurs headers
Eden épinglés ; extraction/exécution des vrais membres `Pump`,
`ValidateRegion` et `IsFormatSupported` sous Clang/GCC UBSan O0/O2
(240 frames PCM16, deux frames float, boucle, saturation, NaN,
backpressure, mémoire invalide, échec d'écriture exclusive) ; harnais
IPC du véritable manager `auddmg:u` vérifiant les retours et les
autorisations. CI preflight câblée, **aucune CI lancée, aucun build PS5**.
Ces tests ne constituent ni preuve d'une session audio HOS native
complète, ni de son audible en jeu, ni de compatibilité matérielle
PS5. Ces derniers points sont transférés à P5.

## P1.3 — isolation des sessions audio concurrentes (04/11)

Après intégration du Sysmix, le protocole possédait deux fenêtres de
course indépendantes. La création vérifiait la limite de **32 sessions**
sous verrou, mais relâchait celui-ci pour construire le stream avant
l'insertion : plusieurs appels concurrents pouvaient dépasser la
capacité admise. Désormais **création, vérification de capacité, attribution
monotone de l'ID et insertion** sont sous le même propriétaire de registre.
Une allocation échouée ne publie pas de flux et ne consomme pas d'ID.
Le retour après débordement des IDs reste refusé. La pompe du timer
emploie son verrou existant, sans voir de session partiellement publiée.

Les commandes de groupe EngageStreams/DisengageStreams vérifient
**tous** les IDs et leurs propriétaires avant de modifier les sinks.
La commande refuse les listes dépassant 32 IDs et les doublons,
empêche les effets partiels causés par un ID inconnu ou appartenant à
un autre processus, puis tente un rollback des flux précédemment
modifiés si le sink rejette une transition en cours de batch. Le
rollback en cas de véritable panne du sink n'est pas une garantie
atomique côté audio matériel : un test PS5 reste requis. Le service
d'un seul ID (auddmg:u) réutilise ce même contrôle.

**Preuve hôte :** extraction et exécution des **méthodes C++ réelles**
Nx2SysmixStreams::CreateBounded, SetEngagedBatch et SetEngaged.
96 créations concurrentes → exactement 32 flux distincts, puis
tests d'ID épuisé, d'échec d'allocation, d'ID dupliqué, de processus
étranger, de liste contenant un ID invalide en dernière position, de
retour arrière sur échec de démarrage et de bornes de session.
Clang/GCC O0/O2, UBSan, en plus de la syntaxe des véritables unités
de traduction et des témoins PCM/IPCs antérieurs.
**Aucune CI exécutée manuellement ni compilation/validation PS5.**
