# nexus_config.py

DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v8.1_extended.pkl"

# --- PARAMÈTRES AUTO-QUALIFICATION ---
CONFIDENCE_THRESHOLD = 0.45

# --- DÉCLENCHEURS MULTI-FORCES (SYNERGIES) ---
SYNERGIES_URGENCE = {
    "fusillade": ["POLICE", "MÉDICAL"],
    "tireur": ["POLICE", "MÉDICAL"],
    "accident grave": ["POMPIER", "POLICE", "MÉDICAL"],
    "explosion": ["POMPIER", "POLICE", "MÉDICAL"],
    "agression avec arme": ["POLICE", "MÉDICAL"],
    "suicide": ["POLICE", "MÉDICAL", "POMPIER"],
    "incendie bâtiment": ["POMPIER", "POLICE"]
}

# --- LEXIQUE DE LOCALISATION (Élargi pour éviter les blocages) ---
MOTS_LIEUX = [
    "rue", "avenue", "boulevard", "étage", "bâtiment", "parking",
    "maison", "appartement", "route", "autoroute", "gare", "école", "magasin",
    "mairie", "hôpital", "clinique", "centre", "place", "parc", "adresse", "ici", "chez"
]

# --- PARAMÈTRES RANDOM FOREST ---
RF_PARAMS = {
    'n_estimators' : 350,
    'max_depth'    : 30,
    'class_weight' : 'balanced',
    'random_state' : 42,
    'n_jobs'       : -1,
}