# main.py — NEXUS V30 (Architecture Multi-Agents / Tri-Cerveaux)
import spacy
import joblib
import os
import sqlite3
import warnings
import datetime
import unicodedata
import re
from difflib import get_close_matches

from nexus_core import TextEncoder
from nexus_config import *

warnings.filterwarnings("ignore")

# ─── AUTO-CORRECTEUR ORTHOGRAPHIQUE ────────────────────────────────
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


# ─── MOTEUR LINGUISTIQUE (spaCy) ───────────────────────────────────
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
        for m in MOTS_ENTREPRISES: patterns.append({"label": "ENTREPRISE", "pattern": m})
        self.ruler.add_patterns(patterns)

    def analyser(self, texte):
        return self.nlp(corriger_fautes_frappe(texte))


# ─── GUARDS & LOGGERS ──────────────────────────────────────────────
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


class NegationGuard:
    def contient_negation(self, doc):
        text_lower = doc.text.lower()
        if any(ex in text_lower for ex in ["exercice", "test", "simulation"]): return True, "Exercice détecté."
        if any(ent.label_ == "FICTION" for ent in doc.ents):
            if "apres le film" not in text_lower and not ("cinema" in text_lower and "feu" in text_lower):
                return True, "Contexte de fiction détecté."
        if [e for e in doc.ents if e.label_ == "NEGATION"] and [e for e in doc.ents if
                                                                e.label_ in ["ARME", "ALERTE_VITALE"]]:
            return True, "Négation détectée près d'un danger."
        return False, ""


# ─── SYSTÈME PRINCIPAL (LE CHEF D'ORCHESTRE) ───────────────────────
class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V30 (Architecture Tri-Cerveaux)...")
        self.engine = NexusLinguisticEngine()

        # 1. LE CERVEAU DE DÉCISION (Domaine, Impact, Urgence)
        self.model_unified = joblib.load(MODEL_PATH)

        # 2. LE CERVEAU ÉMOTIONNEL (Ton, Sentiment, Banalité)
        self.model_sentiment = joblib.load(MODEL_FRICTION_PATH)

        # 3. LE CERVEAU DE DIALOGUE (Traque des infos manquantes)
        # Assure-toi d'avoir entraîné ce modèle avec le script nexus_dialogue_forge.py !
        if os.path.exists("../pickle_result/nexus_v30_dialogue.pkl"):
            self.model_dialogue = joblib.load("../pickle_result/nexus_v30_dialogue.pkl")
        else:
            print("⚠️ Attention: Cerveau de dialogue introuvable. Mode dégradé.")
            self.model_dialogue = None

        self.guard = NegationGuard()
        self.logger = ShadowLogger()

        # Dictionnaire des questions générées par le Cerveau de Dialogue
        self.dictionnaire_questions = {
            "MANQUE_LIEU": "🚨 LOCALISATION MANQUANTE : À quelle adresse ou ville vous trouvez-vous ?",
            "MANQUE_LIEU_VITAL": "🚨 URGENCE VITALE : Donnez-moi immédiatement votre adresse ou ville exacte !",
            "MANQUE_CORPS": "🩹 PRÉCISION REQUISE : À quelle partie du corps se situe la blessure ou la douleur ?",
            "PRECISION_MED_SEVERE": "⚠️ Vous indiquez une blessure sérieuse. Sur 10, quelle est la douleur ? Y a-t-il des saignements ?",
            "MANQUE_ARME": "⚖️ SÉCURITÉ : Y a-t-il des armes visibles (couteau, arme à feu, etc.) ?",
            "PRECISION_POMP": "🔥 Y a-t-il des personnes bloquées à l'intérieur ou des blessés ?",
            "MANQUE_CONTEXTE_IT": "🏢 CONTEXTE REQUIS : Pour quel site ou agence signalez-vous cet incident ?",
            "MANQUE_ERREUR": "💻 TECHNIQUE : Quel est le message d'erreur exact affiché à l'écran ?"
        }

    def evaluer_ticket(self, texte_original: str, force_score: bool = False):
        doc = self.engine.analyser(texte_original)
        texte_propre = doc.text

        # --- ÉTAPE 1 : CERVEAU DE DÉCISION ---
        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = pred_uni[0]
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])
        probas = self.model_unified.predict_proba([texte_original])
        confiance = float(max(probas[0][0])) if len(probas) > 0 else 0.5

        is_negated, raison = self.guard.contient_negation(doc)
        if is_negated:
            return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison}"], True, "INFO", 1, 1, confiance

        # --- ÉTAPE 2 : CERVEAU DE DIALOGUE (Poser les questions) ---
        if not force_score and self.model_dialogue:
            mots_detresse = ["au secours", "a l'aide", "aidez moi", "vite"]
            if any(texte_propre.strip() == md for md in mots_detresse) or (
                    len(texte_propre) < 15 and not any(ent.label_ for ent in doc.ents)):
                return domaine, 0, [
                    "🚨 DÉTRESSE : Que se passe-t-il exactement et où êtes-vous ?"], False, domaine, impact, urgence, confiance

            # Le modèle expert devine ce qui manque dans l'historique de la conversation
            statut_dialogue = self.model_dialogue.predict([texte_original])[0]

            if "COMPLET" not in statut_dialogue:
                question = self.dictionnaire_questions.get(statut_dialogue,
                                                           "Pouvez-vous me donner plus de détails sur la situation ?")
                return domaine, 0, [question], False, domaine, impact, urgence, confiance

        # --- ÉTAPE 3 : CERVEAU ÉMOTIONNEL ET NOTATION EXPERTE ---
        # Ici, l'ancien modèle friction sert à analyser le "sentiment" général de la demande
        sentiment_ia = self.model_sentiment.predict([texte_original])[0]
        ajustements_raisons = []
        override_applique = False

        # 3a. Sur-Notation absolue (Vital)
        mots_critiques = ["reveille plus", "inconscient", "overdose", "crash", "bombe", "terrorist", "attentat",
                          "arret cardiaque", "respire plus"]
        for mc in mots_critiques:
            if mc in texte_propre:
                impact, urgence = 4, 4
                ajustements_raisons.append(f"🚀 SUR-NOTATION : Alerte vitale absolue détectée ('{mc}').")
                override_applique = True
                break

                # 3b. Utilisation du Cerveau Émotionnel (Sentiment)
        if not override_applique:
            # Si le modèle émotionnel détecte une anomalie bénigne ou une simple demande de précision
            if sentiment_ia in ["DEMANDE_DETAILS_GENERAUX", "BENIN"]:
                has_grave = any(ent.label_ in ["ARME", "ALERTE_VITALE"] for ent in doc.ents)
                if not has_grave:
                    impact, urgence = 1, 1
                    ajustements_raisons.append(
                        f"🛡️ AJUSTEMENT (Cerveau Émotionnel) : Ton de la demande jugé bénin ({sentiment_ia}).")

        # Calcul final
        score = MATRICE_PRIORITE[impact - 1][urgence - 1] if 1 <= impact <= 4 and 1 <= urgence <= 4 else 1.0
        raisons = [f"Impact IA : {impact}/4", f"Urgence IA : {urgence}/4", f"Confiance : {confiance:.1%}"]
        raisons.extend(ajustements_raisons)

        return domaine, score, raisons, True, domaine, impact, urgence, confiance


if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 52)
    print("🚀  NEXUS V30 — COMMAND CENTER (Tri-Cerveaux)")
    print("=" * 52)
    print("   Tapez 'exit' ou 'q' pour quitter.\n")

    while True:
        raw = input("📝 Ticket : ").strip()
        if not raw or raw.lower() in {"exit", "q", "quit"}: break

        ticket_final = raw
        ticket_complet = False
        tentatives = 0

        while not ticket_complet and tentatives < 2:
            (domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=False)

            if not ticket_complet:
                print(f"\n   🎯 Domaine pressenti : {domaine}")
                print(f"   🛑 {raisons[0]}")
                complement = input("   💬 Précisez SVP : ").strip()
                if complement.lower() in {"exit", "q", "quit"}: break
                ticket_final = ticket_final + ". " + complement
                tentatives += 1

        if ticket_final.lower() in {"exit", "q", "quit"}: break

        if not ticket_complet:
            (domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=True)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"
        print(f"\n   ✅ TICKET QUALIFIÉ")
        print(f"   🎯 {domaine}  |  🔢 {score}/10  →  {niveau}")
        for r in raisons: print(f"   💡 {r}")
        print()
        nexus.logger.log(raw, ticket_final, dom_brut, imp_brut, urg_brut, conf)