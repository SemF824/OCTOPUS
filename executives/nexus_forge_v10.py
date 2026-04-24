# nexus_forge_v10.py
import joblib
import sqlite3
import pandas as pd
import os
import warnings
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from nexus_core import TextEncoder
from nexus_config import DB_PATH, MODEL_PATH, MODEL_FRICTION_PATH, RF_PARAMS

warnings.filterwarnings("ignore")


def entrainer_v10():
    print("🚀 DÉMARRAGE DE L'ENTRAÎNEMENT NEXUS V10...")

    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    # --- 1. ENTRAÎNEMENT DU MODÈLE DOMAINE (MULTI-LABEL) ---
    print("\n🧠 Entraînement du Modèle Domaine Multi-Label...")
    df_domaines = pd.read_sql("SELECT * FROM tickets_domaines", conn)
    df_domaines = df_domaines.dropna(subset=['texte', 'domaine'])

    # Binarisation des labels pour le MultiOutputClassifier
    mlb = MultiLabelBinarizer()
    y_multi = mlb.fit_transform(df_domaines['domaine'].str.split(','))

    pipeline_domain = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', MultiOutputClassifier(RandomForestClassifier(**RF_PARAMS)))
    ])

    pipeline_domain.fit(df_domaines['texte'], y_multi)
    # On sauvegarde le binarizer dans l'objet pour décoder les prédictions plus tard
    pipeline_domain.mlb = mlb

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline_domain, MODEL_PATH)
    print(f"✅ Modèle Domaine sauvegardé : {MODEL_PATH}")

    # --- 2. ENTRAÎNEMENT DU MODÈLE FRICTION (COMPLÉTUDE) ---
    print("\n⚖️ Entraînement du Modèle Friction (Complétude)...")
    df_friction = pd.read_sql("SELECT * FROM tickets_friction", conn)
    df_friction = df_friction.dropna(subset=['texte', 'label'])

    pipeline_friction = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    pipeline_friction.fit(df_friction['texte'], df_friction['label'])
    joblib.dump(pipeline_friction, MODEL_FRICTION_PATH)
    print(f"✅ Modèle Friction sauvegardé : {MODEL_FRICTION_PATH}")

    print("\n🎉 ENTRAÎNEMENT V10 TERMINÉ ! DEUX CERVEAUX CRÉÉS.")


if __name__ == "__main__":
    entrainer_v10()