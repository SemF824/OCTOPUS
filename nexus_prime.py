"""
NEXUS PRIME — V5.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entraîne le classifieur de domaine et produit un rapport de qualité.
Nouveautés vs V5.0 :
  • Cross-validation 5-fold (score réaliste, pas juste le score d'entraînement)
  • Rapport de classification complet (précision / rappel / F1 par domaine)
  • Détection de déséquilibre de classes
"""
import sqlite3
import pandas as pd
import warnings
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
from sentence_transformers import SentenceTransformer
import joblib

warnings.filterwarnings("ignore")

DB_PATH       = "nexus_bionexus.db"
MODEL_DOMAINE = "nexus_modele_domaine_v4.pkl"


def entrainer_cerveau():
    print("\n🧠  NEXUS PRIME — Entraînement V5.1")
    print("─" * 50)

    # ── 1. Chargement des données ─────────────────────────────────────────────
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT details_ticket, domaine_cible FROM tickets", conn)

    print(f"📂  Tickets chargés : {len(df)}")

    # Vérification de l'équilibre des classes
    dist = df["domaine_cible"].value_counts()
    print("\n📊  Distribution des domaines :")
    for domaine, count in dist.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"    {domaine:<12} {count:>6}  ({pct:5.1f}%)  {bar}")

    ratio_min_max = dist.min() / dist.max()
    if ratio_min_max < 0.5:
        print(f"\n⚠️  Déséquilibre détecté (ratio min/max = {ratio_min_max:.2f}).")
        print("   Conseil : relancez data_forge.py pour rééquilibrer les classes.")

    # ── 2. Encodage sémantique ────────────────────────────────────────────────
    print(f"\n🤖  Chargement du moteur MPNet-Multilingual…")
    embedder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    print(f"🧮  Encodage de {len(df)} tickets…")
    X = embedder.encode(
        df["details_ticket"].tolist(),
        show_progress_bar=True,
        batch_size=64,
    )
    y = df["domaine_cible"].values

    # ── 3. Entraînement + Cross-Validation ───────────────────────────────────
    print("\n⚙️   Entraînement du Random Forest (300 arbres)…")
    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",   # Compense les déséquilibres résiduels
    )

    print("🔄  Cross-validation 5-fold stratifiée…")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores_cv = cross_val_score(clf, X, y, cv=cv, scoring="f1_weighted", n_jobs=-1)

    print(f"\n{'─'*50}")
    print(f"  📈  F1 CV (5-fold) : {scores_cv.mean():.3f}  ±  {scores_cv.std():.3f}")
    print(f"      [Min: {scores_cv.min():.3f}  |  Max: {scores_cv.max():.3f}]")

    # ── 4. Entraînement final sur tout le dataset ─────────────────────────────
    clf.fit(X, y)

    # Rapport sur l'ensemble d'entraînement (à titre indicatif)
    y_pred = clf.predict(X)
    print(f"\n📋  Rapport de classification (données d'entraînement) :")
    print(classification_report(y, y_pred, zero_division=0))

    # ── 5. Sauvegarde ─────────────────────────────────────────────────────────
    joblib.dump(clf, MODEL_DOMAINE)
    print(f"💾  Modèle sauvegardé → {MODEL_DOMAINE}")
    print(f"\n✅  Entraînement V5.1 terminé.")


if __name__ == "__main__":
    entrainer_cerveau()
