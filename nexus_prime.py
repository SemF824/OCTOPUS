"""
NEXUS-PRIME v3 — IA Décisionnelle BioNexus
===========================================
Architecture :
  - Source unique : nexus_bionexus.db  (créée par migration_vers_sql.py)
  - Tout ce que l'IA prédit est automatiquement loggé en SQL (prediction_logs)
  - Le VETO éthique est une règle déterministe, jamais statistique
  - Les modèles .pkl sont sauvegardés sur disque pour réutilisation

ORDRE DE LANCEMENT :
  1. python data_factory_v3.py      ← Génération de la vérité terrain anti-triche
  2. python nexus_prime.py          ← Entraînement strict + tests
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_absolute_error
from scipy.sparse import hstack, csr_matrix
import joblib
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
#  CONFIGURATION CENTRALE
# ─────────────────────────────────────────────────────────────

DB_PATH = "nexus_bionexus.db"
MODEL_VECTORIZER = "nexus_vectorizer_v3.pkl"
MODEL_DOMAINE = "nexus_modele_domaine_v3.pkl"
MODEL_SCORE = "nexus_modele_score_v3.pkl"

MOTS_CLES_VETO = [
    "respire plus", "ne respire", "arrêt respiratoire", "arrêt cardiaque",
    "ne répond plus", "inconscient", "convulsions", "overdose",
    "hémorragie", "ne bouge plus", "sans connaissance",
]


# ─────────────────────────────────────────────────────────────
#  1. CHARGEMENT DEPUIS SQL
# ─────────────────────────────────────────────────────────────

def charger_donnees() -> pd.DataFrame:
    """
    Charge les tickets depuis la table SQL 'tickets'.
    Construit le texte d'entraînement en fusionnant titre + détails.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT
            id_ticket,
            rang_priorite,
            etat_declare,
            titre_ticket,
            details_ticket,
            domaine_cible,
            score_cible,
            ethique_veto
        FROM tickets
    """, conn)
    conn.close()

    if df.empty:
        raise ValueError(
            "❌ La table 'tickets' est vide. "
            "Lancez d'abord : python data_factory_v3.py"
        )

    # Texte fusionné : titre + détails (les NaN sont déjà '' grâce à la migration)
    df["texte"] = (df["titre_ticket"] + " " + df["details_ticket"]).str.strip()

    # Encodage numérique de l'état
    df["etat_num"] = df["etat_declare"].map({"URGENT": 1, "NORMAL": 0}).fillna(0).astype(int)

    # On garde le veto_flag uniquement pour les statistiques, IL N'EST PLUS UTILISÉ POUR L'ENTRAÎNEMENT
    df["veto_flag"] = df["ethique_veto"].str.contains("OUI", na=False).astype(int)

    print(f"✅ {len(df)} tickets chargés depuis '{DB_PATH}'")
    print(f"   Domaines : {sorted(df['domaine_cible'].unique().tolist())}")
    print(f"   Tickets avec veto : {df['veto_flag'].sum()}")
    return df


# ─────────────────────────────────────────────────────────────
#  2. ENTRAÎNEMENT DES MODÈLES
# ─────────────────────────────────────────────────────────────

def entrainer_modeles(df: pd.DataFrame):
    """Vectorise le texte SQL, entraîne les deux cerveaux, évalue, sauvegarde."""

    X_texte = df["texte"]
    # CORRECTION CRITIQUE : Le modèle de score ne s'entraîne plus sur la réponse du veto.
    # Il doit deviner le score uniquement avec le rang et l'état.
    X_num = df[["rang_priorite", "etat_num"]].values
    Y_domaine = df["domaine_cible"]
    Y_score = df["score_cible"]

    # Split stratifié : même proportion de domaines en train et test
    (X_txt_train, X_txt_test,
     y_dom_train, y_dom_test,
     y_sc_train, y_sc_test,
     X_num_train, X_num_test) = train_test_split(
        X_texte, Y_domaine, Y_score, X_num,
        test_size=0.2, random_state=42, stratify=Y_domaine
    )

    # ── Vectorisation TF-IDF ──────────────────────────────────
    print("\n🧮 Vectorisation TF-IDF...")
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        max_features=3000,
        sublinear_tf=True,  # atténue les mots ultra-fréquents
        min_df=2,  # ignore les mots vus < 2 fois
    )
    X_txt_train_vec = vectorizer.fit_transform(X_txt_train)
    X_txt_test_vec = vectorizer.transform(X_txt_test)

    # Matrice étendue pour le modèle de score (Texte + Rang + État)
    X_full_train = hstack([X_txt_train_vec, csr_matrix(X_num_train)])
    X_full_test = hstack([X_txt_test_vec, csr_matrix(X_num_test)])
    print("✅ Vectorisation terminée.")

    # ── Cerveau 1 : Classification du Domaine ─────────────────
    print("\n⚙️  Entraînement [DOMAINE]...")
    ia_domaine = RandomForestClassifier(
        n_estimators=200, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    )
    ia_domaine.fit(X_txt_train_vec, y_dom_train)

    # ── Cerveau 2 : Régression du Score ───────────────────────
    print("⚙️  Entraînement [SCORE]...")
    ia_score = RandomForestRegressor(
        n_estimators=200, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    )
    ia_score.fit(X_full_train, y_sc_train)

    # ── Évaluation ────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  RÉSULTATS D'ÉVALUATION (20% non vus)")
    print("═" * 60)

    preds_dom = ia_domaine.predict(X_txt_test_vec)
    precision = np.mean(preds_dom == y_dom_test) * 100
    cv = cross_val_score(ia_domaine, X_txt_train_vec, y_dom_train, cv=5, scoring="accuracy")
    print(f"\n🎯 [DOMAINE] Précision test : {precision:.1f}%")
    print(f"   CV-5 train           : {cv.mean() * 100:.1f}% ± {cv.std() * 100:.1f}%")
    if precision - cv.mean() * 100 > 10:
        print("   ⚠️  Écart > 10% — risque d'overfitting")
    print(classification_report(y_dom_test, preds_dom, zero_division=0))

    preds_sc = ia_score.predict(X_full_test)
    mae = mean_absolute_error(y_sc_test, preds_sc)
    print(f"🎯 [SCORE]   Erreur absolue moyenne : {mae:.2f} pts / 10")

    # ── Sauvegarde des modèles ────────────────────────────────
    joblib.dump(vectorizer, MODEL_VECTORIZER)
    joblib.dump(ia_domaine, MODEL_DOMAINE)
    joblib.dump(ia_score, MODEL_SCORE)
    print(f"\n💾 Modèles sauvegardés : {MODEL_VECTORIZER}, {MODEL_DOMAINE}, {MODEL_SCORE}")

    return vectorizer, ia_domaine, ia_score


# ─────────────────────────────────────────────────────────────
#  3. VETO ÉTHIQUE (règle déterministe, pas du ML)
# ─────────────────────────────────────────────────────────────

def appliquer_veto(texte: str, domaine: str, score_brut: float, rang: int) -> dict:
    """
    Règles de veto prioritaires sur tout score ML :
      - Mots-clés d'urgence vitale dans le texte → score = 10, rang ignoré
      - Score >= 9.0 en domaine MÉDICAL → score = 10, rang ignoré
      - Sinon : légère modulation par le rang (+/- 0.2 par niveau)
    """
    texte_lower = texte.lower()
    veto_mots = any(mot in texte_lower for mot in MOTS_CLES_VETO)
    veto_score = score_brut >= 9.0 and domaine == "MÉDICAL"
    veto = veto_mots or veto_score

    raison = ""
    if veto_mots:
        raison = "Mots-clés d'urgence vitale détectés"
    elif veto_score:
        raison = f"Score critique ({score_brut}/10) en domaine MÉDICAL"

    score_final = 10.0 if veto else round(
        min(max(score_brut + (rang - 3) * 0.2, 0.0), 10.0), 2
    )

    return {"veto": veto, "raison": raison, "score_final": score_final}


# ─────────────────────────────────────────────────────────────
#  4. ANALYSE D'UN TICKET + LOG SQL
# ─────────────────────────────────────────────────────────────

def analyser_ticket(
        texte: str,
        rang: int,
        etat: str,
        vectorizer,
        ia_domaine,
        ia_score,
        id_client: str = None,
) -> dict:
    """
    Pipeline complet :
      texte SQL → vectorisation → prédiction → veto → log SQL → retour résultat
    """
    etat_num = 1 if etat == "URGENT" else 0
    vec_txt = vectorizer.transform([texte])

    # CORRECTION CRITIQUE : Alignement exact sur la matrice d'entraînement (2 variables)
    vec_full = hstack([vec_txt, csr_matrix([[rang, etat_num]])])

    domaine = ia_domaine.predict(vec_txt)[0]
    score_brut = round(float(ia_score.predict(vec_full)[0]), 2)
    probas = dict(zip(ia_domaine.classes_,
                      (ia_domaine.predict_proba(vec_txt)[0] * 100).round(1)))

    veto_result = appliquer_veto(texte, domaine, score_brut, rang)

    # ── Log en base SQL ───────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO prediction_logs
            (date_insertion, texte_ticket, id_client, rang_priorite, etat_declare,
             domaine_predit, score_brut_ia, score_final, veto_applique, raison_veto,
             confiance_domaine)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        texte, id_client, rang, etat,
        domaine, score_brut, veto_result["score_final"],
        int(veto_result["veto"]), veto_result["raison"],
        probas.get(domaine, 0.0)
    ))
    conn.commit()
    conn.close()

    return {
        "domaine": domaine,
        "score_brut": score_brut,
        "score_final": veto_result["score_final"],
        "veto": veto_result["veto"],
        "raison_veto": veto_result["raison"],
        "confiance": probas,
    }


# ─────────────────────────────────────────────────────────────
#  5. RAPPORT DEPUIS SQL (lecture des logs)
# ─────────────────────────────────────────────────────────────

def afficher_rapport_logs():
    """Lit prediction_logs et affiche un résumé statistique."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM prediction_logs ORDER BY date_insertion DESC", conn)
    conn.close()

    if df.empty:
        print("Aucun log disponible.")
        return

    print("\n" + "═" * 60)
    print(f"  RAPPORT prediction_logs ({len(df)} entrées)")
    print("═" * 60)
    print(f"  Vetos appliqués    : {df['veto_applique'].sum()}")
    print(f"  Score moyen final  : {df['score_final'].mean():.2f}/10")
    print(f"  Domaines détectés  :\n{df['domaine_predit'].value_counts().to_string()}")
    print(f"\n  5 dernières prédictions :")
    cols = ["date_insertion", "texte_ticket", "domaine_predit", "score_final", "veto_applique"]
    print(df[cols].head(5).to_string(index=False))


# ─────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🧠 NEXUS-PRIME v3\n" + "═" * 60)

    # 1. Chargement SQL
    print("\n📥 1. Chargement des données depuis SQL...")
    df = charger_donnees()

    # 2. Entraînement
    print("\n⚙️  2. Entraînement des modèles...")
    vectorizer, ia_domaine, ia_score = entrainer_modeles(df)

    # 3. Tests sur des cas réels
    print("\n" + "═" * 60)
    print("  🚀 TESTS EN DIRECT")
    print("═" * 60)

    cas_tests = [
        {
            "texte": "douleur poitrin. un visiteur ne respire plus batiment a",
            "rang": 5, "etat": "URGENT", "id_client": "CLI-VIP-01",
            "label": "Urgence vitale (orthographe approximative)"
        },
        {
            "texte": "mon clavier a un problème avec la touche espace",
            "rang": 5, "etat": "URGENT", "id_client": "CLI-100",
            "label": "VIP qui abuse du flag URGENT (matériel banal)"
        },
        {
            "texte": "besoin d'un accès VPN pour travailler depuis chez moi",
            "rang": 1, "etat": "NORMAL", "id_client": "CLI-101",
            "label": "Ticket INFRA standard"
        },
        {
            "texte": "Collègue inconscient dans la salle de réunion B2",
            "rang": 2, "etat": "NORMAL", "id_client": "CLI-102",
            "label": "Urgence vitale déclarée NORMAL par un employé standard"
        },
    ]

    for cas in cas_tests:
        res = analyser_ticket(
            texte=cas["texte"], rang=cas["rang"], etat=cas["etat"],
            vectorizer=vectorizer, ia_domaine=ia_domaine, ia_score=ia_score,
            id_client=cas["id_client"]
        )
        top2 = sorted(res["confiance"].items(), key=lambda x: -x[1])[:2]

        print(f"\n  📝 {cas['label']}")
        print(f"     Texte  : \"{cas['texte']}\"")
        print(f"     Profil : rang={cas['rang']} | {cas['etat']}")
        print(f"     ─────────────────────────────────────────")
        print(f"     Domaine      : {res['domaine']}")
        print(f"     Score IA brut: {res['score_brut']}/10")
        print(f"     Score final  : {res['score_final']}/10")
        if res["veto"]:
            print(f"     🛡️  VETO      : {res['raison_veto']}")
        print(f"     Confiance    : {top2[0][0]}={top2[0][1]}%  |  {top2[1][0]}={top2[1][1]}%")

    # 4. Rapport des logs SQL
    afficher_rapport_logs()

    print(f"\n✅ Tous les résultats sont enregistrés dans '{DB_PATH}' → table prediction_logs")
    print("═" * 60)
