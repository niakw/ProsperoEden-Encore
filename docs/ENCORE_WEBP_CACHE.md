# Eden Encore — cache WebP 80 et application compactée

**Addendum du 10 novembre 2026 (branche de maintenance) :** libwebp 1.6.0 est maintenant intégré comme source amont épinglée sous `vendor/sources/libwebp/` (jamais comme override dans `encore-active/`) et n'est plus un sous-module externe. Les validations 1.5.0 rapportées ci-dessous sont historiques ; le nouveau binaire exige une validation hôte et PS5 indépendante.

**6 novembre 2026 · PR #24 DRAFT · validation PS5 encore requise.**

Le cache de couvertures stockait en TGA non compressé les JPEG/PNG
Nlib/LaunchBox téléchargés. Le relevé FTP en lecture seule donne
**97,5 Mio pour 26 fichiers TGA** sous /data/prosperoeden/covers.

## Changements intégrés

- JPEG/PNG source vers WebP qualité 80 directement, sans JPEG 80
  intermédiaire et sans conversion TGA lors du téléchargement.
- libwebp 1.5.0, version figée a4d7a715337ded4451fec90ff8ce79728e04126c,
  ancien sous-module externe libwebp (état historique du 6 novembre), lié en statique ; la version 1.6.0 actuelle est maintenant dans `vendor/sources/libwebp/`.
- Décodage WebP hors du thread UI ; JPEG/PNG et TGA historiques
  restent lisibles, ainsi que les avatars DDS.
- Migration locale des TGA historiques générés par Eden :
  conversion BGRA vers WebP 80, contrôle de l'image WebP,
  remplacement atomique, suppression du TGA uniquement si réussi.
  Les scans retail personnels **sans reçu .source** restent intacts ;
  le reçu de provenance des scans CDN est conservé avec le WebP.
- Packaging de PPSA99008 : fond et photographies en WebP 80,
  logos et éléments UI transparents en WebP sans perte.
  Les images système et les DDS demeurent à leurs formats natifs.
- Aucune modification des fichiers FTP de la PS5 n'a été faite.
  L'installation du nouveau binaire doit précéder la migration.

## Échantillons FTP testés

| Image | TGA brut | WebP q80 | Économie |
| --- | ---: | ---: | ---: |
| Jaquette avant | 8 703 546 octets | 519 936 octets | 94,0 % |
| Bannière 1080p | 8 294 418 octets | 584 012 octets | 93,0 % |
| Icône 256 px | 262 162 octets | 13 550 octets | 94,8 % |

## Validation

libwebp 1.5.0 compilé sur Mac ; tests C++ WebP encode/decode,
alpha conservé et données tronquées rejetées. Le vrai code C++
MigrateGeneratedTga a été compilé isolément avec les sources
de production ; tests positifs sur les images FTP, migration
du reçu et refus de supprimer un scan sans reçu : PASS.

Contrôle de l'interface retail et preflight de métadonnées : PASS.
**Pas de build PS5 complet ni de preuve visuelle sur console.**
Les anciens TGA occupent encore leur espace sur l'installation
actuelle jusqu'à migration par une application compatible.
