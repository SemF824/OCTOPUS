# main.py — NEXUS V29 (Tolérance Fautes de Frappe Multidomaine + Émotions)
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
from nexus_qualification import QualificationEngine

warnings.filterwarnings("ignore")

# ─── AUTO-CORRECTEUR ORTHOGRAPHIQUE (FUZZY MATCHING GLOBAL) ────────
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

# ─── MOTEUR LINGUISTIQUE ───────────────────────────────────────────
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
        texte_corrige = corriger_fautes_frappe(texte)
        return self.nlp(texte_corrige)

# ─── SHADOW LOGGER ─────────────────────────────────────────────────
class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, date_log TEXT, ticket_original TEXT, ticket_final TEXT,
                domaine_ia TEXT, impact_ia TEXT, urgence_ia TEXT, confiance TEXT, statut_humain TEXT DEFAULT 'A_VERIFIER'
            )
        ''')
        self.conn.commit()

    def log(self, t_orig, t_fin, dom, imp, urg, conf):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO interactions_log (date_log, ticket_original, ticket_final, domaine_ia, impact_ia, urgence_ia, confiance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date_now, t_orig, t_fin, dom, str(imp), str(urg), f"{conf:.1%}"))
        self.conn.commit()

# ─── GUARDS AVANCÉS ────────────────────────────────────────────────
class NegationGuard:
    def contient_negation(self, doc):
        text_lower = doc.text.lower()
        if any(ex in text_lower for ex in ["exercice", "test", "simulation"]):
            return True, "Ceci est un exercice ou un test. Procédures annulées."

        if any(ent.label_ == "FICTION" for ent in doc.ents):
            if "apres le film" in text_lower or "apres mon film" in text_lower:
                pass
            elif "cinema" in text_lower and ("incendie" in text_lower or "feu" in text_lower):
                pass
            else:
                return True, "Contexte de fiction ou expression idiomatique détecté."

        entites_neg = [ent for ent in doc.ents if ent.label_ == "NEGATION"]
        entites_danger = [ent for ent in doc.ents if ent.label_ in ["ARME", "ALERTE_VITALE"]]

        if entites_neg and entites_danger:
            return True, f"Négation claire détectée près d'un mot de danger."

        return False, ""

class LocationGuard:
    def verifier_localisation(self, doc):
        has_lieu = False
        corps_trouves = []
        entreprise_trouvee = False

        for ent in doc.ents:
            if ent.label_ == "CORPS":
                corps_trouves.append(ent.text)
            elif ent.label_ == "ENTREPRISE":
                entreprise_trouvee = True
            elif ent.label_ in ["LOC", "LIEU"]:
                mots_entite = enlever_accents(ent.text).split()
                if not any(c in mots_entite for c in MOTS_CORPS):
                    has_lieu = True

        return has_lieu, list(set(corps_trouves)), entreprise_trouvee

# ─── SYSTEME PRINCIPAL NEXUS ───────────────────────────────────────
class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V29 (Auto-Correcteur Multidomaine)...")
        self.engine = NexusLinguisticEngine()
        self.model_unified = joblib.load(MODEL_PATH)
        self.guard = NegationGuard()
        self.location_guard = LocationGuard()
        self.logger = ShadowLogger()
        self.qualifier = QualificationEngine() # 🎯 Ton nouveau moteur est chargé ici

    def evaluer_ticket(self, texte_original: str, force_score: bool = False):
        doc = self.engine.analyser(texte_original)
        texte_propre = doc.text

        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = pred_uni[0]
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])

        probas = self.model_unified.predict_proba([texte_original])
        confiance = float(max(probas[0][0])) if len(probas) > 0 else 0.5

        # ── 1. Filtre Fiction / Négation
        is_negated, raison = self.guard.contient_negation(doc)
        if is_negated:
            # On demande au vigile de vérifier si c'est une blague avant de bloquer
            ton_global = self.qualifier._detecter_ton(texte_original)
            if ton_global != "IRONIE" and not any(mot in texte_propre for mot in ["rigole", "mdr", "blague", "lol"]):
                return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison}"], True, "INFO", 1, 1, confiance

        # ── 2. ANALYSE DES ENTITÉS (NER)
        has_lieu, corps_trouves, entreprise_trouvee = self.location_guard.verifier_localisation(doc)
        armes_trouvees = [ent.text for ent in doc.ents if ent.label_ == "ARME"]

        # ── 3. TRIAGE PRIORITAIRE
        if not force_score:
            mots_detresse = ["au secours", "a l'aide", "aidez moi", "vite"]
            if any(texte_propre.strip() == md for md in mots_detresse) or (
                    len(texte_propre) < 15 and not any(ent.label_ for ent in doc.ents)):
                return domaine, 0, ["🚨 DÉTRESSE : Que se passe-t-il exactement et où êtes-vous ?"], False, domaine, impact, urgence, confiance

            if domaine == "MÉDICAL" and not corps_trouves:
                if not any(mot in texte_propre for mot in SYMPTOMES_GLOBAUX):
                    return domaine, 0, ["🩹 PRÉCISION REQUISE : À quelle partie du corps se situe la blessure ou la douleur ?"], False, domaine, impact, urgence, confiance

            # E. NOUVEAU MOTEUR DE QUALIFICATION (ÉMOTIONS + FRICTION)
            ticket_complet, question_generale = self.qualifier.qualifier_ticket(texte_original, domaine)
            if not ticket_complet:
                return domaine, 0, [f"💬 {question_generale}"], False, domaine, impact, urgence, confiance

            DOMAINES_TERRAIN = {"MÉDICAL", "POLICE", "POMPIER"}
            if domaine in DOMAINES_TERRAIN and not has_lieu:
                msg = f"🚨 J'ai bien noté l'alerte ({', '.join(corps_trouves)}), mais à quelle ADRESSE GÉOGRAPHIQUE vous trouvez-vous ?" if corps_trouves else "🚨 LOCALISATION MANQUANTE : À quelle adresse ou ville vous trouvez-vous ?"
                return domaine, 0, [msg], False, domaine, impact, urgence, confiance

            DOMAINES_IT = {"INFRA", "MATÉRIEL", "ACCÈS"}
            if domaine in DOMAINES_IT and not entreprise_trouvee and not has_lieu:
                return domaine, 0, ["🏢 CONTEXTE REQUIS : Pour quelle société, agence ou site signalez-vous cet incident ?"], False, domaine, impact, urgence, confiance


        # ── 4. NOTATION EXPERTE (Override & Escalade)
        ajustements_raisons = []
        override_applique = False

        # 🛡️ BOUCLIER ANTI-IRONIE
        ton_global = self.qualifier._detecter_ton(texte_original)
        if ton_global == "IRONIE" or any(mot in texte_propre for mot in ["rigole", "mdr", "blague", "lol"]):
            impact, urgence = 1, 1
            ajustements_raisons.append("🤡 IRONIE DÉTECTÉE : L'utilisateur plaisante, urgence rétrogradée.")
            override_applique = True

        if not override_applique:
            mots_critiques = ["reveille plus", "inconscient", "overdose", "crash", "bombe", "terrorist", "attentat",
                              "arret cardiaque", "crise cardiaque", "respire plus"]
            for mc in mots_critiques:
                if mc in texte_propre:
                    impact, urgence = 4, 4
                    ajustements_raisons.append(f"🚀 SUR-NOTATION : Alerte vitale absolue détectée ('{mc}').")
                    override_applique = True
                    break

        if not override_applique:
            escalade_requise = False
            raison_escalade = ""

            if any(c in corps_trouves for c in CORPS_SENSIBLES):
                escalade_requise = True
                raison_escalade = "Partie du corps sensible touchée"

            elif any(ss in texte_propre for ss in SYMPTOMES_SEVERES):
                escalade_requise = True
                raison_escalade = "Symptôme sévère détecté"

            elif domaine in {"INFRA", "MATÉRIEL", "ACCÈS"} and any(
                    vip in texte_propre for vip in ["siege", "datacenter", "direction"]):
                escalade_requise = True
                raison_escalade = "Site IT critique impacté"

            if escalade_requise:
                impact, urgence = max(impact, 3), max(urgence, 3)
                ajustements_raisons.append(f"📈 ESCALADE : {raison_escalade}. Urgence rehaussée.")
                override_applique = True

        # ── 5. ANTI-HYPOCONDRIE
        if not override_applique:
            has_benin = any(mb in texte_propre for mb in MOTS_BENINS)
            has_grave = any(ent.label_ in ["ARME", "ALERTE_VITALE"] for ent in doc.ents)

            if has_benin and not has_grave:
                impact, urgence = 1, 1
                ajustements_raisons.append("🛡️ AJUSTEMENT : Situation bénigne détectée, urgence rétrogradée.")
            elif confiance < 0.40 and not has_grave:
                impact, urgence = min(impact, 2), min(urgence, 2)
                ajustements_raisons.append("📉 AJUSTEMENT : Confiance IA trop faible pour déclarer une crise majeure.")

        # ── 6. SYNERGIES MULTI-FORCES
        domaines_assignes = [domaine]
        synergie_raisons = []

        for mot_cle, services in SYNERGIES_URGENCE.items():
            if enlever_accents(mot_cle) in texte_propre:
                for s in services:
                    if s not in domaines_assignes:
                        domaines_assignes.append(s)
                synergie_raisons.append(f"Mot-clé détecté : '{mot_cle.upper()}'")

        # ── 7. CALCUL DU SCORE FINAL
        score = MATRICE_PRIORITE[impact - 1][urgence - 1] if 1 <= impact <= 4 and 1 <= urgence <= 4 else 1.0

        raisons = [f"Impact IA  : {impact}/4", f"Urgence IA : {urgence}/4", f"Confiance  : {confiance:.1%}"]
        raisons.extend(ajustements_raisons)

        if len(domaines_assignes) > 1:
            score = max(score, 9.5)
            raisons.insert(0, f"🔥 SYNERGIE ACTIVÉE ({' + '.join(domaines_assignes)})")
            for sr in synergie_raisons:
                raisons.insert(1, f"   -> {sr}")
            domaine_final = " + ".join(domaines_assignes)
        else:
            domaine_final = domaine

        return domaine_final, score, raisons, True, domaine, impact, urgence, confiance

# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================
if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 52)
    print("🚀  NEXUS V29 — COMMAND CENTER (Auto-Correcteur Multidomaine)")
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
                if complement.lower() in {"exit", "q", "quit"}:
                    ticket_final = "exit"
                    break
                ticket_final = ticket_final + ". " + complement
                tentatives += 1

        if ticket_final.lower() in {"exit", "q", "quit"}: break

        if not ticket_complet:
            (domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=True)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"

        print(f"\n   ✅ TICKET QUALIFIÉ")
        print(f"   🎯 {domaine}  |  🔢 {score}/10  →  {niveau}")
        for r in raisons:
            print(f"   💡 {r}")
        print()

        nexus.logger.log(raw, ticket_final, dom_brut, imp_brut, urg_brut, conf)