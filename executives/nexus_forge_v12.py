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
    print("🚀 DÉMARRAGE DE L'ENTRAÎNEMENT NEXUS V12...")

    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    # --- 1. MODÈLE DOMAINE / IMPACT / URGENCE ---
    print("\n🧠 Entraînement du Modèle Principal...")
    df_dom = pd.read_sql("SELECT * FROM tickets_domaines", conn).dropna()

    # LA CORRECTION EST ICI : On force tout en string pour éviter le crash int/str
    y_multi = df_dom[['domaine', 'impact', 'urgence']].astype(str).values

    pipeline_domain = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', MultiOutputClassifier(RandomForestClassifier(**RF_PARAMS)))
    ])

    print(f"⚙️  Analyse de {len(df_dom)} tickets (cela peut prendre quelques minutes)...")
    pipeline_domain.fit(df_dom['texte'], y_multi)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline_domain, MODEL_PATH)
    print(f"✅ Modèle Principal sauvegardé.")

    # --- 2. MODÈLE FRICTION (QUESTIONS) ---
    print("\n⚖️ Entraînement du Modèle de Qualification (Friction)...")
    df_fric = pd.read_sql("SELECT * FROM tickets_friction", conn).dropna()

    # On force aussi en string par sécurité
    y_fric = df_fric['label'].astype(str)

    pipeline_friction = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    pipeline_friction.fit(df_fric['texte'], y_fric)
    joblib.dump(pipeline_friction, MODEL_FRICTION_PATH)
    print(f"✅ Modèle Friction sauvegardé.")

    print("\n🎉 NEXUS V12 EST MAINTENANT PRÊT !")


if __name__ == "__main__":
    entrainer_v12()