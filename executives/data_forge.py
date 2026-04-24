# data_forge.py
import sqlite3
import pandas as pd
import random
import os
from nexus_config import DB_PATH, SYNERGIES_URGENCE, MOTS_LIEUX

# Préfixes pour générer la "Friction"
PREFIXES_EMPATHIE = ["", "Au secours, ", "Aidez-moi vite, ", "Je panique, ", "Urgent ! "]


def generer_friction_data(texte_complet):
    """Génère des versions tronquées d'un texte pour apprendre à l'IA ce qu'est un ticket incomplet."""
    mots = texte_complet.split()
    if len(mots) <= 4:
        return [(texte_complet, 0)]

    # Version sans la fin (souvent le lieu ou le détail technique)
    v1 = " ".join(mots[:len(mots) // 2])
    # Version sans le début (souvent l'action)
    v2 = " ".join(mots[len(mots) // 2:])
    return [(v1, 0), (v2, 0), (texte_complet, 1)]


def generer_donnees_v10():
    print("🛠️  GÉNÉRATION DE LA FORGE V10 (Multi-Label & Friction ML)...")

    domaines_data = []
    friction_data = []

    # 1. Génération des Synergies Multi-Labels
    print("🔄 Création des tickets Multi-Labels...")
    for mot_cle, labels in SYNERGIES_URGENCE.items():
        domaine_str = ",".join(labels)
        for _ in range(200):
            prefixe = random.choice(PREFIXES_EMPATHIE)
            lieu = random.choice(MOTS_LIEUX)
            if lieu: lieu = " " + lieu
            texte = f"{prefixe}il y a une {mot_cle}{lieu}"
            domaines_data.append((texte, domaine_str))

            # On en profite pour alimenter la friction
            for var_texte, label in generer_friction_data(texte):
                friction_data.append((var_texte, label))

    # 2. Importation des CSV existants (Mono-label)
    dossier_datasets = "../datasets/"
    if os.path.exists(dossier_datasets):
        print("📂 Importation des datasets CSV existants...")
        for fichier in os.listdir(dossier_datasets):
            if fichier.endswith(".csv"):
                try:
                    df_csv = pd.read_csv(os.path.join(dossier_datasets, fichier))
                    if 'texte' in df_csv.columns and 'domaine' in df_csv.columns:
                        for _, row in df_csv.iterrows():
                            t = str(row['texte'])
                            d = str(row['domaine']).upper()
                            domaines_data.append((t, d))
                            # Générer de la friction à partir des vrais tickets
                            for var_texte, label in generer_friction_data(t):
                                friction_data.append((var_texte, label))

                    elif 'Demande' in df_csv.columns and 'Domaine' in df_csv.columns:
                        for _, row in df_csv.iterrows():
                            t = str(row['Demande'])
                            d = str(row['Domaine']).upper()
                            if "POLICE" in d:
                                d = "POLICE"
                            elif "POMPIER" in d or "INCENDIE" in d:
                                d = "POMPIER"
                            elif "CIRCULATION" in d:
                                d = "POLICE"
                            domaines_data.append((t, d))
                            for var_texte, label in generer_friction_data(t):
                                friction_data.append((var_texte, label))
                except Exception as e:
                    print(f"⚠️ Erreur sur {fichier} : {e}")

    # --- Sauvegarde en Base de Données ---
    df_domaines = pd.DataFrame(domaines_data, columns=["texte", "domaine"]).drop_duplicates()
    df_friction = pd.DataFrame(friction_data, columns=["texte", "label"]).drop_duplicates()

    # Équilibrage rapide de la friction (pour avoir autant de complets que d'incomplets)
    df_friction_0 = df_friction[df_friction['label'] == 0].sample(frac=0.5, random_state=42)
    df_friction_1 = df_friction[df_friction['label'] == 1]
    df_friction_balanced = pd.concat([df_friction_0, df_friction_1]).sample(frac=1).reset_index(drop=True)

    with sqlite3.connect(DB_PATH) as conn:
        df_domaines.to_sql("tickets_domaines", conn, if_exists="replace", index=False)
        df_friction_balanced.to_sql("tickets_friction", conn, if_exists="replace", index=False)

    print(f"✅ Forge V10 terminée :")
    print(f"   - Modèle Domaines : {len(df_domaines)} tickets.")
    print(f"   - Modèle Friction : {len(df_friction_balanced)} tickets.")


if __name__ == "__main__":
    generer_donnees_v10()