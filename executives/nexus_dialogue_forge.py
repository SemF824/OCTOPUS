# executives/nexus_dialogue_forge.py
import pandas as pd
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder

DATASET_PATH = "../datasets/nexus_dialogue_funnel.csv"
MODEL_DIALOGUE_PATH = "../pickle_result/nexus_v32_dialogue.pkl"

def entrainer_cerveau_dialogue():
    print(f"📥 Chargement de {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)

    X = df['texte_conversation']
    y = df['prochaine_question']

    pipeline = Pipeline([
        ('vectorizer', TextEncoder()),
        ('classifier', RandomForestClassifier(n_estimators=200, max_depth=30, random_state=42, n_jobs=-1))
    ])

    print("🧠 Entraînement de l'Entonnoir Conversationnel...")
    pipeline.fit(X, y)

    joblib.dump(pipeline, MODEL_DIALOGUE_PATH)
    print(f"✅ Modèle sauvegardé sous : {MODEL_DIALOGUE_PATH}")

if __name__ == "__main__":
    entrainer_cerveau_dialogue()