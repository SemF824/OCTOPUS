# nexus_forge_v9.py
import pandas as pd
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder
from nexus_config import MODEL_PATH, RF_PARAMS


def train():
    print("🚀 Démarrage de l'entraînement V9 (Multi-Output)...")
    DS = '../datasets'
    frames = []

    # On utilise UNIQUEMENT les fichiers générés par l'Auto-Labeler
    fichiers_base = [
        ('nexus_stress_test_5000_labeled.csv', None),
        ('dataset_tickets_acces_labeled.csv', 'ACCÈS'),
        ('dataset_tickets_acceslogin_labeled.csv', 'ACCÈS'),
        ('dataset_tickets_Infra_labeled.csv', 'INFRA'),
        ('dataset_tickets_Materiel_labeled.csv', 'MATÉRIEL'),
        ('dataset_tickets_medical_labeled.csv', 'MÉDICAL'),
        ('dataset_tickets_PoliceNationale_labeled.csv', 'POLICE'),
        ('dataset_tickets_pompiers_labeled.csv', 'POMPIER')
    ]

    for fichier, domaine_force in fichiers_base:
        chemin = f"{DS}/{fichier}"
        if os.path.exists(chemin):
            df = pd.read_csv(chemin)
            if domaine_force: df['domaine'] = domaine_force

            # Sécurité : vérifier que l'Auto-Labeler a bien fait son travail
            if 'impact' in df.columns and 'urgence' in df.columns and 'texte' in df.columns:
                frames.append(df[['texte', 'domaine', 'impact', 'urgence']])
            else:
                print(f"⚠️ Colonnes manquantes dans {fichier}, fichier ignoré.")

    if not frames:
        print("❌ Aucun fichier valide trouvé. Avez-vous lancé nexus_autolabel.py ?")
        return

    df_all = pd.concat(frames, ignore_index=True).dropna()
    print(f"\n📦 VOLUME FINAL D'ENTRAÎNEMENT : {len(df_all)} exemples")

    # --- L'IA PRÉDIT 3 CHOSES ---
    X = df_all['texte']
    y = df_all[['domaine', 'impact', 'urgence']]

    pipeline = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    print("\n⏳ Calculs en cours (L'encodeur mpnet va travailler)...")
    pipeline.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\n✅ Modèle V9 sauvegardé : {MODEL_PATH}")


if __name__ == "__main__":
    train()