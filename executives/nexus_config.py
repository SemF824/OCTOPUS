# nexus_config.py

# Chemins du projet
DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v9_multi_output.pkl"

# --- PARAMÈTRES AUTO-QUALIFICATION ---
CONFIDENCE_THRESHOLD = 0.45

# --- PARAMÈTRES RANDOM FOREST ---
RF_PARAMS = {
    'n_estimators' : 350,
    'max_depth'    : 30,
    'class_weight' : 'balanced',
    'random_state' : 42,
    'n_jobs'       : -1,
}

# --- LA MATRICE DE PRIORITÉ Urgence & Impact ---
# Lignes (Impact) / Colonnes (Urgence)
MATRICE_PRIORITE = [
    [1.0, 2.0, 4.0, 6.0],  # Impact 1
    [2.0, 4.0, 6.0, 8.0],  # Impact 2
    [4.0, 6.0, 8.0, 9.0],  # Impact 3
    [6.0, 8.0, 9.5, 10.0]  # Impact 4
]

