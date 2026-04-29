# nexus_config.py
import os

DB_PATH              = "../nexus_bionexus.db"
MODEL_PATH           = "../pickle_result/nexus_v21_unified.pkl"
MODEL_FRICTION_PATH  = "../pickle_result/nexus_v21_friction.pkl"
CONFIDENCE_THRESHOLD = 0.45

NEGATION_MARKERS = [
    "pas de", "aucun", "aucune", "rien", "jamais", "plus de",
    "sans", "n'a pas", "n'ont pas", "il n'y a pas", "y a pas",
    "pas besoin", "c'est bon", "tout va bien", "aucun danger",
    "pas grave", "fausse alerte", "erreur"
]

FICTION_MARKERS = [
    "manga", "film", "films", "serie", "series", "jeu video", "jeux videos", "anime", "livre", "blague",
    "roman", "bande dessinee", "bd", "dessin anime", "minecraft", "fortnite", "gta",
    "exercice", "simulation", "entrainement", "test d'alarme", "drill",
    "titan", "titans", "zombie", "zombies", "alien", "aliens", "vampire", "vampires",
    "monstre", "monstres", "dragon", "dragons", "heros",
    "va me tuer", "vais le tuer", "vais la tuer", "je vais mourir de",
    "tuer pour", "mourir de rire", "mourir de honte", "tuer le temps",
    "je suis mort", "il est mort de rire", "crever de chaud", "crever de froid",
    "c'est une blague", "pour rire", "je deconnais"
]

MOTS_ARMES = [
    "arme", "armes", "couteau", "couteaux", "pistolet", "pistolets", "fusil", "fusils",
    "kalachnikov", "kalachnikovs", "machette", "machettes", "hache", "haches",
    "batte", "battes", "poignard", "poignards", "lame", "lames", "revolver", "revolvers",
    "mitraillette", "mitraillettes", "grenade", "grenades", "bombe", "bombes",
    "explosif", "explosifs", "cocktail molotov", "barre de fer", "cutter", "cutters"
]

MOTS_CORPS = [
    "tete", "crane", "visage", "oeil", "yeux", "cou", "nuque", "gorge",
    "epaule", "epaules", "bras", "coude", "coudes", "poignet", "poignets", "main", "mains", "doigt", "doigts", "pouce",
    "dos", "colonne", "poitrine", "thorax", "coeur", "ventre", "estomac", "abdomen",
    "bassin", "hanche", "hanches", "jambe", "jambes", "genou", "genoux", "cheville", "chevilles", "pied", "pieds", "orteil", "orteils"
]

CORPS_SENSIBLES = ["tete", "crane", "visage", "oeil", "yeux", "cou", "nuque", "gorge", "colonne", "poitrine", "thorax", "coeur", "ventre", "estomac", "abdomen"]

SYMPTOMES_GLOBAUX = [
    "malaise", "malaises", "arret", "respire", "inconscient", "inconsciente", "reveil", "reveille",
    "etouffe", "cyanose", "noyade", "suicide", "pendu",
    "overdose", "medicament", "medicaments", "poison", "alcool", "drogue", "ivre",
    "fievre", "temperature", "virus", "infection", "grippe", "septicemie",
    "allergie", "allergique", "choc", "anaphylactique", "gonfle",
    "convulsion", "convulsions", "epilepsie", "tremble", "tremblement", "angoisse", "panique",
    "hallucination", "delire", "agite", "fou",
    "fatigue", "epuise", "faiblesse", "tombe", "froid", "chaud", "brule partout", "mal partout", "fracture", "casse"
]

SYMPTOMES_SEVERES = ["epilepsie", "convulsion", "convulsions", "fracture", "casse", "allergie", "gonfle", "brulure", "brule", "hemorragie"]

MOTS_GRAVES = [
    "sang", "saigne", "hemorragie", "feu", "incendie", "brule", "mort", "morts", "arret cardiaque",
    "viol", "viols", "otage", "otages", "fusillade", "fusillades", "braquage", "braquages",
    "ampute", "crash", "crashe", "avale"
] + SYMPTOMES_GLOBAUX

MOTS_BENINS = [
    "ecorche", "ecorchure", "renseignement", "entorse", "panne", "baton",
    "rien", "va bien", "ras", "pas grave", "juste", "ordinateur", "telephone",
    "rhume", "toux", "bleu", "bosse", "egratignure", "ampoule", "perdu"
]

# --- NOUVEAU : VOCABULAIRE DES AUTRES DOMAINES POUR L'AUTO-CORRECTEUR ---
MOTS_DELITS = [
    "vol", "vols", "cambriolage", "cambriolages", "effraction", "effractions",
    "agression", "agressions", "bagarre", "bagarres", "menace", "menaces", "harcelement", "meurtre", "meurtres"
]

MOTS_SINISTRES = [
    "fumee", "fumees", "fuite", "fuites", "gaz", "eau", "inondation", "inondations",
    "effondrement", "eboulement", "accident", "accidents", "catastrophe"
]

MOTS_IT = [
    "serveur", "serveurs", "reseau", "reseaux", "connexion", "piratage", "pirate", "hacker",
    "ransomware", "mdp", "password", "routeur", "switch", "logiciel", "application", "internet", "wifi"
]

MOTS_ENTREPRISES = ["siege", "agence", "entreprise", "societe", "site", "filiale", "bureau", "etage", "batiment", "campus"]

MOTS_LIEUX = [
    "rue", "rues", "avenue", "avenues", "boulevard", "boulevards", "bd", "allee", "allees",
    "impasse", "impasses", "chemin", "chemins", "route", "routes", "voie", "voies",
    "passage", "passages", "square", "squares", "place", "places", "quai", "quais",
    "berge", "berges", "pont", "ponts", "carrefour", "croisement", "rond-point",
    "autoroute", "autoroutes", "nationale", "departementale", "rocade", "peripherique", "tunnel", "tunnels",
    "adresse", "secteur", "quartier", "zone", "batiment", "batiments", "immeuble", "immeubles",
    "residence", "residences", "etage", "etages", "rez-de-chaussee", "sous-sol", "chez",
    "appartement", "appartements", "maison", "maisons", "villa", "villas", "rdc", "cave", "caves",
    "grenier", "toit", "toits", "parking", "parkings", "garage", "garages", "jardin", "jardins", "cour",
    "gare", "gares", "station", "stations", "metro", "rer", "bus", "arret", "aeroport", "aeroports",
    "tram", "tramway", "port", "ports", "train", "tgv",
    "centre commercial", "centres commerciaux", "supermarche", "supermarches", "marche", "mall",
    "magasin", "magasins", "boutique", "boutiques", "hypermarche",
    "restaurant", "restaurants", "resto", "restos", "cafe", "cafes", "bar", "bars",
    "hotel", "hotels", "auberge", "banque", "banques", "poste",
    "ecole", "ecoles", "college", "colleges", "lycee", "lycees", "universite", "universites", "fac", "campus", "creche", "creches",
    "hopital", "hopitaux", "clinique", "cliniques", "urgences", "pharmacie", "pharmacies", "cabinet", "cabinets", "laboratoire", "ehpad",
    "mairie", "prefecture", "tribunal", "commissariat", "gendarmerie", "prison", "prisons",
    "stade", "stades", "gymnase", "piscine", "piscines", "salle", "salles", "parc", "parcs",
    "foret", "forets", "bois", "plage", "plages", "lac", "lacs", "riviere", "rivieres", "fleuve", "fleuves",
    "musee", "musees", "bibliotheque", "cinema", "cinemas", "theatre", "theatres", "camping", "campings",
    "usine", "usines", "entrepot", "entrepots", "chantier", "chantiers", "bureau", "bureaux",
    "open space", "entreprise", "entreprises", "societe", "societes", "datacenter",
    "ville", "villes", "village", "villages", "commune", "communes", "departement", "region",
    "paris", "lyon", "marseille", "toulouse", "bordeaux", "nantes", "strasbourg", "lille", "rennes", "montpellier", "nice"
]

SYNERGIES_URGENCE = {
    "fusillade":          ["POLICE", "MÉDICAL"],
    "tireur":             ["POLICE", "MÉDICAL"],
    "agression":          ["POLICE", "MÉDICAL"],
    "prise d'otage":      ["POLICE", "MÉDICAL"],
    "attentat":           ["POLICE", "POMPIER", "MÉDICAL"],
    "accident":           ["POMPIER", "POLICE", "MÉDICAL"],
    "crash":              ["POMPIER", "POLICE", "MÉDICAL"],
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

MATRICE_PRIORITE = [
    [1.0, 2.0, 3.0, 4.0],
    [2.0, 4.0, 6.0, 7.0],
    [3.0, 6.0, 8.0, 9.0],
    [4.0, 7.0, 9.0, 10.0],
]

RF_PARAMS = {'n_estimators': 350, 'max_depth': 30, 'class_weight': 'balanced', 'random_state': 42, 'n_jobs': -1}