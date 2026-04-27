# main.py
import joblib
import os
import sqlite3
import warnings
import datetime
from nexus_core import TextEncoder
from nexus_config import *

warnings.filterwarnings("ignore")


class ShadowLogger:
    """Enregistre silencieusement toutes les interactions pour ré-entraînement futur"""

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

        # 1. Filtre Pop-Culture étendu
        mots_fiction_etendus = FICTION_MARKERS + ["titan", "zombie", "alien", "vampire", "monstre"]
        if any(f in t for f in mots_fiction_etendus):
            # Exception : Si on parle d'un cinéma en feu, c'est grave. Sinon, c'est de la fiction.
            if not ("cinéma" in t and ("incendie" in t or "feu" in t)):
                return True, "Contexte de fiction, manga ou fausse alerte détecté."

        # 2. Détection de négation
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
        print("🧠 Initialisation NEXUS V12 UNIFIÉE (Version Finale Corrigée)...")
        self.model_unified = joblib.load(MODEL_PATH)
        self.model_friction = joblib.load(MODEL_FRICTION_PATH)
        self.guard = NegationGuard()
        self.logger = ShadowLogger()

    def evaluer_ticket(self, texte_original, force_score=False):
        # 1. Analyse Unifiée
        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = pred_uni[0]
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])

        probas = self.model_unified.predict_proba([texte_original])
        confiance = max(probas[0][0]) if len(probas) > 0 else 0.5

        # 2. Garde de sécurité (Négation et Fiction)
        is_negated, raison = self.guard.contient_negation(texte_original, ["arme", "feu", "urgence"])
        if is_negated:
            return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison}"], True, domaine, impact, urgence, confiance

        # 3. L'EMPATHIE DYNAMIQUE (Friction)
        # On ne pose la question QUE si le script ne force pas la note finale
        if not force_score:
            statut_friction = self.model_friction.predict([texte_original])[0]
            if statut_friction != "COMPLET":
                import random
                amorce = f"Je vois qu'il s'agit potentiellement d'un cas pour le service {domaine}."

                # Ces questions précises marcheront DÈS QUE les fichiers Kaggle seront installés
                if statut_friction == "PRECISION_MED":
                    questions = ["Où avez-vous mal exactement ?", "La personne est-elle consciente ?"]
                elif statut_friction == "PRECISION_POL":
                    questions = ["Y a-t-il des armes visibles ?", "Où se passe l'incident exactement ?"]
                elif statut_friction == "PRECISION_POMP":
                    questions = ["Y a-t-il des personnes coincées à l'intérieur ?", "Y a-t-il des flammes ?"]
                elif "TECH" in statut_friction or domaine in ["INFRA", "MATÉRIEL", "ACCÈS"]:
                    questions = ["Quel est le message d'erreur affiché ?", "Quel équipement précis est concerné ?"]
                else:
                    # Le texte de secours (pour ton vieux modèle actuel)
                    questions = ["Pouvez-vous m'en dire un peu plus (localisation, symptômes, détails) ?"]

                question_choisie = random.choice(questions)
                return domaine, 0, [f"{amorce} {question_choisie}"], False, domaine, impact, urgence, confiance

        # 4. SYNERGIES & CALCUL DU SCORE FINAL
        domaines_assignes = [domaine]
        texte_lower = texte_original.lower()
        for mot_cle, services in SYNERGIES_URGENCE.items():
            if mot_cle in texte_lower:
                for s in services:
                    if s not in domaines_assignes:
                        domaines_assignes.append(s)

        score = MATRICE_PRIORITE[impact - 1][urgence - 1] if 1 <= impact <= 4 and 1 <= urgence <= 4 else 1.0
        raisons = [f"Impact IA: {impact}/4", f"Urgence IA: {urgence}/4", f"Confiance: {confiance:.1%}"]

        # Si l'IA détecte plusieurs services, on booste le score !
        if len(domaines_assignes) > 1:
            score = max(score, 9.5)
            raisons.insert(0, f"⚠️ SYNERGIE DÉTECTÉE : Intervention {', '.join(domaines_assignes)}")
            domaine_final = " + ".join(domaines_assignes)
        else:
            domaine_final = domaine

        return domaine_final, score, raisons, True, domaine, impact, urgence, confiance


if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 50)
    print("🚀 NEXUS V12 UNIFIÉE - OPÉRATIONNEL")
    print("=" * 50)

    while True:
        ticket = input("\n📝 Ticket : ").strip()
        if not ticket or ticket.lower() in ['exit', 'q', 'quit']: break

        ticket_complet = False
        tentatives_friction = 0
        ticket_final = ticket

        # L'IA a le droit de poser 2 questions maximum pour ne pas agacer le client
        while not ticket_complet and tentatives_friction < 2:
            domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf = nexus.evaluer_ticket(
                ticket_final, force_score=False)

            if not ticket_complet:
                print(f"🎯 Domaine pressenti : {domaine} (Analyse en pause)")
                print(f"🛑 AUTO-QUALIFICATION : {raisons[0]}")
                complement = input("💬 Précisez SVP : ").strip()
                if complement.lower() in ['exit', 'q', 'quit']: break
                ticket_final = ticket_final + ". " + complement
                tentatives_friction += 1

        if ticket_final.lower() in ['exit', 'q', 'quit']: break

        # LE CORRECTIF DU "0/10" EST ICI : On force le calcul des scores finaux !
        if not ticket_complet:
            domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf = nexus.evaluer_ticket(
                ticket_final, force_score=True)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"
        print(f"\n✅ TICKET QUALIFIÉ !")
        print(f"🎯 {domaine} | 🔢 {score}/10 -> {niveau}")
        for r in raisons:
            print(f"💡 {r}")

        # Logging fantôme pour l'apprentissage futur
        nexus.logger.log(ticket, ticket_final, dom_brut, imp_brut, urg_brut, conf)