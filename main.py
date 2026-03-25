"""
NEXUS BIONEXUS — V6.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nouveautés :
  • SentimentEngine  — Malus de détresse émotionnelle (transformers)
  • NegationGuard    — Annule les faux positifs médicaux (spaCy + regex)
  • Récidive Cosinus — Similarité sémantique vs word-overlap
  • Formule V2.0     — Base × PoidsNég + MalusSentiment + BonusHistorique
  • Crash-test OK    — "pas de douleur... furieux... fiches de paie" → RH
"""
import sqlite3
import joblib
import os
import re
import difflib
import numpy as np
from datetime import datetime, timedelta

# ── Logs propres ──────────────────────────────────────────────────────────────
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
import warnings
warnings.filterwarnings("ignore")

from sentence_transformers import SentenceTransformer
from transformers import pipeline as hf_pipeline

# ── Couleurs terminal ─────────────────────────────────────────────────────────
GREEN  = "\033[92m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

DB_PATH      = "nexus_bionexus.db"
MODEL_DOMAINE = "nexus_modele_domaine_v4.pkl"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE 1 — SENTIMENT ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SentimentEngine:
    """
    Transforme l'état émotionnel du client en malus de priorité (0.0 → 3.0).

    Modèle : nlptown/bert-base-multilingual-uncased-sentiment
    Retourne 1-5 étoiles → converti en malus :
        1 ★  (très négatif)  → +3.0
        2 ★  (négatif)       → +2.0
        3 ★  (neutre)        → +0.5
        4-5 ★ (positif)      → +0.0

    Exemple :
        "Le wifi est lent"                       → 3★ → +0.5  → score 4.5
        "Le wifi est lent, catastrophe réunion"  → 1★ → +3.0  → score 7.0
    """
    _MODELE  = "nlptown/bert-base-multilingual-uncased-sentiment"
    _MAPPING = {1: 3.0, 2: 2.0, 3: 0.5, 4: 0.0, 5: 0.0}

    # Fallback lexical si le modèle ne charge pas
    _MOTS_DETRESSE = [
        "catastrophe", "urgence", "sos", "furieux", "scandaleux",
        "désespéré", "impossible", "tout perdre", "encore une fois",
        "inadmissible", "critique", "!!!",
    ]

    def __init__(self):
        self._pipe = None

    def charger(self):
        print(f"  📊 Chargement du Sentiment Engine…", end="", flush=True)
        try:
            self._pipe = hf_pipeline(
                "sentiment-analysis",
                model=self._MODELE,
                truncation=True,
                max_length=512,
            )
            print(f"  {GREEN}✅{RESET}")
        except Exception as e:
            print(f"  {YELLOW}⚠️  Mode dégradé ({e.__class__.__name__}){RESET}")

    def malus(self, texte: str) -> float:
        """Retourne le malus de détresse entre 0.0 et 3.0."""
        if self._pipe is None:
            return self._fallback(texte)
        try:
            label = self._pipe(texte[:512])[0]["label"]   # "1 star" … "5 stars"
            stars = int(label.split()[0])
            return self._MAPPING.get(stars, 0.0)
        except Exception:
            return self._fallback(texte)

    def _fallback(self, texte: str) -> float:
        t = texte.lower()
        hits = sum(1 for m in self._MOTS_DETRESSE if m in t)
        return round(min(hits * 0.8, 3.0), 1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE 2 — NEGATION GUARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class NegationGuard:
    """
    Détecte les mots sensibles placés SOUS UNE NÉGATION pour annuler
    les faux positifs médicaux.

    Stratégie double :
    1. spaCy (fr_core_news_sm)  : analyse de dépendances syntaxiques —
       vérifie si le verbe régissant le token a un enfant "neg".
    2. Regex fallback            : patterns "pas de X", "aucun X", "sans X", etc.

    Crash-test résolu :
        "Je n'ai PAS de douleur à la poitrine, mais je suis furieux…"
        → "douleur" est nié → pas de boost médical → domaine RH + sentiment élevé.
    """
    _SENSIBLES = frozenset({
        "douleur", "douleurs", "mal", "fièvre", "saignement", "sang",
        "malaise", "inconscient", "infarctus", "cardiaque", "avc", "blessure",
    })

    # Regex couvrant les constructions négatives françaises courantes
    _RE_NEG = re.compile(
        r"(?:n['\s]?(?:est|a|ai|avons|êtes|sont|y a)\s+pas"
        r"|ne\s+\w+\s+pas"
        r"|pas\s+de"
        r"|aucun[e]?"
        r"|sans)\s+(\w+)",
        re.IGNORECASE,
    )

    def __init__(self):
        self._nlp = None

    def charger(self):
        print(f"  🔍 Chargement du Negation Guard (spaCy)…", end="", flush=True)
        try:
            import spacy
            self._nlp = spacy.load("fr_core_news_sm")
            print(f"  {GREEN}✅{RESET}")
        except Exception as e:
            print(f"  {YELLOW}⚠️  Mode regex fallback ({e.__class__.__name__}){RESET}")

    def mots_nies(self, texte: str) -> frozenset:
        """
        Retourne l'ensemble des mots sensibles qui sont sous négation.
        Utilise spaCy si disponible, sinon le fallback regex.
        """
        nies = set()

        # ── Passe spaCy ──────────────────────────────────────────────────────
        if self._nlp is not None:
            doc = self._nlp(texte)
            for token in doc:
                lemme = token.lemma_.lower()
                if lemme not in self._SENSIBLES:
                    continue
                # Vérifier si le token lui-même ou son gouverneur est nié
                gouverneur_nie = any(
                    child.dep_ == "neg" for child in token.head.children
                ) if token.head != token else False
                direct_nie = any(child.dep_ == "neg" for child in token.children)
                if direct_nie or gouverneur_nie:
                    nies.add(lemme)

        # ── Passe regex (complément ou fallback) ─────────────────────────────
        for m in self._RE_NEG.finditer(texte.lower()):
            mot = m.group(1).lower()
            if mot in self._SENSIBLES:
                nies.add(mot)

        return frozenset(nies)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INSTANCES GLOBALES (chargées une seule fois au démarrage)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

sentiment_engine = SentimentEngine()
negation_guard   = NegationGuard()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALISATION BASE DE DONNÉES & MIGRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def initialiser_systeme():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fiches_clients (
                id_client TEXT PRIMARY KEY,
                nom TEXT,
                antecedents TEXT,
                derniere_connexion DATETIME,
                dernier_probleme TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                date_saisie     DATETIME,
                texte_ticket    TEXT,
                id_client       TEXT,
                domaine_predit  TEXT,
                score_final     REAL,
                malus_sentiment REAL,
                bonus_recidive  REAL
            )
        """)
        # Migration douce : ajout des colonnes manquantes
        colonnes_migration = [
            "date_saisie DATETIME",
            "malus_sentiment REAL",
            "bonus_recidive REAL",
        ]
        for col in colonnes_migration:
            try:
                conn.execute(f"ALTER TABLE prediction_logs ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass   # Déjà présente


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYSE HISTORIQUE — RÉCIDIVE PAR SIMILARITÉ COSINUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyser_recidive(id_client: str, texte_actuel: str, embedder) -> float:
    """
    V2 — Utilise la similarité cosinus sur les embeddings plutôt que
    l'intersection de mots, ce qui capture les reformulations sémantiques.

    Seuil cosinus > 0.75 → même problème récurrent → +0.5
    Si le ticket précédent date de moins de 3 mois   → +0.2 (aggravation)
    """
    limite_3_mois = datetime.now() - timedelta(days=90)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT texte_ticket, date_saisie
            FROM prediction_logs
            WHERE id_client = ? AND date_saisie IS NOT NULL
            ORDER BY date_saisie DESC
            LIMIT 5
        """, (id_client,)).fetchall()

    if not rows:
        return 0.0

    vec_actuel = embedder.encode([texte_actuel])[0]
    vecs_anciens = embedder.encode([r[0] for r in rows])

    bonus = 0.0
    for i, (_, date_str) in enumerate(rows):
        cos_sim = float(
            np.dot(vec_actuel, vecs_anciens[i])
            / (np.linalg.norm(vec_actuel) * np.linalg.norm(vecs_anciens[i]) + 1e-9)
        )
        if cos_sim >= 0.75:
            bonus += 0.5
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                if dt > limite_3_mois:
                    bonus += 0.2
            except ValueError:
                pass
            break   # Un seul bonus par session

    return round(min(bonus, 1.5), 1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORMULE DE PRIORITÉ V2.0
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calculer_priorite(
    texte: str,
    domaine: str,
    ant: str,
    bonus_histo: float,
) -> tuple:
    """
    Formule :
        Score = BaseDomaine
              + BonusMédical  (si mots sensibles NON niés)
              + MalusSentiment
              + BonusAntécédents
              + BonusHistorique

    Retourne : (score: float, malus_sent: float, raison: str)

    Cas spéciaux :
        • Veto vital (inconscient, infarctus…)  → 10.0 immédiatement
        • Mots médicaux sous négation           → boost annulé
    """
    t = texte.lower()

    # 1 ── BASE DOMAINE ────────────────────────────────────────────────────────
    bases = {
        "INFRA": 4.0, "ACCÈS": 3.0, "RH": 2.0,
        "MATÉRIEL": 1.5, "MÉDICAL": 3.5,
    }
    score = bases.get(domaine, 2.0)

    # 2 ── NEGATION GUARD ─────────────────────────────────────────────────────
    mots_nies = negation_guard.mots_nies(texte)

    # 3 ── VETOS VITAUX (avec protection contre les faux positifs niés) ───────
    VETOS = ["inconscient", "infarctus", "avc", "étouffe", "meurs", "cardiaque"]
    mots_phrase = re.findall(r"\w+", t)
    for v in VETOS:
        if v in mots_nies:
            continue   # "pas de cardiaque" → on ignore
        if v in t or difflib.get_close_matches(v, mots_phrase, cutoff=0.85):
            return 10.0, 0.0, "VETO_VITAL"

    # 4 ── BONUS MÉDICAL (sang, membres) — annulé si nié ─────────────────────
    bonus_medical = 0.0

    BOOSTS = {
        "sang":    2.0, "saign":   2.0,
        "jambe":   1.5, "bras":    1.5,
        "doigt":   1.5, "main":    1.0,
        "pied":    1.0, "blessure":1.0,
    }
    for mot, boost in BOOSTS.items():
        if mot in t and not any(mot in nie for nie in mots_nies):
            bonus_medical += boost

    # Synergie sang+membre
    sang_actif   = any(m in t and m not in mots_nies for m in ("sang", "saign"))
    membre_actif = any(
        m in t and m not in mots_nies
        for m in ("jambe", "bras", "doigt", "main", "pied")
    )
    if sang_actif and membre_actif:
        bonus_medical = min(bonus_medical + 2.0, 4.5)

    score += bonus_medical

    # 5 ── MALUS SENTIMENT (détresse émotionnelle) ────────────────────────────
    malus_sent = sentiment_engine.malus(texte)
    score += malus_sent

    # 6 ── BONUS ANTÉCÉDENTS MÉDICAUX ─────────────────────────────────────────
    bonus_ant = 0.0
    if any(x in ant.lower() for x in ("cardiaque", "diabète", "reins", "épilepsie")):
        bonus_ant = 3.0
    score += bonus_ant

    # 7 ── BONUS HISTORIQUE ───────────────────────────────────────────────────
    score += bonus_histo

    return round(min(score, 10.0), 1), malus_sent, "OK"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CRM — RECHERCHE / CRÉATION CLIENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def rechercher_ou_creer_client(saisie: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id_client, nom, antecedents FROM fiches_clients "
            "WHERE id_client = ? OR nom LIKE ?",
            (saisie, f"%{saisie}%"),
        ).fetchone()
        if row:
            return row[0], row[1], row[2] or ""

        print(f"  {YELLOW}⚠️  Nouveau client — création du dossier.{RESET}")
        new_id = f"CLI-{int(datetime.now().timestamp())}"
        conn.execute(
            "INSERT INTO fiches_clients (id_client, nom, antecedents) VALUES (?, ?, ?)",
            (new_id, saisie, ""),
        )
        return new_id, saisie, ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AFFICHAGE RÉSULTAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def afficher_resultat(
    domaine: str,
    score: float,
    malus_sent: float,
    bonus_h: float,
    raison: str,
):
    couleur = RED if score >= 8 else (YELLOW if score >= 5 else GREEN)
    niveau  = (
        f"{RED}🔴 CRITIQUE{RESET}"   if score >= 8 else
        f"{YELLOW}🟠 HAUTE{RESET}"   if score >= 6 else
        f"{YELLOW}🟡 MOYENNE{RESET}" if score >= 4 else
        f"{GREEN}🟢 BASSE{RESET}"
    )

    print(f"\n{CYAN}{'─'*54}{RESET}")
    print(f"  🎯  Domaine détecté   : {BLUE}{domaine}{RESET}")
    print(f"  🔢  Score de priorité : {couleur}{score} / 10{RESET}")
    print(f"  📊  Niveau            : {niveau}")

    if raison == "VETO_VITAL":
        print(f"\n  {RED}⚠️  ALERTE VITALE — Intervention immédiate requise !{RESET}")
        print(f"  {RED}    → Contacter les services d'urgence (15 / 112){RESET}")
    else:
        details = []
        if malus_sent >= 3.0:
            details.append(f"  😰  Détresse sévère        : +{malus_sent:.1f}")
        elif malus_sent >= 1.5:
            details.append(f"  😟  Détresse modérée       : +{malus_sent:.1f}")
        elif malus_sent > 0:
            details.append(f"  😐  Légère tension         : +{malus_sent:.1f}")
        if bonus_h > 0:
            details.append(f"  🔁  Récidive sémantique    : +{bonus_h:.1f}")
        if details:
            print()
            for d in details:
                print(d)

    print(f"{CYAN}{'─'*54}{RESET}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POINT D'ENTRÉE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run():
    initialiser_systeme()

    print(f"\n{BLUE}{'═'*54}")
    print(f"  🧠  NEXUS BIONEXUS V6.0")
    print(f"      Sentiment Engine  |  Negation Guard  |  Formule 2.0")
    print(f"{'═'*54}{RESET}\n")

    # ── Chargement des modèles ────────────────────────────────────────────────
    print(f"{CYAN}⚙️   Initialisation des modules…{RESET}")
    try:
        print(f"  🤖 Chargement du SentenceTransformer…", end="", flush=True)
        embedder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
        print(f"  {GREEN}✅{RESET}")

        print(f"  🌲 Chargement du classifieur de domaine…", end="", flush=True)
        domain_model = joblib.load(MODEL_DOMAINE)
        print(f"  {GREEN}✅{RESET}")

        sentiment_engine.charger()
        negation_guard.charger()

        print(f"\n{GREEN}✅  Tous les systèmes sont opérationnels.{RESET}\n")

    except Exception as e:
        print(f"\n{RED}❌  Erreur critique au démarrage : {e}{RESET}")
        return

    # ── Boucle principale ─────────────────────────────────────────────────────
    while True:
        print(f"\n{BLUE}{'─'*54}{RESET}")
        saisie = input("👤  Client (Nom ou ID, 'exit' pour quitter) : ").strip()
        if saisie.lower() == "exit":
            print(f"\n{GREEN}Au revoir.{RESET}\n")
            break
        if not saisie:
            continue

        id_c, nom_c, ant = rechercher_ou_creer_client(saisie)
        print(f"  {GREEN}Dossier : {nom_c}{RESET}  |  Antécédents : {ant or 'Néant'}")

        nouveaux_ant = input("📋  Nouveaux antécédents (Entrée pour ignorer) : ").strip()
        ticket_text  = input("📝  Description du problème : ").strip()
        if not ticket_text:
            continue

        # ── Inférence domaine ─────────────────────────────────────────────────
        X_vec   = embedder.encode([ticket_text])
        domaine = domain_model.predict(X_vec)[0]

        # ── Calculs ───────────────────────────────────────────────────────────
        full_ant = f"{ant} {nouveaux_ant}".strip()
        bonus_h  = analyser_recidive(id_c, ticket_text, embedder)
        score, malus_sent, raison = calculer_priorite(
            ticket_text, domaine, full_ant, bonus_h
        )

        # ── Affichage ─────────────────────────────────────────────────────────
        afficher_resultat(domaine, score, malus_sent, bonus_h, raison)

        # ── Persistance ───────────────────────────────────────────────────────
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO prediction_logs
                    (date_saisie, texte_ticket, id_client, domaine_predit,
                     score_final, malus_sentiment, bonus_recidive)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now_str, ticket_text, id_c, domaine, score, malus_sent, bonus_h))
            conn.execute("""
                UPDATE fiches_clients
                SET antecedents = ?, derniere_connexion = ?, dernier_probleme = ?
                WHERE id_client = ?
            """, (full_ant, now_str, ticket_text, id_c))


if __name__ == "__main__":
    run()
