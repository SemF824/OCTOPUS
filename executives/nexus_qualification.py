# nexus_qualification.py

class QualificationEngine:
    def __init__(self):
        # Lexiques de base pour vérifier la présence d'informations clés
        self.mots_anatomie = ["doigt", "ongle", "main", "bras", "jambe", "tête", "crâne", "poitrine", "coeur", "cœur",
                              "ventre", "abdomen", "nez", "oeil", "yeux", "dos", "cou", "pied", "cheville"]
        self.mots_symptomes = ["mal", "douleur", "saigne", "sang", "cassé", "fracture", "hémorragie", "inconscient",
                               "malaise", "brûlure", "étouffe", "respire", "fièvre"]

        self.mots_materiel = ["pc", "ordinateur", "serveur", "vpn", "écran", "imprimante", "réseau", "wifi", "clavier",
                              "souris", "câble", "routeur", "logiciel", "application"]
        self.mots_panne = ["marche plus", "panne", "bloqué", "erreur", "lent", "cassé", "éteint", "hs", "tombé", "bug",
                           "accès", "mot de passe"]

    def qualifier_ticket(self, texte, domaine):
        """
        Analyse le ticket et renvoie (Est_Complet (bool), Question_Relance (str))
        """
        t = texte.lower()

        # Règle globale : Un ticket trop court est toujours incomplet
        if len(texte.split()) < 3:
            return False, "Votre description est trop courte. Pouvez-vous me donner plus de détails ?"

        # --- QUALIFICATION MÉDICALE ---
        if domaine == "MÉDICAL":
            has_loc = any(loc in t for loc in self.mots_anatomie)
            has_symp = any(s in t for s in self.mots_symptomes)

            if not has_loc and not has_symp:
                return False, "Pouvez-vous décrire votre problème et préciser la zone du corps concernée ?"
            if has_loc and not has_symp:
                return False, "J'ai bien noté la zone. Que ressentez-vous exactement (douleur, saignement, etc.) ?"
            if has_symp and not has_loc:
                return False, "Je comprends le symptôme. À quel endroit du corps cela se situe-t-il ?"
            return True, "Complet"

        # --- QUALIFICATION TECHNIQUE ---
        elif domaine in ["INFRA", "MATÉRIEL", "ACCÈS"]:
            has_mat = any(m in t for m in self.mots_materiel)
            has_panne = any(p in t for p in self.mots_panne)

            if not has_mat:
                return False, f"Sur quel équipement ou service ({domaine}) rencontrez-vous ce problème ?"
            if not has_panne:
                return False, "Pouvez-vous décrire la nature exacte de la panne ou le message d'erreur ?"
            return True, "Complet"

        # --- QUALIFICATION POMPIER ---
        elif domaine == "POMPIER":
            mots_urgences_feu = ["feu", "incendie", "fumée", "gaz", "fuite", "explosion", "accident", "coincé", "brûle"]
            if not any(m in t for m in mots_urgences_feu):
                return False, "S'agit-il d'un incendie, d'une fuite de gaz ou d'un accident de la route ? Précisez le contexte."
            return True, "Complet"

        # --- QUALIFICATION POLICE ---
        elif domaine == "POLICE":
            mots_urgences_police = ["arme", "couteau", "fusil", "agression", "vol", "effraction", "menace", "frappe",
                                    "violences", "rodéo", "cambriolage"]
            if not any(m in t for m in mots_urgences_police):
                return False, "Pouvez-vous préciser la nature de l'infraction (vol, agression, arme...) et si les individus sont toujours sur place ?"
            return True, "Complet"

        # Autres domaines (RH, etc.)
        return True, "Complet"