# main.py
import joblib
import os
import warnings
from nexus_core import TextEncoder  # Requis pour décompresser le modèle
from nexus_config import MODEL_PATH, CONFIDENCE_THRESHOLD
from nexus_qualification import QualificationEngine  # Import du nouveau moteur

# Supprimer les alertes de version de librairies
warnings.filterwarnings("ignore", category=UserWarning)


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V8.1 PRO (Avec Auto-Qualification)...")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Le modèle {MODEL_PATH} est absent. Lancez la Forge V8.")
            exit()

        # Chargement direct du modèle global
        self.domain_model = joblib.load(MODEL_PATH)
        # Instanciation de l'agent de qualification
        self.qualifier = QualificationEngine()

    def calculer_priorite_medicale(self, texte):
        t_lower = texte.lower()
        score = 5.0
        raisons = ["Analyse médicale standard"]

        blessures_mineures = ["doigt", "ongle", "égratignure", "coupure", "ampoule", "petit saignement"]
        if any(m in t_lower for m in blessures_mineures):
            score += 1.0
            raisons.append("Blessure périphérique mineure (+1.0)")

        elif any(m in t_lower for m in
                 ["hémorragie", "inconscient", "respire plus", "malaise", "arrêt", "coeur", "cœur", "poitrine",
                  "étouffe"]):
            score += 4.0
            raisons.append("Signe d'urgence vitale (+4.0)")

        elif any(m in t_lower for m in
                 ["sang", "saigne", "cassé", "fracture", "chute", "accident", "brûlure", "jambe", "bras", "nez"]):
            score += 2.0
            raisons.append("Traumatisme physique important (+2.0)")

        if any(m in t_lower for m in ["urgent", "maintenant", "en ce moment", "en cours", "vite"]):
            score += 2.0
            raisons.append("Situation immédiate (+2.0)")

        return min(score, 10.0), raisons

    def calculer_priorite_pompier(self, texte):
        t_lower = texte.lower()
        score = 5.0
        raisons = ["Évaluation pompier standard"]

        if any(m in t_lower for m in ["feu", "incendie", "flammes", "brûle", "fumée"]):
            score += 4.0
            raisons.append("Risque incendie majeur (+4.0)")

        if any(m in t_lower for m in ["gaz", "explosion", "fuite"]):
            score += 3.0
            raisons.append("Risque d'explosion/gaz (+3.0)")

        if any(m in t_lower for m in ["accident", "incarcéré", "bloqué"]):
            score += 2.0
            raisons.append("Sauvetage requis (+2.0)")

        return min(score, 10.0), raisons

    def calculer_priorite_police(self, texte):
        t_lower = texte.lower()
        score = 5.0
        raisons = ["Évaluation police standard"]

        if any(m in t_lower for m in ["arme", "couteau", "fusil", "braquage", "menace"]):
            score += 4.0
            raisons.append("Présence d'arme / Danger grave (+4.0)")

        if any(m in t_lower for m in ["agression", "frappe", "violences", "conjoint"]):
            score += 3.0
            raisons.append("Violences sur personne (+3.0)")

        if any(m in t_lower for m in ["cambriolage", "vol", "rodéo", "effraction"]):
            score += 1.5
            raisons.append("Atteinte aux biens / Ordre public (+1.5)")

        return min(score, 10.0), raisons

    def evaluer_ticket(self, texte):
        # 1. Prédiction avec analyse de probabilité (Niveau de confiance de l'IA)
        probas = self.domain_model.predict_proba([texte])[0]
        max_proba = max(probas)
        domaine = self.domain_model.classes_[probas.argmax()]

        # 2. Vérification de la confiance de l'IA
        if max_proba < CONFIDENCE_THRESHOLD:
            return domaine, 0.0, ["L'IA est incertaine du domaine. Pouvez-vous reformuler ou détailler ?"], False

        # 3. Auto-Qualification
        est_complet, question = self.qualifier.qualifier_ticket(texte, domaine)

        if not est_complet:
            # On bloque le calcul et on renvoie la question
            return domaine, 0.0, [f"📝 INFO MANQUANTE : {question}"], False

        # 4. Routage vers le bon algorithme de priorité (Le ticket est COMPLET)
        if domaine == "MÉDICAL":
            score, raisons = self.calculer_priorite_medicale(texte)
        elif domaine == "POMPIER":
            score, raisons = self.calculer_priorite_pompier(texte)
        elif domaine == "POLICE":
            score, raisons = self.calculer_priorite_police(texte)
        else:
            bases = {"INFRA": 4.0, "ACCÈS": 3.0, "MATÉRIEL": 1.5, "RH": 2.0}
            score = bases.get(domaine, 2.0)
            raisons = [f"Standard {domaine}"]

            if any(m in texte.lower() for m in ["urgent", "bloqué", "panne", "critique"]):
                score += 3.0
                raisons.append("Urgence technique détectée (+3.0)")

        return domaine, round(score, 1), raisons, True


if __name__ == "__main__":
    system = NexusMainSystem()
    print("\n" + "=" * 50)
    print("🚀 NEXUS V8.1 - MOTEUR D'INFÉRENCE OPÉRATIONNEL")
    print("=" * 50)
    print("Tapez 'q' ou 'exit' pour quitter le programme.")

    while True:
        ticket = input("\n📝 Description : ").strip()
        if ticket.lower() in ['exit', 'q', 'quit']:
            print("Arrêt du système NEXUS. À bientôt !")
            break

        # Boucle d'Auto-Qualification Conversationnelle
        ticket_complet = False
        while not ticket_complet:
            domaine, score, raisons, ticket_complet = system.evaluer_ticket(ticket)

            if not ticket_complet:
                print(f"🎯 Domaine pressenti : {domaine} (Analyse en pause)")
                print(f"⚠️ {raisons[0]}")
                # Demande à l'utilisateur de compléter
                complement = input("💬 Votre réponse : ").strip()
                if complement.lower() in ['exit', 'q', 'quit']:
                    ticket_complet = True  # Force la sortie
                    break
                # On fusionne l'ancienne description avec la nouvelle information
                ticket = ticket + " " + complement

        if ticket.lower() not in ['exit', 'q', 'quit']:
            # Affichage final une fois le ticket qualifié
            indicateur = "🔴" if score >= 8 else "🟠" if score >= 5 else "🟢"
            print(f"\n✅ TICKET QUALIFIÉ !")
            print(f"🎯 Domaine final : {domaine} | 🔢 Score : {score}/10 {indicateur}")
            print(f"💡 Analyse : {', '.join(raisons)}")