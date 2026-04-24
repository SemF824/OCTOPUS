# nexus_massive_forge.py
import sqlite3
import pandas as pd
import random
import itertools
import os
from nexus_config import DB_PATH

print("🚀 INITIALISATION DU GÉNÉRATEUR MASSIF NEXUS (Objectif : 600 000 tickets)...")

# ==========================================
# 1. LES BRIQUES DE LANGAGE (RÉALISTES)
# ==========================================

EMOTIONS = [
    "", "Au secours, ", "Aidez-moi, ", "Vite ! ", "Je vous en supplie, ",
    "C'est urgent, ", "Je panique, ", "S'il vous plaît, ", "Putain venez vite, "
]

LIEUX_DOMICILE = ["chez moi", "dans mon appartement", "dans ma maison", "dans mon jardin", "sur mon palier"]
LIEUX_PUBLIC = ["dans la rue", "devant la gare", "sur le parking", "au centre commercial", "dans le métro"]

# --- MÉDICAL ---
MED_SUJETS = ["Je", "Ma femme", "Mon mari", "Mon enfant", "Un passant"]
MED_ACTIONS = [
    ("ai mal à la tête", 2, 2), ("ai le nez cassé", 2, 2),
    ("ai la jambe arrachée", 4, 4), ("ai une douleur au coeur", 4, 4),
    ("me suis coupé le doigt", 1, 1), ("ai une grosse entaille au bras", 3, 3),
    ("ai fait une chute dans les escaliers", 3, 3), ("ne sens plus mes jambes", 4, 4)
]
MED_SYMPTOMES = [
    ("", 0, 0), (" et je saigne", 1, 1), (" et ça pisse le sang", 2, 2),
    (" et j'ai des vertiges", 1, 1), (" et je vais m'évanouir", 2, 2),
    (" et je n'arrive plus à respirer", 2, 2)
]

# --- POLICE ---
POL_ACTIONS = [
    ("quelqu'un s'est introduit", 3, 3), ("on a forcé ma porte", 3, 3),
    ("des gens se battent", 2, 3), ("on m'a volé mon téléphone", 2, 2),
    ("il y a un rodéo urbain", 2, 2), ("on m'a tiré dessus", 4, 4),
    ("je suis suivi par un homme", 3, 3), ("mon conjoint me frappe", 4, 4)
]
POL_ARMES = [
    ("", 0, 0), (" avec un couteau", 1, 1), (" il est armé", 1, 1),
    (" ils ont des fusils", 1, 1), (" et il menace de me tuer", 1, 1)
]

# --- POMPIER ---
POM_ACTIONS = [
    ("il y a le feu", 4, 4), ("ça sent le gaz", 3, 4),
    ("un immeuble s'est effondré", 4, 4), ("gros accident de voiture", 3, 4),
    ("ma cave est inondée", 2, 2), ("il y a une explosion", 4, 4)
]
POM_DETAILS = [
    ("", 0, 0), (" avec beaucoup de fumée", 1, 0), (" des gens sont coincés", 0, 1),
    (" le feu se propage vite", 1, 1)
]

# --- INFRA / MATÉRIEL / ACCÈS (Simplifiés pour l'exemple) ---
TECH_ACTIONS = [
    ("mon PC", "MATÉRIEL", 1, 1), ("l'imprimante", "MATÉRIEL", 1, 1),
    ("le serveur principal", "INFRA", 4, 4), ("le réseau wifi", "INFRA", 3, 2),
    ("mon mot de passe", "ACCÈS", 2, 2), ("le VPN", "ACCÈS", 3, 2)
]
TECH_PANNES = [" ne marche plus", " est en panne", " a explosé", " affiche une erreur", " est bloqué"]


# ==========================================
# 2. MOTEUR DE GÉNÉRATION
# ==========================================

def generer_tickets():
    dataset = []

    print("⏳ Génération des 100 000 tickets MÉDICAL...")
    while len(dataset) < 100000:
        emo = random.choice(EMOTIONS)
        suj = random.choice(MED_SUJETS)
        act, i1, u1 = random.choice(MED_ACTIONS)
        sym, i2, u2 = random.choice(MED_SYMPTOMES)

        texte = f"{emo}{suj.lower() if emo else suj} {act}{sym}".strip()
        # Plafonner l'impact et l'urgence à 4
        imp = min(4, i1 + i2)
        urg = min(4, u1 + u2)
        dataset.append((texte, "MÉDICAL", imp, urg))

    print("⏳ Génération des 100 000 tickets POLICE...")
    count_police = 0
    while count_police < 100000:
        emo = random.choice(EMOTIONS)
        lieu = random.choice(LIEUX_DOMICILE + LIEUX_PUBLIC)
        act, i1, u1 = random.choice(POL_ACTIONS)
        arme, i2, u2 = random.choice(POL_ARMES)

        texte = f"{emo}{act} {lieu}{arme}".strip()
        imp = min(4, i1 + i2)
        urg = min(4, u1 + u2)
        dataset.append((texte, "POLICE", imp, urg))
        count_police += 1

    print("⏳ Génération des 100 000 tickets POMPIER...")
    count_pompier = 0
    while count_pompier < 100000:
        emo = random.choice(EMOTIONS)
        lieu = random.choice(LIEUX_DOMICILE + LIEUX_PUBLIC)
        act, i1, u1 = random.choice(POM_ACTIONS)
        det, i2, u2 = random.choice(POM_DETAILS)

        texte = f"{emo}{act} {lieu}{det}".strip()
        imp = min(4, i1 + i2)
        urg = min(4, u1 + u2)
        dataset.append((texte, "POMPIER", imp, urg))
        count_pompier += 1

    print("⏳ Génération des 300 000 tickets TECHNIQUES (Infra, Matériel, Accès)...")
    count_tech = 0
    while count_tech < 300000:
        emo = random.choice(["", "Urgent, ", "Bonjour, "])
        sujet, dom, i1, u1 = random.choice(TECH_ACTIONS)
        panne = random.choice(TECH_PANNES)

        texte = f"{emo}{sujet}{panne}".strip()
        dataset.append((texte, dom, i1, u1))
        count_tech += 1

    return pd.DataFrame(dataset, columns=["texte", "domaine", "impact", "urgence"])


# ==========================================
# 3. EXÉCUTION ET SAUVEGARDE
# ==========================================
df_massif = generer_tickets()

# Mélange aléatoire de toutes les lignes
df_massif = df_massif.sample(frac=1, random_state=42).reset_index(drop=True)

# Sauvegarde en CSV pour consultation
chemin_csv = "../datasets/nexus_massive_dataset.csv"
os.makedirs("../datasets", exist_ok=True)
df_massif.to_csv(chemin_csv, index=False)
print(f"✅ Fichier CSV généré avec succès : {chemin_csv} ({len(df_massif)} lignes)")

# Injection dans la base de données SQLite pour l'entraînement
print("💾 Injection dans la base de données SQLite...")
with sqlite3.connect(DB_PATH) as conn:
    df_massif.to_sql("tickets_domaines", conn, if_exists="replace", index=False)

# Création d'une table friction minimale pour que la V12 continue de fonctionner
print("⚖️ Génération de la table Friction...")
friction_data = []
# On prend 10000 tickets au hasard pour la friction
for _, row in df_massif.head(10000).iterrows():
    mots = row['texte'].split()
    if len(mots) > 4:
        v1 = " ".join(mots[:len(mots) // 2])
        friction_data.append((v1, "DEMANDE_DETAILS_GENERAUX"))
        friction_data.append((row['texte'], "COMPLET"))

df_friction = pd.DataFrame(friction_data, columns=["texte", "label"]).drop_duplicates()
with sqlite3.connect(DB_PATH) as conn:
    df_friction.to_sql("tickets_friction", conn, if_exists="replace", index=False)

print(f"🎉 OPÉRATION TERMINÉE. Base de données prête pour l'entraînement !")