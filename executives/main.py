# main.py — NEXUS V24 (Priorité Triage Anatomique)
import spacy
import joblib
import os
import sqlite3
import warnings
import datetime
import random
import unicodedata

from nexus_core import TextEncoder
from nexus_config import *

warnings.filterwarnings("ignore")


# ==============================================================================
# FONCTION DE NETTOYAGE
# ==============================================================================
def enlever_accents(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn').lower()


# ==============================================================================
# LE MOTEUR LINGUISTIQUE (spaCy)
# ==============================================================================
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
        return self.nlp(enlever_accents(texte))


# ==============================================================================
# SHADOW LOGGER
# ==============================================================================
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


# ==============================================================================
# GUARDS AVANCÉS (Sécurité, Négation, Géographie vs Anatomie)
# ==============================================================================
class NegationGuard:
    def contient_negation(self, doc):
        text_lower = doc.text.lower()
        if any(ex in text_lower for ex in ["exercice", "test", "simulation"]):
            return True, "Ceci est un exercice ou un test. Procédures annulées."

        if any(ent.label_ == "FICTION" for ent in doc.ents):
            if "cinema" in text_lower and ("incendie" in text_lower or "feu" in text_lower):
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
        """
        Retourne (has_lieu, corps_trouves)
        Distingue l'adresse géographique (rue, ville) de la localisation anatomique.
        """
        has_lieu = False
        corps_trouves = []

        for ent in doc.ents:
            if ent.label_ == "CORPS":
                corps_trouves.append(ent.text)
            elif ent.label_ in ["LOC", "LIEU"]:
                mots_entite = enlever_accents(ent.text).split()
                # On annule le lieu si spaCy a confondu une partie du corps avec un lieu
                is_body_part = any(c in mots_entite for c in MOTS_CORPS)
                if not is_body_part:
                    has_lieu = True

        return has_lieu, list(set(corps_trouves))


# ==============================================================================
# SYSTEME PRINCIPAL NEXUS
# ==============================================================================
class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V24 (Priorité Triage Anatomique)...")
        self.engine = NexusLinguisticEngine()
        self.model_unified = joblib.load(MODEL_PATH)
        self.model_friction = joblib.load(MODEL_FRICTION_PATH)
        self.guard = NegationGuard()
        self.location_guard = LocationGuard()
        self.logger = ShadowLogger()

    def evaluer_ticket(self, texte_original: str, force_score: bool = False):
        doc = self.engine.analyser(texte_original)
        texte_propre = doc.text

        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = pred_uni[0]
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])

        probas = self.model_unified.predict_proba([texte_original])
        confiance = float(max(probas[0][0])) if len(probas) > 0 else 0.5

        # ── 1. Filtre Fiction / Négation ──────────────────
        is_negated, raison = self.guard.contient_negation(doc)
        if is_negated:
            return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison}"], True, domaine, impact, urgence, confiance

        # ── 2. ANALYSE DES ENTITÉS (NER) ──────────────────
        has_lieu, corps_trouves = self.location_guard.verifier_localisation(doc)
        armes_trouvees = [ent.text for ent in doc.ents if ent.label_ == "ARME"]

        # ── 3. TRIAGE PRIORITAIRE (Anatomie avant Géo) ──────
        if not force_score:

            # A. PRIORITÉ MÉDICALE : Où est le mal ?
            if domaine == "MÉDICAL" and not corps_trouves:
                # Sauf si c'est une urgence globale comme un malaise ou arrêt
                if not any(mot in texte_propre for mot in ["malaise", "arret", "respire plus", "inconscient"]):
                    return domaine, 0, [
                        "🩹 PRÉCISION REQUISE : À quelle partie du corps se situe la blessure ou la douleur ?"], False, domaine, impact, urgence, confiance

            # B. PRIORITÉ POLICE : Y a-t-il une arme ?
            if domaine == "POLICE" and not armes_trouvees and "vol" not in texte_propre:
                statut_f = self.model_friction.predict([texte_original])[0]
                if statut_f == "PRECISION_POL":
                    return domaine, 0, [
                        "⚖️ SÉCURITÉ : Y a-t-il des armes visibles (couteau, arme à feu, etc.) ?"], False, domaine, impact, urgence, confiance

            # C. LOCALISATION GÉOGRAPHIQUE
            DOMAINES_TERRAIN = {"MÉDICAL", "POLICE", "POMPIER"}
            if domaine in DOMAINES_TERRAIN and not has_lieu:
                if corps_trouves:
                    msg = f"🚨 J'ai bien noté la blessure ({', '.join(corps_trouves)}), mais à quelle ADRESSE GÉOGRAPHIQUE exacte vous trouvez-vous ?"
                else:
                    msg = "🚨 LOCALISATION MANQUANTE : À quelle adresse ou ville vous trouvez-vous ?"
                return domaine, 0, [msg], False, domaine, impact, urgence, confiance

            # D. FRICTION ML CLASSIQUE (Reste des cas)
            statut_friction = self.model_friction.predict([texte_original])[0]
            if statut_friction != "COMPLET":
                amorce = f"Je vois qu'il s'agit potentiellement d'un cas pour le service {domaine}."

                if statut_friction == "PRECISION_POMP":
                    question = random.choice(
                        ["Y a-t-il des personnes coincées à l'intérieur ?", "Voyez-vous des flammes ou de la fumée ?"])
                elif "TECH" in statut_friction or domaine in {"INFRA", "MATÉRIEL", "ACCÈS"}:
                    question = "Quel est le message d'erreur exact ou l'équipement touché ?"
                else:
                    question = "Pouvez-vous donner plus de détails sur la situation ?"

                return domaine, 0, [f"{amorce} {question}"], False, domaine, impact, urgence, confiance

        # ── 4. ANTI-HYPOCONDRIE ────────────────────────────
        ajustements_raisons = []
        has_benin = any(mb in texte_propre for mb in MOTS_BENINS)
        has_grave = any(ent.label_ in ["ARME", "ALERTE_VITALE"] for ent in doc.ents)

        if has_benin and not has_grave:
            impact, urgence = 1, 1
            ajustements_raisons.append("🛡️ AJUSTEMENT : Situation bénigne détectée, urgence rétrogradée.")
        elif confiance < 0.40 and not has_grave:
            impact, urgence = min(impact, 2), min(urgence, 2)
            ajustements_raisons.append("📉 AJUSTEMENT : Confiance IA trop faible pour déclarer une crise majeure.")

        # ── 5. SYNERGIES MULTI-FORCES ──────────────────────
        domaines_assignes = [domaine]
        synergie_raisons = []

        for mot_cle, services in SYNERGIES_URGENCE.items():
            if enlever_accents(mot_cle) in texte_propre:
                for s in services:
                    if s not in domaines_assignes:
                        domaines_assignes.append(s)
                synergie_raisons.append(f"Mot-clé détecté : '{mot_cle.upper()}'")

        # ── 6. CALCUL DU SCORE ─────────────────────────────
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
    print("🚀  NEXUS V24 — COMMAND CENTER (spaCy NER + Anatomie)")
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