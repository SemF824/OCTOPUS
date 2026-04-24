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


# --- LA MATRICE DE PRIORITÉ
# Lignes (Impact) : 1=Mineur, 2=Significatif, 3=Majeur, 4=Critique
# Colonnes (Urgence) : 1=Faible, 2=Moyenne, 3=Haute, 4=Immédiate
MATRICE_PRIORITE = [
    [1.0, 2.0, 4.0, 6.0],  # Impact 1
    [2.0, 4.0, 6.0, 8.0],  # Impact 2
    [4.0, 6.0, 8.0, 9.0],  # Impact 3
    [6.0, 8.0, 9.5, 10.0]  # Impact 4
]

# --- RÉFÉRENTIEL DES IMPACTS (Anatomie) ---
LOCALISATIONS = {
    "EXTRÉMITÉS": {"impact": 1, "phrases": ["saigne du doigt", "coupure à la main", "blessure au pied", "orteil cassé"]},
    "MEMBRES":    {"impact": 2, "phrases": ["fracture de la jambe", "bras cassé", "douleur au genou", "mal à l'épaule"]},
    "TRONC/TÊTE": {"impact": 3, "phrases": ["mal au ventre", "mal à la tête", "douleur au dos", "nez cassé", "douleur aux yeux"]},
    "VITAUX":     {"impact": 4, "phrases": ["sang qui sort du coeur", "blessure au crâne", "hémorragie interne", "crise cardiaque", "poitrine"]}
}

# --- RÉFÉRENTIEL DES URGENCES (Signes Cliniques) ---
RED_FLAGS = {
    "choc": {"mots": ["pâle", "froid", "sueur", "soif", "faible", "marbré"], "urgence": 3},
    "neuro": {"mots": ["vertige", "étourdi", "vomir", "nausée", "confus", "flou"], "urgence": 3},
    "vital": {"mots": ["inconscient", "respire plus", "étouffe", "agonie", "arrêt"], "urgence": 4}
}

# Alertes techniques critiques (Force l'impact 4 / Urgence 4)
CRITICAL_TECH_KEYWORDS = ["explosion", "incendie", "feu", "fumée", "inondation", "catastrophe"]
