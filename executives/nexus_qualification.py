# executives/nexus_qualification.py
import joblib
import os
import numpy as np
from nexus_config import MODEL_UNIFIED_PATH


class QualificationEngine:
    def __init__(self):
        if os.path.exists(MODEL_UNIFIED_PATH):
            self.model = joblib.load(MODEL_UNIFIED_PATH)
            self.mode = "ML"
            print(f"🔌 Cerveau Unifié ML chargé : {MODEL_UNIFIED_PATH}")
        else:
            self.model = None
            self.mode = "SIMULATION"
            print("⚠️ Aucun modèle ML trouvé. Mode SIMULATION activé.")

    def calculer_score_logique(self, severite, impact, cible):
        """Formule stratégique ajustée pour les urgences vitales."""
        try:
            sev = float(severite)
            imp = float(impact)
            cib = float(cible)

            score_base = ((sev * 2) + imp + cib) / 2

            # Override critique : Si la sévérité est maximale (mort/danger immédiat),
            # le score DOIT exploser dans le rouge, même si l'impact n'est que sur 1 personne.
            if sev >= 4:
                return max(score_base, 8.5)
            elif sev >= 3:
                return max(score_base, 6.0)

            return round(score_base, 1)
        except ValueError:
            return 5.0

    def evaluer_ticket(self, texte):
        if self.mode == "ML":
            try:
                prediction = self.model.predict([texte])[0]

                if len(prediction) == 5:
                    domaine = str(prediction[0])
                    severite = int(float(prediction[1]))
                    impact = int(float(prediction[2]))
                    cible = int(float(prediction[3]))
                    friction = str(prediction[4])

                    score = self.calculer_score_logique(severite, impact, cible)
                    return domaine, score, friction
                else:
                    return "ERREUR_ROUTAGE", 10.0, "COMPLET"

            except Exception as e:
                print(f"❌ Erreur lors de l'inférence ML : {e}")
                return "ERREUR_SYSTEME", 10.0, "COMPLET"
        else:
            domaine = "MÉDICAL" if "sang" in texte.lower() else "DIGITAL SUPPORT"
            return domaine, 2.5, "MANQUE_LIEU"