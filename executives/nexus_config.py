# nexus_config.py
import os

# --- CHEMINS LOCAUX (PC) ---
DB_PATH              = "../nexus_bionexus.db"
MODEL_PATH           = "../pickle_result/nexus_v21_unified.pkl"
MODEL_FRICTION_PATH  = "../pickle_result/nexus_v21_friction.pkl"

# --- PARAMÈTRES IA ---
CONFIDENCE_THRESHOLD = 0.45

# --- SÉCURITÉ : NÉGATIONS ET FICTION ---
NEGATION_MARKERS = [
    "pas de", "aucun", "aucune", "rien", "jamais", "plus de",
    "sans", "n'a pas", "n'ont pas", "il n'y a pas", "y a pas",
    "pas besoin", "c'est bon", "tout va bien", "aucun danger",
    "pas grave", "fausse alerte", "erreur"
]

FICTION_MARKERS = [
    "manga", "film", "serie", "jeu video", "anime", "livre", "blague",
    "roman", "bande dessinee", "bd", "dessin anime", "minecraft", "fortnite", "gta",
    "exercice", "simulation", "entrainement", "test d'alarme", "drill",
    "titan", "zombie", "alien", "vampire", "monstre", "dragon", "heros",
    "va me tuer", "vais le tuer", "vais la tuer", "je vais mourir de",
    "tuer pour", "mourir de rire", "mourir de honte", "tuer le temps",
    "je suis mort", "il est mort de rire", "crever de chaud", "crever de froid",
    "c'est une blague", "pour rire", "je deconnais"
]

# --- LES DICTIONNAIRES NER SPACY ---
MOTS_ARMES = [
    "arme", "couteau", "pistolet", "fusil", "kalachnikov", "machette", "hache",
    "batte", "poignard", "lame", "revolver", "mitraillette", "grenade", "bombe",
    "explosif", "cocktail molotov", "barre de fer", "cutter"
]

MOTS_CORPS = [
    "tete", "crane", "visage", "oeil", "yeux", "cou", "nuque", "gorge",
    "epaule", "bras", "coude", "poignet", "main", "doigt", "pouce",
    "dos", "colonne", "poitrine", "thorax", "coeur", "ventre", "estomac", "abdomen",
    "bassin", "hanche", "jambe", "genou", "cheville", "pied", "orteil"
]

MOTS_GRAVES = [
    "sang", "saigne", "hemorragie", "feu", "incendie", "brule", "mort", "arret cardiaque",
    "respire plus", "viol", "otage", "fusillade", "braquage", "overdose",
    "inconscient", "etouffe", "cyanose", "ampute", "suicide", "noyade"
]

MOTS_BENINS = [
    "ecorche", "ecorchure", "renseignement", "entorse", "panne", "casse", "baton",
    "rien", "va bien", "ras", "pas grave", "juste", "ordinateur", "telephone",
    "rhume", "toux", "bleu", "bosse", "egratignure", "ampoule", "perdu"
]

# --- MOTS-CLÉS DE LOCALISATION (LocationGuard) ---
MOTS_LIEUX = [
    "rue", "avenue", "boulevard", "bd", "allee", "impasse", "chemin", "route", "voie",
    "passage", "square", "place", "quai", "berge", "pont", "carrefour", "rond-point",
    "autoroute", "nationale", "departementale", "rocade", "peripherique", "tunnel",
    "adresse", "secteur", "quartier", "zone", "batiment", "immeuble", "residence",
    "etage", "rez-de-chaussee", "sous-sol", "chez",
    "appartement", "maison", "villa", "rdc", "cave", "grenier", "toit", "parking", "garage", "jardin", "cour",
    "gare", "station", "metro", "rer", "bus", "arret", "aeroport", "tram", "tramway", "port", "train", "tgv",
    "centre commercial", "supermarche", "marche", "mall", "magasin", "boutique", "hypermarche",
    "restaurant", "resto", "cafe", "bar", "hotel", "auberge", "banque", "poste",
    "ecole", "college", "lycee", "universite", "fac", "campus", "creche",
    "hopital", "clinique", "urgences", "pharmacie", "cabinet", "laboratoire", "ehpad",
    "mairie", "prefecture", "tribunal", "commissariat", "gendarmerie", "prison",
    "stade", "gymnase", "piscine", "salle", "parc", "foret", "bois", "plage", "lac", "riviere", "fleuve",
    "musee", "bibliotheque", "cinema", "theatre", "camping",
    "usine", "entrepot", "chantier", "bureau", "open space", "entreprise", "societe", "datacenter",
    "ville", "village", "commune", "departement", "region",
    "paris", "lyon", "marseille", "toulouse", "bordeaux", "nantes", "strasbourg", "lille", "rennes", "montpellier", "nice"
]

# --- SYNERGIES MULTI-FORCES ---
SYNERGIES_URGENCE = {
    "fusillade":          ["POLICE", "MÉDICAL"],
    "tireur":             ["POLICE", "MÉDICAL"],
    "agression":          ["POLICE", "MÉDICAL"],
    "prise d'otage":      ["POLICE", "MÉDICAL"],
    "attentat":           ["POLICE", "POMPIER", "MÉDICAL"],
    "accident grave":     ["POMPIER", "POLICE", "MÉDICAL"],
    "explosion":          ["POMPIER", "POLICE", "MÉDICAL"],
    "suicide":            ["POLICE", "MÉDICAL", "POMPIER"],
    "incendie":           ["POMPIER", "POLICE"],
    "fuite de gaz":       ["POMPIER", "POLICE"],
    "effondrement":       ["POMPIER", "POLICE", "MÉDICAL"],
    "noyade":             ["POMPIER", "MÉDICAL"],
    "ransomware":         ["INFRA", "ACCÈS", "INFORMATION / SÉCURITÉ"],
    "cyberattaque":       ["INFRA", "ACCÈS"],
    "blackout":           ["INFRA", "MATÉRIEL"]
}

# --- MATRICE DE PRIORITÉ ---
MATRICE_PRIORITE = [
    [1.0, 2.0, 3.0, 4.0],
    [2.0, 4.0, 6.0, 7.0],
    [3.0, 6.0, 8.0, 9.0],
    [4.0, 7.0, 9.0, 10.0],
]

RF_PARAMS = {'n_estimators': 350, 'max_depth': 30, 'class_weight': 'balanced', 'random_state': 42, 'n_jobs': -1}