# Eden Encore — Lossless Scaling et « Fluidité améliorée » (PS5)

Le menu **Paramètres > Vidéo > Fluidité améliorée** et le réglage par jeu
**Bibliothèque > Jeu > Fluidité améliorée** proposent quatre valeurs :

- **Désactivé** : aucun frame generation.
- **MihawkGen** : interpolation neurale portée en Vulkan, avec données réseau
  et GPU privés à Eden Encore.
- **FSR 3** : génération d'images AMD ; intégration Vulkan non achevée,
  en attente de données de mouvement, profondeur et jitter fiables provenant
  des images invitées. Le choix ne garantit aucune frame supplémentaire.
- **Lossless Scaling (LSFG)** : utilise les shaders contenus dans le
  fichier Lossless.dll fourni **par l'utilisateur**. Le projet ne copie
  ni n'exécute une DLL Windows et ne fournit pas ce fichier.

## Installer votre fichier personnel pour LSFG

1. Sur un PC où vous possédez légalement Lossless Scaling, récupérez
   **votre propre** fichier nommé exactement Lossless.dll. Vérifiez les
   conditions de licence du logiciel avant d'en copier le contenu vers PS5.
2. Depuis votre gestionnaire de fichiers FTP PS5, créez le dossier
   /data/prosperoeden/user/lossless/ si nécessaire.
3. Placez le fichier **à ce chemin exact** :
   /data/prosperoeden/user/lossless/Lossless.dll.
   Respectez la casse du nom ; lossless.dll, un fichier .exe, un
   raccourci ou un répertoire ne sont pas reconnus.
4. Revenez au menu vidéo d'Eden Encore, puis choisissez **LSFG** dans
   « Fluidité améliorée ». Si le fichier manque ou semble invalide,
   un message indique le chemin requis et le choix n'est pas conservé.
5. Redémarrez la session de jeu après tout changement. La lecture des
   shaders et l'initialisation de la chaîne Vulkan ont lieu au lancement
   du moteur. Si un choix sauvegardé reste sur LSFG après suppression
   du fichier, le moteur **désactive l'interpolation** et affiche les
   vraies images du jeu sans tenter de lire une DLL inexistante.

La vérification du menu contrôle le type de fichier, les liens symboliques,
sa taille (128 octets à 256 Mio) et l'en-tête MZ des exécutables PE.
Ce n'est **pas** la validation complète des shaders : le chargeur natif
doit ensuite extraire les ressources, identifier les variantes FP16/FP32,
les traduire en SPIR-V et vérifier les capacités Vulkan.

## À quoi s'attendre

FSR **1 spatial** est un filtre d'**upscaling**, indépendant de ces trois
méthodes de création de frames. L'exécution du code invité, les FPS réels
du jeu et sa vitesse ne sont pas accélérés par la création de frames
intermédiaires. La fluidité d'affichage peut augmenter si le GPU et la
sortie vidéo le permettent, avec une latence et des artefacts variables.

L'intégration LSFG dans le code natif et les contrôles hôtes sont
présents ; **aucun test GPU PS5 complet ni résultat 30→60 réel** n'est
encore démontré. Ne pas présenter une option visible dans le menu comme
une validation de qualité sur les jeux. Le HUD natif Encore est composé
après l'interpolation ; les scores, menus ou sous-titres intégrés aux
pixels du jeu peuvent subir du ghosting.

## En cas de message « Lossless.dll manquant ou invalide »

Vérifiez le chemin absolu, la casse de Lossless.dll, les droits de
lecture et la présence d'un fichier régulier, non d'un lien symbolique.
Un simple renommage d'un autre fichier en .dll ne fonctionne pas.
Il n'existe aucun téléchargement automatique de cette DLL par Encore.
Supprimez toute copie corrompue et utilisez une source personnelle
légalement obtenue. Si la génération échoue malgré un fichier lisible,
revenez à **Désactivé** ou essayez MihawkGen lorsque la méthode sera
qualifiée sur votre PS5.
