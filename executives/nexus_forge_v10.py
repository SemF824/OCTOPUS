# nexus_forge_v10.py
import joblib
import sqlite3
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from nexus_core import TextEncoder
from nexus_config import *


def entrainer_v10():
    conn = sqlite3.connect(DB_PATH)

    # --- 1. Entraînement Domaine (Multi-Label) ---
    print("🧠 Entraînement du modèle Domaine Multi-Label...")
    df_d = pd.read_sql("SELECT * FROM tickets_domaines", conn)

    # Transformation des labels pour le Multi-Label
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(df_d['domaine'].str.split(','))

    model_domain = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', MultiOutputClassifier(RandomForestClassifier(**RF_PARAMS)))
    ])
    model_domain.fit(df_d['texte'], y)
    model_domain.mlb = mlb  # On garde le binarizer
    joblib.dump(model_domain, MODEL_PATH)

    # --- 2. Entraînement Friction (Binaire) ---
    print("⚖️ Entraînement du modèle Friction (Complétude)...")
    df_f = pd.read_sql("SELECT * FROM tickets_friction", conn)

    model_friction = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])
    model_friction.fit(df_f['texte'], df_f['label'])
    joblib.dump(model_friction, MODEL_FRICTION_PATH)

    print("✅ V10 terminée. Deux cerveaux créés.")


if __name__ == "__main__":
    entrainer_v10()