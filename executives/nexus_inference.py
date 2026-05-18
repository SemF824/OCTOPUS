# nexus_inference.py
import joblib
import pandas as pd
import os
import numpy as np
import warnings

warnings.filterwarnings("ignore")

# Chemins adaptés à la sortie Kaggle (Place les fichiers dans le même dossier ou ajuste le chemin)
CSV_PATH = "../nexus_dataset_v33_premium.csv"
MODEL_PATH = "../pickle_result/nexus_v33_unified.pkl"
AUDIT_DIR = "../audit"


def run_full_audit():
    print("==================================================")
    print("🚀 INITIALISATION DE L'AUDIT COMPLET NEXUS V33")
    print("==================================================")

    if not os.path.exists(MODEL_PATH):
        print(f"❌ Modèle introuvable : {MODEL_PATH}")
        return

    if not os.path.exists(CSV_PATH):
        print(f"❌ Dataset introuvable : {CSV_PATH}")
        return

    print("\n🧠 Chargement du cerveau unifié V33...")
    model_unified = joblib.load(MODEL_PATH)

    print(f"📊 Chargement des données de test ({CSV_PATH})...")
    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=['texte', 'domaine', 'severite', 'impact', 'cible', 'friction'])

    # On audite un échantillon robuste
    df_audit = df.sample(n=min(2500, len(df)), random_state=42).copy()

    print(f"\n⚙️ Évaluation de {len(df_audit)} interactions (Multi-Cibles)...")

    # Prédiction unifiée (le modèle renvoie un array 2D avec les 5 prédictions d'un coup)
    X = df_audit['texte'].astype(str)
    y_true = df_audit[['domaine', 'severite', 'impact', 'cible', 'friction']].astype(str).values
    y_pred = model_unified.predict(X)

    colonnes = ['domaine', 'severite', 'impact', 'cible', 'friction']
    erreurs_indices = set()

    for i, col in enumerate(colonnes):
        acc = np.mean(y_true[:, i] == y_pred[:, i]) * 100
        print(f"🎯 Précision {col.upper():<10} : {acc:.2f} %")

        # Identifier les lignes avec des erreurs pour cette colonne
        err_mask = y_true[:, i] != y_pred[:, i]
        for idx in np.where(err_mask)[0]:
            erreurs_indices.add(idx)

    # Extraction chirurgicale des erreurs pour analyse
    erreurs_list = list(erreurs_indices)
    df_erreurs = df_audit.iloc[erreurs_list].copy()

    # Ajout des colonnes de prédiction pour comparer avec la vérité
    for i, col in enumerate(colonnes):
        df_erreurs[f'pred_{col}'] = y_pred[erreurs_list, i]

    os.makedirs(AUDIT_DIR, exist_ok=True)
    audit_file = os.path.join(AUDIT_DIR, 'audit_erreurs_v33.csv')
    df_erreurs.to_csv(audit_file, index=False)

    print(f"\n💾 {len(df_erreurs)} tickets présentant au moins UNE erreur ont été isolés.")
    print(f"👉 Fichier généré : {audit_file}")
    print(
        "💡 Analyse ce fichier. Si le modèle confond souvent 'POLICE' et 'SERVICES URBAINS', tu sauras où réentraîner.")


if __name__ == "__main__":
    run_full_audit()