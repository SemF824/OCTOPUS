# nexus_forge_v9.py
import pandas as pd
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder
from nexus_config import MODEL_PATH, RF_PARAMS


def train():
    print("🚀 Démarrage de l'entraînement V9 (Correction des Biais)...")
    DS = '../datasets'  # Dossier des datasets d'entraînement
    AUDIT_DIR = '../audit'  # Dossier des fichiers d'audit
    frames = []

    # 1. Chargement de tes datasets de base
    fichiers_base = [
        ('nexus_stress_test_5000.csv', None),
        ('dataset_tickets_acces.csv', 'ACCÈS'),
        ('dataset_tickets_acceslogin.csv', 'ACCÈS'),
        ('dataset_tickets_Infra.csv', 'INFRA'),
        ('dataset_tickets_Materiel.csv', 'MATÉRIEL'),
        ('dataset_tickets_medical.csv', 'MÉDICAL'),
        ('dataset_tickets_PoliceNationale.csv', 'POLICE'),
        ('dataset_tickets_pompiers.csv', 'POMPIER')
    ]

    for fichier, domaine_force in fichiers_base:
        chemin = f"{DS}/{fichier}"
        if os.path.exists(chemin):
            df = pd.read_csv(chemin)
            if 'Demande' in df.columns: df = df.rename(columns={'Demande': 'texte'})
            if domaine_force: df['domaine'] = domaine_force
            if 'texte' in df.columns and 'domaine' in df.columns:
                frames.append(df[['texte', 'domaine']])

    # 2. Chargement du nouveau dataset de 17 500 lignes généré
    if os.path.exists(f"{DS}/nexus_renfort_15000_complet.csv"):
        print("💉 Injection du sérum de renfort (17 500 tickets ciblés)...")
        df_renfort = pd.read_csv(f"{DS}/nexus_renfort_15000_complet.csv")
        frames.append(df_renfort)

    # 3. APPRENTISSAGE PAR L'ERREUR (Le fichier d'audit V5)
    fichier_audit = f"{AUDIT_DIR}/audit_erreurs_nexus_v5.csv"
    if os.path.exists(fichier_audit):
        print("🧑‍🏫 Apprentissage à partir du fichier d'audit...")
        df_audit = pd.read_csv(fichier_audit)
        # On ne garde que les erreurs (correct == False)
        if 'correct' in df_audit.columns:
            erreurs = df_audit[df_audit['correct'] == False][['texte', 'domaine']]
            # On multiplie ces erreurs par 20 pour que l'IA soit OBLIGÉE de les retenir
            frames.append(pd.concat([erreurs] * 20, ignore_index=True))
        else:
            print(f"⚠️ Attention : Fichier d'audit introuvable à l'emplacement {fichier_audit}")

    # --- ASSEMBLAGE ---
    df_all = pd.concat(frames, ignore_index=True).dropna(subset=['texte', 'domaine'])
    print(f"\n📦 VOLUME FINAL D'ENTRAÎNEMENT : {len(df_all)} exemples")

    # --- ENTRAÎNEMENT ---
    pipeline = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    print("\n⏳ Calculs en cours (L'encodeur mpnet va travailler)...")
    pipeline.fit(df_all['texte'], df_all['domaine'])

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\n✅ Modèle local V9 sauvegardé et prêt : {MODEL_PATH}")


if __name__ == "__main__":
    train()