# nexus_massive_forge.py
import sqlite3
import pandas as pd
import random
import os
from nexus_config import DB_PATH

print("🚀 INITIALISATION DU GÉNÉRATEUR V15 ULTRA-DIVERSE (Objectif : 600 000+ tickets uniques)...")

# --- DICTIONNAIRES GIGA-EXTENSIFS ---
EMOTIONS = ["", "Au secours ! ", "Aidez-moi vite ! ", "Je panique, ", "C'est urgent, ", "S'il vous plaît, ",
            "Venez vite, ", "Je suis terrifié, ", "Hé ho, ", "C'est la catastrophe, "]
RUES = ["Victor Hugo", "de la République", "Jean Jaurès", "Pasteur", "des Fleurs", "de la Gare", "du Port",
        "Main Street", "des Lilas", "du Château", "de Paris", "de Lyon", "de Marseille", "des Alpes", "du Mistral",
        "de l'Avenir", "du Soleil", "Verdun", "Gambetta", "Leclerc", "Foch", "de l'Europe", "Bellevue", "des Roses"]
PRENOMS = ["Jean", "Marie", "Kevin", "Sarah", "Lucas", "Léa", "Thomas", "Chloé", "Nicolas", "Emma", "Julien", "Inès",
           "Hugo", "Camille", "Antoine", "Manon", "Paul", "Clara", "Mathieu", "Zoé"]
NOMS = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau", "Simon",
        "Laurent", "Lefebvre", "Michel", "Garcia"]
DEPARTEMENTS = ["Compta", "RH", "IT", "Marketing", "Logistique", "Ventes", "Direction", "Accueil", "Sécurité",
                "Support"]
TEMPS = ["à l'instant", "il y a 2 minutes", "en ce moment", "depuis 10 minutes", "ça vient d'arriver", "juste là",
         "immédiatement"]

# --- 1. MÉDICAL (150 000) ---
MED_ACTIONS = [
    ("a une douleur thoracique", 4, 4), ("est tombé et ne bouge plus", 3, 4),
    ("saigne énormément", 4, 4), ("est en train de s'étouffer", 4, 4),
    ("a une forte fièvre", 2, 3), ("a mal au ventre", 1, 2),
    ("s'est cassé le bras", 2, 3), ("a fait une réaction allergique", 3, 4),
    ("a perdu connaissance", 4, 4), ("a une coupure au visage", 2, 2),
    ("semble faire un AVC", 4, 4), ("a une entorse sévère", 1, 2)
]


def gen_med():
    return (
        f"{random.choice(EMOTIONS)}{random.choice(['Mon fils', 'Mon mari', 'Ma femme', 'Moi', 'Un ami'])} ({random.choice(PRENOMS)} {random.choice(NOMS)}, {random.randint(1, 95)} ans) {random.choice(MED_ACTIONS)[0]} au {random.randint(1, 999)} rue {random.choice(RUES)} {random.choice(TEMPS)}",
        "MÉDICAL", *random.choice(MED_ACTIONS)[1:])


# --- 2. POLICE (150 000) ---
POL_ACTIONS = [
    ("braquage en cours", 4, 4), ("agression physique", 3, 4),
    ("cambriolage", 2, 3), ("individu suspect", 1, 2),
    ("violences conjugales", 4, 4), ("vol à la tire", 2, 2),
    ("menace de mort", 3, 4), ("intrusion illégale", 3, 3)
]


def gen_pol():
    act = random.choice(POL_ACTIONS)
    arme = random.choice(
        ["", " avec un couteau", " il est armé", " ils ont des pistolets", " avec une batte", " sans arme visible"])
    return (
        f"{random.choice(EMOTIONS)}{act[0]} au {random.randint(1, 999)} rue {random.choice(RUES)}{arme} {random.choice(TEMPS)}",
        "POLICE", act[1], act[2])


# --- 3. POMPIER (100 000) ---
POM_ACTIONS = [
    ("incendie d'appartement", 4, 4), ("odeur de gaz suspecte", 3, 4),
    ("accident de voiture", 3, 4), ("départ de feu", 2, 3),
    ("inondation massive", 2, 2), ("explosion", 4, 4),
    ("fumée épaisse", 2, 3), ("ascenseur bloqué", 1, 2)
]


def gen_pom():
    act = random.choice(POM_ACTIONS)
    details = random.choice(["", " au 2ème étage", " dans le garage", " des gens crient", " ça brûle vite"])
    return (f"{random.choice(EMOTIONS)}{act[0]} au {random.randint(1, 999)} rue {random.choice(RUES)}{details}",
            "POMPIER", act[1], act[2])


# --- 4. TECHNIQUES (300 000) ---
# On multiplie les variables pour éviter les doublons techniques
TECH_OBJETS = [
    ("serveur", "INFRA", 4, 4), ("ordinateur", "MATÉRIEL", 1, 1),
    ("routeur", "INFRA", 3, 2), ("session", "ACCÈS", 2, 2),
    ("VPN", "ACCÈS", 3, 3), ("imprimante", "MATÉRIEL", 1, 2),
    ("base de données", "INFRA", 4, 3), ("compte mail", "ACCÈS", 2, 2)
]


def gen_tech():
    obj, dom, imp, urg = random.choice(TECH_OBJETS)
    err = f"code {random.randint(100, 999)}" if random.random() > 0.5 else f"erreur {random.choice(['système', 'fatale', 'inconnue', 'réseau'])}"
    return (
        f"Bonjour, {obj} du service {random.choice(DEPARTEMENTS)} {random.choice(['bloqué', 'HS', 'en panne', 'ne répond plus'])} ({err}) au bureau {random.randint(1, 999)}",
        dom, imp, urg)


# --- BOUCLE DE GÉNÉRATION ---
def run_massive_forge_v15():
    dataset = []
    print("⏳ Création des 600 000 tickets...")

    tasks = [(gen_med, 150000), (gen_pol, 150000), (gen_pom, 100000), (gen_tech, 300000)]

    for func, count in tasks:
        print(f"   -> Génération {count} tickets...")
        for _ in range(count):
            dataset.append(func())

    df = pd.DataFrame(dataset, columns=["texte", "domaine", "impact", "urgence"])

    print("🧹 Suppression des doublons...")
    df = df.drop_duplicates(subset=['texte'])

    final_count = len(df)
    print(f"✅ Forge V15 terminée : {final_count} tickets UNIQUES générés.")

    # Sauvegarde
    os.makedirs("../datasets", exist_ok=True)
    df.to_csv("../datasets/nexus_massive_dataset.csv", index=False)

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("tickets_domaines", conn, if_exists="replace", index=False)
    print(f"💾 Base SQLite {DB_PATH} mise à jour.")


if __name__ == "__main__":
    run_massive_forge_v15()