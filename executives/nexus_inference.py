import joblib
import pandas as pd
import os
from nexus_core import TextEncoder  # <-- REQUIS POUR LE DÉPICKLAGE


def run_nexus_audit(model_file, test_file):
    print("\n🚀 INITIALISATION NEXUS V5.0 AUDIT")

    if not os.path.exists(model_file) or not os.path.exists(test_file):
        print("❌ Fichiers manquants.")
        return

    print("🧠 Chargement du cerveau unifié...")
    # Grâce à l'import de TextEncoder, joblib ne sera plus perdu
    model = joblib.load(model_file)

    print("📊 Lecture du Stress-Test...")
    df = pd.read_csv(test_file).drop_duplicates(subset=['texte'])

    print(f"⚙️ Analyse de {len(df)} cas uniques...")
    predictions = model.predict(df['texte'])

    df['prediction_nexus'] = predictions
    df['resultat'] = df['prediction_nexus'] == df['domaine']

    accuracy = (df['resultat'].sum() / len(df)) * 100
    print(f"✅ AUDIT TERMINÉ. PRÉCISION : {accuracy:.2f}%")

    # Sauvegarde des erreurs pour analyse
    df[df['resultat'] == False].to_csv('../audit/audit_erreurs_nexus_v5.csv', index=False)


if __name__ == "__main__":
    run_nexus_audit('../pickle_result/nexus_v8.1_extended.pkl', '../datasets/nexus_stress_test_5000.csv')
