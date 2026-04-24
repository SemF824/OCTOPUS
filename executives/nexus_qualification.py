# nexus_qualification.py
from nexus_config import MOTS_LIEUX


class QualificationEngine:
    def __init__(self):
        # Lexiques de base pour vérifier la présence d'informations clés
        self.mots_anatomie = ["doigt", "ongle", "main", "bras", "jambe", "tête", "crâne", "poitrine", "coeur", "cœur",
                              "ventre", "abdomen", "nez", "oeil", "yeux", "dos", "cou", "pied", "cheville"]
        self.mots_symptomes = ["mal", "douleur", "saigne", "sang", "cassé", "fracture", "hémorragie", "inconscient",
                               "malaise", "brûlure", "étouffe", "respire", "fièvre", "coupure"]

        self.mots_materiel = ["pc", "ordinateur", "serveur", "vpn", "écran", "imprimante", "réseau", "wifi", "clavier",
                              "souris", "câble", "routeur", "logiciel", "application"]
        self.mots_panne = ["marche plus", "panne", "bloqué", "erreur", "lent", "cassé", "éteint", "hs", "tombé", "bug",
                           "accès", "mot de passe"]

    def qualifier_ticket(self, texte, domaine_principal, domaines_multiples=None):
        """
        Analyse le ticket et renvoie (Est_Complet (bool), Question_Relance (str))
        Gère les vérifications tactiques (lieux, évacuation, etc.)
        """
        t = texte.lower()

        # Règle globale : Un ticket trop court est toujours incomplet
        if len(texte.split()) < 3:
            return False, "Votre description est trop courte. Pouvez-vous me donner plus de détails ?"

        # --- VÉRIFICATION GLOBALE : LE LIEU ---
        # Si c'est une urgence vitale ou multi-forces, on exige une localisation
        is_urgence_vitale = domaine_principal in ["MÉDICAL", "POMPIER", "POLICE"] or (
                    domaines_multiples and len(domaines_multiples) > 1)
        has_lieu = any(lieu in t for lieu in MOTS_LIEUX)

        if is_urgence_vitale and not has_lieu:
            return False, "URGENCE : Veuillez préciser IMMÉDIATEMENT l'adresse ou le lieu exact de l'incident."

        # --- QUALIFICATION MÉDICALE ---
        if domaine_principal == "MÉDICAL":
            has_loc = any(loc in t for loc in self.mots_anatomie)
            has_symp = any(s in t for s in self.mots_symptomes)

            if not has_loc and not has_symp:
                return False, "Pouvez-vous décrire votre problème médical et préciser la zone du corps concernée ?"
            if has_loc and not has_symp:
                return False, "J'ai bien noté la zone. Que ressentez-vous exactement (douleur, saignement, etc.) ?"
            if has_symp and not has_loc:
                return False, "Je comprends le symptôme. À quel endroit du corps cela se situe-t-il ?"

            # Question Tactique Médicale
            if any(m in t for m in ["inconscient", "respire plus", "hémorragie", "malaise"]):
                if not any(m in t for m in ["massage", "garrot", "compress", "seul"]):
                    return False, "URGENCE VITALE : Êtes-vous seul avec la victime ? Les premiers secours (massage, compression) ont-ils commencé ?"
            return True, "Complet"

        # --- QUALIFICATION POMPIER ---
        elif domaine_principal == "POMPIER":
            mots_urgences_feu = ["feu", "incendie", "fumée", "gaz", "fuite", "explosion", "accident", "coincé", "brûle"]
            if not any(m in t for m in mots_urgences_feu):
                return False, "S'agit-il d'un incendie, d'une fuite de gaz ou d'un accident de la route ? Précisez le contexte."

            # Question Tactique Pompier
            if any(m in t for m in ["feu", "incendie", "fumée", "explosion"]):
                if not any(m in t for m in ["évacué", "personne à l'intérieur", "vide", "sortis", "sauvé"]):
                    return False, "SÉCURITÉ : Le bâtiment a-t-il été évacué ? Y a-t-il encore des personnes à l'intérieur ?"
            return True, "Complet"

        # --- QUALIFICATION POLICE ---
        elif domaine_principal == "POLICE":
            mots_urgences_police = ["arme", "couteau", "fusil", "agression", "vol", "effraction", "menace", "frappe",
                                    "violences", "rodéo", "cambriolage"]
            if not any(m in t for m in mots_urgences_police):
                return False, "Pouvez-vous préciser la nature exacte de l'infraction (vol, agression, arme...) ?"

            # Question Tactique Police
            if any(m in t for m in ["arme", "couteau", "fusil", "agression", "tireur", "fusillade"]):
                if not any(m in t for m in ["fui", "parti", "maîtrisé", "sur place", "caché"]):
                    return False, "SÉCURITÉ : Le ou les agresseurs sont-ils TOUJOURS SUR PLACE ?"
            return True, "Complet"

        # --- QUALIFICATION TECHNIQUE ---
        elif domaine_principal in ["INFRA", "MATÉRIEL", "ACCÈS"]:
            has_mat = any(m in t for m in self.mots_materiel)
            has_panne = any(p in t for p in self.mots_panne)

            if not has_mat:
                return False, f"Sur quel équipement ou service ({domaine_principal}) rencontrez-vous ce problème ?"
            if not has_panne:
                return False, "Pouvez-vous décrire la nature exacte de la panne ou le message d'erreur ?"
            return True, "Complet"

        # Autres domaines (RH, etc.)
        return True, "Complet"