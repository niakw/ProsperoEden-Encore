# Eden Encore — Registre NS1 de couverture fonctionnelle SwitchBrew

> **Objet :** disposer d'un registre NS1 vivant, lisible comme les tables SwitchBrew, qui permette de répondre rapidement à : *cette fonction/commande existe-t-elle ? est-elle réellement implémentée ? seulement enregistrée ? stub ? partielle ? testée ? quand et sur quel propriétaire ?*
>
> **Dernière mise à jour : 21 novembre 2026.**
>
> **Branche de qualification :** `opt/ns1-fc27-runtime-20261121`.
>
> **Snapshot initial :** moteur `5bef0df2b23f650b470659e928e3682cf2db3916` → vendor/gitlink `b8883667410054db189d00b3a5144088f47d3af9`.
>
> Ce document est un **registre de couverture**, pas une preuve de compatibilité console. Une ligne « implémentée source » ne devient « validée PS5 » qu'après un test représentatif.

## 1. Références et règle de vérité

Référence fonctionnelle principale :

- SwitchBrew **Services API** : https://switchbrew.org/wiki/Services_API
- SwitchBrew **SVC** : https://switchbrew.org/wiki/SVC
- Catégorie des services : https://switchbrew.org/wiki/Category:Services
- SwIPC historique : https://github.com/reswitched/SwIPC — utile pour les signatures/IDs anciens, **mais figé autour des firmwares 3.x et jamais utilisé seul pour conclure sur 23.x**.
- libnx / Atmosphère servent de contre-vérification client/kernel lorsque SwitchBrew laisse une signature ou une évolution ambiguë.

Pour Eden Encore, la vérité n'est **jamais** « un fichier portant le bon nom existe ». L'ordre est :

1. source réellement sélectionnée par CMake pour le binaire natif PS5 ;
2. handler effectivement enregistré pour l'ID IPC/SVC ;
3. corps du handler : implémentation, valeur fixe, stub, fail-closed, objet/handle/event réellement retourné ;
4. version firmware à laquelle la commande s'applique ;
5. test hôte proportionné ;
6. validation PS5 représentative.

Les sources `vendor/sources/eden` sont l'entrée épinglée. Les remplacements `vendor/encore-active/*`, les backports R23 et les overlays générés par CMake peuvent devenir les propriétaires réellement compilés ; la colonne **Owner actif** doit donc être réévaluée à chaque changement de gitlink/CMake.

## 2. Légende de statut

| Code | Signification |
|---|---|
| **OK-PS5** | comportement validé sur console dans un scénario représentatif et couple de SHAs indiqué |
| **OK-HOST** | handler réel + test hôte/CI pertinent ; console non qualifiée |
| **SRC** | handler réel présent dans le propriétaire actif, sans preuve comportementale suffisante |
| **PARTIEL** | une partie du contrat est implémentée ; flags, variantes firmware, handles, buffers, erreurs ou états restent incomplets |
| **STUB** | handler existe mais renvoie une valeur fixe, succès factice, résultat minimal ou ne reproduit pas le contrat |
| **NULL** | commande enregistrée avec `nullptr` / explicitement non implémentée |
| **ABSENT** | commande/interface SwitchBrew connue mais non trouvée dans le propriétaire actif |
| **N/A** | commande hors NS1 retail / firmware hors périmètre |
| **?** | non qualifié : ne pas conclure |
| **SB-CURRENT** | ligne recroisée avec SwitchBrew actuel le 21/11/2026 |
| **SWIPC-HIST** | ligne issue de SwIPC historique ; vérifier SwitchBrew avant correction |

### Règle importante

`FunctionInfo { id, &Class::Method, "Name" }` signifie seulement **« handler raccordé »**. Cela ne suffit pas à classer **OK-HOST**. À l'inverse, un `nullptr` est un écart source explicite pour cette commande, sans prouver qu'un jeu l'appelle.

## 3. Métadonnées d'une ligne

Chaque ligne détaillée utilise :

| Champ | Contenu |
|---|---|
| Famille / service | nom SwitchBrew (`hid`, `fsp-srv`, `acc:u0`, etc.) |
| Interface | nom SDK/IPC si connu |
| Cmd/SVC | identifiant numérique |
| Fonction SwitchBrew | nom courant, avec plage firmware si nécessaire |
| Statut Encore | un code de la légende |
| Owner actif | fichier C++ réellement sélectionné ou propriétaire à qualifier |
| Handler Encore | méthode ou `nullptr` |
| Depuis / jusqu'à | versions HOS documentées |
| Dernière revalidation | date + SHAs moteur/vendor |
| Preuve | test/CI/console ou raison du statut |
| Notes | sémantique manquante, risque, jeu/log connu, upstream pertinent |

## 4. Référentiel actuel SwitchBrew à suivre

Ces pages sont les références de commande actuelles pour les familles les plus importantes au boot et au gameplay NS1 :

| Domaine | Référence |
|---|---|
| SM | https://switchbrew.org/wiki/Services_API#sm: |
| Kernel/SVC | https://switchbrew.org/wiki/SVC |
| Account | https://switchbrew.org/wiki/Account_services |
| HID/HIDBUS | https://switchbrew.org/wiki/HID_services |
| Applet Manager | https://switchbrew.org/wiki/Applet_Manager_services |
| Filesystem | https://switchbrew.org/wiki/Filesystem_services |
| NS/AOC | https://switchbrew.org/wiki/NS_services |
| Sockets/DNS | https://switchbrew.org/wiki/Sockets_services |
| SSL | https://switchbrew.org/wiki/SSL_services |
| Audio/Opus | https://switchbrew.org/wiki/Audio_services |
| Settings | https://switchbrew.org/wiki/Settings_services |
| Nvnflinger/VI | https://switchbrew.org/wiki/Nvnflinger_services ; https://switchbrew.org/wiki/VI_services |
| NVDRV | https://switchbrew.org/wiki/NV_services |
| LDN | https://switchbrew.org/wiki/LDN_services |
| NIFM | https://switchbrew.org/wiki/Network_Interface_services |
| NCM | https://switchbrew.org/wiki/NCM_services |
| NIM | https://switchbrew.org/wiki/NIM_services |
| NFC/NFP | https://switchbrew.org/wiki/NFC_services |
| Loader | https://switchbrew.org/wiki/Loader_services |
| Process Manager | https://switchbrew.org/wiki/Process_Manager_services |
| PTM/APM/PSM | https://switchbrew.org/wiki/PTM_services |
| USB | https://switchbrew.org/wiki/USB_services |
| BCAT | https://switchbrew.org/wiki/BCAT_services |
| Capture | https://switchbrew.org/wiki/Capture_services |
| Error report | https://switchbrew.org/wiki/Error_Report_services |
| Log | https://switchbrew.org/wiki/Log_services |
| Fatal | https://switchbrew.org/wiki/Fatal_services |
| NGC / StreamPlay | https://switchbrew.org/wiki/NGC_services |
| OLSC | https://switchbrew.org/wiki/OLSC_services |

## 5. Écarts firmware récents à ne pas perdre

Cette section évite qu'un inventaire historique SwIPC fasse croire à tort que la couverture est complète.

| Référence actuelle | Version | Constat Encore initial |
|---|---:|---|
| `stpl:u`, `stpl:sys` | NS1 **23.0.0+** | backport R23 sélectionné dans le graphe PS5 ; commandes détaillées à maintenir ci-dessous |
| NS application manager / qlaunch | **23.5.0+** | backport R23 FW23.5 sélectionné ; les nouveaux IDs doivent rester distingués des commandes historiques |
| HID/HIDBUS | jusqu'à **23.x** | plusieurs commandes 19–23.x n'existent pas dans SwIPC historique ; SwitchBrew actuel prime |
| AudioRenderer | NS1 **23.0.0+** | commande 14 `SetAsyncMemoryPoolControlEnabled` à vérifier séparément |
| Mii | NS1 **23.0.0+** | commandes 27/28 renommées/évoluées ; ne pas se fier aux noms SwIPC seuls |
| Error Report | **23.0.0+** | interfaces/namespaces et certaines commandes ont changé |
| SVC | 13.x–23.x | plusieurs SVC modernes ne figurent pas dans les vieilles matrices SwIPC ; utiliser la table SwitchBrew SVC courante |

## 6. Priorités de lecture

Le registre complet doit être trié par impact, pas seulement par numéro de commande :

- **P0 boot / progression :** SM, SVC, FS, Loader/PM, AM, NS, VI/Nvnflinger, NVDRV, HID, time, settings.
- **P1 gameplay / fidélité / réseau / média :** audio/hwopus, sockets/DNS/SSL/NIFM/LDN, Account, NCM/NIM, NFC/NFP, BCAT, capture.
- **P2/P3 :** debug/manufacturing, télémétrie, services non retail, fonctions non exercées et utilitaires.

Une fonction **ABSENT/NULL** reste un écart de couverture, mais ne passe devant un P0/P1 exercé que si un log, un Title ID, un PC invité ou une chaîne de dépendances montre qu'elle bloque réellement le runtime.

---

# PARTIE A — Couverture détaillée actuelle

Les sections suivantes sont progressivement remplies à partir des tables SwitchBrew actuelles et des `FunctionInfo` des propriétaires Encore. Les lignes marquées **SWIPC-HIST** sont un filet historique ; **SB-CURRENT** indique une recroisée actuelle.

## A.1 Service Manager `sm:` — SB-CURRENT

SwitchBrew documente quatre commandes principales. Elles sont critiques pour toute la chaîne HLE.

| Cmd | Fonction | Statut Encore | Owner/handler | Revalidation | Notes |
|---:|---|---|---|---|---|
| 0 | RegisterClient | ? | service SM à qualifier dans le graphe actif | 21/11/2026 | TIPC à partir de HOS 12 ; vérifier adaptation des IDs |
| 1 | GetServiceHandle | ? | idem | 21/11/2026 | P0 : acquisition réelle des services |
| 2 | RegisterService | ? | idem | 21/11/2026 | surtout services système |
| 3 | UnregisterService | ? | idem | 21/11/2026 | cycle de vie |

## A.2 Kernel SVC — SB-CURRENT

La table exhaustive de référence est SwitchBrew SVC. Le registre ne confond pas « dispatcher présent » et sémantique correcte. Les SVC déjà observés dans les logs FC27 (`WaitSynchronization`, `WaitProcessWideKeyAtomic`, `SignalProcessWideKey`) restent prioritaires pour la qualification comportementale.

| ID | Fonction | Statut Encore | Revalidation | Note |
|---:|---|---|---|---|
| 0x01 | SetHeapSize | ? | 21/11/2026 | vérifier limites/alignement et erreurs |
| 0x18 | WaitSynchronization | ? | 21/11/2026 | observé dans traces FC27 ; sampling ≠ preuve de blocage |
| 0x1C | WaitProcessWideKeyAtomic | ? | 21/11/2026 | observé dans traces FC27 |
| 0x1D | SignalProcessWideKey | ? | 21/11/2026 | observé dans traces FC27 |
| 0x45 | CreateEvent | ? | 21/11/2026 | table moderne SwitchBrew |
| 0x46 | MapIoRegion | ? | 21/11/2026 | HOS 13+ |
| 0x47 | UnmapIoRegion | ? | 21/11/2026 | HOS 13+ |

> La sous-table SVC complète sera tenue ici au même format lorsque la comparaison automatique du dispatcher actif sera terminée ; les entrées D/P du registre NS1 existant restent les preuves source jusque-là.

## A.3 Account — SB-CURRENT + source Eden

Le propriétaire Eden contient un grand nombre de commandes enregistrées mais encore `nullptr`. Cela doit rester visible : la présence du service ne signifie pas une couverture fonctionnelle complète.

| Service/interface | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| acc:su / IAccountServiceForAdministrator | 0 | GetUserCount | SRC | 21/11/2026 |
|  | 1 | GetUserExistence | SRC | 21/11/2026 |
|  | 2 | ListAllUsers | SRC | 21/11/2026 |
|  | 3 | ListOpenUsers | SRC | 21/11/2026 |
|  | 4 | GetLastOpenedUser | SRC | 21/11/2026 |
|  | 5 | GetProfile | SRC | 21/11/2026 |
|  | 6 | GetProfileDigest | **NULL** | 21/11/2026 |
|  | 50 | IsUserRegistrationRequestPermitted | SRC | 21/11/2026 |
|  | 51 | TrySelectUserWithoutInteractionDeprecated | SRC | 21/11/2026 |
|  | 52 | TrySelectUserWithoutInteraction | SRC | 21/11/2026 |
|  | 99 | DebugActivateOpenContextRetention | **NULL** | 21/11/2026 |
|  | 100 | GetUserRegistrationNotifier | **NULL** | 21/11/2026 |
|  | 101 | GetUserStateChangeNotifier | **NULL** | 21/11/2026 |
|  | 102 | GetBaasAccountManagerForSystemService | SRC | 21/11/2026 |
|  | 103 | GetBaasUserAvailabilityChangeNotifier | **NULL** | 21/11/2026 |

Le même audit doit être conservé pour `acc:u0`, `acc:u1`, `acc:aa` et les sous-interfaces Baas/Profile : plusieurs tables Eden sont majoritairement NULL malgré un service enregistré.

## A.4 NFC — SB-CURRENT + source Eden

| Interface | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| IUser/ISystem | 0–3 | Initialize/Finalize/GetState/IsNfcEnabled (legacy) | SRC | 21/11/2026 |
| IUser/ISystem | 400–412 | Initialize → GetDeactivateEventHandle | SRC | 21/11/2026 |
| IUser/ISystem | 1000 | ReadMifare | SRC | 21/11/2026 |
| IUser/ISystem | 1001 | WriteMifare | SRC | 21/11/2026 |
| IUser/ISystem | 1300 | SendCommandByPassThrough | SRC | 21/11/2026 |
| IUser/ISystem | 1301 | KeepPassThroughSession | **NULL** | 21/11/2026 |
| IUser/ISystem | 1302 | ReleasePassThroughSession | **NULL** | 21/11/2026 |
| nfc:am / IAm | 0 | Initialize | **NULL** dans l'interface AM retournée | 21/11/2026 |
| nfc:am / IAm | 1 | Finalize | **NULL** | 21/11/2026 |
| nfc:am / IAm | 2 | NotifyForegroundApplet | **NULL** | 21/11/2026 |

## A.5 Loader / Process Manager — SB-CURRENT + source active R23

### Loader

| Service | Cmd | Fonction SwitchBrew | Statut source initial | Revalidation |
|---|---:|---|---|---|
| ldr:shel | 0 | SetProgramArgument | **NULL** | 21/11/2026 |
| ldr:shel | 1 | FlushArguments | **NULL** | 21/11/2026 |
| ldr:dmnt | 0 | SetProgramArgument2 | **NULL** | 21/11/2026 |
| ldr:dmnt | 1 | FlushArguments2 | **NULL** | 21/11/2026 |
| ldr:dmnt | 2 | GetProcessModuleInfo | **NULL** | 21/11/2026 |
| ldr:pm | 0 | CreateProcess | **NULL** | 21/11/2026 |
| ldr:pm | 1 | GetProgramInfo | **NULL** | 21/11/2026 |
| ldr:pm | 2 | PinProgram | **NULL** | 21/11/2026 |
| ldr:pm | 3 | UnpinProgram | **NULL** | 21/11/2026 |
| ldr:pm | 4 | SetEnabledProgramVerification | **NULL** | 21/11/2026 |

Ces NULL sont importants : il faut vérifier si le runtime réel délègue ces fonctions à une autre couche avant de conclure à une absence comportementale.

### Process Manager

| Service | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| pm:bm | 0 | GetBootMode | SRC | 21/11/2026 |
| pm:bm | 1 | SetMaintenanceBoot | SRC | 21/11/2026 |
| pm:info | 0 | GetProgramId | SRC | 21/11/2026 |
| pm:shell | 0 | LaunchProgram | **NULL** | 21/11/2026 |
| pm:shell | 1 | TerminateProcess | **NULL** | 21/11/2026 |
| pm:shell | 2 | TerminateProgram | **NULL** | 21/11/2026 |
| pm:shell | 3 | GetProcessEventEvent/Handle | **NULL** | 21/11/2026 |
| pm:shell | 4 | GetProcessEventInfo | **NULL** | 21/11/2026 |
| pm:shell | 5 | NotifyBootFinished | **NULL** | 21/11/2026 |
| pm:shell | 6 | GetApplicationProcessIdForShell | SRC | 21/11/2026 |
| pm:shell | 7 | BoostSystemMemoryResourceLimit | **NULL** | 21/11/2026 |
| pm:shell | 8 | BoostApplicationThreadResourceLimit | **NULL** | 21/11/2026 |
| pm:shell | 9 | GetBootFinishedEvent | **NULL** | 21/11/2026 |

## A.6 Log / Fatal — SB-CURRENT

| Service/interface | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| lm | 0 | OpenLogger | SRC | 21/11/2026 |
| ILogger | 0 | Log | SRC | 21/11/2026 |
| ILogger | 1 | SetDestination | SRC | 21/11/2026 |
| ILogger | 2 | TransmitHashedLog | **NULL** | 21/11/2026 |
| ILogger | 3 | DevNotify | **NULL** | 21/11/2026 |
| lm:get | 0 | StartLogging | **NULL** | 21/11/2026 |
| lm:get | 1 | StopLogging | **NULL** | 21/11/2026 |
| lm:get | 2 | GetLog | **NULL** | 21/11/2026 |
| lm:get | 100 | CreateDevNotificationReceiver | **NULL** | 21/11/2026 |
| fatal:u | 0 | ThrowFatal | SRC | 21/11/2026 |
| fatal:u | 1 | ThrowFatalWithPolicy | SRC | 21/11/2026 |
| fatal:u | 2 | ThrowFatalWithCpuContext | SRC | 21/11/2026 |
| fatal:u | 3 | HOS 21+ commande supplémentaire | **ABSENT/à qualifier** | 21/11/2026 |

---

# PARTIE B — Inventaire automatisé Eden / baseline SwIPC historique

Cette partie sert de **filet exhaustif** pour les interfaces historiques : elle compare les IDs/noms de SwIPC aux tables `FunctionInfo` Eden. Elle ne remplace jamais les pages SwitchBrew actuelles pour les firmwares récents.

Les sections seront regroupées par famille avec les colonnes :

`Interface | Service | Cmd | Nom de référence | Eden | Handler | Owner | Référence | Revalidation`.

### Interprétation automatique

- entrée Eden avec `nullptr` → **NULL** ;
- handler non nul → **SRC** jusqu'à lecture du corps ;
- commande SwIPC sans entrée Eden correspondante → **ABSENT** ;
- entrée Eden sans équivalent SwIPC → **NOUVEAU/À RECROISER SWITCHBREW** ;
- les fonctions modernes 4.0.0–23.5.0 sont ajoutées à partir de SwitchBrew sous **SB-CURRENT**, pas déduites de SwIPC.

> **Important :** les comptes automatiques sont un outil de navigation. Les décisions P0/P1 sont prises sur le propriétaire C++ effectivement sélectionné, les logs et la console.

## B.1 Familles prioritaires à maintenir exhaustivement

- [ ] SM + SVC
- [ ] Account
- [ ] HID / HIDBUS / IRS
- [ ] AM / appletOE / appletAE
- [ ] Filesystem / fsp-srv / IStorage / IFile / IDirectory
- [ ] NS / AOC / NCM / NIM
- [ ] VI / Nvnflinger
- [ ] NVDRV / nvmap / nvhost
- [ ] Audio / hwopus
- [ ] Sockets / DNS / SSL / NIFM / LDN
- [ ] Settings / time
- [ ] Loader / PM / PGL
- [ ] NFC / NFP / Mii
- [ ] BCAT / OLSC / capture / erpt
- [ ] services firmware 23.x (`stpl:*`, nouveaux IDs NS/HID/audio/etc.)

---

# PARTIE C — File d'écarts explicites

Ce tableau ne contient que des trous/limites prouvés par la source ou la référence. Il évite de perdre les fonctions importantes au milieu des milliers de lignes.

| Priorité | Domaine | Fonction/commande | Statut | Pourquoi c'est ouvert | Action de fermeture |
|---|---|---|---|---|---|
| P0 | Loader | ldr:pm 0–4 | **NULL** | handlers R23 enregistrés mais nuls dans le propriétaire inspecté | vérifier délégation réelle/owner CMake puis implémenter le contrat requis |
| P0 | PM | pm:shell 0–5, 7–9 | **NULL** | couverture très faible de l'interface shell | vérifier chemin de lancement utilisé par Eden avant patch |
| P0/P1 | Account | plusieurs Baas/notifiers/cache | **NULL** | nombreuses commandes enregistrées sans handler | prioriser seulement celles exercées par logs/jeux |
| P1 | NFC | 1301/1302 | **NULL** | pass-through session incomplète | implémenter si Title ID/log l'exerce |
| P2 | LM | hashed/dev/getter récents | **NULL** | logging retail est largement stub côté HOS lui-même | ne pas détourner P0/P1 sans consommateur |
| P1/P2 | Firmware 23.x | commandes absentes de SwIPC historique | **?** | baseline historique insuffisante | recroiser SwitchBrew actuel et source active à chaque backport |

---

# PARTIE D — Politique de mise à jour

À chaque ajout/modification HLE/SVC :

1. modifier **la ligne existante** de ce registre ;
2. renseigner le nouveau statut, owner exact, SHA moteur + vendor et date ;
3. si le handler passe de NULL/ABSENT à SRC, ne pas écrire « résolu » ;
4. passer à OK-HOST uniquement avec un témoin réellement pertinent ;
5. passer à OK-PS5 uniquement avec une session console représentative ;
6. conserver l'historique concis dans la cellule Notes, pas dans un nouveau Markdown ;
7. recroiser SwitchBrew lorsqu'un firmware change l'ID, le nom, les buffers, les handles, le type IPC HIPC/TIPC ou les erreurs attendues.

## Contrôle périodique conseillé

Lors d'un changement de firmware invité, d'un backport HLE ou avant une grosse campagne console :

- comparer `Services_API` S1 avec les services enregistrés ;
- comparer les pages de famille pour les IDs nouveaux ;
- comparer la table SVC ;
- scanner les `FunctionInfo` pour `nullptr`;
- scanner les corps pour `UNIMPLEMENTED`, `Stubbed`, TODO, succès constant et objets factices ;
- vérifier les remplacements CMake/overlays ;
- mettre à jour **ce fichier uniquement**.

---

## État de ce premier snapshot

Le document est **créé et utilisable dès maintenant**, mais son but est d'être enrichi jusqu'à la matrice exhaustive. Les premières lignes montrent déjà un point important que le registre d'architecture ne rendait pas visible : plusieurs services existent et sont enregistrés alors qu'une part significative de leurs commandes reste NULL ou minimale. Cette distinction doit guider les futures recherches par signature exacte plutôt que d'assimiler « service présent » à « service complet ».
