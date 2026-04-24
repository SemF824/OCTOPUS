# main.py
import joblib
import os
import warnings
import numpy as np
from nexus_core import TextEncoder
from nexus_config import *
from nexus_qualification import QualificationEngine

warnings.filterwarnings("ignore")


class NegationGuard:
    def contient_negation(self, texte, mots_sensibles):
        t = texte.lower()

        # 1. Filtre fiction (anime, film, manga)
        if any(f in t for f in FICTION_MARKERS):
            return True, "Contexte de fiction, manga ou fausse alerte détecté."

        # 2. Vérification syntaxique (tolérante aux fautes légères)
        mots_texte = t.split()
        for i, mot in enumerate(mots_texte):
            # On vérifie si une partie d'un mot sensible est là (ex: 'arm' attrape 'amres' si faute légère ou 'armes')
            for sensible in mots_sensibles:
                if sensible[:3] in mot:  # vérifie la racine
                    fenetre_avant = " ".join(mots_texte[max(0, i - 3):i])
                    if any(neg in fenetre_avant for neg in NEGATION_MARKERS):
                        return True, f"Négation détectée près du mot clé ({sensible})."
        return False, ""


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V12 UNIFIÉE (Nuances & Questions ML)...")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Modèle absent à {MODEL_PATH}.")
            exit()
        self.model = joblib.load(MODEL_PATH)
        self.qualifier = QualificationEngine()
        self.negation_guard = NegationGuard()

    def evaluer_ticket(self, texte):
        t_lower = texte.lower()

        # --- NEGATION & FICTION GUARD ---
        mots_critiques = ["arme", "couteau", "feu", "incendie", "blessé", "mort", "urgence", "saigne", "braquage",
                          "voleur", "tueur"]
        est_nie, raison_negation = self.negation_guard.contient_negation(texte, mots_critiques)
        if est_nie:
            return "INFORMATION / SÉCURITÉ", 1.0, [f"⚠️ {raison_negation}"], True

        # --- SYNERGIES MULTI-FORCES ---
        domaines_assignes = []
        for mot_cle, liste_domaines in SYNERGIES_URGENCE.items():
            if mot_cle in t_lower:
                domaines_assignes = liste_domaines
                break

        # --- PRÉDICTION IA (Domaine, Impact, Urgence) ---
        pred = self.model.predict([texte])[0]
        domaine_ia, impact, urgence = pred[0], int(pred[1]), int(pred[2])

        probas = self.model.predict_proba([texte])
        try:
            confiance = np.max(probas[0][0])
        except:
            confiance = np.max(probas[0])

        if not domaines_assignes:
            if confiance < CONFIDENCE_THRESHOLD and len(texte.split()) <= 4:
                return "INCONNU", 0.0, [
                    "Je ne suis pas certain de bien comprendre la situation. Pouvez-vous reformuler ?"], False
            domaines_assignes = [domaine_ia]

        domaine_principal = domaines_assignes[0]

        # --- AUTO-QUALIFICATION PAR ML ---
        est_complet, question = self.qualifier.qualifier_ticket(texte, domaine_principal)

        if not est_complet:
            return " + ".join(domaines_assignes), 0.0, [f"🛑 AUTO-QUALIFICATION : {question}"], False

        # --- CALCUL DU SCORE (Matrice Dynamique) ---
        impact = max(1, min(4, impact))
        urgence = max(1, min(4, urgence))
        score = MATRICE_PRIORITE[impact - 1][urgence - 1]

        raisons = [f"Impact IA: {impact}/4", f"Urgence IA: {urgence}/4", f"Confiance: {confiance:.1%}"]

        if len(domaines_assignes) > 1:
            score = max(score, 9.5)
            raisons.insert(0, f"⚠️ SYNERGIE DÉTECTÉE : Intervention {', '.join(domaines_assignes)}")

        return " + ".join(domaines_assignes), score, raisons, True


if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 50)
    print("🚀 NEXUS V12 UNIFIÉE - OPÉRATIONNEL")
    print("=" * 50)

    while True:
        ticket = input("\n📝 Ticket : ").strip()
        if not ticket or ticket.lower() in ['exit', 'q', 'quit']: break

        ticket_complet = False
        while not ticket_complet:
            domaine, score, raisons, ticket_complet = nexus.evaluer_ticket(ticket)

            if not ticket_complet:
                print(f"🎯 Domaine pressenti : {domaine} (Analyse en pause)")
                print(f"{raisons[0]}")
                complement = input("💬 Votre réponse : ").strip()
                if complement.lower() in ['exit', 'q', 'quit']: break
                ticket = ticket + " " + complement

        if ticket.lower() not in ['exit', 'q', 'quit'] and ticket_complet and score > 0:
            prio = "🔴 CRITIQUE" if score >= 8 else ("🟠 HAUTE" if score >= 5 else "🟢 BASSE")
            print(f"\n✅ TICKET QUALIFIÉ !")
            print(f"🎯 {domaine} | 🔢 {score}/10 -> {prio}")
            print(f"💡 {', '.join(raisons)}")