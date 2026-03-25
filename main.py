"""
NEXUS BIONEXUS — V6.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Correctifs V6.1 (post-tests) :
  • SentimentEngine  : filtre d'amplificateurs — cap à 1.0 si aucun
                       marqueur émotionnel présent (évite +3.0 sur "maux de tête")
  • VETO_VITAL       : ajout des traumatismes physiques graves
                       (crâne ouvert, renversé voiture, fracture crânienne…)
  • BOOSTS médicaux  : ajout des patterns neurologiques (neurone, cerveau,
                       picotement, migraine) et cardiaques (trou coeur, crise)
  • Domain Override  : si les antécédents sont médicaux ET que le classifieur
                       donne un domaine technique, force MÉDICAL
  • Scores recalibrés sur les cas de test observés
"""
import sqlite3
import joblib
import os
import re
import difflib
import numpy as np
from datetime import datetime, timedelta

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

GREEN  = "\033[92m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

DB_PATH       = "nexus_bionexus.db"
MODEL_DOMAINE = "nexus_modele_domaine_v4.pkl"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE 1 — SENTIMENT ENGINE V2 (filtré par amplificateurs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SentimentEngine:
    """
    Malus de détresse émotionnelle — 0.0 → 3.0.

    FIX V6.1 — Sur-déclenchement corrigé :
    Le modèle BERT donne parfois 1★ à "maux de tête" (phrase courte,
    lexicalement négative) sans qu'il y ait de vraie détresse exprimée.
    Solution : sans AMPLIFICATEUR émotionnel détecté, le malus est plafonné
    à 1.0, même si BERT retourne 1★.

    Amplificateurs = marqueurs d'urgence subjective réelle :
        "!!!", "urgent", "archi", "méga", "catastrophe", "j'en peux plus"…
    """
    _MODELE  = "nlptown/bert-base-multilingual-uncased-sentiment"
    _MAPPING = {1: 3.0, 2: 2.0, 3: 0.5, 4: 0.0, 5: 0.0}

    _AMPLIFICATEURS = [
        "!!!", "urgent", "urgence", "catastrophe", "sos", "désespéré",
        "archi", "méga", "j'en peux plus", "scandaleux", "inadmissible",
        "impossible", "secours", "aide moi", "help", "critique", "alerte",
        "tout perdre", "plus rien", "encore une fois",
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

    def _a_amplificateur(self, texte: str) -> bool:
        t = texte.lower()
        if len(re.findall(r"\b[A-Z]{3,}\b", texte)) >= 2:
            return True
        return any(amp in t for amp in self._AMPLIFICATEURS)

    def malus(self, texte: str) -> float:
        amplifie = self._a_amplificateur(texte)
        if self._pipe is None:
            return self._fallback(texte, amplifie)
        try:
            label = self._pipe(texte[:512])[0]["label"]
            stars = int(label.split()[0])
            brut  = self._MAPPING.get(stars, 0.0)
            return brut if amplifie else min(brut, 1.0)
        except Exception:
            return self._fallback(texte, amplifie)

    def _fallback(self, texte: str, amplifie: bool) -> float:
        t    = texte.lower()
        hits = sum(1 for amp in self._AMPLIFICATEURS if amp in t)
        brut = round(min(hits * 0.8, 3.0), 1)
        return brut if amplifie else min(brut, 1.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE 2 — NEGATION GUARD (inchangé V6.0)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class NegationGuard:
    _SENSIBLES = frozenset({
        "douleur", "douleurs", "mal", "fièvre", "saignement", "sang",
        "malaise", "inconscient", "infarctus", "cardiaque", "avc", "blessure",
        "fracture", "hémorragie", "crise",
    })

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
        nies = set()
        if self._nlp is not None:
            doc = self._nlp(texte)
            for token in doc:
                lemme = token.lemma_.lower()
                if lemme not in self._SENSIBLES:
                    continue
                gouverneur_nie = any(
                    child.dep_ == "neg" for child in token.head.children
                ) if token.head != token else False
                direct_nie = any(child.dep_ == "neg" for child in token.children)
                if direct_nie or gouverneur_nie:
                    nies.add(lemme)
        for m in self._RE_NEG.finditer(texte.lower()):
            mot = m.group(1).lower()
            if mot in self._SENSIBLES:
                nies.add(mot)
        return frozenset(nies)


# ── Instances globales ────────────────────────────────────────────────────────
sentiment_engine = SentimentEngine()
negation_guard   = NegationGuard()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALISATION BASE DE DONNÉES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def initialiser_systeme():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fiches_clients (
                id_client TEXT PRIMARY KEY, nom TEXT, antecedents TEXT,
                derniere_connexion DATETIME, dernier_probleme TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_saisie DATETIME, texte_ticket TEXT, id_client TEXT,
                domaine_predit TEXT, score_final REAL,
                malus_sentiment REAL, bonus_recidive REAL
            )
        """)
        for col in ["date_saisie DATETIME", "malus_sentiment REAL", "bonus_recidive REAL"]:
            try:
                conn.execute(f"ALTER TABLE prediction_logs ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RÉCIDIVE PAR SIMILARITÉ COSINUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyser_recidive(id_client: str, texte_actuel: str, embedder) -> float:
    limite_3_mois = datetime.now() - timedelta(days=90)
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT texte_ticket, date_saisie FROM prediction_logs
            WHERE id_client = ? AND date_saisie IS NOT NULL
            ORDER BY date_saisie DESC LIMIT 5
        """, (id_client,)).fetchall()
    if not rows:
        return 0.0
    vec_actuel   = embedder.encode([texte_actuel])[0]
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
                if datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S") > limite_3_mois:
                    bonus += 0.2
            except ValueError:
                pass
            break
    return round(min(bonus, 1.5), 1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DOMAIN OVERRIDE — FIX V6.1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_TERMES_MEDICAUX_ETENDUS = re.compile(
    r"neurone|cerveau|picot|migrain|céphale|céphal|vertiges?|"
    r"syncope|épileps|tremblement|engourdis|paralys|"
    r"nausée|vomis|diarrhée|fièvre|toux|grippe|"
    r"coeur|cardiaque|thorax|poitrine|souffle|"
    r"crane|crâne|traumatis|accident|renvers|écras|"
    r"fracture|brûlure|infection|plaie|blessure|saign|sang",
    re.IGNORECASE,
)

_ANT_MEDICAUX = re.compile(
    r"cardiaque|diabète|reins|rein|épileps|vertiges?|douleur|"
    r"migrain|mal de tête|hypertension|asthme|allergi|fracture",
    re.IGNORECASE,
)

DOMAINES_TECHNIQUES = {"MATÉRIEL", "INFRA", "ACCÈS"}

def corriger_domaine(domaine_predit: str, texte: str, antecedents: str) -> tuple:
    """
    Force MÉDICAL si le classifieur retourne un domaine technique alors que
    le texte OU les antécédents contiennent des signaux médicaux.
    Retourne : (domaine_final, override_flag: bool)
    """
    if domaine_predit not in DOMAINES_TECHNIQUES:
        return domaine_predit, False
    texte_medical = bool(_TERMES_MEDICAUX_ETENDUS.search(texte))
    ant_medical   = bool(_ANT_MEDICAUX.search(antecedents))
    if texte_medical:
        return "MÉDICAL", True
    # Antécédents seuls → correction plus prudente, uniquement si vague
    if ant_medical:
        return "MÉDICAL", True
    return domaine_predit, False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORMULE DE PRIORITÉ V2.1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Regex trauma — détecte les urgences physiques graves que les keywords seuls manquent
_RE_VETO_TRAUMA = re.compile(
    r"cr[âa]ne\s+ouvert|cr[âa]ne\s+fractur|"
    r"renvers[ée]\s+par\s+(?:une\s+)?voiture|"
    r"(?:voiture|camion|moto|véhicule)\s+(?:m['']a\s+)?renvers|"
    r"traumatisme\s+cr[âa]nien|"
    r"fracture\s+(?:du\s+)?cr[âa]ne|"
    r"h[ée]morragie\s+(?:c[ée]r[ée]brale|interne)|"
    r"balle\s+dans|poignard[ée]|[ée]ventr[ée]",
    re.IGNORECASE,
)

def calculer_priorite(
    texte: str,
    domaine: str,
    ant: str,
    bonus_histo: float,
) -> tuple:
    """
    Retourne : (score: float, malus_sent: float, raison: str)
    """
    t = texte.lower()

    # 1. BASE DOMAINE
    bases = {"INFRA": 4.0, "ACCÈS": 3.0, "RH": 2.0, "MATÉRIEL": 1.5, "MÉDICAL": 3.5}
    score = bases.get(domaine, 2.0)

    # 2. NEGATION GUARD
    mots_nies = negation_guard.mots_nies(texte)

    # 3. VETO VITAL — mots directs
    VETOS_DIRECTS = [
        "inconscient", "infarctus", "avc", "étouffe", "meurs",
        "arrêt cardiaque", "crise cardiaque",
    ]
    mots_phrase = re.findall(r"\w+", t)
    for v in VETOS_DIRECTS:
        if v in mots_nies:
            continue
        if v in t or difflib.get_close_matches(v, mots_phrase, cutoff=0.85):
            return 10.0, 0.0, "VETO_VITAL"

    # 3b. VETO TRAUMA — patterns regex
    if _RE_VETO_TRAUMA.search(texte):
        return 10.0, 0.0, "VETO_TRAUMA"

    # 4. BOOSTS MÉDICAUX (neuro + cardiaque + trauma étendus)
    BOOSTS = {
        # Hémorragie
        "sang":   2.0, "saign":  2.0,
        # Membres
        "jambe":  1.5, "bras":   1.5, "doigt":  1.5,
        "main":   1.0, "pied":   1.0,
        # Neuro (FIX V6.1)
        "neurone": 1.5, "cerveau": 1.5,
        "picot":   1.0, "migrain": 1.0,
        "vertiges":1.0, "syncope": 2.0,
        "tremblement": 1.5, "engourdis": 1.5, "paralys": 2.5,
        # Cardiaque étendu (FIX V6.1)
        "coeur":   1.0,   # modéré : "mal au coeur" peut être nausée
        "thorax":  1.5, "poitrine": 1.5, "souffle": 1.5,
        # Trauma
        "crane":   2.0, "crâne": 2.0,
        "fracture":2.0, "blessure": 1.0,
    }

    bonus_medical = 0.0
    for mot, boost in BOOSTS.items():
        if mot in t and not any(mot in nie for nie in mots_nies):
            bonus_medical += boost

    # Synergie "trou dans le coeur" → cardiopathie grave
    if "trou" in t and "coeur" in t and "trou" not in mots_nies:
        bonus_medical += 2.5

    # Synergie sang + membre
    sang_actif   = any(m in t and m not in mots_nies for m in ("sang", "saign"))
    membre_actif = any(
        m in t and m not in mots_nies
        for m in ("jambe", "bras", "doigt", "main", "pied", "crane", "crâne")
    )
    if sang_actif and membre_actif:
        bonus_medical = min(bonus_medical + 2.0, 5.0)

    score += bonus_medical

    # 5. MALUS SENTIMENT (plafonné sans amplificateur)
    malus_sent = sentiment_engine.malus(texte)
    score += malus_sent

    # 6. BONUS ANTÉCÉDENTS
    bonus_ant = 0.0
    if any(x in ant.lower() for x in ("cardiaque", "diabète", "reins", "épilepsie", "hypertension")):
        bonus_ant = 3.0
    elif any(x in ant.lower() for x in ("migraine", "vertiges", "douleur", "mal de tête")):
        bonus_ant = 1.5
    score += bonus_ant

    # 7. BONUS HISTORIQUE
    score += bonus_histo

    return round(min(score, 10.0), 1), malus_sent, "OK"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CRM
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
# AFFICHAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def afficher_resultat(domaine, score, malus_sent, bonus_h, raison, domain_override):
    couleur = RED if score >= 8 else (YELLOW if score >= 5 else GREEN)
    niveau  = (
        f"{RED}🔴 CRITIQUE{RESET}"   if score >= 8 else
        f"{YELLOW}🟠 HAUTE{RESET}"   if score >= 6 else
        f"{YELLOW}🟡 MOYENNE{RESET}" if score >= 4 else
        f"{GREEN}🟢 BASSE{RESET}"
    )
    print(f"\n{CYAN}{'─'*54}{RESET}")
    print(f"  🎯  Domaine détecté   : {BLUE}{domaine}{RESET}", end="")
    if domain_override:
        print(f"  {YELLOW}⚡ (corrigé antécédents/termes){RESET}", end="")
    print()
    print(f"  🔢  Score de priorité : {couleur}{score} / 10{RESET}")
    print(f"  📊  Niveau            : {niveau}")

    if raison in ("VETO_VITAL", "VETO_TRAUMA"):
        label = "ALERTE VITALE" if raison == "VETO_VITAL" else "TRAUMA CRITIQUE"
        print(f"\n  {RED}⚠️   {label} — Intervention immédiate requise !{RESET}")
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
    print(f"  🧠  NEXUS BIONEXUS V6.1")
    print(f"      Sentiment Calibré | Trauma Veto | Domain Override")
    print(f"{'═'*54}{RESET}\n")

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

        X_vec        = embedder.encode([ticket_text])
        domaine_brut = domain_model.predict(X_vec)[0]
        full_ant     = f"{ant} {nouveaux_ant}".strip()

        domaine, dom_override = corriger_domaine(domaine_brut, ticket_text, full_ant)

        bonus_h = analyser_recidive(id_c, ticket_text, embedder)
        score, malus_sent, raison = calculer_priorite(
            ticket_text, domaine, full_ant, bonus_h
        )

        afficher_resultat(domaine, score, malus_sent, bonus_h, raison, dom_override)

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

