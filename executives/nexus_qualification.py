# executives/nexus_qualification.py
import joblib
import os
import re
from nexus_config import MODEL_FRICTION_PATH, MOTS_STRESS, MOTS_IRONIE


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

        # Templates dynamiques avec variantes de TONS
        self.dictionnaire_questions = {
            "DEMANDE_SYMPTOME_MED": {
                "NEUTRE": "J'ai bien noté que cela concerne {zone}. Que ressentez-vous exactement (douleur, saignement, etc.) ?",
                "STRESS": "Respirez calmement, les secours sont alertés. Quels sont les symptômes exacts au niveau de {zone} ?",
                "IRONIE": "Si c'est une blague concernant {zone}, merci de libérer la ligne pour les vraies urgences."
            },
            "DEMANDE_LIEU_POLICE": {
                "NEUTRE": "Pour envoyer les forces de l'ordre, j'ai absolument besoin de l'adresse ou du lieu précis.",
                "STRESS": "Restez en sécurité et cachez-vous si besoin ! À quelle adresse exacte dois-je envoyer la police ?",
                "IRONIE": "Faire des canulars à la police est passible de poursuites. Confirmez-vous cette urgence ?"
            },
            "DEMANDE_PANNE_TECH": {
                "NEUTRE": "Je vois que le problème vient de {equipement}. Quel est le problème exact ou le message d'erreur ?",
                "STRESS": "Je vois que cette panne vous bloque fortement. Quel est le message d'erreur sur {equipement} pour qu'on aille vite ?",
                "IRONIE": "Ce n'est pas le moment de tester l'IT avec {equipement} 😉. Quel est le vrai souci ?"
            },
            # Modèle par défaut pour les autres cas
            "DEFAUT": {
                "NEUTRE": "Votre message est très court. Pouvez-vous m'en dire un peu plus pour que je comprenne bien ?",
                "STRESS": "Essayez de garder votre calme et décrivez-moi la situation plus en détail s'il vous plaît.",
                "IRONIE": "L'intelligence artificielle a aussi le sens de l'humour, mais j'ai besoin de faits réels. Que se passe-t-il ?"
            }
        }

    def _detecter_ton(self, texte):
        t_lower = texte.lower()

        # 1. Détection de l'ironie (Priorité absolue)
        if any(mot in t_lower for mot in MOTS_IRONIE):
            return "IRONIE"

        # 2. Détection du stress (Mots clés OU beaucoup de majuscules/points d'exclamation)
        nb_exclamations = texte.count('!')
        mots_majuscules = sum(1 for mot in texte.split() if mot.isupper() and len(mot) > 3)
        is_stressed = any(mot in t_lower for mot in MOTS_STRESS)

        if is_stressed or nb_exclamations >= 2 or mots_majuscules >= 2:
            return "STRESS"

        return "NEUTRE"

    def qualifier_ticket(self, texte, domaine_principal):
        t = texte.lower()

        # Petit radar pour voir si la fonction s'active bien !
        print(f"\n   ⚙️ [DEBUG IA] Analyse des émotions en cours...")

        if self.friction_model is None:
            print("   ⚙️ [DEBUG IA] Attention: le modèle de friction est introuvable !")
            return True, "Complet"

        # 1. L'IA prédit le type d'information manquante
        prediction_label = self.friction_model.predict([texte])[0]

        # 2. Détection du ton
        ton_detecte = self._detecter_ton(texte)

        # Affichage de ce que l'IA a trouvé
        print(f"   ⚙️ [DEBUG IA] Label IA : {prediction_label} | Ton détecté : {ton_detecte}")

        # Si c'est complet ET qu'il n'y a pas d'ironie, le ticket passe.
        if prediction_label == "COMPLET" and ton_detecte != "IRONIE":
            return True, "Complet"

        # Si c'est complet mais ironique, on force une question par DEFAUT
        if prediction_label == "COMPLET" and ton_detecte == "IRONIE":
            prediction_label = "DEFAUT"

        # 3. Extraction dynamique pour PERSONNALISER le texte
        zone_trouvee = next((mot for mot in self.mots_anatomie if mot in t), "cette zone")
        equipement_trouve = next((mot for mot in self.mots_materiel if mot in t), "votre matériel")

        if zone_trouvee != "cette zone": zone_trouvee = "votre " + zone_trouvee
        if equipement_trouve != "votre matériel": equipement_trouve = "votre " + equipement_trouve

        # 4. On récupère le bon template en fonction du label ET du ton
        bloc_questions = self.dictionnaire_questions.get(prediction_label, self.dictionnaire_questions["DEFAUT"])
        question_brute = bloc_questions.get(ton_detecte, bloc_questions["NEUTRE"])

        question_personnalisee = question_brute.format(zone=zone_trouvee, equipement=equipement_trouve)

        return False, question_personnalisee
