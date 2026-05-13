# executives/nexus_qualification.py
import joblib
import os
from nexus_config import MODEL_UNIFIED_PATH


class QualificationEngine:
    def __init__(self):
        # On charge ton futur modèle entraîné sur les 15 000 tickets
        if os.path.exists(MODEL_UNIFIED_PATH):
            self.model = joblib.load(MODEL_UNIFIED_PATH)
        else:
            self.model = None
            print(f"⚠️ Modèle {MODEL_UNIFIED_PATH} introuvable. Mode 'Simulation' activé.")

    def evaluer_ticket(self, texte):
        """
        Prend le texte et renvoie : (Domaine, Score sur 10, Friction manquante)
        """
        if self.model is None:
            # FALLBACK MOCK : Permet de tester le code avant d'avoir entraîné le ML
            return "DIGITAL SUPPORT", 3.5, "MANQUE_IDENTIFIANT"

        try:
            # On part du principe que ton futur modèle prédit ces 3 variables
            prediction = self.model.predict([texte])[0]
            domaine = prediction[0]
            score = float(prediction[1])
            friction = prediction[2]
            return domaine, score, friction
        except Exception as e:
            print(f"Erreur d'évaluation ML : {e}")
            return "INCONNU", 1.0, "MANQUE_CONTEXTE"