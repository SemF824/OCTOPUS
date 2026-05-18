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
        """Formule stratégique : Poids double sur la sévérité."""
        try:
            return ((float(severite) * 2) + float(impact) + float(cible)) / 2
        except ValueError:
            # Sécurité si le modèle ML renvoie des caractères inattendus
            return 5.0

    def evaluer_ticket(self, texte):
        if self.mode == "ML":
            try:
                prediction = self.model.predict([texte])[0]

                # Le pipeline V33 crache exactement 5 variables
                if len(prediction) == 5:
                    domaine = str(prediction[0])
                    severite = int(float(prediction[1]))
                    impact = int(float(prediction[2]))
                    cible = int(float(prediction[3]))
                    friction = str(prediction[4])

                    score = self.calculer_score_logique(severite, impact, cible)
                    return domaine, score, friction
                else:
                    print(f"⚠️ Format de prédiction inattendu (longueur {len(prediction)}).")
                    return "ERREUR_ROUTAGE", 10.0, "COMPLET"

            except Exception as e:
                print(f"❌ Erreur lors de l'inférence ML : {e}")
                return "ERREUR_SYSTEME", 10.0, "COMPLET"
        else:
            # Fallback en développement
            domaine = "MÉDICAL" if "sang" in texte.lower() else "DIGITAL SUPPORT"
            return domaine, 2.5, "MANQUE_LIEU"