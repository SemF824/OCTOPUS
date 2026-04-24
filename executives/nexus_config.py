# nexus_config.py

DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v12_unified.pkl"
MODEL_FRICTION_PATH = "../pickle_result/nexus_v12_friction.pkl"

CONFIDENCE_THRESHOLD = 0.45

# --- NÉGATIONS ET FICTION (Ajout de "anime") ---
NEGATION_MARKERS = ["pas de", "aucun", "aucune", "rien", "jamais", "plus de", "sans", "n'a pas", "n'ont pas"]
FICTION_MARKERS = ["fausse alerte", "erreur", "résolu", "c'est bon", "manga", "film", "série", "jeu vidéo", "anime", "livre", "blague"]

SYNERGIES_URGENCE = {
    "fusillade": ["POLICE", "MÉDICAL"],
    "tireur": ["POLICE", "MÉDICAL"],
    "accident grave": ["POMPIER", "POLICE", "MÉDICAL"],
    "explosion": ["POMPIER", "POLICE", "MÉDICAL"],
    "agression avec arme": ["POLICE", "MÉDICAL"],
    "suicide": ["POLICE", "MÉDICAL", "POMPIER"],
    "incendie bâtiment": ["POMPIER", "POLICE"]
}

MOTS_LIEUX = ["rue", "avenue", "boulevard", "étage", "bâtiment", "parking", "maison", "appartement", "route", "gare", "école", "magasin", "banque", "place"]

MATRICE_PRIORITE = [
    [1.0, 2.0, 3.0, 4.0],  # Impact 1
    [2.0, 4.0, 6.0, 7.0],  # Impact 2
    [3.0, 6.0, 8.0, 9.0],  # Impact 3
    [4.0, 7.0, 9.0, 10.0]  # Impact 4
]

RF_PARAMS = {'n_estimators': 350, 'max_depth': 30, 'class_weight': 'balanced', 'random_state': 42, 'n_jobs': -1}