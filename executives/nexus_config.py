# nexus_config.py
import os

# --- CHEMINS LOCAUX (PC) ---
DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v12_unified.pkl"
MODEL_FRICTION_PATH = "../pickle_result/nexus_v12_friction.pkl"

# --- PARAMÈTRES IA ---
CONFIDENCE_THRESHOLD = 0.45

# --- SÉCURITÉ : NÉGATIONS ET FICTION ---
NEGATION_MARKERS = ["pas de", "aucun", "aucune", "rien", "jamais", "plus de", "sans", "n'a pas", "n'ont pas"]
FICTION_MARKERS = ["manga", "film", "série", "jeu vidéo", "anime", "livre", "blague", "fausse alerte"]

# --- SYNERGIES MULTI-FORCES ---
SYNERGIES_URGENCE = {
    "fusillade": ["POLICE", "MÉDICAL"],
    "tireur": ["POLICE", "MÉDICAL"],
    "accident grave": ["POMPIER", "POLICE", "MÉDICAL"],
    "explosion": ["POMPIER", "POLICE", "MÉDICAL"],
    "agression avec arme": ["POLICE", "MÉDICAL"],
    "suicide": ["POLICE", "MÉDICAL", "POMPIER"],
    "incendie bâtiment": ["POMPIER", "POLICE"]
}

# --- MATRICE DE PRIORITÉ (Version Ghali) ---
MATRICE_PRIORITE = [
    [1.0, 2.0, 3.0, 4.0],  # Impact 1
    [2.0, 4.0, 6.0, 7.0],  # Impact 2
    [3.0, 6.0, 8.0, 9.0],  # Impact 3
    [4.0, 7.0, 9.0, 10.0]  # Impact 4
]

# Note : Si ton PC souffle un peu trop fort lors de l'entraînement, tu peux passer n_jobs de -1 à 2.
RF_PARAMS = {'n_estimators': 350, 'max_depth': 30, 'class_weight': 'balanced', 'random_state': 42, 'n_jobs': -1}