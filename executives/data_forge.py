# nexus_forge.py
import pandas as pd
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder
from nexus_config import MODEL_PATH, RF_PARAMS


def train():
    print("🚀 Entraînement NEXUS V9 Multi-Output...")
    chemin_ds = "../datasets/nexus_massive_dataset.csv"

    if not os.path.exists(chemin_ds):
        print("❌ Dataset introuvable. Lancez nexus_dataset_generator.py")
        return

    df = pd.read_csv(chemin_ds)

    # On apprend à prédire le Domaine, l'Impact ET l'Urgence
    X = df['texte']
    y = df[['domaine', 'impact', 'urgence']]

    pipeline = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    pipeline.fit(X, y)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"✅ IA Entraînée et sauvegardée : {MODEL_PATH}")


if __name__ == "__main__":
    train()