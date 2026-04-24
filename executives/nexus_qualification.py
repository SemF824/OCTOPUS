# nexus_qualification.py
import joblib
import os
from nexus_config import MODEL_FRICTION_PATH


class QualificationEngine:
    def __init__(self):
        if not os.path.exists(MODEL_FRICTION_PATH):
            self.friction_model = None
        else:
            self.friction_model = joblib.load(MODEL_FRICTION_PATH)

        # Lexiques pour la PERSONNALISATION DYNAMIQUE des messages
        self.mots_anatomie = ["nez", "doigt", "ongle", "main", "bras", "jambe", "tête", "crâne", "poitrine", "coeur",
                              "cœur", "ventre", "abdomen", "oeil", "yeux", "dos", "cou", "pied", "cheville"]
        self.mots_materiel = ["pc", "ordinateur", "serveur", "vpn", "écran", "imprimante", "réseau", "wifi", "clavier",
                              "souris", "câble", "routeur", "logiciel", "application"]

        # Templates dynamiques (Les {zone} et {equipement} seront remplacés par l'IA)
        self.dictionnaire_questions = {
            "DEMANDE_SYMPTOME_MED": "J'ai bien noté que cela concerne {zone}. Que ressentez-vous exactement (douleur, saignement, etc.) ?",
            "DEMANDE_LIEU_CORPS": "Je comprends vos symptômes. À quel endroit précis du corps avez-vous mal ?",
            "DEMANDE_ACTION_POLICE": "Mettez-vous à l'abri. Les suspects ou agresseurs sont-ils toujours sur place ?",
            "DEMANDE_LIEU_POLICE": "Pour envoyer les forces de l'ordre, j'ai absolument besoin de l'adresse ou du lieu précis.",
            "DEMANDE_ETAT_POMPIER": "SÉCURITÉ : Le bâtiment a-t-il été évacué ? Y a-t-il encore des personnes à l'intérieur ?",
            "DEMANDE_LIEU_POMPIER": "Les pompiers ont besoin de votre localisation exacte pour intervenir. Où êtes-vous ?",
            "DEMANDE_PANNE_TECH": "Je vois que le problème vient de {equipement}. Quel est le problème exact ou le message d'erreur ?",
            "DEMANDE_MATERIEL_TECH": "Je comprends la panne, mais sur quel équipement ou logiciel cela se produit-il ?",
            "DEMANDE_DETAILS_GENERAUX": "Votre message est très court. Pouvez-vous m'en dire un peu plus pour que je comprenne bien ?"
        }

    def qualifier_ticket(self, texte, domaine_principal):
        t = texte.lower()

        if self.friction_model is None:
            return True, "Complet"

        # 1. L'IA prédit le type d'information manquante
        prediction_label = self.friction_model.predict([texte])[0]

        if prediction_label == "COMPLET":
            return True, "Complet"

        # 2. Extraction dynamique pour PERSONNALISER le texte
        # Cherche le mot exact utilisé par le client (ex: "nez", "pc")
        zone_trouvee = next((mot for mot in self.mots_anatomie if mot in t), "cette zone")
        equipement_trouve = next((mot for mot in self.mots_materiel if mot in t), "votre matériel")

        # Astuce linguistique : si le mot n'a pas de déterminant, on ajoute "votre"
        if zone_trouvee != "cette zone": zone_trouvee = "votre " + zone_trouvee
        if equipement_trouve != "votre matériel": equipement_trouve = "votre " + equipement_trouve

        # 3. On récupère le template et on injecte les mots personnalisés
        question_brute = self.dictionnaire_questions.get(prediction_label, "Pouvez-vous donner plus de détails ?")
        question_personnalisee = question_brute.format(zone=zone_trouvee, equipement=equipement_trouve)

        return False, question_personnalisee