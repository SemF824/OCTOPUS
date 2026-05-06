# main.py — NEXUS V32 (Système Expert - Entonnoir Conversationnel ML)
import spacy
import joblib
import os
import sqlite3
import warnings
import datetime
import random
import unicodedata
import re
from difflib import get_close_matches

from nexus_core import TextEncoder
from nexus_config import *

warnings.filterwarnings("ignore")

# Le dictionnaire maître pour corriger les fautes de frappe de l'utilisateur
DICTIONNAIRE_MAITRE = set(
    MOTS_LIEUX + MOTS_ARMES + MOTS_CORPS + MOTS_GRAVES +
    SYMPTOMES_GLOBAUX + SYMPTOMES_SEVERES + MOTS_BENINS +
    MOTS_ENTREPRISES + MOTS_DELITS + MOTS_SINISTRES + MOTS_IT
)


def enlever_accents(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn').lower()


def corriger_fautes_frappe(texte):
    texte_sans_accents = enlever_accents(texte)
    mots = re.findall(r'\b\w+\b', texte_sans_accents)
    texte_corrige = texte_sans_accents
    for mot in set(mots):
        if len(mot) >= 4 and mot not in DICTIONNAIRE_MAITRE:
            corrections = get_close_matches(mot, DICTIONNAIRE_MAITRE, n=1, cutoff=0.75)
            if corrections:
                bon_mot = corrections[0]
                texte_corrige = re.sub(rf'\b{mot}\b', bon_mot, texte_corrige)
    return texte_corrige


class NexusLinguisticEngine:
    def __init__(self):
        self.nlp = spacy.load("fr_core_news_md")
        self.ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = []
        for m in MOTS_LIEUX: patterns.append({"label": "LIEU", "pattern": m})
        for m in MOTS_ARMES: patterns.append({"label": "ARME", "pattern": m})
        for m in MOTS_CORPS: patterns.append({"label": "CORPS", "pattern": m})
        for m in MOTS_GRAVES: patterns.append({"label": "ALERTE_VITALE", "pattern": m})
        for m in FICTION_MARKERS: patterns.append({"label": "FICTION", "pattern": m})
        for m in NEGATION_MARKERS: patterns.append({"label": "NEGATION", "pattern": m})
        self.ruler.add_patterns(patterns)

    def analyser(self, texte):
        return self.nlp(corriger_fautes_frappe(texte))


class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS interactions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date_log TEXT, ticket_original TEXT, ticket_final TEXT,
            domaine_ia TEXT, impact_ia TEXT, urgence_ia TEXT, confiance TEXT, statut_humain TEXT DEFAULT 'A_VERIFIER')''')
        self.conn.commit()

    def log(self, t_orig, t_fin, dom, imp, urg, conf):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''INSERT INTO interactions_log (date_log, ticket_original, ticket_final, domaine_ia, impact_ia, urgence_ia, confiance)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (date_now, t_orig, t_fin, dom, str(imp), str(urg), f"{conf:.1%}"))
        self.conn.commit()


class LocationGuard:
    """Utilisé uniquement pour l'escalade des scores à la fin (savoir quelle zone du corps est touchée)"""

    def verifier_localisation(self, doc):
        has_lieu = False
        corps_trouves = []
        for ent in doc.ents:
            if ent.label_ == "CORPS":
                corps_trouves.append(ent.text)
            elif ent.label_ in ["LOC", "LIEU"]:
                mots_entite = enlever_accents(ent.text).split()
                if not any(c in mots_entite for c in MOTS_CORPS): has_lieu = True
        return has_lieu, list(set(corps_trouves))


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V32 (Entonnoir Conversationnel Machine Learning)...")
        self.engine = NexusLinguisticEngine()
        self.logger = ShadowLogger()
        self.location_guard = LocationGuard()

        # 1. CERVEAU D'ÉVALUATION (Domaine, Impact, Urgence)
        self.model_unified = joblib.load(MODEL_PATH)

        # 2. CERVEAU DE DIALOGUE (L'Entonnoir appris via le CSV)
        chemin_dialogue = "../pickle_result/nexus_v32_dialogue.pkl"
        if os.path.exists(chemin_dialogue):
            self.model_dialogue = joblib.load(chemin_dialogue)
        else:
            print(f"⚠️ ATTENTION : Le modèle de dialogue {chemin_dialogue} est introuvable !")
            print("Lancez le script nexus_dialogue_forge.py en premier.")
            self.model_dialogue = None

        # 3. LE DICTIONNAIRE DE RÉPONSES
        self.phrases_bot = {
            "DEMANDE_CORPS": "🩹 À quelle partie du corps se situe le problème ?",
            "DEMANDE_SYMPTOMES": "🩺 Quels sont les symptômes précis (vertiges, saignements, gonflement, type de douleur) ?",
            "DEMANDE_ANTECEDENTS": "👤 Quel est l'âge de la victime et a-t-elle des antécédents médicaux connus ?",
            "DEMANDE_ARME": "⚖️ Y a-t-il des armes visibles sur l'agresseur ou des blessés ?",
            "DEMANDE_LIEU": "🚨 Pour déclencher l'intervention, j'ai besoin de l'adresse ou de la ville exacte :"
        }

    def evaluer_ticket(self, texte_original: str, force_score: bool = False):
        doc = self.engine.analyser(texte_original)
        texte_propre = doc.text

        # ── 1. OVERRIDES STRICTS (Sécurité pour forcer le bon domaine si le ML hésite) ──
        domaine_force = None
        if any(d in texte_propre for d in MOTS_DELITS + ["braquage", "vol", "voleur"]):
            domaine_force = "POLICE"
        elif any(s in texte_propre for s in ["incendie", "feu", "fumee"]):
            domaine_force = "POMPIER"

        # On prédit le domaine de base pour l'affichage visuel
        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = domaine_force if domaine_force else pred_uni[0]

        # ==============================================================================
        # ── 2. LA MAGIE DE LA V32 : LE CERVEAU DE DIALOGUE GÈRE TOUT SEUL
        # ==============================================================================
        if not force_score and self.model_dialogue is not None:

            # Le modèle lit tout l'historique et prédit la PROCHAINE ÉTAPE
            prochaine_etape = self.model_dialogue.predict([texte_original])[0]

            # Tant que ce n'est pas COMPLET, on pose la question qu'il a choisie
            if prochaine_etape != "COMPLET":
                question_a_poser = self.phrases_bot.get(prochaine_etape, "Pouvez-vous préciser votre situation ?")
                return domaine, 0, [question_a_poser], False, domaine, 0, 0, 0.0

        # ==============================================================================
        # ── 3. VALIDATION ET NOTATION FINALE (Quand c'est "COMPLET")
        # ==============================================================================
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])
        confiance = float(max(self.model_unified.predict_proba([texte_original])[0])) if not domaine_force else 0.99

        has_lieu, corps_trouves = self.location_guard.verifier_localisation(doc)

        ajustements_raisons = []
        override_applique = False

        # A. Sur-notation Vitale Absolue
        mots_vitaux = ["reveille plus", "inconscient", "overdose", "crash", "bombe", "terrorist", "attentat",
                       "arret cardiaque", "respire plus", "hemorragie"]
        for mc in mots_vitaux:
            if mc in texte_propre:
                impact, urgence = 4, 4
                ajustements_raisons.append(f"🚀 SUR-NOTATION : Alerte vitale absolue détectée ('{mc}').")
                override_applique = True
                break

        # B. Escalade Sévère (Si pas vital, mais aggravant)
        if not override_applique:
            escalade_requise = False

            # L'IA vérifie le corps
            if any(c in corps_trouves for c in CORPS_SENSIBLES):
                escalade_requise = True
                ajustements_raisons.append("📈 ESCALADE : Partie du corps sensible touchée (Urgence rehaussée).")

            # L'IA vérifie les symptômes donnés
            elif any(ss in texte_propre for ss in
                     SYMPTOMES_SEVERES) or "vertige" in texte_propre or "sang" in texte_propre:
                escalade_requise = True
                ajustements_raisons.append("📈 ESCALADE : Symptômes cliniques aggravants détectés.")

            if escalade_requise:
                impact, urgence = max(impact, 3), max(urgence, 3)

        # Calcul du score final 1-10
        score = MATRICE_PRIORITE[impact - 1][urgence - 1] if 1 <= impact <= 4 and 1 <= urgence <= 4 else 1.0
        raisons = [f"Impact IA : {impact}/4", f"Urgence IA : {urgence}/4", f"Confiance : {confiance:.1%}"]
        raisons.extend(ajustements_raisons)

        return domaine, score, raisons, True, domaine, impact, urgence, confiance


# ==============================================================================
# BOUCLE PRINCIPALE (Multi-tours - 5 tentatives max)
# ==============================================================================
if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 52)
    print("🚀  NEXUS V32 — COMMAND CENTER (IA Data-Driven)")
    print("=" * 52)
    print("   Tapez 'exit' ou 'q' pour quitter.\n")

    while True:
        raw = input("📝 Ticket : ").strip()
        if not raw or raw.lower() in {"exit", "q", "quit"}: break

        ticket_final = raw
        ticket_complet = False
        tentatives = 0

        while not ticket_complet and tentatives < 5:
            (domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=False)

            if not ticket_complet:
                print(f"\n   🎯 Domaine estimé : {domaine}")
                print(f"   🤖 NEXUS : {raisons[0]}")
                complement = input("   💬 Vous : ").strip()
                if complement.lower() in {"exit", "q", "quit"}:
                    ticket_final = "exit"
                    break

                # LA CONCATÉNATION MAGIQUE DE L'HISTORIQUE !
                ticket_final = ticket_final + ". " + complement
                tentatives += 1

        if ticket_final.lower() in {"exit", "q", "quit"}: break

        # Si au bout de 5 tentatives ce n'est pas fini, on force le score (évite les boucles infinies)
        if not ticket_complet:
            (domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=True)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"

        print(f"\n   ✅ DOSSIER VALIDÉ ET TRANSMIS")
        print(f"   🎯 {domaine}  |  🔢 {score}/10  →  {niveau}")
        print(f"   📄 Résumé du dossier : {ticket_final}")
        for r in raisons:
            print(f"   💡 {r}")
        print()

        nexus.logger.log(raw, ticket_final, dom_brut, imp_brut, urg_brut, conf)