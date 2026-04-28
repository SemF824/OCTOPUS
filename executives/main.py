import joblib
import os
import sqlite3
import warnings
import datetime
import random
from nexus_core import TextEncoder
from nexus_config import *

warnings.filterwarnings("ignore")


class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_log TEXT,
                ticket_original TEXT,
                ticket_final TEXT,
                domaine_ia TEXT,
                impact_ia TEXT,
                urgence_ia TEXT,
                confiance TEXT,
                statut_humain TEXT DEFAULT 'A_VERIFIER'
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


class NegationGuard:
    def contient_negation(self, texte, mots_sensibles):
        t = texte.lower()

        # Filtre anti-exercice (Nouveau !)
        mots_exercices = ["exercice", "test", "simulation", "entraînement"]
        if any(ex in t for ex in mots_exercices):
            return True, "Ceci est un exercice ou un test. Procédures d'urgence réelles annulées."

        mots_fiction_etendus = FICTION_MARKERS + ["titan", "zombie", "alien", "vampire", "monstre"]
        if any(f in t for f in mots_fiction_etendus):
            if not ("cinéma" in t and ("incendie" in t or "feu" in t)):
                return True, "Contexte de fiction, manga ou fausse alerte détecté."

        mots_texte = t.split()
        for i, mot in enumerate(mots_texte):
            for sensible in mots_sensibles:
                if sensible[:3] in mot:
                    fenetre_avant = " ".join(mots_texte[max(0, i - 3):i])
                    if any(neg in fenetre_avant for neg in NEGATION_MARKERS):
                        return True, f"Négation détectée près du mot clé ({sensible})."
        return False, ""


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V20 UNIFIÉE (Friction & Localisation Strictes)...")
        self.model_unified = joblib.load(MODEL_PATH)
        self.model_friction = joblib.load(MODEL_FRICTION_PATH)
        self.guard = NegationGuard()
        self.logger = ShadowLogger()

    def evaluer_ticket(self, texte_original, force_score=False):
        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = pred_uni[0]
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])

        probas = self.model_unified.predict_proba([texte_original])
        confiance = max(probas[0][0]) if len(probas) > 0 else 0.5
        texte_lower = texte_original.lower()

        # 1. Filtres absolus (Négation, Fiction, Exercice)
        is_negated, raison = self.guard.contient_negation(texte_original, ["arme", "feu", "urgence"])
        if is_negated:
            return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison}"], True, domaine, impact, urgence, confiance

        # 2. RÈGLE MÉTIER STRICTE : La Localisation Obligatoire (LocationGuard)
        mots_lieux = ["rue", "avenue", "boulevard", "bd", "secteur", "place", "route", "chemin", "ici", "adresse",
                      "bâtiment", "étage", "ville", "gare", "métro", "chez"]
        if domaine in ["MÉDICAL", "POLICE", "POMPIER"] and not force_score:
            if not any(lieu in texte_lower for lieu in mots_lieux):
                return domaine, 0, [
                    "🚨 LOCALISATION MANQUANTE : À quelle adresse ou lieu exact se déroule l'incident ?"], False, domaine, impact, urgence, confiance

        # 3. EMPATHIE DYNAMIQUE (Friction ML)
        if not force_score:
            statut_friction = self.model_friction.predict([texte_original])[0]
            if statut_friction != "COMPLET":
                amorce = f"Je vois qu'il s'agit potentiellement d'un cas pour le service {domaine}."
                if statut_friction == "PRECISION_MED":
                    q = ["Quels sont les symptômes exacts ?", "La victime est-elle consciente ?"]
                elif statut_friction == "PRECISION_POL":
                    q = ["Y a-t-il des armes visibles ?", "Combien d'individus sont impliqués ?"]
                elif statut_friction == "PRECISION_POMP":
                    q = ["Y a-t-il des personnes coincées ?", "Voyez-vous des flammes ou seulement de la fumée ?"]
                elif "TECH" in statut_friction or domaine in ["INFRA", "MATÉRIEL", "ACCÈS"]:
                    q = ["Quel est le message d'erreur ?", "Quel équipement est touché ?"]
                else:
                    q = ["Pouvez-vous donner plus de détails sur la situation ?"]

                return domaine, 0, [f"{amorce} {random.choice(q)}"], False, domaine, impact, urgence, confiance

        # 4. SYNERGIES & CALCUL DU SCORE
        domaines_assignes = [domaine]
        synergie_raisons = []

        # On lit le dictionnaire des synergies dans nexus_config.py
        for mot_cle, services in SYNERGIES_URGENCE.items():
            if mot_cle in texte_lower:
                for s in services:
                    if s not in domaines_assignes:
                        domaines_assignes.append(s)
                synergie_raisons.append(f"Mot-clé détecté : '{mot_cle.upper()}'")

        score = MATRICE_PRIORITE[impact - 1][urgence - 1] if 1 <= impact <= 4 and 1 <= urgence <= 4 else 1.0
        raisons = [f"Impact IA: {impact}/4", f"Urgence IA: {urgence}/4", f"Confiance: {confiance:.1%}"]

        # Boost du score si synergie
        if len(domaines_assignes) > 1:
            score = max(score, 9.5)  # Le point en plus est forcé ici
            raisons.insert(0, f"🔥 SYNERGIE ACTIVÉE ({' + '.join(domaines_assignes)})")
            for sr in synergie_raisons:
                raisons.insert(1, f"   -> {sr}")
            domaine_final = " + ".join(domaines_assignes)
        else:
            domaine_final = domaine

        return domaine_final, score, raisons, True, domaine, impact, urgence, confiance


if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 50)
    print("🚀 NEXUS V20 UNIFIÉE - COMMAND CENTER")
    print("=" * 50)

    while True:
        ticket = input("\n📝 Ticket : ").strip()
        if not ticket or ticket.lower() in ['exit', 'q', 'quit']: break

        ticket_complet = False
        tentatives_friction = 0
        ticket_final = ticket

        while not ticket_complet and tentatives_friction < 2:
            domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf = nexus.evaluer_ticket(
                ticket_final, force_score=False)

            if not ticket_complet:
                print(f"🎯 Domaine pressenti : {domaine} (Analyse en pause)")
                print(f"🛑 {raisons[0]}")
                complement = input("💬 Précisez SVP : ").strip()
                if complement.lower() in ['exit', 'q', 'quit']: break
                ticket_final = ticket_final + ". " + complement
                tentatives_friction += 1

        if ticket_final.lower() in ['exit', 'q', 'quit']: break

        if not ticket_complet:
            domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf = nexus.evaluer_ticket(
                ticket_final, force_score=True)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"
        print(f"\n✅ TICKET QUALIFIÉ !")
        print(f"🎯 {domaine} | 🔢 {score}/10 -> {niveau}")
        for r in raisons:
            print(f"💡 {r}")

        nexus.logger.log(ticket, ticket_final, dom_brut, imp_brut, urg_brut, conf)