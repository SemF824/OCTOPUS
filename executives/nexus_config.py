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


# --- LA MATRICE DE PRIORITÉ Urgence & Impact ---
# Lignes (Impact) : 1=Mineur, 2=Significatif, 3=Majeur, 4=Critique
# Colonnes (Urgence) : 1=Faible, 2=Moyenne, 3=Haute, 4=Immédiate

MATRICE_PRIORITE = [
    [1.0, 2.0, 4.0, 6.0],  # Impact 1
    [2.0, 4.0, 6.0, 8.0],  # Impact 2
    [4.0, 6.0, 8.0, 9.0],  # Impact 3
    [6.0, 8.0, 9.5, 10.0]  # Impact 4
]

# --- 1. ANCRES SÉMANTIQUES : L'IMPACT (Où est le problème ?) ---
LOCALISATIONS = {
    "EXTRÉMITÉS": {"impact": 1, "phrases": ["saigne du doigt", "coupure à la main", "blessure au pied", "orteil cassé"]},
    "MEMBRES":    {"impact": 2, "phrases": ["fracture de la jambe", "bras cassé", "douleur au genou", "mal à l'épaule"]},
    "TRONC/TÊTE": {"impact": 3, "phrases": ["mal au ventre", "mal à la tête", "douleur au dos", "nez cassé", "douleur aux yeux"]},
    "VITAUX":     {"impact": 4, "phrases": ["sang qui sort du coeur", "blessure au crâne", "hémorragie interne", "crise cardiaque", "poitrine"]}
}

# --- 2. ANCRES SÉMANTIQUES : L'URGENCE (Quelle est la gravité ?) ---
# L'IA va projeter le ticket ici pour comprendre la gravité, même avec des fautes.
URGENCES = {
    "FAIBLE": {
        "urgence": 1,
        "phrases": ["petite coupure", "douleur légère", "tout va bien", "rien de grave", "légèrement enflé"]
    },
    "MOYENNE": {
        "urgence": 2,
        "phrases": ["ça saigne un peu", "douleur modérée", "j'ai mal quand je bouge", "petite fièvre"]
    },
    "HAUTE": {
        "urgence": 3,
        "phrases": ["je me sens faible", "j'ai des vertiges", "envie de vomir", "très pâle", "douleur insupportable", "saigne beaucoup"]
    },
    "IMMÉDIATE": {
        "urgence": 4,
        "phrases": ["hémorragie massive", "le sang gicle", "amputation", "jambe arrachée", "inconscient", "ne respire plus", "je perds connaissance", "sectionné"]
    }
}

# Alertes techniques
CRITICAL_TECH_KEYWORDS = ["explosion", "incendie", "feu", "fumée", "inondation", "catastrophe"]