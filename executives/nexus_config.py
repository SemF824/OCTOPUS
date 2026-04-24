# nexus_config.py

DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v8.1_extended.pkl"

# --- PARAMÈTRES AUTO-QUALIFICATION ---
# Si l'IA est sûre d'elle à moins de 45%, on force une demande de précision
CONFIDENCE_THRESHOLD = 0.45

# --- NOUVEAU : DÉCLENCHEURS MULTI-FORCES (SYNERGIES) ---
# Si un de ces événements est détecté, on force l'appel à plusieurs services
SYNERGIES_URGENCE = {
    "fusillade": ["POLICE", "MÉDICAL"],
    "tireur": ["POLICE", "MÉDICAL"],
    "accident grave": ["POMPIER", "POLICE", "MÉDICAL"],
    "explosion": ["POMPIER", "POLICE", "MÉDICAL"],
    "agression avec arme": ["POLICE", "MÉDICAL"],
    "suicide": ["POLICE", "MÉDICAL", "POMPIER"],
    "incendie bâtiment": ["POMPIER", "POLICE"]
}

# --- NOUVEAU : LEXIQUE DE LOCALISATION ---
MOTS_LIEUX = [
    "rue", "avenue", "boulevard", "étage", "bâtiment", "parking",
    "maison", "appartement", "route", "autoroute", "gare", "école", "magasin"
]

# --- PARAMÈTRES RANDOM FOREST ---
RF_PARAMS = {
    'n_estimators' : 350,
    'max_depth'    : 30,
    'class_weight' : 'balanced',
    'random_state' : 42,
    'n_jobs'       : -1,
}