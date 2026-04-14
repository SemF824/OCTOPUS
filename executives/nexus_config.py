# nexus_config.py
#import re

#DB_PATH = "../nexus_bionexus.db"
#MODEL_PATH = "../pickle_result/nexus_v7_pipeline.pkl"

# --- RÉFÉRENTIEL MÉDICAL (Ancrages par phrases) ---
# L'IA comparera le ticket à ces phrases pour trouver la zone
#LOCALISATIONS = {
#    "TÊTE & CRÂNE": {
#        "base": 6.0,
#        "phrases": ["mal à la tête", "mon crâne saigne", "blessure au crane", "coup sur le front", "choc à la tête", "mon crane saigne"]
#    },
#    "THORAX & COEUR": {
#        "base": 6.0,
#        "phrases": ["douleur à la poitrine", "sang qui sort du coeur", "mal au thorax", "problème cardiaque", "saigne de la poitrine", "douleur au cœur"]
#    },
#    "VENTRE & ABDOMEN": {
#        "base": 5.0,
#        "phrases": ["mal au ventre", "douleur abdominale", "saigne du ventre", "maux d'estomac", "ventre dur"]
#    },
#    "BRAS & JAMBE": {
#        "base": 4.0,
#        "phrases": ["j'ai perdu ma jambe", "saigne du bras", "fracture de la jambe", "douleur au genou", "bras cassé", "blessure à la jambe"]
#    },
#    "EXTRÉMITÉS (Doigt/Main/Pied)": {
#        "base": 2.0,
#        "phrases": ["je saigne du doigt", "coupure à la main", "blessure au pied", "ongle arraché", "orteil cassé", "doigt coupé"]
#    },
#    "DOS & COLONNE": {
#        "base": 7.0,
#        "phrases": ["douleur au dos", "mal à la colonne vertébrale", "choc dans le dos", "lombalgie aiguë"]
#    }
#}

## Signes de gravité (Red Flags)
#RED_FLAGS = {
#    "choc": {"mots": ["pâle", "froid", "sueur", "soif", "faible", "marbré"], "plus": 5},
#    "neuro": {"mots": ["vertige", "étourdi", "vomir", "nausée", "confus", "flou"], "plus": 4},
#    "vital": {"mots": ["inconscient", "respire plus", "étouffe", "agonie", "arrêt"], "plus": 8}
#}

# Paramètres Forge
#RF_PARAMS = {"n_estimators": 200, "max_depth": 20, "class_weight": "balanced", "random_state": 42}


DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v8.1_extended.pkl"

# Paramètres de l'algorithme Random Forest
RF_PARAMS = {
    'n_estimators' : 350,
    'max_depth'    : 30,
    'class_weight' : 'balanced',
    'random_state' : 42,
    'n_jobs'       : -1,
}