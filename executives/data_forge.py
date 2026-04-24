# data_forge.py
import sqlite3
import pandas as pd
import random
import os

DB_PATH = "../nexus_bionexus.db"

# --- Briques de construction pour des tickets "Humains" ---
PREFIXES_EMPATHIE = [
    "", "", "",  # Beaucoup de tickets restent neutres
    "Au secours, ", "Aidez-moi vite, ", "Je panique, ", "C'est affreux, ",
    "S'il vous plaît faites vite, ", "Je vous en supplie, ", "Urgent ! "
]

LIEUX = [
    "", "",  # Parfois les gens oublient le lieu
    " au 3ème étage", " dans la rue", " sur le parking", " à la mairie",
    " dans l'école", " au centre commercial", " sur l'autoroute", " chez moi"
]

# --- Templates de base par domaine ---
TEMPLATES_BASE = {
    "MÉDICAL": [
        "je saigne beaucoup du bras", "ma femme a fait un malaise",
        "douleur atroce à la poitrine", "il est inconscient et ne respire plus",
        "coupure profonde au doigt", "j'ai la jambe cassée"
    ],
    "POMPIER": [
        "il y a le feu", "énormément de fumée noire sort du toit",
        "ça sent très fort le gaz", "les flammes se propagent",
        "il y a eu une grosse explosion", "accident de voiture grave, quelqu'un est coincé"
    ],
    "POLICE": [
        "un homme nous menace avec un couteau", "il y a des individus louches qui rodent",
        "quelqu'un essaie de forcer ma porte", "on m'a volé mon sac avec violence",
        "mon mari me frappe", "braquage en cours"
    ],
    "INFRA": [
        "le serveur de base de données est en panne", "coupure générale du réseau",
        "le routeur principal a cramé", "latence énorme sur le datacenter"
    ],
    "MATÉRIEL": [
        "mon pc est tombé par terre et l'écran est cassé", "la souris ne marche plus",
        "le clavier est bloqué", "l'imprimante fait un bruit bizarre"
    ],
    "ACCÈS": [
        "j'ai oublié mon mot de passe", "mon accès VPN est refusé",
        "compte verrouillé", "impossible de me connecter au logiciel RH"
    ]
}

# --- Événements Multi-Forces (Synergies) ---
# Ces tickets vont apprendre à l'IA les mots-clés ultimes
SYNERGIES = [
    ("fusillade en cours, plusieurs personnes à terre", "POLICE"),
    ("il y a un tireur fou, des gens saignent", "POLICE"),
    ("gros accident de bus, il y a le feu et des blessés graves", "POMPIER"),
    ("homme armé d'un fusil, il vient de tirer", "POLICE"),
    ("suicide, il s'est jeté par la fenêtre", "MÉDICAL"),
    ("incendie dans un grand immeuble, des gens sont coincés", "POMPIER")
]


def generer_donnees_v10():
    print("🛠️  GÉNÉRATION DE LA FORGE V10 (Empathie, Lieux & Synergies)...")
    donnees = []

    # 1. Génération des tickets standards (Avec variations humaines)
    for domaine, phrases in TEMPLATES_BASE.items():
        for phrase_base in phrases:
            # On génère 300 variantes de chaque phrase
            for _ in range(300):
                prefixe = random.choice(PREFIXES_EMPATHIE)
                lieu = random.choice(LIEUX)
                ticket_complet = f"{prefixe}{phrase_base}{lieu}"
                donnees.append((ticket_complet, domaine))

    # 2. Génération massive des Synergies (Pour forcer l'apprentissage des Red Flags)
    for phrase_syn, domaine in SYNERGIES:
        for _ in range(500):  # Poids très lourd pour ces événements vitaux
            prefixe = random.choice(PREFIXES_EMPATHIE)
            lieu = random.choice(LIEUX)
            ticket_complet = f"{prefixe}{phrase_syn}{lieu}"
            donnees.append((ticket_complet, domaine))

    # 3. Ajout de tes datasets CSV existants s'ils sont dans le dossier
    dossier_datasets = "../datasets/"
    if os.path.exists(dossier_datasets):
        print("📂 Importation des datasets CSV existants...")
        for fichier in os.listdir(dossier_datasets):
            if fichier.endswith(".csv"):
                try:
                    df_csv = pd.read_csv(os.path.join(dossier_datasets, fichier))
                    # On suppose que tes CSV ont des colonnes 'texte' et 'domaine' ou 'Sujets', 'Demande', 'Domaine'
                    if 'texte' in df_csv.columns and 'domaine' in df_csv.columns:
                        for _, row in df_csv.iterrows():
                            donnees.append((str(row['texte']), str(row['domaine']).upper()))
                    elif 'Demande' in df_csv.columns and 'Domaine' in df_csv.columns:
                        for _, row in df_csv.iterrows():
                            # Nettoyage rapide des domaines pour coller à ta norme
                            dom = str(row['Domaine']).upper()
                            if "POLICE" in dom:
                                dom = "POLICE"
                            elif "POMPIER" in dom or "INCENDIE" in dom:
                                dom = "POMPIER"
                            elif "CIRCULATION" in dom:
                                dom = "POLICE"
                            donnees.append((str(row['Demande']), dom))
                except Exception as e:
                    print(f"⚠️ Impossible de lire {fichier} : {e}")

    # --- Sauvegarde en Base de Données ---
    df_final = pd.DataFrame(donnees, columns=["details_ticket", "domaine_cible"])

    # Mélange des données pour l'entraînement
    df_final = df_final.sample(frac=1).reset_index(drop=True)

    with sqlite3.connect(DB_PATH) as conn:
        df_final.to_sql("tickets", conn, if_exists="replace", index=False)

    print(f"✅ Forge V10 terminée : {len(df_final)} tickets générés et importés dans la base de données.")


if __name__ == "__main__":
    generer_donnees_v10()