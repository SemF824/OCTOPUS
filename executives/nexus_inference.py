# nexus_inference.py
import joblib
import pandas as pd
import sqlite3
import os
import numpy as np
from nexus_core import TextEncoder  # Requis pour le chargement des modèles
from nexus_config import DB_PATH, MODEL_PATH, MODEL_FRICTION_PATH


def run_full_audit():
    print("==================================================")
    print("🚀 INITIALISATION DE L'AUDIT COMPLET NEXUS V12")
    print("==================================================")

    if not os.path.exists(MODEL_PATH) or not os.path.exists(MODEL_FRICTION_PATH):
        print(f"❌ Les modèles sont introuvables. Vérifiez les chemins dans nexus_config.py.")
        return

    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données {DB_PATH} introuvable. Avez-vous importé les résultats de Kaggle ?")
        return

    print("\n🧠 Chargement des cerveaux V12...")
    model_unified = joblib.load(MODEL_PATH)
    model_friction = joblib.load(MODEL_FRICTION_PATH)

    print(f"📊 Connexion à la base de données de test ({DB_PATH})...")
    conn = sqlite3.connect(DB_PATH)

    # ==========================================
    # AUDIT 1 : DOMAINE ET NOTATION (Impact/Urgence)
    # ==========================================
    print("\n🔎 --- AUDIT DU CERVEAU PRINCIPAL (Domaine & Notation) ---")
    # On prélève 10 000 tickets au hasard pour le test
    df_dom = pd.read_sql("SELECT * FROM tickets_domaines ORDER BY RANDOM() LIMIT 10000", conn)

    if df_dom.empty:
        print("⚠️ Aucun ticket trouvé dans 'tickets_domaines'.")
    else:
        # Données réelles
        y_true_multi = df_dom[['domaine', 'impact', 'urgence']].values

        # Prédictions de l'IA
        print(f"⚙️ Évaluation de {len(df_dom)} tickets...")
        y_pred_multi = model_unified.predict(df_dom['texte'])

        # Calcul des précisions
        acc_domaine = np.mean(y_true_multi[:, 0] == y_pred_multi[:, 0]) * 100
        # On convertit en string au cas où il y ait des mélanges int/str
        acc_impact = np.mean(y_true_multi[:, 1].astype(str) == y_pred_multi[:, 1].astype(str)) * 100
        acc_urgence = np.mean(y_true_multi[:, 2].astype(str) == y_pred_multi[:, 2].astype(str)) * 100

        print(f"🎯 Précision DOMAINE : {acc_domaine:.2f} %")
        print(f"💥 Précision IMPACT  : {acc_impact:.2f} %")
        print(f"⏱️ Précision URGENCE : {acc_urgence:.2f} %")

        # Sauvegarde des erreurs pour analyse humaine
        df_dom['pred_domaine'] = y_pred_multi[:, 0]
        df_dom['pred_impact'] = y_pred_multi[:, 1]
        df_dom['pred_urgence'] = y_pred_multi[:, 2]

        erreurs_dom = df_dom[
            (df_dom['domaine'] != df_dom['pred_domaine']) |
            (df_dom['impact'].astype(str) != df_dom['pred_impact'].astype(str)) |
            (df_dom['urgence'].astype(str) != df_dom['pred_urgence'].astype(str))
            ]

        os.makedirs('../audit', exist_ok=True)
        erreurs_dom.to_csv('../audit/audit_erreurs_notation_v12.csv', index=False)
        print(f"💾 {len(erreurs_dom)} erreurs de tri/notation sauvegardées dans audit_erreurs_notation_v12.csv")

    # ==========================================
    # AUDIT 2 : EMPATHIE ET COMPORTEMENT (Friction)
    # ==========================================
    print("\n🗣️ --- AUDIT DU CERVEAU EMPATHIQUE (Façon de parler) ---")
    df_fric = pd.read_sql("SELECT * FROM tickets_friction ORDER BY RANDOM() LIMIT 10000", conn)

    if df_fric.empty:
        print("⚠️ Aucun ticket trouvé dans 'tickets_friction'.")
    else:
        y_true_fric = df_fric['label'].values

        print(f"⚙️ Évaluation de {len(df_fric)} interactions...")
        y_pred_fric = model_friction.predict(df_fric['texte'])

        acc_fric = np.mean(y_true_fric == y_pred_fric) * 100
        print(f"💬 Précision CHOIX DE LA QUESTION (Empathie) : {acc_fric:.2f} %")

        df_fric['pred_label'] = y_pred_fric
        erreurs_fric = df_fric[df_fric['label'] != df_fric['pred_label']]
        erreurs_fric.to_csv('../audit/audit_erreurs_questions_v12.csv', index=False)
        print(f"💾 {len(erreurs_fric)} erreurs de dialogue sauvegardées dans audit_erreurs_questions_v12.csv")

    print("\n✅ AUDIT TERMINÉ.")


if __name__ == "__main__":
    run_full_audit()