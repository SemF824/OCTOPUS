# executives/nexus_dialogue_forge.py
import pandas as pd
import joblib
import os
import warnings
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder
from nexus_config import MODEL_DIALOGUE_PATH

warnings.filterwarnings("ignore")

DATASET_PATH = "../datasets/nexus_15000_dialogue_expert.csv"

def entrainer_cerveau_dialogue():
    print(f"📥 1. Chargement du dataset de Dialogue depuis {DATASET_PATH}...")
    if not os.path.exists(DATASET_PATH):
        print("❌ Fichier introuvable. Place le fichier CSV dans le dossier 'datasets'.")
        return

    df = pd.read_csv(DATASET_PATH)

    print(f"⚙️ 2. Préparation de l'entraînement du Cerveau de Dialogue sur {len(df)} lignes...")
    X = df['texte']
    # Ce cerveau ne s'occupe QUE du statut de la conversation (MANQUE_LIEU, MANQUE_CORPS, COMPLET...)
    y = df['statut_friction']

    pipeline = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', RandomForestClassifier(
            n_estimators=300,
            max_depth=30,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    print("🧠 3. Apprentissage de l'art de poser des questions (patientez)...")
    pipeline.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_DIALOGUE_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_DIALOGUE_PATH)
    print(f"✅ Terminé ! Le Cerveau de Dialogue est sauvegardé sous : {MODEL_DIALOGUE_PATH}")

if __name__ == "__main__":
    entrainer_cerveau_dialogue()