# nexus_qualification.py
from nexus_config import MOTS_LIEUX


class QualificationEngine:
    def __init__(self):
        # Lexiques avec racines pour plus de tolérance (ex: "arm" capte arme, armé, armes)
        self.mots_anatomie = ["doigt", "ongle", "main", "bras", "jambe", "tête", "crâne", "poitrine", "coeur", "cœur",
                              "ventre", "abdomen", "nez", "oeil", "yeux", "dos", "cou", "pied", "cheville"]

        self.mots_symptomes = ["mal", "douleur", "saigne", "sang", "cass", "fracture", "hémorragie", "inconscient",
                               "malaise", "brûlure", "étouffe", "respire", "fièvre", "coupure", "picotement"]

        self.mots_materiel = ["pc", "ordinateur", "serveur", "vpn", "écran", "imprimante", "réseau", "wifi", "clavier",
                              "souris", "câble", "routeur", "logiciel", "application"]

        self.mots_panne = ["marche plus", "panne", "bloqu", "erreur", "lent", "cass", "éteint", "hs", "tomb", "bug",
                           "accès", "mot de passe"]

    def qualifier_ticket(self, texte, domaine_principal, domaines_multiples=None):
        t = texte.lower()

        # 1. Règle globale : Un ticket trop court
        if len(texte.split()) < 3:
            return False, "Respirez calmement. Je suis là pour vous aider mais votre message est un peu court. Que se passe-t-il exactement ?"

        # 2. Vérification du Lieu (Pour les urgences vitales)
        is_urgence_vitale = domaine_principal in ["MÉDICAL", "POMPIER", "POLICE"] or (
                    domaines_multiples and len(domaines_multiples) > 1)
        has_lieu = any(lieu in t for lieu in MOTS_LIEUX)

        if is_urgence_vitale and not has_lieu:
            return False, "Restez en ligne avec moi. Pour envoyer les secours immédiatement, j'ai besoin de votre adresse exacte ou du lieu où vous vous trouvez."

        # --- QUALIFICATION MÉDICALE ---
        if domaine_principal == "MÉDICAL":
            has_loc = any(loc in t for loc in self.mots_anatomie)
            has_symp = any(s in t for s in self.mots_symptomes)

            if not has_loc and not has_symp:
                return False, "Les secours sont prévenus. Pouvez-vous me dire précisément où la personne a mal et quels sont les symptômes ?"
            if has_loc and not has_symp:
                return False, "J'ai bien noté la zone touchée. Ne bougez pas et dites-moi ce que vous ressentez exactement (douleur, saignement...) ?"
            if has_symp and not has_loc:
                return False, "Je comprends. À quel endroit précis du corps cela se situe-t-il ?"

            # Question Tactique Médicale (Tolérance avec 'oui', 'non', etc.)
            if any(m in t for m in ["inconscient", "respire plus", "hémorragie", "malaise"]):
                if not any(m in t for m in ["massage", "garrot", "compress", "seul", "oui", "non", "je fais"]):
                    return False, "C'est une urgence. Êtes-vous seul avec la victime ? Avez-vous commencé les premiers secours (massage, compression) ?"
            return True, "Complet"

        # --- QUALIFICATION POMPIER ---
        elif domaine_principal == "POMPIER":
            mots_urgences_feu = ["feu", "incendie", "fumée", "gaz", "fuite", "explosion", "accident", "coincé", "brûl"]
            if not any(m in t for m in mots_urgences_feu):
                return False, "Les pompiers sont en écoute. S'agit-il d'un incendie, d'une fuite ou d'un accident ? Détaillez la situation."

            # Question Tactique Pompier
            if any(m in t for m in ["feu", "incendie", "fumée", "explosion"]):
                # Acceptation de "oui", "non", "en cours", "évacu" pour éviter la boucle infinie
                if not any(m in t for m in
                           ["évacu", "personne", "vide", "sorti", "sauvé", "oui", "non", "sais pas", "dedans",
                            "encore"]):
                    return False, "SÉCURITÉ : Ne prenez pas de risques. Le bâtiment est-il en cours d'évacuation ? Reste-t-il des personnes à l'intérieur ?"
            return True, "Complet"

        # --- QUALIFICATION POLICE ---
        elif domaine_principal == "POLICE":
            # Ajout de "arm" (qui capte arme, armé, armes), "tir" (tire, tireur, tirent), "effract"
            mots_urgences_police = ["arm", "couteau", "fusil", "agress", "vol", "effract", "menace", "frapp",
                                    "violences", "rodéo", "cambriolage", "tir", "tueur"]
            if not any(m in t for m in mots_urgences_police):
                return False, "La police est alertée. Mettez-vous à l'abri et précisez ce qu'il se passe (vol, agression, individus armés...)."

            # Question Tactique Police
            if any(m in t for m in ["arm", "couteau", "fusil", "agress", "tir", "fusillade"]):
                # Tolérance des réponses
                if not any(m in t for m in ["fui", "parti", "maîtris", "sur place", "cach", "oui", "non", "là", "ici"]):
                    return False, "SÉCURITÉ : Cachez-vous si nécessaire. L'agresseur ou les individus sont-ils TOUJOURS SUR PLACE ?"
            return True, "Complet"

        # --- QUALIFICATION TECHNIQUE ---
        elif domaine_principal in ["INFRA", "MATÉRIEL", "ACCÈS"]:
            has_mat = any(m in t for m in self.mots_materiel)
            has_panne = any(p in t for p in self.mots_panne)

            if not has_mat:
                return False, f"Nos techniciens ({domaine_principal}) sont prêts. Sur quel équipement ou service rencontrez-vous ce problème ?"
            if not has_panne:
                return False, "Pouvez-vous nous décrire la nature exacte de la panne ou nous donner le message d'erreur ?"
            return True, "Complet"

        # Autres domaines
        return True, "Complet"