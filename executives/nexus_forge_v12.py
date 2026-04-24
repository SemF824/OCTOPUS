# nexus_forge_v12.py
import joblib
import sqlite3
import pandas as pd
import os
import warnings
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from nexus_core import TextEncoder
from nexus_config import DB_PATH, MODEL_PATH, MODEL_FRICTION_PATH, RF_PARAMS

warnings.filterwarnings("ignore")


def entrainer_v12():
    print("🚀 ENTRAÎNEMENT NEXUS V12...")
    conn = sqlite3.connect(DB_PATH)

    print("\n🧠 Modèle Multi-Output (Domaine, Impact, Urgence)...")
    df_dom = pd.read_sql("SELECT * FROM tickets_domaines", conn).dropna()
    y_multi = df_dom[['domaine', 'impact', 'urgence']].values

    pipeline_domain = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', MultiOutputClassifier(RandomForestClassifier(**RF_PARAMS)))
    ])
    pipeline_domain.fit(df_dom['texte'], y_multi)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline_domain, MODEL_PATH)

    print("\n⚖️ Modèle Friction (Classifieur de Questions)...")
    df_fric = pd.read_sql("SELECT * FROM tickets_friction", conn).dropna()

    pipeline_friction = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])
    # Entraînement sur les Labels Textuels (ex: DEMANDE_LIEU)
    pipeline_friction.fit(df_fric['texte'], df_fric['label'])
    joblib.dump(pipeline_friction, MODEL_FRICTION_PATH)

    print("✅ ENTRAÎNEMENT V12 TERMINÉ !")


if __name__ == "__main__":
    entrainer_v12()