# nexus_3d_viz.py
import sqlite3
import pandas as pd
import joblib
import plotly.express as px
from sklearn.manifold import TSNE
import warnings

# On importe ton encodeur pour que joblib puisse lire le pickle
from nexus_core import TextEncoder
warnings.filterwarnings("ignore")

# --- 1. CONFIGURATION ---
DB_PATH = "../nexus_bionexus.db"
MODEL_PATH = "../pickle_result/nexus_v21_unified.pkl" # Mets le nom de ton dernier modèle
SAMPLE_SIZE = 20000 # On prend 1500 tickets au hasard pour que le calcul soit rapide

print("🔍 1. Chargement de l'encodeur depuis le modèle...")
pipeline = joblib.load(MODEL_PATH)
# Le premier composant de ton pipeline est le 'vec' (TextEncoder)
encodeur = pipeline.named_steps['vec']

print(f"📂 2. Extraction de {SAMPLE_SIZE} tickets depuis la base de données...")
conn = sqlite3.connect(DB_PATH)
# On prend un échantillon équilibré pour la visualisation
df = pd.read_sql(f"SELECT texte, domaine FROM tickets_domaines ORDER BY RANDOM() LIMIT {SAMPLE_SIZE}", conn)
conn.close()

print("🧠 3. Transformation des textes en vecteurs à 768 dimensions...")
# On utilise l'encodeur pour générer les matrices
vecteurs_768d = encodeur.transform(df['texte'])

print("📉 4. Réduction en 3D avec l'algorithme t-SNE (patiente quelques secondes)...")
# t-SNE va grouper les tickets qui parlent de la même chose.
# CORRECTION : 'n_iter' remplacé par 'max_iter'
tsne = TSNE(n_components=3, random_state=42, perplexity=30, max_iter=1000)
vecteurs_3d = tsne.fit_transform(vecteurs_768d)

# On ajoute les coordonnées 3D à notre DataFrame
df['Axe X'] = vecteurs_3d[:, 0]
df['Axe Y'] = vecteurs_3d[:, 1]
df['Axe Z'] = vecteurs_3d[:, 2]

# Raccourcir le texte pour l'affichage au survol de la souris
df['Apercu'] = df['texte'].apply(lambda x: (x[:80] + '...') if len(x) > 80 else x)

print("✨ 5. Génération de la galaxie 3D...")
fig = px.scatter_3d(
    df,
    x='Axe X', y='Axe Y', z='Axe Z',
    color='domaine',         # Chaque domaine aura une couleur différente
    hover_name='domaine',
    hover_data={'Axe X': False, 'Axe Y': False, 'Axe Z': False, 'texte': True}, # Affiche le texte complet au survol
    title="Galaxie NEXUS - Visualisation 3D de l'Espace Sémantique",
    opacity=0.7
)

# On améliore le rendu visuel
fig.update_traces(marker=dict(size=4))
fig.update_layout(scene=dict(xaxis_title='', yaxis_title='', zaxis_title=''), margin=dict(l=0, r=0, b=0, t=40))

# Sauvegarde et affichage
fichier_html = "nexus_galaxie_3d.html"
fig.write_html(fichier_html)
print(f"🎉 Terminé ! Ouverture de {fichier_html} dans ton navigateur...")

# Ouvre directement le fichier dans ton navigateur web (Mac/Windows)
import webbrowser
import os
webbrowser.open('file://' + os.path.realpath(fichier_html))