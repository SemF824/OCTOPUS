DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v8.1_extended.pkl"

# --- PARAMÈTRES AUTO-QUALIFICATION ---
# Si l'IA est sûre d'elle à moins de 45%, on force une demande de précision
CONFIDENCE_THRESHOLD = 0.45

# --- PARAMÈTRES RANDOM FOREST ---
RF_PARAMS = {
    'n_estimators' : 350,
    'max_depth'    : 30,
    'class_weight' : 'balanced',
    'random_state' : 42,
    'n_jobs'       : -1,
}