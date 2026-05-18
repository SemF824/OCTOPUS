# nexus_3d_viz.py
import pandas as pd
import joblib
import plotly.express as px
from sklearn.manifold import TSNE
from sklearn.decomposition import TruncatedSVD
import warnings
import os

warnings.filterwarnings("ignore")

# --- 1. CONFIGURATION ---
CSV_PATH = "../datasets/nexus_dataset_v32.csv"
MODEL_PATH = "../pickle_result/nexus_v32_unified.pkl"
SAMPLE_SIZE = 2500  # Limite pour maintenir une navigation 3D fluide

print("🔍 1. Chargement de l'encodeur TF-IDF depuis le modèle V33...")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"❌ Modèle introuvable : {MODEL_PATH}")

pipeline = joblib.load(MODEL_PATH)

# Le pipeline Kaggle utilise 'tfidf', on l'extrait directement
encodeur = pipeline.named_steps['tfidf']

print(f"📂 2. Extraction d'un échantillon depuis {CSV_PATH}...")
df = pd.read_csv(CSV_PATH, on_bad_lines='skip')
df = df.dropna(subset=['texte', 'domaine']).sample(n=min(SAMPLE_SIZE, len(df)), random_state=42)

print("🧠 3. Transformation des textes en vecteurs TF-IDF...")
vecteurs_haute_dim = encodeur.transform(df['texte'].astype(str))

print("⚡ 4. Compression SVD (Étape critique anti-crash)...")
# TF-IDF génère ~15 000 dimensions. On réduit à 50 dimensions pour ne pas saturer le CPU
svd = TruncatedSVD(n_components=50, random_state=42)
vecteurs_50d = svd.fit_transform(vecteurs_haute_dim)

print("📉 5. Réduction en 3D avec l'algorithme t-SNE (patiente quelques secondes)...")
tsne = TSNE(n_components=3, random_state=42, perplexity=30, max_iter=1000)
vecteurs_3d = tsne.fit_transform(vecteurs_50d)

# Ajout des coordonnées géospatiales au DataFrame
df['Axe X'] = vecteurs_3d[:, 0]
df['Axe Y'] = vecteurs_3d[:, 1]
df['Axe Z'] = vecteurs_3d[:, 2]

# Raccourcir le texte pour l'affichage au survol de la souris
df['Apercu'] = df['texte'].apply(lambda x: (str(x)[:100] + '...') if len(str(x)) > 100 else str(x))

print("✨ 6. Génération de la galaxie Sémantique...")
fig = px.scatter_3d(
    df,
    x='Axe X', y='Axe Y', z='Axe Z',
    color='domaine',
    hover_name='domaine',
    hover_data={'Axe X': False, 'Axe Y': False, 'Axe Z': False, 'texte': True, 'friction': True, 'Apercu': False},
    title="Galaxie NEXUS V33 - Visualisation Spatiale des Contextes d'Urgence",
    opacity=0.75
)

# Optimisation chirurgicale du rendu visuel
fig.update_traces(marker=dict(size=4, line=dict(width=0.5, color='DarkSlateGrey')))
fig.update_layout(
    scene=dict(
        xaxis_title='',
        yaxis_title='',
        zaxis_title='',
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        zaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    template="plotly_dark"  # Tonalité sombre et professionnelle
)

print("✅ Ouverture du navigateur...")
fig.show()