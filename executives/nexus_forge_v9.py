# nexus_forge_v10.py (anciennement v9)
import pandas as pd
import sqlite3
import joblib
import os
import warnings
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder
from nexus_config import DB_PATH, MODEL_PATH, RF_PARAMS

warnings.filterwarnings("ignore")


def entrainer_modele():
    print("🚀 DÉMARRAGE DE L'ENTRAÎNEMENT DU MODÈLE NEXUS V10...")

    if not os.path.exists(DB_PATH):
        print(f"❌ La base de données {DB_PATH} n'existe pas. Lancez d'abord data_forge.py.")
        return

    print("📊 Extraction des données depuis la base SQLite...")
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT details_ticket AS texte, domaine_cible AS domaine FROM tickets", conn)

    # Nettoyage : retirer les tickets vides ou mal formés
    df = df.dropna(subset=['texte', 'domaine'])
    df = df[df['texte'].str.len() > 5]

    print(f"📚 {len(df)} tickets validés pour l'apprentissage.")
    print("📈 Répartition par domaine :")
    print(df['domaine'].value_counts())

    print("\n⚙️ Création du Pipeline (Compréhension sémantique + Random Forest)...")
    # On utilise ton encodeur TextEncoder qui charge mpnet-base-v2
    pipeline = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    print("🧠 Entraînement en cours (cela peut prendre quelques minutes)...")
    pipeline.fit(df['texte'], df['domaine'])

    print("\n💾 Sauvegarde du Cerveau...")
    # Assurer que le dossier de destination existe
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    joblib.dump(pipeline, MODEL_PATH)
    print(f"✅ MODÈLE SAUVEGARDÉ AVEC SUCCÈS : {MODEL_PATH}")


if __name__ == "__main__":
    entrainer_modele()