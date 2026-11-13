// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string_view>
namespace pe::ui::embedded {
inline constexpr std::string_view kFrFr = R"FRPO(# ProsperoEden launcher - fr-FR
# English text is the key (msgid); msgstr is the translation. Keep {0} {1} as they are,
# keep UPPERCASE labels uppercase, and keep names (ProsperoEden, Eden, PS5, Vulkan, OpenGL,
# AMD FSR, DLC, NSP, XCI, prod.keys, Ryujinx) unchanged.

#: settings_store.h
msgid "0.25x (minimum)"
msgstr "0,25x (minimum)"

#: settings_store.h
msgid "0.5x (fastest, softer)"
msgstr "0,5x (le plus rapide, plus doux)"

#: settings_store.h
msgid "0.75x (faster)"
msgstr "0,75x (plus rapide)"

#: settings_store.h
msgid "1.25x (recommended)"
msgstr "1.25x (recommandé)"

#: settings_store.h
msgid "1.5x (sharper)"
msgstr "1,5x (plus net)"

#: pe/ui/settings.cpp
msgid "100% is full DualSense rumble strength. Lower it if vibration feels too strong."
msgstr "100 % correspond à l'intensité maximale des vibrations DualSense. Réduisez-la si elles sont trop fortes."

#: settings_store.h
msgid "1x (native)"
msgstr "1x (natif)"

#: settings_store.h
msgid "2x (high memory)"
msgstr "2x (mémoire élevée)"

#: settings_store.h
msgid "3x (very high memory)"
msgstr "3x (mémoire très élevée)"

#: settings_store.h
msgid "4x (extreme memory)"
msgstr "4x (mémoire extrême)"

#: pe/ui/settings.cpp
msgid "60 Hz is recommended. 120 Hz changes display mode only; the game still needs to render above 60 FPS to benefit."
msgstr "60 Hz est recommandé. 120 Hz ne change que le mode d'affichage ; le jeu doit quand même dépasser 60 FPS pour en profiter."

#: pe/ui/library.cpp
msgid "60 Hz is the safe default. Use 120 Hz only with a compatible display or high-FPS patch."
msgstr "60 Hz est le réglage sûr. Utilisez 120 Hz seulement avec un écran compatible ou un patch haute fréquence d'images."

#: eden_services.cpp
msgid "A firmware NCA cannot be read. Reinstall the firmware dump."
msgstr "Un fichier NCA du firmware est illisible. Réinstallez les fichiers du firmware."

#: pe/ui/switch_theme.cpp
msgid "About"
msgstr "À propos"

#: pe/ui/browse.cpp, pe/ui/switch_theme.cpp
msgid "About Eden Encore"
msgstr "À propos d'Eden Encore"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Accent"
msgstr "Accent"

#. Label: which folders the app can read.
#: pe/ui/browse.cpp
msgid "ACCESS"
msgstr "ACCÈS"

#. A settings category: options that make the menu easier to see and follow.
#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Accessibility"
msgstr "Accessibilité"

#: pe/ui/settings.cpp
msgid "ACCESSIBILITY"
msgstr "ACCESSIBILITÉ"

#: Nlib metadata
msgid "Action"
msgstr "Action"

#: Nlib metadata
msgid "Action-Adventure"
msgstr "Action-aventure"

#. {0}: updates, DLC and mods of the game; {1}: the language it will use.
#: pe/ui/home.cpp
msgid "Add-ons: {0}  /  Language: {1}"
msgstr "Extensions : {0}  /  Langue : {1}"

#: Nlib metadata
msgid "Adventure"
msgstr "Aventure"

#: pe/ui/browse.cpp, pe/ui/switch_theme.cpp
msgid "All credit for the Eden emulator goes to its developers and contributors."
msgstr "Tout le mérite de l'émulateur Eden revient à ses développeurs et contributeurs."

#: pe/ui/switch_theme.cpp
msgid "All Software"
msgstr "Tous les logiciels"

#: pe/ui/launcher.cpp
msgid "Already up to date: {0}"
msgstr "Déjà à jour : {0}"

#: eden_services.cpp
msgid "Another language"
msgstr "Autre langue"

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Anti-aliasing"
msgstr "Anticrénelage"

#: pe/ui/settings.cpp
msgid "ANTI-ALIASING"
msgstr "ANTICRÉNELAGE"

#: pe/ui/library.cpp, pe/ui/settings.cpp
msgid "Anti-aliasing smooths jagged edges. None is fastest; FXAA is light; SMAA prioritizes image quality."
msgstr "L’anticrénelage lisse les contours. Aucun est le plus rapide ; FXAA est léger ; SMAA privilégie la qualité d’image."

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Appearance"
msgstr "Apparence"

#: pe/ui/settings.cpp
msgid "APPEARANCE"
msgstr "APPARENCE"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Application"
msgstr "Application"

#: pe/ui/settings.cpp
msgid "APPLICATION"
msgstr "APPLICATION"

#: pe/ui/launcher.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Application updates"
msgstr "Mises à jour de l'application"

#: Nlib metadata
msgid "Arcade"
msgstr "Arcade"

#: pe/ui/home.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Audio"
msgstr "Audio"

#: pe/ui/settings.cpp
msgid "AUDIO"
msgstr "AUDIO"

#: eden_services.cpp, pe/ui/launcher.cpp
msgid "Australia"
msgstr "Australie"

#: pe/ui/settings.cpp
msgid "AUTO CHECK"
msgstr "AUTO VÉRIFIER"

#: pe/ui/switch_theme.cpp
msgid "Auto check"
msgstr "Vérification auto"

#: pe/ui/settings.cpp
msgid "Auto check on"
msgstr "Vérification auto activée"

#. Button hint: go back one screen.
#: pe/ui/browse.cpp, pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/multiplayer.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Back"
msgstr "Retour"

#: pe/ui/switch_theme.cpp
msgid "Back to HOME"
msgstr "Retour à l'accueil"

#: pe/ui/settings.cpp
msgid "BACKGROUND"
msgstr "FOND D'ÉCRAN"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Background"
msgstr "Fond d'écran"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Background motion"
msgstr "Animation du fond"

#. An upscaling filter.
#: settings_store.h
msgid "Bicubic"
msgstr "Bicubique"

#. An upscaling filter.
#: settings_store.h
msgid "Bilinear"
msgstr "Bilinéaire"

#: pe/ui/settings.cpp
msgid "Bilinear is the lightest default. AMD FSR is most useful when rendering below the TV output size."
msgstr "Bilinéaire est le réglage le plus léger. AMD FSR est surtout utile lorsque le rendu est inférieur à la résolution de sortie TV."

#: pe/ui/library.cpp
msgid "Bilinear is the lightest default. AMD FSR is useful when rendering below the TV output size."
msgstr "Bilinéaire est le réglage le plus léger. AMD FSR est utile lorsque le rendu est inférieur à la résolution de sortie TV."

#: Nlib metadata
msgid "Board Game"
msgstr "Jeu de société"

#. Button hint: move through the list.
#: pe/ui/browse.cpp, pe/ui/multiplayer.cpp
msgid "Browse"
msgstr "Parcourir"

#: pe/ui/switch_theme.cpp
msgid "Browse folders: D-pad / Open: A"
msgstr "Parcourir : croix directionnelle · Ouvrir : A"

#: pe/ui/library.cpp
msgid "Browse games"
msgstr "Parcourir les jeux"

#: pe/ui/settings.cpp
msgid "Browse settings"
msgstr "Parcourir les paramètres"

#: pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Button mapping"
msgstr "Attribution des touches"

#: pe/ui/settings.cpp
msgid "BUTTON MAPPING"
msgstr "ATTRIBUTION DES TOUCHES"

#: pe/ui/mapping.cpp
msgid "Button mapping reset to global settings."
msgstr "Attribution des touches réinitialisée sur les réglages globaux."

#: pe/ui/mapping.cpp
msgid "Button mapping reset to the active profile."
msgstr "Attribution des touches réinitialisée selon le profil actif."

#: pe/ui/mapping.cpp
msgid "Button mapping saved."
msgstr "Touches enregistrées."

#: pe/ui/settings.cpp
msgid "BUTTON PROFILE"
msgstr "PROFIL DE TOUCHES"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Button profile"
msgstr "Profil de touches"

#: pe/ui/home.cpp, pe/ui/settings.cpp
msgid "CACHE"
msgstr "CACHE"

#: pe/ui/switch_theme.cpp
msgid "Cache"
msgstr "Cache"

#: pe/ui/settings.cpp
msgid "Cache: {0}  |  Logs: {1}"
msgstr "Cache : {0}  |  Journaux : {1}"

#: pe/ui/launcher.cpp, pe/ui/switch_theme.cpp
msgid "Cancel"
msgstr "Annuler"

#: eden_services.cpp
msgid "Cannot read firmware/ in {0}. Install extracted firmware NCAs."
msgstr "Impossible de lire firmware/ dans {0}. Installez les fichiers NCA extraits du firmware."

#: Nlib metadata
msgid "Card Game"
msgstr "Jeu de cartes"

#: Nlib metadata
msgid "Casual"
msgstr "Occasionnel"

#. Button hint: change the highlighted setting.
#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Change"
msgstr "Modifier"

#: pe/ui/launcher.cpp
msgid "Change console mode for this game?"
msgstr "Changer le mode console de ce jeu ?"

#. What a mod is made of: cheat codes.
#: eden_services.cpp, host/fake_services.cpp
msgid "Cheats"
msgstr "Codes de triche"

#: pe/ui/launcher.cpp
msgid "Check for an Eden Encore update now?"
msgstr "Vérifier maintenant les mises à jour d'Eden Encore ?"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Check now"
msgstr "Vérifier maintenant"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Check on launcher start"
msgstr "Vérifier au démarrage du launcher"

#: pe/ui/launcher.cpp, pe/ui/settings.cpp
msgid "Checking official releases..."
msgstr "Vérification des versions officielles..."

#: pe/ui/multiplayer.cpp
msgid "Checking public rooms..."
msgstr "Recherche des salons publics..."

#: pe/ui/settings.cpp
msgid "Checks official stable GitHub Releases only. No automatic installation."
msgstr "Consulte uniquement les versions stables officielles sur GitHub. Aucune installation automatique."

#: eden_services.cpp, pe/ui/library.cpp
msgid "China"
msgstr "Chine"

#: settings_store.h
msgid "Chinese (Simplified)"
msgstr "Chinois (simplifié)"

#: settings_store.h
msgid "Chinese (Traditional)"
msgstr "Chinois (traditionnel)"

#. Button hint: choose the highlighted language.
#: pe/ui/browse.cpp
msgid "Choose"
msgstr "Choisir"

#: pe/ui/home.cpp
msgid "Choose a game from your library."
msgstr "Choisissez un jeu dans votre bibliothèque."

#: pe/ui/browse.cpp
msgid "Choose one root for keys, firmware, games, updates and mods"
msgstr "Choisissez une racine unique pour les clés, le firmware, les jeux, les mises à jour et les mods"

#: pe/ui/settings.cpp
msgid "Choose the launcher interface without changing game or controller settings."
msgstr "Choisissez l'interface sans modifier les jeux ni les commandes."

#: pe/ui/switch_theme.cpp
msgid "Choose your preferred language"
msgstr "Choisissez votre langue"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Circle"
msgstr "Rond"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Clear"
msgstr "Vider"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Clear cache"
msgstr "Vider le cache"

#: pe/ui/launcher.cpp
msgid "Clear cache?"
msgstr "Vider le cache ?"

#: eden_services.cpp
msgid "Cleared {0} of cache."
msgstr "Cache vidé : {0}."

#: pe/ui/launcher.cpp, pe/ui/library.cpp
msgid "Close"
msgstr "Fermer"

#: Nlib metadata
msgid "Co-op"
msgstr "Coopératif"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 1 blue"
msgstr "Bleu couleur 1"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 1 green"
msgstr "Vert couleur 1"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 1 preset"
msgstr "Préréglage couleur 1"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 1 red"
msgstr "Rouge couleur 1"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 2 blue"
msgstr "Bleu couleur 2"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 2 green"
msgstr "Vert couleur 2"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 2 preset"
msgstr "Préréglage couleur 2"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Color 2 red"
msgstr "Rouge couleur 2"

#: pe/ui/switch_theme.cpp
msgid "Configure"
msgstr "Configurer"

#: pe/ui/launcher.cpp, pe/ui/switch_theme.cpp
msgid "Confirm"
msgstr "Confirmer"

#: pe/ui/launcher.cpp
msgid "Confirm this action?"
msgstr "Confirmer cette action ?"

#: pe/ui/home.cpp, pe/ui/launcher.cpp, pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Console mode"
msgstr "Mode console"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Contain"
msgstr "Ajuster"

#: pe/ui/home.cpp
msgid "CONTINUE PLAYING"
msgstr "CONTINUER À JOUER"

#: pe/ui/home.cpp
msgid "Controller mapping"
msgstr "Attribution des touches"

#: pe/ui/switch_theme.cpp
msgid "Controller profile"
msgstr "Profil de manette"

#: pe/ui/settings.cpp
msgid "Controller profile: {0}"
msgstr "Profil de manette : {0}"

#: pe/ui/home.cpp
msgid "CONTROLLERS"
msgstr "MANETTES"

#: pe/ui/home.cpp, pe/ui/switch_theme.cpp
msgid "Controllers"
msgstr "Manettes"

#: pe/ui/launcher.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Controls"
msgstr "Commandes"

#: pe/ui/settings.cpp
msgid "CONTROLS"
msgstr "COMMANDES"

#: pe/ui/library.cpp
msgid "Could not create the folder. Check that the game files folder can be written."
msgstr "Impossible de créer le dossier. Vérifiez que le dossier des fichiers de jeu est accessible en écriture."

#: pe/ui/library.cpp
msgid "Could not load game library. Reopen Encore to retry."
msgstr "Impossible de charger la bibliothèque de jeux. Relancez Encore pour réessayer."

#: pe/ui/library.cpp
msgid "Could not load game list. Please try again."
msgstr "Impossible de charger la liste des jeux. Réessayez."

#: pe/ui/launcher.cpp
msgid "Could not save settings. Please try again."
msgstr "Impossible d'enregistrer les paramètres. Veuillez réessayer."

#: pe/ui/browse.cpp
msgid "Could not save the storage root. Please try again."
msgstr "Impossible d'enregistrer la racine de stockage. Réessayez."

#: pe/ui/browse.cpp, pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/mapping.cpp
msgid "Could not save. Please try again."
msgstr "Impossible d'enregistrer. Veuillez réessayer."

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Create"
msgstr "Create"

#. Button hint: make the folder a game's mods go in.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Create the folder"
msgstr "Créer le dossier"

#. {0} is a folder.
#: pe/ui/library.cpp
msgid "Created {0}. Copy each mod's folder into it."
msgstr "{0} a été créé. Copiez-y le dossier de chaque mod."

#: pe/ui/browse.cpp, pe/ui/switch_theme.cpp
msgid "Credits and setup"
msgstr "Crédits et configuration"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Cross"
msgstr "Croix"

#: pe/ui/settings.cpp, settings_store.h
msgid "Custom"
msgstr "Personnalisé"

#: pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Custom PS5"
msgstr "PS5 personnalisé"

#: pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Custom Switch"
msgstr "Switch personnalisé"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Customize"
msgstr "Personnaliser"

#: pe/ui/settings.cpp
msgid "Customize every guest button. The profile automatically becomes Custom PS5 or Custom Switch."
msgstr "Personnalisez chaque touche du jeu. Le profil devient automatiquement PS5 personnalisé ou Switch personnalisé."

#: pe/ui/settings.cpp
msgid "DATA"
msgstr "DONNÉES"

#: pe/ui/settings.cpp
msgid "Data: {0}"
msgstr "Données : {0}"

#. A per-game setting that follows the general setting; {0} is its value.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Default ({0})"
msgstr "Par défaut ({0})"

#: pe/ui/settings.cpp
msgid "DETAILED LOGGING"
msgstr "JOURNALISATION DÉTAILLÉE"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Detailed logging"
msgstr "Journaux détaillés"

#: pe/ui/settings.cpp
msgid "Detailed logs on"
msgstr "Journaux détaillés activés"

#: pe/ui/launcher.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Diagnostics"
msgstr "Diagnostic"

#: pe/ui/settings.cpp
msgid "DIAGNOSTICS"
msgstr "DIAGNOSTIC"

#. Console mode: the console as if connected to a TV. Keep it short (about 9 letters).
#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Docked"
msgstr "Téléviseur"

#: pe/ui/library.cpp
msgid "Docked can improve graphics but may cost performance; Handheld is lighter for demanding games."
msgstr "Le mode TV peut améliorer les graphismes mais coûter en performances ; le mode portable est plus léger pour les jeux exigeants."

#: pe/ui/home.cpp
msgid "Done"
msgstr "Terminé"

#: pe/ui/settings.cpp
msgid "Draws the menu's small text larger."
msgstr "Agrandit les petits textes du menu."

#: pe/ui/settings.cpp
msgid "DualSense mapping, calibration, vibration and shortcuts."
msgstr "Attribution DualSense, calibrage, vibrations et raccourcis."

#: settings_store.h
msgid "Dutch"
msgstr "Néerlandais"

#: pe/ui/switch_theme.cpp
msgid "Eden Encore"
msgstr "Eden Encore"

#: pe/ui/browse.cpp
msgid "Eden Encore builds on the proven ProsperoEden 0.40 PS5 base for firmware 13.60, with the Eden core, safer recovery, and targeted compatibility, performance and TV-first UX improvements."
msgstr "Eden Encore s'appuie sur la base PS5 éprouvée de ProsperoEden 0.40 pour le firmware 13.60, avec le cœur Eden, une récupération plus sûre et des améliorations ciblées de compatibilité, de performances et d'interface TV."

#: pe/ui/home.cpp
msgid "Edit"
msgstr "Modifier"

#: pe/ui/settings.cpp
msgid "Edit custom mapping"
msgstr "Modifier les touches"

#: Nlib metadata
msgid "Education"
msgstr "Éducatif"

#: pe/ui/browse.cpp
msgid "Encore uses the same keys, firmware, roms, updates and mods folders under every storage root."
msgstr "Encore utilise les mêmes dossiers keys, firmware, roms, updates et mods sous chaque racine de stockage."

#. Label of the shortcut that ends the running game.
#: pe/ui/settings.cpp
msgid "END GAME"
msgstr "FERMER LE JEU"

#: settings_store.h
msgid "English (UK)"
msgstr "Anglais (Royaume-Uni)"

#: settings_store.h
msgid "English (US)"
msgstr "Anglais (États-Unis)"

#: pe/ui/library.cpp
msgid "Enlarge cover"
msgstr "Agrandir la jaquette"

#: eden_services.cpp
msgid "Europe"
msgstr "Europe"

#: pe/ui/launcher.cpp, pe/ui/switch_theme.cpp
msgid "Exit Eden Encore"
msgstr "Quitter Eden Encore"

#: pe/ui/launcher.cpp
msgid "Exit Eden Encore?"
msgstr "Quitter Eden Encore ?"

#. Button hint: copy the game's save out to a folder.
#: pe/ui/library.cpp
msgid "Export a copy"
msgstr "Exporter une copie"

#: eden_services.cpp
msgid "Export failed. Check that the storage root can be written."
msgstr "Échec de l'export. Vérifiez que la racine de stockage est accessible en écriture."

#. {0} is a folder.
#: eden_services.cpp, host/fake_services.hpp
msgid "Exported to {0}."
msgstr "Copie exportée vers {0}."

#: Nlib metadata
msgid "Family"
msgstr "Familial"

#: Nlib metadata
msgid "Fighting"
msgstr "Combat"

#. What a mod is made of: files that replace the game's own.
#: eden_services.cpp, host/fake_services.cpp
msgid "Files"
msgstr "Fichiers"

#: pe/ui/settings.cpp
msgid "FILESYSTEM"
msgstr "SYSTÈME DE FICHIERS"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Fill"
msgstr "Remplir"

#: pe/ui/switch_theme.cpp
msgid "Filter"
msgstr "Filtre"

#: pe/ui/library.cpp, pe/ui/settings.cpp
msgid "Final app output size. Choose 1080p for lower memory use, 1440p for balance, or 2160p for maximum output detail."
msgstr "Taille finale de l'image envoyée par l'application. Choisissez 1080p pour réduire l'usage mémoire, 1440p pour un bon équilibre ou 2160p pour un maximum de détails en sortie."

#: pe/ui/settings.cpp
msgid "Fine-tune your experience"
msgstr "Peaufinez votre expérience"

#: pe/ui/browse.cpp
msgid "FIRMWARE"
msgstr "FIRMWARE"

#: eden_services.cpp
msgid "Firmware NCA validation failed (code {0}). Check that firmware and prod.keys are compatible."
msgstr "La validation d'un fichier NCA du firmware a échoué (code {0}). Vérifiez que le firmware et prod.keys sont compatibles."

#: eden_services.cpp, host/fake_services.cpp, pe/ui/switch_theme.cpp
msgid "Firmware ready"
msgstr "Firmware prêt"

#: eden_services.cpp
msgid "Firmware SystemVersion data is missing or unreadable. Install a complete firmware dump."
msgstr "Les données SystemVersion du firmware sont absentes ou illisibles. Installez une copie complète du firmware."

#: pe/ui/settings.cpp
msgid "Fixed Encore folder structure"
msgstr "Structure de dossiers Encore fixe"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Focus glow"
msgstr "Halo de sélection"

#: pe/ui/browse.cpp
msgid "FOLDERS"
msgstr "DOSSIERS"

#. Label: the frames-per-second counter drawn over a game.
#: pe/ui/settings.cpp
msgid "FPS OVERLAY"
msgstr "COMPTEUR DE FPS"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "FPS overlay"
msgstr "Compteur de FPS"

#: settings_store.h
msgid "French"
msgstr "Français"

#: settings_store.h
msgid "French (Canada)"
msgstr "Français (Canada)"

#. The app can read every folder of the console.
#: eden_services.cpp, pe/ui/browse.cpp
msgid "Full filesystem"
msgstr "Tous les dossiers"

#: settings_store.h
msgid "FXAA"
msgstr "FXAA"

#: pe/ui/settings.cpp
msgid "Game audio; PS5 system-menu music is unchanged."
msgstr "Audio des jeux. La musique du menu de la PS5 reste inchangée."

#: pe/ui/settings.cpp
msgid "GAME BACKDROP"
msgstr "JEU FOND D'ÉCRAN"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Game background"
msgstr "Fond du jeu"

#. {0} is the reason, a sentence in English; {1} is a file.
#: eden_services.cpp, host/fake_services.cpp
msgid "Game could not start: {0} Details: {1}"
msgstr "Impossible de lancer le jeu : {0} Détails dans {1}"

#: pe/ui/switch_theme.cpp
msgid "Game files"
msgstr "Fichiers des jeux"

#: pe/ui/library.cpp
msgid "Game library unavailable"
msgstr "Bibliothèque de jeux indisponible"

#: pe/ui/library.cpp
msgid "Game overrides reset to global defaults."
msgstr "Réglages du jeu réinitialisés."

#: pe/ui/settings.cpp
msgid "Game render scale follows the selected profile. Lower it for performance or memory; raise it only when a game has headroom."
msgstr "L'échelle de rendu du jeu suit le profil sélectionné. Réduisez-la pour gagner en performances ou en mémoire ; augmentez-la seulement si le jeu a de la marge."

#: pe/ui/settings.cpp
msgid "GAME RESOLUTION"
msgstr "RÉSOLUTION DU JEU"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Game resolution"
msgstr "Résolution du jeu"

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Game settings"
msgstr "Paramètres du jeu"

#: pe/ui/settings.cpp
msgid "GAME VOLUME"
msgstr "VOLUME DES JEUX"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Game volume"
msgstr "Volume des jeux"

#: pe/ui/settings.cpp
msgid "Game volume, and the sounds of this menu."
msgstr "Volume des jeux et sons de ce menu."

#: pe/ui/browse.cpp
msgid "GAMES"
msgstr "JEUX"

#: pe/ui/home.cpp
msgid "Games and cache"
msgstr "Jeux · Cache"

#: pe/ui/switch_theme.cpp
msgid "Games found"
msgstr "Jeux trouvés"

#: pe/ui/browse.cpp
msgid "Games use this language when they offer it, and their own default otherwise. It applies when a game starts."
msgstr "Les jeux utilisent cette langue lorsqu'ils la proposent, sinon leur langue par défaut. S'applique au lancement d'un jeu."

#: pe/ui/home.cpp
msgid "Games you launch will appear here."
msgstr "Les jeux que vous lancez apparaîtront ici."

#: pe/ui/library.cpp
msgid "GB"
msgstr "Go"

#: settings_store.h
msgid "German"
msgstr "Allemand"

#: pe/ui/browse.cpp
msgid "GETTING STARTED"
msgstr "PREMIERS PAS"

#: pe/ui/launcher.cpp
msgid "GitHub Releases unavailable. You can keep using the launcher."
msgstr "GitHub Releases est indisponible. Vous pouvez continuer à utiliser le launcher."

#: pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Global ({0})"
msgstr "Global ({0})"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Global controller profile: {0}"
msgstr "Profil de manette global : {0}"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Glow intensity"
msgstr "Intensité du halo"

#: pe/ui/settings.cpp
msgid "Graphics backend and how games are scaled to your TV."
msgstr "Moteur de rendu et mise à l'échelle sur votre téléviseur."

#: eden_services.cpp
msgid "Graphics backend initialization failed. Try another backend in Settings; see stderr.log and eden_log.txt for driver details."
msgstr "L'initialisation du moteur de rendu a échoué. Essayez un autre moteur de rendu dans Paramètres. Consultez stderr.log et eden_log.txt pour en savoir plus sur le pilote."

#. Console mode: the console as if held in the hands. Keep it short (about 9 letters).
#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Handheld"
msgstr "Portable"

#: pe/ui/settings.cpp
msgid "Health and storage tools. Cache cleanup never removes saves, settings, keys or games."
msgstr "Outils d'état et de stockage. Le nettoyage du cache ne supprime jamais les sauvegardes, réglages, clés ni jeux."

#: settings_store.h
msgid "High"
msgstr "Haute"

#: pe/ui/settings.cpp
msgid "HIGH CONTRAST"
msgstr "CONTRASTE ÉLEVÉ"

#. A switch: solid dark panels, brighter text.
#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "High contrast"
msgstr "Contraste élevé"

#: pe/ui/launcher.cpp
msgid "Home"
msgstr "Accueil"

#: Nlib metadata
msgid "Horror"
msgstr "Horreur"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Image darkness"
msgstr "Assombrissement de l'image"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Image scaling"
msgstr "Ajustement de l'image"

#. Button hint: copy a save in.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Import"
msgstr "Importer"

#: eden_services.cpp
msgid "Import failed. The current save is unchanged."
msgstr "Échec de l'importation. La sauvegarde actuelle est inchangée."

#: eden_services.cpp
msgid "Imported."
msgstr "Sauvegarde importée."

#: eden_services.cpp, host/fake_services.hpp
msgid "Imported. The save it replaced was backed up."
msgstr "Sauvegarde importée. Une copie de l'ancienne a été conservée."

#. Tag on the language or folder that is in use now.
#: pe/ui/browse.cpp
msgid "IN USE"
msgstr "UTILISÉ"

#: Nlib metadata
msgid "Indie"
msgstr "Indépendant"

#: pe/ui/settings.cpp
msgid "INSTALLED"
msgstr "INSTALLÉE"

#: pe/ui/switch_theme.cpp
msgid "Installed"
msgstr "Installée"

#: pe/ui/browse.cpp
msgid "Internal storage"
msgstr "Stockage interne"

#: pe/ui/browse.cpp
msgid "Internal storage saved. Reopen Encore to use it."
msgstr "Stockage interne enregistré. Rouvrez Encore pour l'utiliser."

#: settings_store.h
msgid "Italian"
msgstr "Italien"

#: eden_services.cpp, pe/ui/library.cpp
msgid "Japan"
msgstr "Japon"

#: settings_store.h
msgid "Japanese"
msgstr "Japonais"

#. Label: the encryption keys file (prod.keys).
#: pe/ui/browse.cpp
msgid "KEYS"
msgstr "CLÉS"

#: eden_services.cpp, host/fake_services.cpp
msgid "Keys and firmware: startup checks passed. Game-specific compatibility is checked at launch."
msgstr "Clés et firmware : vérifications de démarrage réussies. La compatibilité propre à chaque jeu est vérifiée à son lancement."

#: pe/ui/switch_theme.cpp
msgid "Keys found"
msgstr "Clés présentes"

#: pe/ui/switch_theme.cpp
msgid "Keys missing"
msgstr "Clés manquantes"

#: eden_services.cpp, pe/ui/library.cpp
msgid "Korea"
msgstr "Corée"

#: settings_store.h
msgid "Korean"
msgstr "Coréen"

#: pe/ui/browse.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Language"
msgstr "Langue"

#: pe/ui/settings.cpp
msgid "LANGUAGE"
msgstr "LANGUE"

#: pe/ui/browse.cpp
msgid "LANGUAGES"
msgstr "LANGUES"

#: pe/ui/settings.cpp
msgid "LARGER TEXT"
msgstr "TEXTE PLUS GRAND"

#. A switch: the menu's small text is drawn larger.
#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Larger text"
msgstr "Texte plus grand"

#. Caption under the title of the game played last.
#: eden_services.cpp
msgid "Last game opened"
msgstr "Dernier jeu lancé"

#: pe/ui/launcher.cpp
msgid "Later"
msgstr "Plus tard"

#: pe/ui/settings.cpp
msgid "LATEST RELEASE"
msgstr "DERNIÈRE VERSION"

#: pe/ui/switch_theme.cpp
msgid "Latest release"
msgstr "Dernière version publiée"

#: pe/ui/library.cpp
msgid "Launch game"
msgstr "Lancer le jeu"

#: pe/ui/settings.cpp
msgid "LAYOUT"
msgstr "STRUCTURE"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Left stick press"
msgstr "Clic stick gauche"

#: pe/ui/library.cpp
msgid "Left/right: Global, PlayStation or Switch for this game; Cross: edit individual buttons."
msgstr "Gauche/droite : global, PlayStation ou Switch pour ce jeu ; Croix : personnaliser les touches."

#: pe/ui/launcher.cpp
msgid "Library"
msgstr "Bibliothèque"

#: pe/ui/library.cpp
msgid "Loading artwork"
msgstr "Chargement du visuel"

#: pe/ui/launcher.cpp
msgid "Loading game library..."
msgstr "Chargement des jeux..."

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Local image"
msgstr "Image locale"

#: pe/ui/settings.cpp
msgid "LOGO"
msgstr "LOGO"

#: pe/ui/switch_theme.cpp
msgid "Logo"
msgstr "Logo"

#: pe/ui/settings.cpp
msgid "LOGS"
msgstr "JOURNAUX"

#: pe/ui/settings.cpp
msgid "Make the menu easier to see and follow."
msgstr "Rendez le menu plus lisible et plus facile à suivre."

#: pe/ui/switch_theme.cpp
msgid "Manage"
msgstr "Gérer"

#: pe/ui/settings.cpp
msgid "Manual"
msgstr "Manuel"

#: pe/ui/settings.cpp
msgid "Manual check available"
msgstr "Vérification manuelle disponible"

#: pe/ui/home.cpp
msgid "Max. players: {0}"
msgstr "Joueurs max. : {0}"

#: pe/ui/settings.cpp
msgid "MENU SOUNDS"
msgstr "SONS DU MENU"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Menu sounds"
msgstr "Sons du menu"

#: settings_store.h
msgid "Minimum"
msgstr "Minimum"

#: pe/ui/settings.cpp
msgid "Minimum reduces GPU load and may use lower GPU accuracy for speed. Recommended balances quality and stability. High and Ultra raise image quality when the game has headroom."
msgstr "Minimum réduit la charge GPU et peut utiliser une précision GPU plus faible pour gagner en vitesse. Recommandé équilibre qualité et stabilité. Haute et Ultra améliorent la qualité d'image lorsque le jeu a suffisamment de marge."

#: pe/ui/library.cpp
msgid "Minimum, Recommended, High and Ultra apply the title-aware Encore profile. Manual changes become Custom for this game."
msgstr "Minimum, Recommandé, Haute et Ultra appliquent le profil Encore adapté au jeu. Les modifications manuelles passent ce jeu en Personnalisé."

#: eden_services.cpp, host/fake_services.cpp
msgid "Missing or empty keys/prod.keys in {0}."
msgstr "Fichier keys/prod.keys absent ou vide dans {0}."

#. Label on the About screen: the folder that holds games' mods (see 'Mods').
#: pe/ui/browse.cpp
msgid "MODS"
msgstr "MODS"

#. Changes to a game that the player added: patches, replaced files, cheats. Keep the word 'mod' if the language uses it.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Mods"
msgstr "Mods"

#: pe/ui/library.cpp
msgid "Move cover"
msgstr "Déplacer la jaquette"

#: Nlib metadata
msgid "Multiplayer"
msgstr "Multijoueur"

#: Nlib metadata
msgid "Music"
msgstr "Musique"

#: pe/ui/settings.cpp
msgid "MUTE"
msgstr "SOURDINE"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Mute"
msgstr "Sourdine"

#: pe/ui/settings.cpp
msgid "Muted"
msgstr "En sourdine"

#. Button hint: move the highlight.
#: pe/ui/home.cpp
msgid "Navigate"
msgstr "Naviguer"

#. An upscaling filter (nearest neighbour). Keep it short.
#: settings_store.h
msgid "Nearest"
msgstr "Au plus proche"

#: pe/ui/settings.cpp
msgid "Needs attention"
msgstr "À vérifier"

#: pe/ui/launcher.cpp
msgid "New Eden Encore release"
msgstr "Nouvelle version d'Eden Encore"

#: pe/ui/launcher.cpp
msgid "New Eden Encore release {0}; installation is not available yet."
msgstr "Nouvelle version d'Eden Encore {0} ; installation indisponible pour le moment."

#: pe/ui/launcher.cpp
msgid "New manual check queued after current request."
msgstr "Nouvelle vérification manuelle programmée après la recherche en cours."

#. {0} is the folder used the next time the app starts.
#: pe/ui/browse.cpp
msgid "Next launch: {0}"
msgstr "Au redémarrage : {0}"

#: pe/ui/launcher.cpp
msgid "No eligible official stable release could be verified."
msgstr "Aucune version stable officielle admissible n'a pu être vérifiée."

#: pe/ui/browse.cpp
msgid "No firmware folder"
msgstr "Aucun dossier firmware"

#: eden_services.cpp
msgid "No firmware NCAs found in {0}."
msgstr "Aucun fichier NCA de firmware trouvé dans {0}."

#: pe/ui/browse.cpp
msgid "No folders here."
msgstr "Aucun dossier ici."

#: pe/ui/switch_theme.cpp
msgid "No games found"
msgstr "Aucun jeu trouvé"

#. Shown on the Mods row of a game that has none.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "No mods"
msgstr "Aucun mod"

#. {0} is a folder; roms/ is a folder name (unchanged).
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "No mods for this game yet. Copy each mod's folder to {0}, next to roms/."
msgstr "Aucun mod pour ce jeu pour l'instant. Copiez le dossier de chaque mod dans {0}, à côté de roms/."

#: pe/ui/multiplayer.cpp
msgid "No public rooms to display."
msgstr "Aucun salon public à afficher."

#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "No ROM files found."
msgstr "Aucun fichier ROM trouvé."

#: pe/ui/browse.cpp
msgid "No roms folder"
msgstr "Aucun dossier roms"

#: pe/ui/library.cpp
msgid "No screenshots available"
msgstr "Aucune capture disponible"

#: pe/ui/settings.cpp
msgid "No wallpaper. Copy PNG, JPEG or TGA to the app wallpapers folder."
msgstr "Aucun fond d'écran. Copiez une image PNG, JPEG ou TGA dans le dossier wallpapers de l'application."

#. Neither a game update nor DLC is installed.
#: pe/ui/library.cpp
msgid "No DLC/updates"
msgstr "Aucun DLC/MAJ"

#. Generic None option.
#: pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp, settings_store.h
msgid "None"
msgstr "Aucune"

#: pe/ui/settings.cpp
msgid "Not checked"
msgstr "Non vérifié"

#. Short status at the right of the Save data row.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Nothing to import"
msgstr "Rien à importer"

#. A setting that is switched off.
#: pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Off"
msgstr "Désactivé"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Official logo"
msgstr "Logo officiel"

#. A setting that is switched on.
#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "On"
msgstr "Activé"

#: pe/ui/settings.cpp
msgid "One root for keys, firmware, games, updates, mods and transfers."
msgstr "Une seule racine pour les clés, le firmware, les jeux, les mises à jour, les mods et les transferts."

#: Nlib metadata
msgid "Online"
msgstr "En ligne"

#. Short tag on a folder row.
#: pe/ui/browse.cpp
msgid "OPEN"
msgstr "OUVRIR"

#. Button hint: open the highlighted folder.
#: pe/ui/browse.cpp, pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Open"
msgstr "Ouvrir"

#: pe/ui/switch_theme.cpp
msgid "Open folders"
msgstr "Ouvrir les dossiers"

#: pe/ui/home.cpp
msgid "Open library"
msgstr "Ouvrir la bibliothèque"

#: pe/ui/home.cpp
msgid "Open quick settings"
msgstr "Ouvrir les paramètres rapides"

#: pe/ui/home.cpp
msgid "Open settings"
msgstr "Ouvrir les paramètres"

#: pe/ui/home.cpp
msgid "Open storage"
msgstr "Ouvrir le stockage"

#: pe/ui/library.cpp
msgid "Open the per-game DualSense mapping. Global uses Settings > Controls; Custom overrides it only for this game."
msgstr "Ouvre l’attribution DualSense propre à ce jeu. Global utilise Réglages > Contrôles ; Personnalisé la remplace uniquement pour ce jeu."

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Options"
msgstr "Options"

#: Nlib metadata
msgid "Other"
msgstr "Autre"

#. Button hint: jump a page of the list (L1 / R1).
#: pe/ui/browse.cpp
msgid "Page"
msgstr "Page"

#: pe/ui/browse.cpp
msgid "Parent folder"
msgstr "Dossier parent"

#: Nlib metadata
msgid "Party"
msgstr "Jeu de groupe"

#: pe/ui/multiplayer.cpp
msgid "Password"
msgstr "Mot de passe"

#. What a mod is made of: a change to the game's program (not a game update).
#: eden_services.cpp, host/fake_services.cpp
msgid "Patch"
msgstr "Patch"

#: Nlib metadata
msgid "Platformer"
msgstr "Plateforme"

#: pe/ui/home.cpp
msgid "Play"
msgstr "Jouer"

#: pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "PlayStation"
msgstr "PlayStation"

#: settings_store.h
msgid "Polish"
msgstr "Polonais"

#: settings_store.h
msgid "Portuguese"
msgstr "Portugais"

#: settings_store.h
msgid "Portuguese (Brazil)"
msgstr "Portugais (Brésil)"

#. Eden is the emulator's name (unchanged).
#: pe/ui/browse.cpp, pe/ui/switch_theme.cpp
msgid "Powered by Eden"
msgstr "Propulsé par Eden"

#: pe/ui/settings.cpp
msgid "Preset"
msgstr "Préréglage"

#. Asked before a save is imported over the one in use.
#: pe/ui/library.cpp
msgid "Press again to replace this game's save. The current one is backed up."
msgstr "Appuyez à nouveau pour remplacer la sauvegarde de ce jeu. Une copie de l'actuelle est conservée."

#: eden_services.cpp
msgid "prod.keys could not supply an NCA header key. Replace it with a valid key dump."
msgstr "Le fichier prod.keys n'a pas fourni de clé d'en-tête NCA. Remplacez-le par un fichier de clés valide."

#: pe/ui/browse.cpp
msgid "prod.keys found"
msgstr "prod.keys trouvé"

#: pe/ui/browse.cpp
msgid "prod.keys missing"
msgstr "prod.keys introuvable"

#: pe/ui/browse.cpp
msgid "PROJECT CREDITS"
msgstr "CRÉDITS DU PROJET"

#. Shown on the home screen after the app crashed and started again; {0} is a file.
#: eden_services.cpp, host/fake_services.cpp
msgid "ProsperoEden stopped because of an error. A report was saved to {0}."
msgstr "ProsperoEden s'est arrêté à cause d'une erreur. Un rapport a été enregistré dans {0}."

#: pe/ui/browse.cpp
msgid "PS5 13.60 FORK"
msgstr "FORK PS5 13.60"

#. Why a game did not start.
#: eden_services.cpp
msgid "PS5 controller initialization failed"
msgstr "L'initialisation de la manette PS5 a échoué."

#: pe/ui/multiplayer.cpp
msgid "Public room service unavailable."
msgstr "Service des salons publics indisponible."

#: Nlib metadata
msgid "Puzzle"
msgstr "Réflexion"

#: pe/ui/home.cpp
msgid "QUICK SETTINGS"
msgstr "PARAMÈTRES RAPIDES"

#: pe/ui/home.cpp
msgid "Quick settings"
msgstr "Paramètres rapides"

#: pe/ui/home.cpp
msgid "Quit"
msgstr "Quitter"

#: Nlib metadata
msgid "Racing"
msgstr "Course"

#: pe/ui/settings.cpp
msgid "Ready"
msgstr "Prête"

#: pe/ui/launcher.cpp
msgid "Recent"
msgstr "Récents"

#: pe/ui/home.cpp
msgid "RECENTLY PLAYED"
msgstr "JOUÉS RÉCEMMENT"

#: settings_store.h
msgid "Recommended"
msgstr "Recommandé"

#: pe/ui/settings.cpp
msgid "Recommended defaults restored."
msgstr "Réglages recommandés restaurés."

#: pe/ui/settings.cpp
msgid "REDUCE MOTION"
msgstr "RÉDUIRE LES ANIMATIONS"

#. A switch: no drifting, sliding or zooming on screen.
#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Reduce motion"
msgstr "Réduire les animations"

#: pe/ui/multiplayer.cpp
msgid "Refresh"
msgstr "Actualiser"

#. Setting: how many times a second the TV picture is refreshed while a game runs (60 or 120 Hz).
#: pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Refresh rate"
msgstr "Fréquence écran"

#. Label: see 'Refresh rate'.
#: pe/ui/settings.cpp
msgid "REFRESH RATE"
msgstr "FRÉQUENCE ÉCRAN"

#: pe/ui/browse.cpp, pe/ui/settings.cpp
msgid "REGION"
msgstr "RÉGION"

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Renderer"
msgstr "Moteur de rendu"

#: pe/ui/settings.cpp
msgid "RENDERER"
msgstr "MOTEUR DE RENDU"

#: pe/ui/mapping.cpp
msgid "Reset"
msgstr "Réinitialiser"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Reset appearance"
msgstr "Réinitialiser l'apparence"

#: pe/ui/launcher.cpp
msgid "Reset controller mapping?"
msgstr "Réinitialiser les touches ?"

#: pe/ui/library.cpp
msgid "Reset overrides"
msgstr "Réinitialiser"

#: pe/ui/launcher.cpp
msgid "Reset this game's custom settings?"
msgstr "Réinitialiser les paramètres personnalisés de ce jeu ?"

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Resolution"
msgstr "Résolution"

#: pe/ui/library.cpp
msgid "Resolution follows the selected title-aware profile. Lower it for performance or memory; raise it only when the title has headroom."
msgstr "La résolution suit le profil Encore adapté au jeu. Réduisez-la pour gagner en performances ou en mémoire ; augmentez-la seulement si le jeu a de la marge."

#: pe/ui/launcher.cpp
msgid "Restore default settings?"
msgstr "Rétablir les paramètres par défaut ?"

#: pe/ui/settings.cpp
msgid "Restore defaults"
msgstr "Restaurer les réglages"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Restore Neon"
msgstr "Rétablir Neon"

#: Nlib metadata
msgid "Rhythm"
msgstr "Rythme"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Right stick press"
msgstr "Clic stick droit"

#: Nlib metadata
msgid "Role-Playing"
msgstr "Jeu de rôle"

#: pe/ui/launcher.cpp, pe/ui/library.cpp
msgid "ROM missing from the game files folder"
msgstr "ROM absente du dossier des fichiers de jeu"

#: eden_services.cpp
msgid "ROM missing from the storage root"
msgstr "ROM absente de la racine de stockage"

#: pe/ui/settings.cpp
msgid "ROOT"
msgstr "RACINE"

#: Nlib metadata
msgid "RPG"
msgstr "JDR"

#: pe/ui/settings.cpp
msgid "Runtime health, storage and recovery tools."
msgstr "État d'exécution, stockage et outils de récupération."

#: settings_store.h
msgid "Russian"
msgstr "Russe"

#. Short status at the right of the Save data row. Ryujinx is a name (unchanged).
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Ryujinx save found"
msgstr "Sauvegarde Ryujinx trouvée"

#: pe/ui/library.cpp
msgid "Safe launch"
msgstr "Lancement sûr"

#: pe/ui/library.cpp
msgid "Safe launch: OpenGL, Handheld, 1x, 60 Hz, 1080p and mods off for this launch only."
msgstr "Démarrage sûr : OpenGL, mode portable, 1x, 60 Hz, 1080p et mods désactivés uniquement pour ce lancement."

#: Nlib metadata
msgid "Sandbox"
msgstr "Bac à sable"

#: eden_services.cpp, pe/ui/browse.cpp
msgid "Sandbox only"
msgstr "Sandbox uniquement"

#. The app can read only its own folder; {0} is a number.
#: pe/ui/browse.cpp
msgid "Sandboxed (code {0}): app folder only"
msgstr "Limité au dossier de l'application (code {0})"

#. A row of a game's settings: the game's saved progress, which can be copied in or out.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Save data"
msgstr "Données sauvegardées"

#. Short status at the right of the Save data row: a folder with a save to import.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Save folder found"
msgstr "Dossier de sauvegarde trouvé"

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/mapping.cpp
msgid "Saved for this game. Applies on next launch."
msgstr "Enregistré pour ce jeu. S'applique au prochain lancement."

#. Shown after choosing 120 Hz.
#: pe/ui/library.cpp, pe/ui/settings.cpp
msgid "Saved. A display that cannot show 120 Hz stays at 60 Hz."
msgstr "Enregistré. Un écran incompatible avec le 120 Hz reste à 60 Hz."

#: pe/ui/launcher.cpp
msgid "Saved. Applies when a game starts."
msgstr "Enregistré. S'applique au lancement d'un jeu."

#: pe/ui/settings.cpp
msgid "Scanning local wallpapers..."
msgstr "Recherche des fonds d'écran locaux..."

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Search GitHub Releases"
msgstr "Rechercher sur GitHub Releases"

#. Button hint: choose the highlighted item (not the Select button).
#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Select"
msgstr "Sélectionner"

#: pe/ui/library.cpp
msgid "Select a game"
msgstr "Sélectionnez un jeu"

#: pe/ui/library.cpp
msgid "Select a game to begin"
msgstr "Sélectionnez un jeu pour commencer"

#: pe/ui/switch_theme.cpp
msgid "Select a settings category"
msgstr "Choisir une catégorie de paramètres"

#. Heading: the language highlighted in the list.
#: pe/ui/browse.cpp
msgid "SELECTED"
msgstr "SÉLECTION"

#: pe/ui/home.cpp
msgid "SELECTED GAME"
msgstr "JEU SÉLECTIONNÉ"

#. Why a game did not start (the file is gone).
#: eden_services.cpp
msgid "Selected ROM is no longer available"
msgstr "La ROM sélectionnée n'est plus disponible."

#: pe/ui/home.cpp, pe/ui/launcher.cpp, pe/ui/settings.cpp
msgid "Settings"
msgstr "Paramètres"

#. Label: whether keys and firmware are in place.
#: pe/ui/settings.cpp
msgid "SETUP"
msgstr "CONFIGURATION"

#: eden_services.cpp, host/fake_services.cpp, pe/ui/switch_theme.cpp
msgid "Setup required"
msgstr "Configuration nécessaire"

#: host/fake_services.cpp
msgid "Setup required: {0} Open Settings, Game files to choose the folder that holds your keys, firmware and roms folders (or add the files to {1}), then reopen ProsperoEden."
msgstr "Configuration nécessaire : {0} Dans Paramètres, ouvrez Fichiers de jeu pour choisir le dossier contenant vos dossiers keys, firmware et roms (ou ajoutez les fichiers dans {1}), puis rouvrez ProsperoEden."

#: eden_services.cpp
msgid "Setup required: {0} Open Settings, Storage to choose the root that holds the standard keys, firmware and roms folders (or add the files to {1}), then reopen Encore."
msgstr "Configuration requise : {0} Ouvrez Réglages, Stockage pour choisir la racine contenant les dossiers standard keys, firmware et roms (ou ajoutez les fichiers dans {1}), puis rouvrez Encore."

#: eden_services.cpp
msgid "Setup validation failed. Check that firmware and key files are readable and valid."
msgstr "La validation de la configuration a échoué. Vérifiez que les fichiers du firmware et des clés sont lisibles et valides."

#: Nlib metadata
msgid "Shooter"
msgstr "Tir"

#: pe/ui/settings.cpp
msgid "Shows live FPS while playing. Off is cleaner for normal use; Touchpad + R1 toggles it at any time."
msgstr "Affiche les FPS en direct pendant le jeu. Désactivé est plus propre au quotidien ; Touchpad + R1 permet de le basculer à tout moment."

#: Nlib metadata
msgid "Simulation"
msgstr "Simulation"

#: Nlib metadata
msgid "Single Player"
msgstr "Solo"

#: pe/ui/switch_theme.cpp
msgid "Software options: Triangle"
msgstr "Options des logiciels : Triangle"

#: pe/ui/settings.cpp
msgid "Solid panels, brighter text and an outlined highlight."
msgstr "Panneaux opaques, texte plus lumineux et surbrillance avec contour."

#: eden_services.cpp
msgid "Some cache files could not be removed."
msgstr "Certains fichiers de cache n'ont pas pu être supprimés."

#: settings_store.h
msgid "Spanish"
msgstr "Espagnol"

#: settings_store.h
msgid "Spanish (Latin America)"
msgstr "Espagnol (Amérique latine)"

#: Nlib metadata
msgid "Sports"
msgstr "Sport"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Square"
msgstr "Carré"

#. The app creates its user the first time a game runs.
#: eden_services.cpp
msgid "Start any game once before importing a save."
msgstr "Lancez n'importe quel jeu une fois avant d'importer une sauvegarde."

#. Shown over a game's cover while it starts.
#: pe/ui/launcher.cpp
msgid "STARTING"
msgstr "LANCEMENT"

#: pe/ui/settings.cpp
msgid "STATUS"
msgstr "ÉTAT"

#: pe/ui/switch_theme.cpp
msgid "Status"
msgstr "État"

#: pe/ui/settings.cpp
msgid "STICK DEADZONE"
msgstr "ZONE MORTE DES STICKS"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Stick deadzone"
msgstr "Zone morte des sticks"

#: pe/ui/settings.cpp
msgid "Stops the background drifting and the screens sliding, here and on the loading screen."
msgstr "Arrête le mouvement de l'arrière-plan et le glissement des écrans, ici et sur l'écran de chargement."

#: pe/ui/browse.cpp, pe/ui/home.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Storage"
msgstr "Stockage"

#: pe/ui/settings.cpp
msgid "STORAGE"
msgstr "STOCKAGE"

#: pe/ui/home.cpp
msgid "Storage not configured"
msgstr "Stockage non configuré"

#: pe/ui/home.cpp
msgid "Storage ready"
msgstr "Stockage configuré"

#: pe/ui/browse.cpp
msgid "Storage root saved. Reopen Encore to use it."
msgstr "Racine de stockage enregistrée. Rouvrez Encore pour l'utiliser."

#: Nlib metadata
msgid "Strategy"
msgstr "Stratégie"

#: pe/ui/browse.cpp
msgid "Supply your own files"
msgstr "Fournissez vos propres fichiers"

#: pe/ui/library.cpp, pe/ui/mapping.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Switch"
msgstr "Switch"

#: pe/ui/home.cpp
msgid "Switch card"
msgstr "Changer de carte"

#: pe/ui/home.cpp
msgid "System"
msgstr "Système"

#: pe/ui/switch_theme.cpp
msgid "System Settings"
msgstr "Paramètres de la console"

#: eden_services.cpp, pe/ui/library.cpp
msgid "Taiwan"
msgstr "Taïwan"

#: settings_store.h
msgid "Thai"
msgstr "Thaï"

#. Heading of the acknowledgements.
#: pe/ui/browse.cpp
msgid "THANKS"
msgstr "REMERCIEMENTS"

#: pe/ui/browse.cpp, pe/ui/switch_theme.cpp
msgid "Thanks to the whole PS5 homebrew community and to every developer whose drivers, tools and libraries make Eden Encore possible."
msgstr "Merci à toute la communauté homebrew PS5 et à chaque développeur dont les pilotes, outils et bibliothèques rendent Eden Encore possible."

#: eden_services.cpp
msgid "The game could not allocate PS5 memory. Close Eden Encore completely before retrying to release memory retained between games."
msgstr "Le jeu n'a pas pu allouer de mémoire sur la PS5. Fermez complètement Eden Encore avant de réessayer pour libérer la mémoire conservée entre les jeux."

#. Why a game stopped. 'Settings, Video' is the menu path; 'the game's own settings' is the Game settings dialog of the Library.
#: eden_services.cpp
msgid "The game ran out of graphics memory. Lower the resolution in Settings, Video (or in the game's own settings) and start it again."
msgstr "Le jeu a manqué de mémoire graphique. Réduisez la résolution dans Paramètres, Vidéo (ou dans Paramètres du jeu), puis relancez-le."

#: pe/ui/settings.cpp
msgid "The language games use when they offer it."
msgstr "La langue utilisée par les jeux qui la proposent."

#: pe/ui/settings.cpp
msgid "THEME"
msgstr "THÈME"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Theme"
msgstr "Thème"

#: pe/ui/browse.cpp
msgid "This folder cannot be opened."
msgstr "Impossible d'ouvrir ce dossier."

#: eden_services.cpp
msgid "This game has no save to export yet."
msgstr "Ce jeu n'a pas encore de sauvegarde à exporter."

#: pe/ui/library.cpp
msgid "This game's settings cannot be saved (no title ID)."
msgstr "Impossible d'enregistrer les paramètres du jeu (aucun ID de titre)."

#: pe/ui/browse.cpp
msgid "THIS ROOT"
msgstr "CETTE RACINE"

#. ryujinx/, save-import/ and roms/ are folder names (unchanged); {0} is the game's ID.
#: eden_services.cpp
msgid "To import, copy a Ryujinx folder to ryujinx/ or a save to save-import/{0}/, next to roms/."
msgstr "Pour importer, copiez un dossier Ryujinx dans ryujinx/ ou une sauvegarde dans save-import/{0}/, à côté de roms/."

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Touchpad"
msgstr "Pavé tactile"

#: pe/ui/mapping.cpp, pe/ui/switch_theme.cpp
msgid "Triangle"
msgstr "Triangle"

#. Button hint: switch the highlighted mod on or off.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "Turn on or off"
msgstr "Activer ou désactiver"

#: pe/ui/settings.cpp
msgid "Turns DualSense vibration on or off for games."
msgstr "Active ou désactive les vibrations DualSense dans les jeux."

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "TV output"
msgstr "Sortie TV"

#: pe/ui/settings.cpp
msgid "TV OUTPUT"
msgstr "SORTIE TV"

#: settings_store.h
msgid "Ultra"
msgstr "Ultra"

#: pe/ui/home.cpp, pe/ui/library.cpp
msgid "Unknown"
msgstr "Inconnu"

#. Short tag on the 'Parent folder' row.
#: pe/ui/browse.cpp
msgid "UP"
msgstr "REMONTER"

#. A game update; {0} is its version, for example 1.2.0.
#: eden_services.cpp, host/fake_services.cpp
msgid "Update {0}"
msgstr "Mise à jour {0}"

#: pe/ui/settings.cpp
msgid "Updates for the Eden Encore app, not games or firmware."
msgstr "Mises à jour de l'application Eden Encore, pas des jeux ni du firmware."

#: pe/ui/browse.cpp
msgid "UPDATES, DLC"
msgstr "MISES À JOUR, DLC"

#: eden_services.cpp, pe/ui/launcher.cpp, pe/ui/library.cpp
msgid "USA"
msgstr "USA"

#: pe/ui/browse.cpp
msgid "Use extracted firmware NCA files. Choose the root in Settings, Storage; restart the app after changing it."
msgstr "Utilisez des fichiers NCA de firmware extraits. Choisissez la racine dans Réglages, Stockage ; redémarrez l'application après l'avoir modifiée."

#: pe/ui/browse.cpp
msgid "Use this root"
msgstr "Utiliser cette racine"

#: pe/ui/settings.cpp
msgid "VIBRATION"
msgstr "VIBRATION"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Vibration"
msgstr "Vibration"

#: pe/ui/settings.cpp
msgid "VIBRATION STRENGTH"
msgstr "INTENSITÉ DES VIBRATIONS"

#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Vibration strength"
msgstr "Intensité des vibrations"

#: pe/ui/home.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Video"
msgstr "Vidéo"

#: pe/ui/settings.cpp
msgid "VIDEO"
msgstr "VIDÉO"

#: pe/ui/home.cpp, pe/ui/library.cpp, pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Video preset"
msgstr "Profil vidéo"

#: pe/ui/settings.cpp
msgid "VIDEO PRESET"
msgstr "PRÉRÉGLAGE VIDÉO"

#: Nlib metadata
msgid "Visual Novel"
msgstr "Roman visuel"

#: pe/ui/switch_theme.cpp
msgid "Volume"
msgstr "Volume"

#. Vulkan is a name (unchanged).
#: pe/ui/settings.cpp, pe/ui/switch_theme.cpp
msgid "Vulkan (recommended)"
msgstr "Vulkan (recommandé)"

#: pe/ui/settings.cpp
msgid "Vulkan is recommended on PS5. Use OpenGL only as a fallback for a game with Vulkan issues."
msgstr "Vulkan est recommandé sur PS5. Utilisez OpenGL seulement en solution de repli pour un jeu ayant des problèmes avec Vulkan."

#: pe/ui/library.cpp
msgid "Vulkan is recommended on PS5. Use OpenGL only as a fallback for a title with Vulkan issues."
msgstr "Vulkan est recommandé sur PS5. Utilisez OpenGL seulement en solution de repli pour un jeu ayant des problèmes avec Vulkan."

#: pe/ui/library.cpp
msgid "Your games"
msgstr "Vos jeux"

#. Headline when no game has been played yet.
#: pe/ui/home.cpp
msgid "Your next adventure"
msgstr "Votre prochaine aventure"

#: pe/ui/library.cpp
msgid "Zoom in"
msgstr "Zoom avant"

#: pe/ui/library.cpp
msgid "Zoom out"
msgstr "Zoom arrière"

#. {0} is how many DLC (add-on content) a game has installed.
#: eden_services.cpp, host/fake_services.cpp
msgid "{0} DLC"
msgstr "{0} DLC"

#. Exactly one game. In a language with more than two plural forms, word it so that it reads well with any number (Games: {0}).
#: pe/ui/browse.cpp
msgid "{0} game"
msgstr "{0} jeu"

#. Exactly one game. See '{0} game'.
#: eden_services.cpp
msgid "{0} game installed"
msgstr "{0} jeu installé"

#. Any number of games other than one (also 0). See '{0} game'.
#: pe/ui/browse.cpp
msgid "{0} games"
msgstr "{0} jeux"

#. Any number of games other than one. See '{0} game'.
#: eden_services.cpp, host/fake_services.cpp
msgid "{0} games installed"
msgstr "{0} jeux installés"

#. {0} is 60 or 120 (hertz).
#: pe/ui/library.cpp
msgid "{0} Hz"
msgstr "{0} Hz"

#. Exactly one mod, in the list of what a game comes with (Update 1.2.0, 2 DLC, 1 mod). See '{0} game'.
#: pe/ui/library.cpp
msgid "{0} mod"
msgstr "{0} mod"

#. Any number of mods other than one. See '{0} mod'.
#: pe/ui/library.cpp
msgid "{0} mods"
msgstr "{0} mods"

#. Exactly one file. See '{0} game'.
#: pe/ui/browse.cpp
msgid "{0} NCA file"
msgstr "{0} fichier NCA"

#. Any number of files other than one. See '{0} game'.
#: pe/ui/browse.cpp
msgid "{0} NCA files"
msgstr "{0} fichiers NCA"

#. {0} is a language name. Shown beside a game that lacks that language.
#: eden_services.cpp, host/fake_services.cpp
msgid "{0} not available"
msgstr "{0} indisponible"

#. Position in a list: 3 OF 12.
#: pe/ui/widgets.cpp
msgid "{0} OF {1}"
msgstr "{0} SUR {1}"

#. In the same list, when some of the game's mods are switched off: 1 of 2 mods on. Keep it short.
#: pe/ui/library.cpp
msgid "{0} of {1} mods on"
msgstr "{0} sur {1} mods activés"

#. How many of a game's mods are switched on: 2 of 3 on.
#: pe/ui/library.cpp, pe/ui/switch_theme.cpp
msgid "{0} of {1} on"
msgstr "{0} sur {1} activés"

#. A percentage (a volume): write it as the language does, for example with a space before the sign.
#: pe/ui/library.cpp, pe/ui/settings.cpp
msgid "{0}%"
msgstr "{0} %"

#. {0} is a folder; NSP and XCI are file types.
#: pe/ui/browse.cpp
msgid "{0}/ (NSP or XCI)"
msgstr "{0}/ (NSP ou XCI)"

#. {0} is the mods folder; inside it each game has a folder named after its ID (16 letters and digits).
#: pe/ui/browse.cpp
msgid "{0}/ (one folder per game ID)"
msgstr "{0}/ (un dossier par ID de titre)"

#: pe/ui/multiplayer.cpp
msgid "Public rooms"
msgstr "Salons publics"

#: pe/ui/multiplayer.cpp
msgid "Connecting to room..."
msgstr "Connexion au salon..."

#: pe/ui/multiplayer.cpp
msgid "Connected to room"
msgstr "Connecté au salon"

#: pe/ui/multiplayer.cpp
msgid "Choose a room to join or host a LAN room."
msgstr "Rejoignez un salon ou hébergez un salon LAN."

#: pe/ui/multiplayer.cpp
msgid "Room not available."
msgstr "Salon indisponible."

#: pe/ui/multiplayer.cpp
msgid "Join"
msgstr "Rejoindre"

#: pe/ui/multiplayer.cpp
msgid "Host / Leave"
msgstr "Héberger / Quitter"

#: pe/ui/launcher.cpp
msgid "Install"
msgstr "Installer"

#: pe/ui/launcher.cpp
msgid "Install the verified update? Eden Encore will close afterward."
msgstr "Installer la mise à jour vérifiée ? Eden Encore se fermera ensuite."

#: pe/ui/launcher.cpp
msgid "Downloading and verifying the PS5 update..."
msgstr "Téléchargement et vérification de la mise à jour PS5..."

#: pe/ui/launcher.cpp
msgid "Updates unavailable on this host."
msgstr "Mises à jour indisponibles sur cet appareil."

msgid "Frame generation can smooth the display without speeding up the game. Lossless Scaling needs your own DLL."
msgstr "La génération d’images peut améliorer la fluidité d’affichage sans accélérer le jeu. Lossless Scaling nécessite votre propre fichier DLL."

#: pe/ui/library.cpp, pe/ui/settings.cpp
msgid "Lossless.dll missing or invalid. Place your own file in /data/prosperoeden/user/lossless/Lossless.dll."
msgstr "Lossless.dll manquant ou invalide. Placez votre fichier dans /data/prosperoeden/user/lossless/Lossless.dll."

#: pe/ui/library.cpp, pe/ui/settings.cpp
msgid "DLSS-NR: nvngx_dlssnr.dll missing or invalid. Place your own file in /data/prosperoeden/user/dlssnr/nvngx_dlssnr.dll."
msgstr "DLSS-NR : fichier nvngx_dlssnr.dll absent ou invalide. Placez votre fichier dans /data/prosperoeden/user/dlssnr/nvngx_dlssnr.dll."

#: R10 graphics UX
msgid "AMD FSR 1: EASU enlarges the picture; RCAS adds sharpness. Most useful below the TV output resolution."
msgstr "AMD FSR 1 : EASU agrandit l'image ; RCAS ajoute de la netteté. Très utile en dessous de la résolution de sortie TV."

#: R10 graphics UX
msgid "Automatic"
msgstr "Automatique"

#: R10 graphics UX
msgid "Bilinear: fast and soft. Best when the game already renders near the TV resolution."
msgstr "Bilinéaire : rapide et doux. Idéal lorsque le rendu du jeu est déjà proche de la résolution du téléviseur."

#: R10 graphics UX
msgid "Choose a setting; its effect is explained below."
msgstr "Choisissez un paramètre ; son effet est expliqué ci-dessous."

#: R10 graphics UX
msgid "FXAA: lightweight edge smoothing in one pass. It can slightly soften text and fine details."
msgstr "FXAA : lissage léger des bords en un seul passage. Il peut adoucir légèrement le texte et les détails fins."

#: R10 graphics UX
msgid "Game default"
msgstr "Jeu par défaut"

#: R10 graphics UX
msgid "Nearest: keeps hard pixel edges, with visible stair-steps. Best for pixel art, not most 3D games."
msgstr "Le plus proche : conserve les bords des pixels durs, avec des marches d'escalier visibles. Idéal pour le pixel art, pas pour la plupart des jeux 3D."

#: R10 graphics UX
msgid "Off: no edge smoothing. Fastest, but diagonal lines may look jagged."
msgstr "Désactivé : pas de lissage des bords. Le plus rapide, mais les lignes diagonales peuvent paraître irrégulières."

#: R10 graphics UX
msgid "Only AMD FSR 1 uses this percentage. Start at 50%. Increase gently for detail; reduce if edges shimmer or show halos."
msgstr "Seul AMD FSR 1 utilise ce pourcentage. Commencez à 50 %. Augmentez doucement pour plus de détails ; réduire si les bords scintillent ou présentent des halos."

#: R10 graphics UX
msgid "SMAA Ultra"
msgstr "SMAA Ultra"

#: R10 graphics UX
msgid "SMAA Ultra: high-quality multi-pass edge smoothing. Clearer contours but more GPU work than FXAA."
msgstr "SMAA Ultra : lissage des bords multi-passes de haute qualité. Des contours plus clairs mais plus de travail GPU que FXAA."

#: R10 graphics UX
msgid "TEXTURE FILTERING"
msgstr "FILTRAGE DES TEXTURES"

#: R10 graphics UX
msgid "Texture filtering"
msgstr "Filtrage des textures"

#: R10 graphics UX
msgid "Texture filtering keeps distant ground and surfaces clearer at an angle; higher anisotropy uses more GPU bandwidth."
msgstr "Le filtrage des textures maintient les sols et les surfaces éloignés plus clairs selon un angle ; une anisotropie plus élevée utilise plus de bande passante GPU."

#: R10 graphics UX
msgid "UPSCALING"
msgstr "AMÉLIORATION"

#: R10 graphics UX
msgid "Upscaling"
msgstr "Mise à l'échelle"

#: R10 video menu
msgid "FSR 1"
msgstr "FSR 1"

#: R10 video menu
msgid "Frame generation needs Vulkan. Select Vulkan to enable this option."
msgstr "La génération de trames nécessite Vulkan. Sélectionnez Vulkan pour activer cette option."

#: R10 video menu
msgid "This option needs Vulkan. OpenGL cannot generate extra frames; changing it would have no effect."
msgstr "Cette option nécessite Vulkan. OpenGL ne peut pas générer de trames supplémentaires ; le changer n'aurait aucun effet."
#: R24 FXAA Quality
msgid "FXAA+"
msgstr "FXAA+"

#: R24 FXAA Quality
msgid "FXAA+ requires Vulkan. Choose Vulkan or another anti-aliasing method."
msgstr "FXAA+ nécessite Vulkan. Choisis Vulkan ou un autre anticrénelage."

#: R24 FXAA Quality
msgid "FXAA+: extended edge search. Can smooth more jagged edges but may soften textures. Compare with SMAA Ultra."
msgstr "FXAA+ : recherche étendue des contours. Lisse davantage certains escaliers, mais peut adoucir les textures. Compare avec SMAA Ultra."

#: R10 graphics UX
msgid "Inactive: this upscale method does not support the sharpness slider. Use FSR 1 or SGSR with Vulkan."
msgstr "Inactif : cette méthode haut de gamme ne prend pas en charge le curseur de netteté. Utilisez FSR 1 ou SGSR avec Vulkan."

#: R10 graphics UX
msgid "Lanczos"
msgstr "Lanczos"

#: R10 graphics UX
msgid "Lanczos: sharp reconstruction of a scaled image. Fine detail may look clearer, but edges can form bright halos."
msgstr "Lanczos : reconstruction nette d'une image mise à l'échelle. Les détails fins peuvent paraître plus clairs, mais les bords peuvent former des halos lumineux."

#: R10 graphics UX
msgid "SGSR"
msgstr "SGSR"

#: R10 graphics UX
msgid "SGSR Edge"
msgstr "SGSR Edge"

#: R10 graphics UX
msgid "SGSR Edge: edge-directed Qualcomm upscale with a different Vulkan shader. Compare fine detail and halos."
msgstr "SGSR Edge : mise à niveau Qualcomm orientée vers les bords avec un shader Vulkan différent. Comparez les détails fins et les halos."

#: R10 graphics UX
msgid "SGSR edge sharpness: 0% disables extra edge intensity, 50% is balanced, 100% is strongest. Reduce halos if needed."
msgstr "Netteté des bords SGSR : 0 % désactive l'intensité supplémentaire des bords, 50 % est équilibré, 100 % est le plus fort. Réduisez les halos si nécessaire."

#: R10 graphics UX
msgid "SGSR: Qualcomm spatial upscale using a separate Vulkan shader. Try it when FSR 1 looks soft."
msgstr "SGSR : mise à l'échelle spatiale Qualcomm à l'aide d'un shader Vulkan séparé. Essayez-le lorsque FSR 1 semble mou."

#: R10 graphics UX
msgid "Sharpness"
msgstr "Netteté"

#: R07 SGSR graphics
msgid "Bicubic: sharper than bilinear, but may create bright edges. The sharpness slider does not apply."
msgstr "Bicubique : plus net que le bilinéaire, mais peut créer des halos. Le réglage de netteté n'a aucun effet ici."

#: R07 SGSR graphics
msgid "Image sharpness affects FSR 1 and SGSR only. Start at 50% and reduce it if fine edges shimmer or show halos."
msgstr "La netteté agit uniquement avec FSR 1 ou SGSR. Commence à 50 % et diminue si les contours scintillent ou présentent des halos."

#: R07 SGSR graphics
msgid "SHARPNESS"
msgstr "NETTETÉ"

#: R07 SGSR graphics
msgid "Texture filtering sharpens roads, floors and walls viewed at an angle. Start at 4x; 8x/16x use more GPU bandwidth. Unlike image sharpness, it does not sharpen the whole picture."
msgstr "Le filtrage des textures rend plus nets les routes, sols et murs vus en biais. Commence à 4× ; 8×/16× utilisent plus de bande passante GPU. Contrairement à la netteté de l'image, ce réglage ne renforce pas toute l'image."

#: pe/ui/settings.cpp
msgid "Turn OFF Neural Rendering first. NR and frame generation are not validated together on PS5."
msgstr "Désactive d'abord Neural Rendering. Son utilisation avec la génération d'images n'est pas encore validée sur PS5."

#: pe/ui/settings.cpp
msgid "Neural Rendering saved for this game."
msgstr "Neural Rendering enregistré pour ce jeu."

#: pe/ui/settings.cpp
msgid "DLSS-NR intensity saved for this game."
msgstr "Intensité DLSS-NR enregistrée pour ce jeu."

#: pe/ui/settings.cpp
msgid "Preset: Default ({0})"
msgstr "Préréglage : Par défaut ({0})"

#: pe/ui/settings.cpp
msgid "Preset: {0}"
msgstr "Préréglage : {0}"

#: pe/ui/settings.cpp
msgid "Frame Generation"
msgstr "Génération d'images"

#: pe/ui/settings.cpp
msgid "Neural Rendering"
msgstr "Rendu neuronal"

#: pe/ui/settings.cpp
msgid "Intensité DLSS-NR"
msgstr "Intensité DLSS-NR"

#: pe/ui/settings.cpp
msgid "Frame generation is OFF by default. It smooths presentation but not game speed. Its simultaneous use with NR is unverified on PS5."
msgstr "La génération d'images est désactivée par défaut. Elle fluidifie l'affichage, mais pas le jeu lui-même. Son utilisation avec NR n'est pas encore validée sur PS5."

#: pe/ui/settings.cpp
msgid "Choix direct : Défaut, Désactivé, A4K Détails améliorés, A4K Image adoucie, A4K Image nettoyée, DLSS-NR Original et DLSS-NR Compact."
msgstr "Choix direct : Défaut, Désactivé, A4K Détails améliorés, A4K Image adoucie, A4K Image nettoyée, DLSS-NR Original et DLSS-NR Compact."

#: pe/ui/settings.cpp
msgid "L'intensité DLSS-NR (0 à 100 %) ne concerne que les deux DLSS-NR. Les valeurs par jeu sont conservées même après désactivation."
msgstr "L'intensité DLSS-NR (0 à 100 %) ne concerne que les deux DLSS-NR. Les valeurs par jeu sont conservées même après désactivation."

#: pe/ui/settings.cpp
msgid "Neural Rendering : Désactivé, A4K Détails améliorés, A4K Image adoucie, A4K Image nettoyée, DLSS-NR Original ou DLSS-NR Compact. Un seul moteur à la fois."
msgstr "Neural Rendering : Désactivé, A4K Détails améliorés, A4K Image adoucie, A4K Image nettoyée, DLSS-NR Original ou DLSS-NR Compact. Un seul moteur à la fois."

#: pe/ui/settings.cpp
msgid "Intensité DLSS-NR : 0 à 100 %. Inactif avec les trois A4K et quand le NR est désactivé ; valeur conservée."
msgstr "Intensité DLSS-NR : 0 à 100 %. Inactif avec les trois A4K et quand le NR est désactivé ; valeur conservée."

#: pe/ui/settings.cpp
msgid "A4K — Détails améliorés : réseau neuronal pour améliorer les contours et les détails de l’image en 3D. Nécessite Vulkan et un agrandissement x2."
msgstr "A4K — Détails améliorés : réseau neuronal pour améliorer les contours et les détails de l’image en 3D. Nécessite Vulkan et un agrandissement x2."

#: pe/ui/settings.cpp
msgid "A4K — Image adoucie : restauration douce avant amélioration des détails. Utile si les contours sont trop durs. Plus coûteux pour le GPU."
msgstr "A4K — Image adoucie : restauration douce avant amélioration des détails. Utile si les contours sont trop durs. Plus coûteux pour le GPU."

#: pe/ui/settings.cpp
msgid "A4K — Image nettoyée : reconstruction neurale avec débruitage. Utile si l’image présente du grain ou des artefacts, avec agrandissement x2."
msgstr "A4K — Image nettoyée : reconstruction neurale avec débruitage. Utile si l’image présente du grain ou des artefacts, avec agrandissement x2."

#: pe/ui/settings.cpp
msgid "Ce traitement nécessite Vulkan. Choisis Vulkan ou un autre agrandissement d’image pour éviter un retour automatique au bilinéaire."
msgstr "Ce traitement nécessite Vulkan. Choisis Vulkan ou un autre agrandissement d’image pour éviter un retour automatique au bilinéaire."

#: pe/ui/settings.cpp
msgid "A4K — Détails améliorés"
msgstr "A4K — Détails améliorés"

#: pe/ui/settings.cpp
msgid "A4K — Image adoucie"
msgstr "A4K — Image adoucie"

#: pe/ui/settings.cpp
msgid "A4K — Image nettoyée"
msgstr "A4K — Image nettoyée"

#: pe/ui/settings.cpp
msgid "DLSS-NR — Original"
msgstr "DLSS-NR — Original"

#: pe/ui/settings.cpp
msgid "DLSS-NR — Compact"
msgstr "DLSS-NR — Compact"

#: pe/ui/settings.cpp
msgid "Désactivé"
msgstr "Désactivé"

#: pe/ui/settings.cpp
msgid "A4K Détails améliorés : réseau de traitement de l'image privilégiant la définition des contours. Un seul moteur NR peut être sélectionné."
msgstr "A4K Détails améliorés : réseau de traitement de l'image privilégiant la définition des contours. Un seul moteur NR peut être sélectionné."

#: pe/ui/settings.cpp
msgid "A4K Image adoucie : réseau de traitement de l'image privilégiant la douceur du rendu et la stabilité des contours."
msgstr "A4K Image adoucie : réseau de traitement de l'image privilégiant la douceur du rendu et la stabilité des contours."

#: pe/ui/settings.cpp
msgid "A4K Image nettoyée : réseau de traitement visant les parasites visuels et le bruit de l'image."
msgstr "A4K Image nettoyée : réseau de traitement visant les parasites visuels et le bruit de l'image."

#: pe/ui/settings.cpp
msgid "DLSS-NR Original : réseau neuronal complet. Son intensité est configurable par jeu. Le rendu PS5 complet reste à valider."
msgstr "DLSS-NR Original : réseau neuronal complet. Son intensité est configurable par jeu. Le rendu PS5 complet reste à valider."

#: pe/ui/settings.cpp
msgid "DLSS-NR Compact : réseau neuronal réduit. Son intensité est configurable par jeu. Le rendu PS5 complet reste à valider."
msgstr "DLSS-NR Compact : réseau neuronal réduit. Son intensité est configurable par jeu. Le rendu PS5 complet reste à valider."

#: pe/ui/settings.cpp
msgid "Neural Rendering est désactivé par défaut. Choisis directement l'un des trois A4K ou l'un des deux DLSS-NR."
msgstr "Neural Rendering est désactivé par défaut. Choisis directement l'un des trois A4K ou l'un des deux DLSS-NR."

#: pe/ui/settings.cpp
msgid "L'intensité est propre au DLSS-NR Original/Compact ; elle est inactive en mode A4K ou Désactivé. Le réglage enregistré est conservé."
msgstr "L'intensité est propre au DLSS-NR Original/Compact ; elle est inactive en mode A4K ou Désactivé. Le réglage enregistré est conservé."

#: pe/ui/settings.cpp
msgid "Intensité du DLSS-NR de 0 à 100 %. Ce réglage ne modifie ni la netteté FSR, ni l'anticrénelage, ni le Frame Generation."
msgstr "Intensité du DLSS-NR de 0 à 100 %. Ce réglage ne modifie ni la netteté FSR, ni l'anticrénelage, ni le Frame Generation."

#: pe/ui/settings.cpp
msgid "Ce Neural Rendering nécessite Vulkan ; OpenGL n'est pas compatible."
msgstr "Ce Neural Rendering nécessite Vulkan ; OpenGL n'est pas compatible."

#: pe/ui/settings.cpp
msgid "Pour ce Neural Rendering, choisis Bilinéaire dans Upscaling : les compositions avec les autres méthodes ne sont pas encore validées sur PS5."
msgstr "Pour ce Neural Rendering, choisis Bilinéaire dans Upscaling : les compositions avec les autres méthodes ne sont pas encore validées sur PS5."

#: pe/ui/settings.cpp
msgid "Le MSAA forcé n'est pas encore validé avec Neural Rendering. Utilise Aucun, FXAA ou SMAA."
msgstr "Le MSAA forcé n'est pas encore validé avec Neural Rendering. Utilise Aucun, FXAA ou SMAA."

#: pe/ui/settings.cpp
msgid "Neural Rendering et Frame Generation ne sont pas encore validés ensemble. Désactive Frame Generation."
msgstr "Neural Rendering et Frame Generation ne sont pas encore validés ensemble. Désactive Frame Generation."

#: pe/ui/settings.cpp
msgid "Ce moteur n'est pas encore raccordé au rendu complet du jeu."
msgstr "Ce moteur n'est pas encore raccordé au rendu complet du jeu."

#: pe/ui/settings.cpp
msgid "MSAA 2x"
msgstr "MSAA 2x"

#: pe/ui/settings.cpp
msgid "MSAA 4x"
msgstr "MSAA 4x"

#: pe/ui/settings.cpp
msgid "MSAA 8x"
msgstr "MSAA 8x"

#: pe/ui/settings.cpp
msgid "MSAA 16x"
msgstr "MSAA 16x"

# Obsolete gettext entries: retained for translator history only; never active at runtime.
#~ msgid "AMD FSR"
#~ msgstr "AMD FSR"

#~ msgid "FSR sharpness"
#~ msgstr "Netteté FSR"

#~ msgid "FSR SHARPNESS"
#~ msgstr "NETTETÉ FSR"

#~ msgid "FSR sharpness changes detail recovery only when AMD FSR is selected. Lower it if the picture looks grainy or over-sharpened."
#~ msgstr "La netteté FSR agit uniquement avec AMD FSR. Réduisez-la si l’image paraît granuleuse ou trop accentuée."

#~ msgid "SMAA"
#~ msgstr "SMAA"

#~ msgid "Upscaling filter"
#~ msgstr "Filtre de mise à l'échelle"

#~ msgid "UPSCALING FILTER"
#~ msgstr "FILTRE DE MISE À L'ÉCHELLE"

#~ msgid "Enhanced smoothness"
#~ msgstr "Fluidité améliorée"

#~ msgid "Public rooms (read-only)"
#~ msgstr "Salons publics (consultation seule)"

#~ msgid "Read-only room directory"
#~ msgstr "Annuaire des salons (lecture seule)"

#~ msgid "Room joining is not available yet."
#~ msgstr "La connexion aux salons n'est pas encore disponible."

#~ msgid "SGSR needs Vulkan. OpenGL would silently use Bilinear; select Vulkan or another upscale method."
#~ msgstr "SGSR a besoin de Vulkan. OpenGL utiliserait silencieusement Bilinéaire ; sélectionnez Vulkan ou une autre méthode haut de gamme."

#: settings_store.h
msgid "Arabic"
msgstr "Arabe"

#: settings_store.h
msgid "Czech"
msgstr "Tchèque"

#: settings_store.h
msgid "Danish"
msgstr "Danois"

#: settings_store.h
msgid "Greek"
msgstr "Grec"

#: settings_store.h
msgid "Finnish"
msgstr "Finnois"

#: settings_store.h
msgid "Hungarian"
msgstr "Hongrois"

#: settings_store.h
msgid "Indonesian"
msgstr "Indonésien"

#: settings_store.h
msgid "Norwegian (Bokmål)"
msgstr "Norvégien (bokmål)"

#: settings_store.h
msgid "Romanian"
msgstr "Roumain"

#: settings_store.h
msgid "Swedish"
msgstr "Suédois"

#: settings_store.h
msgid "Turkish"
msgstr "Turc"

#: settings_store.h
msgid "Ukrainian"
msgstr "Ukrainien"

#: settings_store.h
msgid "Vietnamese"
msgstr "Vietnamien"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Encore Neon"
msgstr "Encore Néon"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Encore Non-Neon"
msgstr "Encore Sans néon"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Encore Dark"
msgstr "Encore Sombre"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Encore Light"
msgstr "Encore Clair"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Neon"
msgstr "Néon"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Non-Neon"
msgstr "Sans néon"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "White"
msgstr "Blanc"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Dark"
msgstr "Sombre"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Theme default"
msgstr "Thème par défaut"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Encore artwork"
msgstr "Visuel Encore"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Solid color"
msgstr "Couleur unie"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Gradient"
msgstr "Dégradé"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Daily Switch"
msgstr "Jeux du jour"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Original"
msgstr "Original"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Ocean"
msgstr "Océan"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Emerald"
msgstr "Émeraude"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Amber"
msgstr "Ambre"

#: pe/ui/settings.cpp pe/ui/switch_theme.cpp
msgid "Rose"
msgstr "Rose"

#: pe/ui/settings.cpp
msgid "Choose PlayStation or Switch button positions. The selected mapping stays fixed during menus and gameplay; customizing a button creates a custom profile."
msgstr "Choisissez la disposition des touches PlayStation ou Switch. La configuration reste fixe dans les menus et les jeux ; modifier une touche crée un profil personnalisé."

#: pe/ui/settings.cpp
msgid "The deadzone ignores small stick movements near the center. At 8%, movements below 8% do not steer the game. Increase it if your character moves by itself; lower it if aiming feels unresponsive."
msgstr "La zone morte ignore les petits mouvements du stick autour du centre. À 8 %, un mouvement inférieur à 8 % est ignoré. Augmentez-la si le personnage bouge seul ; réduisez-la si la visée manque de réactivité."

#: pe/ui/settings.cpp
msgid "Choose the Encore or Switch launcher theme; gameplay rendering does not change."
msgstr "Choisissez le thème Encore ou Switch du lanceur, sans modifier le rendu des jeux."

#: pe/ui/settings.cpp
msgid "Choose the logo treatment independently of the selected interface palette."
msgstr "Choisissez le style du logo indépendamment des couleurs de l'interface."

#: pe/ui/settings.cpp
msgid "Change the color of selection highlights and focus rings."
msgstr "Changez la couleur des sélections et des contours de mise au point."

#: pe/ui/settings.cpp
msgid "Choose a theme background, two custom colors, a local image or the daily game artwork."
msgstr "Choisissez un fond du thème, deux couleurs personnalisées, une image locale ou le visuel du jeu du jour."

#: pe/ui/settings.cpp
msgid "Copy PNG, JPEG, WebP or TGA images to /data/prosperoeden/user/wallpapers. The PS5 Media Gallery is not automatically scanned."
msgstr "Copiez des images PNG, JPEG, WebP ou TGA dans /data/prosperoeden/user/wallpapers. La galerie multimédia PS5 n'est pas analysée automatiquement."

#: pe/ui/settings.cpp
msgid "Pick a preset for the first background color, or adjust its channels below."
msgstr "Choisissez une couleur prédéfinie pour le premier fond, ou ajustez ses composantes ci-dessous."

#: pe/ui/settings.cpp
msgid "Adjust the red channel of background color one."
msgstr "Réglez la composante rouge de la première couleur."

#: pe/ui/settings.cpp
msgid "Adjust the green channel of background color one."
msgstr "Réglez la composante verte de la première couleur."

#: pe/ui/settings.cpp
msgid "Adjust the blue channel of background color one."
msgstr "Réglez la composante bleue de la première couleur."

#: pe/ui/settings.cpp
msgid "Pick a preset for the second gradient color, or adjust its channels below."
msgstr "Choisissez une couleur prédéfinie pour la seconde couleur du dégradé, ou ajustez ses composantes."

#: pe/ui/settings.cpp
msgid "Adjust the red channel of background color two."
msgstr "Réglez la composante rouge de la seconde couleur."

#: pe/ui/settings.cpp
msgid "Adjust the green channel of background color two."
msgstr "Réglez la composante verte de la seconde couleur."

#: pe/ui/settings.cpp
msgid "Adjust the blue channel of background color two."
msgstr "Réglez la composante bleue de la seconde couleur."

#: pe/ui/settings.cpp
msgid "Show or hide the selection glow. It does not affect games."
msgstr "Affichez ou masquez la lueur de sélection. Cela ne modifie pas les jeux."

#: pe/ui/settings.cpp
msgid "Change the intensity of selection highlights."
msgstr "Réglez l'intensité de la lueur de sélection."

#: pe/ui/settings.cpp
msgid "Darken only the background image. Higher values preserve menu readability."
msgstr "Assombrissez uniquement l'image de fond pour améliorer la lisibilité des menus."

#: pe/ui/settings.cpp
msgid "Change the opacity of launcher cards, panels and boxes from 0 to 100%. High contrast keeps panels opaque for legibility."
msgstr "Réglez l'opacité des cartes, panneaux et encadrés du lanceur de 0 à 100 %. Le contraste élevé conserve des panneaux opaques."

#: pe/ui/settings.cpp
msgid "Allow subtle launcher background motion, or keep it still."
msgstr "Activez de légers mouvements du fond du lanceur, ou gardez-le fixe."

#: pe/ui/settings.cpp
msgid "Fill crops the wallpaper to the screen; Contain keeps the complete image."
msgstr "Remplir recadre l'image sur l'écran ; Contenir affiche l'image entière."

#: pe/ui/settings.cpp
msgid "Show a selected game's artwork behind its library details."
msgstr "Affichez le visuel du jeu sélectionné derrière ses informations."

#: pe/ui/settings.cpp
msgid "Restore the default Neon look without altering game settings."
msgstr "Rétablissez le thème Néon sans modifier les paramètres des jeux."

#: pe/ui/settings.cpp
msgid "Panel opacity"
msgstr "Opacité des panneaux"

#: pe/ui/settings.cpp
msgid "Notice"
msgstr "Information"
)FRPO";
}
