# executives/nexus_3d_viz.py
import pandas as pd
import joblib
import plotly.express as px
from sklearn.manifold import TSNE
from sklearn.decomposition import TruncatedSVD
import warnings
import os

warnings.filterwarnings("ignore")

# --- 1. CONFIGURATION ---
# Assure-toi que ces fichiers sont bien présents dans tes dossiers locaux
CSV_PREMIUM = "../datasets/nexus_dataset_v33_premium.csv"
CSV_HARDCORE = "../datasets/nexus_dataset_v34_hardcore.csv"
CSV_AUDIT = "../audit/audit_corrections_expert.csv"

# Le modèle V35 que tu as téléchargé depuis Kaggle
MODEL_PATH = "../pickle_result/nexus_modele_final_V35.pkl"
SAMPLE_SIZE = 3000  # Limite optimisée pour voir le mix sans saturer la RAM

print("🔍 1. Chargement de l'encodeur TF-IDF depuis le modèle final...")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"❌ Modèle introuvable : {MODEL_PATH}")

pipeline = joblib.load(MODEL_PATH)
encodeur = pipeline.named_steps['tfidf']

print("📂 2. Extraction, fusion et taggage des datasets...")
dataframes = []

def charger_dataset(chemin, tag_source):
    """Charge un CSV, ignore les lignes corrompues, et taggue la provenance."""
    if os.path.exists(chemin):
        try:
            df_temp = pd.read_csv(chemin, on_bad_lines='skip')
            df_temp = df_temp.dropna(subset=['texte', 'domaine'])
            df_temp['Source'] = tag_source # Injection de la métadonnée de traçabilité
            print(f"   ✅ {tag_source:<15} : {len(df_temp)} tickets chargés.")
            return df_temp
        except Exception as e:
            print(f"   ❌ Erreur sur {chemin} : {e}")
    else:
        print(f"   ⚠️ Fichier introuvable (ignoré) : {chemin}")
    return None

df_prem = charger_dataset(CSV_PREMIUM, "Premium (V33)")
df_hard = charger_dataset(CSV_HARDCORE, "Poison (V34)")
df_aud = charger_dataset(CSV_AUDIT, "Audit Expert")

for d in [df_prem, df_hard, df_aud]:
    if d is not None:
        dataframes.append(d)

if not dataframes:
    raise ValueError("❌ ERREUR FATALE : Aucun dataset n'a pu être chargé.")

# Fusion de tous les univers
df_master = pd.concat(dataframes, ignore_index=True)

# On prélève un échantillon aléatoire pour la 3D
df = df_master.sample(n=min(SAMPLE_SIZE, len(df_master)), random_state=42)

print("🧠 3. Transformation des textes en vecteurs TF-IDF...")
vecteurs_haute_dim = encodeur.transform(df['texte'].astype(str))

print("⚡ 4. Compression SVD (Étape critique anti-crash)...")
svd = TruncatedSVD(n_components=50, random_state=42)
vecteurs_50d = svd.fit_transform(vecteurs_haute_dim)

print("📉 5. Réduction en 3D avec l'algorithme t-SNE (patiente quelques secondes)...")
tsne = TSNE(n_components=3, random_state=42, perplexity=30, max_iter=1000)
vecteurs_3d = tsne.fit_transform(vecteurs_50d)

df['Axe X'] = vecteurs_3d[:, 0]
df['Axe Y'] = vecteurs_3d[:, 1]
df['Axe Z'] = vecteurs_3d[:, 2]

df['Apercu'] = df['texte'].apply(lambda x: (str(x)[:100] + '...') if len(str(x)) > 100 else str(x))

print("✨ 6. Génération de la Galaxie Sémantique...")
fig = px.scatter_3d(
    df,
    x='Axe X', y='Axe Y', z='Axe Z',
    color='domaine',         # La couleur identifie le métier (Police, Pompier...)
    symbol='Source',         # LA NOUVEAUTÉ : La forme identifie la source de la donnée
    hover_name='domaine',
    hover_data={'Axe X': False, 'Axe Y': False, 'Axe Z': False, 'Source': True, 'texte': True, 'friction': True, 'Apercu': False},
    title="Galaxie NEXUS V35 - Cartographie Sémantique de l'Urgence",
    opacity=0.75
)

fig.update_traces(marker=dict(size=4, line=dict(width=0.5, color='DarkSlateGrey')))
fig.update_layout(
    scene=dict(
        xaxis_title='', yaxis_title='', zaxis_title='',
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        zaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    template="plotly_dark",
    legend_title_text='Classification & Provenance'
)

print("✅ Ouverture du navigateur...")
fig.show()