# nexus_qualification.py
import joblib
import os
from nexus_config import MODEL_FRICTION_PATH


class QualificationEngine:
    def __init__(self):
        if not os.path.exists(MODEL_FRICTION_PATH):
            raise FileNotFoundError(f"Modèle de friction absent : {MODEL_FRICTION_PATH}")
        self.friction_model = joblib.load(MODEL_FRICTION_PATH)

    def qualifier_ticket(self, texte, domaine_principal):
        """
        Utilise le classifieur binaire pour déterminer si le ticket est complet (1) ou incomplet (0).
        """
        t = texte.lower()

        if len(t.split()) < 3:
            return False, "Respirez calmement. Je suis là pour vous aider mais votre message est un peu court. Que se passe-t-il exactement ?"

        # Prédiction ML : 1 = Complet, 0 = Incomplet
        prediction = self.friction_model.predict([texte])[0]

        if prediction == 1:
            return True, "Complet"

        # Si le modèle détecte une phrase pauvre, on adapte la relance au domaine pressenti
        if domaine_principal == "MÉDICAL":
            return False, "Restez avec moi. Pouvez-vous me dire précisément où la personne a mal et quels sont les symptômes ?"
        elif domaine_principal == "POMPIER":
            return False, "Les pompiers sont en écoute. S'agit-il d'un incendie, d'une fuite ou d'un accident ? Détaillez la situation et le lieu."
        elif domaine_principal == "POLICE":
            return False, "Mettez-vous à l'abri. Précisez ce qu'il se passe, l'adresse exacte, et si les individus sont toujours là."
        elif domaine_principal in ["INFRA", "MATÉRIEL", "ACCÈS"]:
            return False, "Nos techniciens sont prêts. Sur quel équipement rencontrez-vous ce problème et quelle est l'erreur exacte ?"
        else:
            return False, "Je n'ai pas assez d'informations pour vous diriger. Pouvez-vous détailler votre situation ?"