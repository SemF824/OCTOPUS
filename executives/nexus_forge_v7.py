import pandas as pd
import sqlite3
import joblib
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from nexus_core import TextEncoder

DB_PATH = "nexus_bionexus.db"

print("📊 Chargement de TOUS les domaines depuis la DB...")
# Charge les données synthétiques (tous domaines confondus)
with sqlite3.connect(DB_PATH) as conn:
    df_db = pd.read_sql(
        "SELECT details_ticket AS texte, domaine_cible AS domaine FROM tickets",
        conn
    )

# Charge le dataset médical traduit
df_med = pd.read_csv('medDataset_processed.csv')[['texte', 'domaine']]

# ── VACCINATION ANTI-BIAIS MATÉRIEL ──────────────────────────────────────
# "souris" = périphérique informatique, pas un animal médical
anti_biais_materiel = pd.DataFrame({
    'texte': [
        'ma souris ne fonctionne plus',
        'problème avec ma souris sans fil',
        'la souris de mon PC est cassée',
        'clic gauche de la souris ne répond pas',
        'souris bluetooth déconnectée',
        'j\'ai un problème avec ma souris',
        'ma souris USB ne clique plus',
        'le curseur de ma souris saute partout',
    ],
    'domaine': ['MATÉRIEL'] * 8
})

anti_biais_infra = pd.DataFrame({
    'texte': [
        'Latence réseau critique sur le serveur',
        'Panne critique du routeur de l\'étage 4',
        'Alerte infra critique : stockage plein',
        'Le pare-feu affiche une erreur critique',
    ],
    'domaine': ['INFRA'] * 4
})

# ── FUSION ÉQUILIBRÉE ─────────────────────────────────────────────────────
# Plafonne MÉDICAL pour éviter qu'il écrase les autres classes
df_med_cap = df_med.sample(
    n=min(len(df_med), len(df_db) // 4),  # max 25% du dataset total
    random_state=42
)

df_final = pd.concat(
    [df_db, df_med_cap, anti_biais_materiel, anti_biais_infra],
    ignore_index=True
)

# Vérification de l'équilibre
print("\n📊 Distribution finale :")
print(df_final['domaine'].value_counts().to_string())

# ── PIPELINE ──────────────────────────────────────────────────────────────
nexus_pipeline = Pipeline([
    ('vectorizer', TextEncoder()),
    ('classifier', RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        class_weight='balanced',  # Compense les déséquilibres résiduels
        random_state=42,
        n_jobs=-1
    ))
])

print(f"\n🧠 Apprentissage sur {len(df_final)} exemples...")
nexus_pipeline.fit(df_final['texte'], df_final['domaine'])

joblib.dump(nexus_pipeline, 'nexus_v5_pipeline.pkl')
print("✅ NEXUS V5.0 RÉEL FORGÉ.")
