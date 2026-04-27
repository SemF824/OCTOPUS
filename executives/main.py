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
        # CORRECTION DU BUG "FILM" : Si on détecte un danger vital proche, on annule le filtre fiction
        urgences_reelles = ["incendie", "feu", "attaque", "blessé", "sang"]

        if any(f in t for f in FICTION_MARKERS):
            if not any(u in t for u in urgences_reelles):
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
        print("🧠 Initialisation NEXUS V12 UNIFIÉE (Shadow Logger Activé)...")
        self.model_unified = joblib.load(MODEL_PATH)
        self.model_friction = joblib.load(MODEL_FRICTION_PATH)
        self.guard = NegationGuard()
        self.logger = ShadowLogger()

    def evaluer_ticket(self, texte_original):
        # ... (Garde ta logique de base de prédiction unifiée ici) ...
        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine = pred_uni[0]
        impact = int(pred_uni[1])
        urgence = int(pred_uni[2])

        # Simulation de probabilité (RandomForest renvoie des probas par arbre)
        probas = self.model_unified.predict_proba([texte_original])
        confiance = max(probas[0][0]) if len(probas) > 0 else 0.5

        score = MATRICE_PRIORITE[impact - 1][urgence - 1] if 1 <= impact <= 4 and 1 <= urgence <= 4 else 1.0

        is_negated, raison = self.guard.contient_negation(texte_original, ["arme", "feu", "urgence"])
        if is_negated:
            return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison}"], True, domaine, impact, urgence, confiance

        # Évaluation Friction
        statut_friction = self.model_friction.predict([texte_original])[0]
        if statut_friction != "COMPLET":
            return domaine, 0, [
                "Votre message est très court ou manque de détails."], False, domaine, impact, urgence, confiance

        raisons = [f"Impact IA: {impact}/4", f"Urgence IA: {urgence}/4", f"Confiance: {confiance:.1%}"]
        return domaine, score, raisons, True, domaine, impact, urgence, confiance


if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 50)
    print("🚀 NEXUS V12 UNIFIÉE - OPÉRATIONNEL")
    print("=" * 50)

    while True:
        ticket = input("\n📝 Ticket : ").strip()
        if not ticket or ticket.lower() in ['exit', 'q', 'quit']: break

        ticket_complet = False
        tentatives_friction = 0  # <-- L'ANTI-BOUCLE EST LÀ
        ticket_final = ticket

        while not ticket_complet and tentatives_friction < 1:
            domaine, score, raisons, ticket_complet, dom_brut, imp_brut, urg_brut, conf = nexus.evaluer_ticket(
                ticket_final)

            if not ticket_complet:
                print(f"🎯 Domaine pressenti : {domaine} (Analyse en pause)")
                print(f"🛑 AUTO-QUALIFICATION : {raisons[0]}")
                complement = input("💬 Précisez SVP : ").strip()
                if complement.lower() in ['exit', 'q', 'quit']: break
                ticket_final = ticket_final + " . " + complement
                tentatives_friction += 1
                # À la prochaine boucle, tentatives_friction = 1, ça force le calcul final

        # Forcer le calcul final si l'anti-boucle a été déclenché
        if not ticket_complet:
            domaine, score, raisons, _, dom_brut, imp_brut, urg_brut, conf = nexus.evaluer_ticket(ticket_final)
            ticket_complet = True

        if ticket_final.lower() not in ['exit', 'q', 'quit']:
            niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"
            print(f"\n✅ TICKET QUALIFIÉ !")
            print(f"🎯 {domaine} | 🔢 {score}/10 -> {niveau}")
            print(f"💡 {raisons[0]}")

            # --- LOGGING SILENCIEUX ---
            nexus.logger.log(ticket, ticket_final, dom_brut, imp_brut, urg_brut, conf)