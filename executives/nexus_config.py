# nexus_config.py
import os

# --- CHEMINS LOCAUX (PC) ---
# ⚠️ Après téléchargement Kaggle V21, mets à jour les noms de fichiers ici :
DB_PATH              = "../nexus_bionexus.db"
MODEL_PATH           = "../pickle_result/nexus_v21_unified.pkl"
MODEL_FRICTION_PATH  = "../pickle_result/nexus_v21_friction.pkl"

# --- PARAMÈTRES IA ---
CONFIDENCE_THRESHOLD = 0.45

# --- SÉCURITÉ : NÉGATIONS ET FICTION ---
NEGATION_MARKERS = [
    "pas de", "aucun", "aucune", "rien", "jamais", "plus de",
    "sans", "n'a pas", "n'ont pas", "il n'y a pas", "y a pas"
]

# Marqueurs de fiction / métaphore — le modèle doit ignorer ces phrases
FICTION_MARKERS = [
    # Médias
    "manga", "film", "série", "jeu vidéo", "anime", "livre", "blague",
    "fausse alerte", "roman", "bande dessinée", "bd", "dessin animé",
    # Exercices / simulations
    "exercice", "simulation", "entraînement", "test d'alarme", "drill",
    # Personnages / créatures fictives
    "titan", "zombie", "alien", "vampire", "monstre", "dragon",
    "minecraft", "fortnite", "personnage", "héros",
    # ✅ NOUVEAU — Métaphores idiomatiques courantes
    "va me tuer", "vais le tuer", "vais la tuer", "je vais mourir de",
    "tuer pour", "mourir de rire", "mourir de honte", "tuer le temps",
    "je suis mort", "il est mort de rire", "crever de chaud",
    "c'est une blague", "pour rire", "je déconnais",
]

# --- SYNERGIES MULTI-FORCES ---
SYNERGIES_URGENCE = {
    "fusillade":          ["POLICE", "MÉDICAL"],
    "tireur":             ["POLICE", "MÉDICAL"],
    "accident grave":     ["POMPIER", "POLICE", "MÉDICAL"],
    "explosion":          ["POMPIER", "POLICE", "MÉDICAL"],
    "agression avec arme":["POLICE", "MÉDICAL"],
    "suicide":            ["POLICE", "MÉDICAL", "POMPIER"],
    "incendie bâtiment":  ["POMPIER", "POLICE"],
}

# --- MOTS-CLÉS DE LOCALISATION ---
# Utilisés par le LocationGuard dans main.py
# ✅ NOUVEAU — Lieux nommés et points de repère ajoutés
MOTS_LIEUX = [
    # Voirie classique
    "rue", "avenue", "boulevard", "bd", "allée", "impasse", "chemin",
    "route", "voie", "passage", "square", "place", "quai", "berge",
    # Adresse / repère
    "adresse", "secteur", "quartier", "zone", "ici", "là", "devant",
    "derrière", "à côté", "en face", "bâtiment", "immeuble", "résidence",
    "étage", "rez-de-chaussée", "sous-sol",
    # Transport
    "gare", "station", "métro", "rer", "bus", "arrêt", "aéroport",
    "autoroute", "périphérique", "parking",
    # Lieux publics & monuments (LocationGuard rate ces cas sans liste)
    "cathédrale", "église", "mosquée", "synagogue", "temple",
    "école", "collège", "lycée", "université", "fac", "campus",
    "hôpital", "clinique", "urgences", "pharmacie", "cabinet",
    "mairie", "préfecture", "tribunal", "commissariat",
    "stade", "gymnase", "piscine", "salle", "parc", "jardin", "forêt",
    "centre commercial", "supermarché", "marché", "mall",
    "restaurant", "café", "bar", "hôtel",
    "musée", "bibliothèque", "cinéma", "théâtre",
    "usine", "entrepôt", "chantier", "bureau", "open space",
    # Repères géographiques
    "ville", "village", "commune", "département", "région",
    "paris", "lyon", "marseille", "toulouse", "bordeaux", "nantes",
    "strasbourg", "lille", "rennes", "montpellier", "nice",
]

# --- MATRICE DE PRIORITÉ (Version Ghali) ---
# MATRICE_PRIORITE[impact-1][urgence-1] → score /10
MATRICE_PRIORITE = [
    [1.0, 2.0, 3.0, 4.0],   # Impact 1
    [2.0, 4.0, 6.0, 7.0],   # Impact 2
    [3.0, 6.0, 8.0, 9.0],   # Impact 3
    [4.0, 7.0, 9.0, 10.0],  # Impact 4
]

# --- PARAMÈTRES RANDOM FOREST ---
# Si ton PC souffle, passe n_jobs de -1 à 2.
RF_PARAMS = {
    'n_estimators': 350,
    'max_depth': 30,
    'class_weight': 'balanced',
    'random_state': 42,
    'n_jobs': -1,
}