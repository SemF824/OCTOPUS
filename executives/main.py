# main.py
import joblib
import os
import warnings
from nexus_core import TextEncoder
from nexus_config import MODEL_PATH, NEGATION_MARKERS
from nexus_qualification import QualificationEngine

warnings.filterwarnings("ignore", category=UserWarning)


class NegationGuard:
    def contient_negation(self, texte, mots_sensibles):
        """Intercepte les phrases où un mot grave est annulé par une négation."""
        t = texte.lower()

        # 1. Annulations directes
        if any(annul in t for annul in ["fausse alerte", "erreur", "résolu", "c'est bon", "annuler"]):
            return True, "Annulation ou fausse alerte signalée."

        # 2. Vérification syntaxique de proximité
        mots_texte = t.split()
        for i, mot in enumerate(mots_texte):
            for sensible in mots_sensibles:
                if sensible in mot:
                    # On cherche une négation dans les 3 mots avant le mot sensible
                    fenetre_avant = " ".join(mots_texte[max(0, i - 3):i])
                    if any(neg in fenetre_avant for neg in NEGATION_MARKERS):
                        return True, f"Négation détectée près du mot clé ({sensible})."
        return False, ""


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V10 ORCHESTRATOR (Deep-Logic)...")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Modèle absent : {MODEL_PATH}")
            exit()

        self.domain_model = joblib.load(MODEL_PATH)
        self.qualifier = QualificationEngine()
        self.negation_guard = NegationGuard()

    def evaluer_ticket(self, texte):
        # 1. NEGATION GUARD
        mots_critiques = ["arme", "couteau", "feu", "incendie", "blessé", "mort", "urgence", "saigne"]
        est_nie, raison_negation = self.negation_guard.contient_negation(texte, mots_critiques)

        if est_nie:
            return "INFORMATION / ANNULATION", 1.0, [f"⚠️ {raison_negation}"], True

        # 2. PRÉDICTION MULTI-LABEL
        # On utilise predict() qui renvoie une matrice binaire, puis on la décode
        y_pred = self.domain_model.predict([texte])
        domaines_assignes = list(self.domain_model.mlb.inverse_transform(y_pred)[0])

        if not domaines_assignes:
            domaines_assignes = ["INCONNU"]

        domaine_principal = domaines_assignes[0]

        # 3. AUTO-QUALIFICATION PAR ML (Friction)
        est_complet, question = self.qualifier.qualifier_ticket(texte, domaine_principal)

        if not est_complet:
            nom_affichage = " + ".join(domaines_assignes) if domaines_assignes != ["INCONNU"] else "ANALYSE EN COURS"
            return nom_affichage, 0.0, [f"📝 INFO MANQUANTE : {question}"], False

        # 4. CALCUL DU SCORE GLOBAL (Simplifié pour l'exemple, priorise les urgences)
        score_global = 2.0
        raisons_globales = []

        for dom in domaines_assignes:
            r = [f"Analyse {dom}"]
            s = 2.0
            t_lower = texte.lower()

            if dom == "MÉDICAL":
                s = 5.0
                if any(m in t_lower for m in
                       ["hémorragie", "inconscient", "respire plus", "malaise", "arrêt", "coeur", "cœur"]):
                    s += 4.0
                    r.append("Signe d'urgence vitale (+4.0)")
            elif dom == "POMPIER":
                s = 5.0
                if any(m in t_lower for m in ["feu", "incendie", "flammes", "brûle"]):
                    s += 4.0
                    r.append("Risque incendie majeur (+4.0)")
            elif dom == "POLICE":
                s = 5.0
                if any(m in t_lower for m in ["arme", "couteau", "fusil", "braquage"]):
                    s += 4.0
                    r.append("Présence d'arme (+4.0)")

            raisons_globales.extend([f"[{dom}] {raison}" for raison in r])
            if s > score_global:
                score_global = s

        if len(domaines_assignes) > 1 and "INCONNU" not in domaines_assignes:
            score_global = max(score_global, 9.0)
            raisons_globales.insert(0, "⚠️ INTERVENTION MULTI-FORCES REQUISE")

        nom_domaine_final = " + ".join(domaines_assignes)
        return nom_domaine_final, round(score_global, 1), raisons_globales, True


if __name__ == "__main__":
    system = NexusMainSystem()
    print("\n" + "=" * 50)
    print("🚀 NEXUS V10 - INTELLIGENCE MULTI-MODÈLES")
    print("=" * 50)
    print("Tapez 'q' ou 'exit' pour quitter le programme.")

    while True:
        ticket = input("\n📝 Description : ").strip()
        if ticket.lower() in ['exit', 'q', 'quit']:
            print("Arrêt du système NEXUS.")
            break

        ticket_complet = False
        while not ticket_complet:
            domaine, score, raisons, ticket_complet = system.evaluer_ticket(ticket)

            if not ticket_complet:
                print(f"🎯 Domaine pressenti : {domaine} (Analyse en pause)")
                print(f"⚠️ {raisons[0]}")
                complement = input("💬 Votre réponse : ").strip()
                if complement.lower() in ['exit', 'q', 'quit']:
                    ticket_complet = True
                    break
                ticket = ticket + " " + complement

        if ticket.lower() not in ['exit', 'q', 'quit'] and ticket_complet and score > 0:
            indicateur = "🔴" if score >= 8 else "🟠" if score >= 5 else "🟢"
            print(f"\n✅ TICKET QUALIFIÉ !")
            print(f"🎯 Domaine final : {domaine} | 🔢 Score : {score}/10 {indicateur}")
            print(f"💡 Analyse : {', '.join(raisons)}")