# Eden Encore — vérification R14 salons / R21 mises à jour

Audit source sans build complet PS5, sans tentative d'installation ni
connexion à une salle. Branche dédiée superposée à la PR #20 ; main et le
sous-module vendor sont inchangés.

## R21 — mise à jour de l'application native

La recherche des releases stables est **automatique au lancement par
défaut** pour les nouvelles installations, sur un worker non bloquant.
L'utilisateur peut la désactiver dans les réglages. Les préférences
déjà enregistrées, y compris un ancien refus, restent respectées.
Ce contrôle ne télécharge ni n'installe rien automatiquement.

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

Le candidat de release comprend maintenant taille, SHA256, nom,
chemin reconstruit depuis le dépôt officiel (jamais depuis les notes)
et version cible. Le vérificateur portable VerifiedArchive refuse
taille incorrecte, octets en trop, SHA256 divergent ou flux finalisé
réutilisé. Tests hôtes ASan/UBSan. Ce précontrôle n'autorise pas seul
le remplacement des fichiers : le helper doit encore vérifier
l'archive ZIP et la cible d'installation.

Le chemin natif est maintenant raccordé en source : le packager
construit et copie self-updater.elf ; la version stable possède un
état available seulement si cet ELF est présent et l'archive officielle
répond aux règles. Sur confirmation explicite, un worker recharge
les métadonnées stables et refuse tout changement, télécharge sur HTTPS
avec le magasin de certificats maintenu et vérifie intégralement
taille/SHA256. Il transmet alors le helper ELF au loader local 9021,
puis les chunks bornés ZIP. Le helper valide fichiers, chemin, version,
empreinte, sauvegardes, restauration et espace libre avant de répondre
staged. L'application envoie apply, attend applying puis ferme le
processus pour que le helper puisse modifier le répertoire cible.

**Attention** : compilation syntaxique PS5 simulée sur Mac, tests
de contrat/cryptographie hôtes seulement. Aucun build PS5 complet,
téléchargement réel sur console, ni installation/rollback en conditions
PS5 13.60 démontrés. L'activation réelle ne sera établie qu'après tests
console. La recherche peut être automatique ; l'installation exige
toujours une confirmation et ne s'effectue jamais silencieusement.

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

Le menu est désormais relié aux actions de transport amont :
**Croix : rejoindre** un salon public compatible, non protégé et non plein ;
**Carré : héberger** un salon LAN privé ou le **quitter**. Les commandes
Network::Room, RoomMember et ENet s'exécutent sur un worker séparé
sans bloquer l'interface. L'initialisation réutilise le Network::Init
déjà présent pour ne pas écraser les objets réseau du guest. Le worker
ne capture ni le lanceur ni le service, et une opération en cours
ne peut pas être lancée deux fois. La vue et les commandes sont
traduites dans les 29 catalogues.

**Périmètre :** hébergement local LAN uniquement, sans enregistrement
du salon dans un annuaire public ni traversée NAT ; aucun mot de passe
ni système de comptes. LDN/traffic proxy, paquets invités NS1/NS2,
compatibilité firmware et sessions entre consoles demandent une
validation sur PS5. Les messages de statut du réseau doivent encore
être qualifiés avec les scénarios réels de déconnexion. Ne pas annoncer
le multijoueur comme garanti fonctionnel sur console.

## Vérifications effectivement exécutées

Tests C++ hôtes du parseur de salles, des versions et des releases
stables (dont rejet des URL du fork). Contrôle source R14/R21.
Tests hôtes de l'extraction ZIP et de l'helper local (cas sûrs,
chemins interdits, cible exacte, sauvegardes et restauration) ;
19 tests Python de prévalidation ZIP. Aucun build PS5 complet,
aucune mise à jour de fichiers sur console et aucune session
multijoueur effective.
