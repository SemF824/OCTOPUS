# executives/nexus_qualification.py
import joblib
import os
from nexus_config import MODEL_UNIFIED_PATH


class QualificationEngine:
    def __init__(self):
        if os.path.exists(MODEL_UNIFIED_PATH):
            self.model = joblib.load(MODEL_UNIFIED_PATH)
            self.mode = "ML"
            print(f"🔌 Modèle ML chargé : {MODEL_UNIFIED_PATH}")
        else:
            self.model = None
            self.mode = "SIMULATION"
            print("⚠️ Aucun modèle ML trouvé. Mode SIMULATION activé.")

    def calculer_score_logique(self, severite, impact, cible):
        # Formule : ((Sévérité * 2) + Impact + Cible) / 2
        return ((severite * 2) + impact + cible) / 2

    def evaluer_ticket(self, texte):
        if self.mode == "ML":
            prediction = self.model.predict([texte])[0]

            # 🔄 COMPATIBILITÉ AVEC L'ANCIEN MODÈLE V21 (3 variables)
            if len(prediction) == 3:
                domaine = prediction[0]
                impact = int(prediction[1])
                urgence = int(prediction[2])  # Dans l'ancien modèle, c'était l'urgence

                # On adapte l'ancienne "urgence" à la nouvelle "sévérité"
                score = self.calculer_score_logique(severite=urgence, impact=impact, cible=0)

                # L'ancien modèle ne prédisait pas la friction. On la simule pour tester Llama.
                if domaine in ["ACCÈS", "DIGITAL SUPPORT", "MATÉRIEL"]:
                    friction = "MANQUE_IDENTIFIANT"
                elif domaine == "MÉDICAL":
                    friction = "MANQUE_SYMPTOMES"
                else:
                    friction = "MANQUE_LIEU"

                return domaine, score, friction

            # 🚀 POUR LE FUTUR NOUVEAU MODÈLE (5 variables)
            else:
                domaine = prediction[0]
                score = self.calculer_score_logique(int(prediction[1]), int(prediction[2]), int(prediction[3]))
                friction = prediction[4]
                return domaine, score, friction

        else:
            # MODE SIMULATION (Si pas de .pkl du tout)
            domaine = "MÉDICAL" if "mal" in texte.lower() else "DIGITAL SUPPORT"
            score = 2.5
            friction = "MANQUE_LIEU"
            return domaine, score, friction