# nexus_forge_v8.py
import pandas as pd
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder
from nexus_config import MODEL_PATH, RF_PARAMS


def train():
    print("🚀 Démarrage de l'entraînement V8.1 (Local)...")
    DS = '../datasets'  # Ton dossier local contenant les CSV
    frames = []

    print("📂 Ingurgitation des données...")

    # Liste de tous tes datasets avec le domaine forcé associé
    fichiers = [
        ('nexus_stress_test_5000.csv', None),  # Contient déjà la colonne 'domaine'
        ('nexus_medical_3000.csv', None),  # À renommer ci-dessous
        ('nexus_urgences_priorises.csv', None),  # À renommer ci-dessous
        ('dataset_tickets_acces.csv', 'ACCÈS'),
        ('dataset_tickets_acceslogin.csv', 'ACCÈS'),
        ('dataset_tickets_Infra.csv', 'INFRA'),
        ('dataset_tickets_Materiel.csv', 'MATÉRIEL'),
        ('dataset_tickets_medical.csv', 'MÉDICAL'),
        ('dataset_tickets_PoliceNationale.csv', 'POLICE'),
        ('dataset_tickets_pompiers.csv', 'POMPIER')
    ]

    for fichier, domaine_force in fichiers:
        chemin = f"{DS}/{fichier}"
        if not os.path.exists(chemin):
            print(f"⚠️ Ignoré : {fichier} introuvable.")
            continue

        df = pd.read_csv(chemin)

        # Standardisation des colonnes selon le fichier
        if 'Demande' in df.columns:
            df = df.rename(columns={'Demande': 'texte'})
        if 'ticket_fr' in df.columns:
            df = df.rename(columns={'ticket_fr': 'texte', 'domaine_cible': 'domaine'})
        if 'label' in df.columns:
            df = df.rename(columns={'label': 'domaine'})

        # Forçage du domaine si demandé
        if domaine_force:
            df['domaine'] = domaine_force

        if 'texte' in df.columns and 'domaine' in df.columns:
            frames.append(df[['texte', 'domaine']])
            print(f"✔️ {fichier[:20]:<20} ajouté.")

    # --- DONNÉES SYNTHÉTIQUES (Correction des trous de mémoire) ---
    vaccins = [
        ('POMPIER',
         ['incendie dans l\'immeuble', 'feu de forêt', 'fuite de gaz détectée', 'explosion au rez-de-chaussée']),
        ('POLICE',
         ['agression dans la rue', 'cambriolage', 'vol de voiture', 'individu armé', 'braquage', 'rodéo urbain']),
    ]
    vacc_rows = [{'texte': p, 'domaine': d} for d, phrases in vaccins for p in phrases for _ in range(100)]
    frames.append(pd.DataFrame(vacc_rows))

    # --- ASSEMBLAGE ---
    df_all = pd.concat(frames, ignore_index=True).dropna(subset=['texte', 'domaine'])
    print(f"\n📦 VOLUME FINAL : {len(df_all)} exemples")

    # --- ENTRAÎNEMENT ---
    pipeline = Pipeline([
        ('vectorizer', TextEncoder(model_name='paraphrase-multilingual-mpnet-base-v2')),
        ('classifier', RandomForestClassifier(**RF_PARAMS))
    ])

    print("\n⏳ Calculs en cours (L'encodeur mpnet va travailler)...")
    pipeline.fit(df_all['texte'], df_all['domaine'])

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\n✅ Modèle local sauvegardé et prêt : {MODEL_PATH}")


if __name__ == "__main__":
    train()