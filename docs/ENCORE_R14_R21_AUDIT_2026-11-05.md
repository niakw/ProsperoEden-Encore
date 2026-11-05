# Eden Encore — vérification R14 salons / R21 mises à jour

Audit source sans build complet PS5, sans tentative d'installation ni
connexion à une salle. Branche dédiée superposée à la PR #20 ; main et le
sous-module vendor sont inchangés.

## R21 — mise à jour de l'application native

Le lanceur dispose d'un bouton de vérification manuel à côté des
paramètres, avec état visuel : vert (version stable connue à jour),
orange (nouvelle version), gris (état inconnu/hors ligne), bleu
(vérification en cours). La confirmation déclenche une nouvelle requête
GitHub, pas le remplacement de fichiers sur la PS5.

Le dépôt officiel interrogé est désormais niakw/ProsperoEden-Encore ;
l'ancienne URL de niakw/Prospero.Eden-Encore n'est plus utilisée pour les
métadonnées ni comme origine de téléchargement admise. Le validateur
impose la forme exacte d'une archive FTP PPSA99008, une taille bornée et
le digest SHA256 annoncé, sans faire confiance aux notes de release.

Le statut State::available n'est jamais émis par les services natifs.
Le helper self_update_helper dispose d'un protocole sécurisé, d'extraction
bornée et de sauvegarde, mais n'est pas connecté au launcher, à un
téléchargement vérifié ni à un redémarrage PS5. Il serait donc trompeur
d'annoncer que le bouton installe l'application.

La cible d'installation du helper est exclusivement
/data/homebrew/PPSA99008. Les archives FFPFSC ou PKG ne sont pas
acceptées comme mises à jour du dossier natif.

Mapping de version natif : R1 -> 01.400.001 ; R323 -> 01.400.323.
Les artefacts déjà publiés avant la migration sont une exception
historique, pas une raison de réutiliser les URL du fork.

## R14 — multijoueur : salons

Les salons publics sont récupérés sur un worker séparé, par une requête
GET https://api.ynet-fun.xyz/lobby. Le parser contrôle taille, JSON,
adresses IPv4 publiques, ports et population.

Le champ compatible compare maintenant netVersion au
Network::network_version réellement défini dans le moteur Eden
(1 sur le vendor inspecté), et non à l'ancien argument 0. Cela permet
d'identifier correctement les salles du même protocole.
Un test refuse les salles de version 0 ou 2.

Le menu reste en lecture seule. Les boutons rejoindre, créer/héberger
et les échanges invité via Network::RoomMember, ENet, BSD et LDN
ne sont pas raccordés au launcher PS5. L'amont possède bien ces
composants, mais cela ne prouve pas leur compatibilité native sur
firmware 13.60. Aucun transfert invité ni salon joignable vérifié.

## Vérifications effectivement exécutées

Tests C++ hôtes du parseur de salles, des versions et des releases
stables (dont rejet des URL du fork). Contrôle source R14/R21.
Tests hôtes de l'extraction ZIP et de l'helper local (cas sûrs,
chemins interdits, cible exacte, sauvegardes et restauration) ;
19 tests Python de prévalidation ZIP. Aucun build PS5 complet,
aucune mise à jour de fichiers sur console et aucune session
multijoueur effective.
