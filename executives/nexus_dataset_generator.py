import pandas as pd
import random

# ==========================================
# 1. DICTIONNAIRES COMBINATOIRES PAR DOMAINE
# ==========================================

# --- MÉDICAL ---
MED_SUJETS = ["J'ai", "Mon collègue a", "Un employé a", "Je ressens", "Il y a"]
MED_IMPACTS = {
    4: ["au coeur", "à la tête", "au crâne", "à la poitrine", "au thorax"],
    3: ["au ventre", "au dos", "à la colonne", "au nez", "aux yeux"],
    2: ["à la jambe", "au bras", "au genou", "à l'épaule", "à la cheville"],
    1: ["au doigt", "à la main", "au pied", "à l'orteil", "sur la peau"]
}
MED_URGENCES = {
    4: ["et une hémorragie massive", "et il est inconscient", "et le sang gicle", "et c'est amputé",
        "et il ne respire plus"],
    3: ["avec des vertiges", "et je vais m'évanouir", "avec des vomissements", "et une douleur insupportable",
        "et je perds beaucoup de sang"],
    2: ["qui est très gonflé", "avec un gros bleu", "qui saigne un peu", "avec une douleur modérée",
        "et j'ai de la fièvre"],
    1: ["avec une petite coupure", "c'est une douleur légère", "mais rien de grave", "c'est un peu rouge",
        "pour un simple contrôle"]
}

# --- INFRA ---
INFRA_SUJETS = ["Le réseau", "Le serveur principal", "Le datacenter", "Le switch", "L'infrastructure"]
INFRA_IMPACTS = {
    4: ["de toute l'entreprise", "du bâtiment principal", "du datacenter central", "du site entier"],
    3: ["de l'étage", "du département", "de la salle de réunion", "de l'équipe de dev"],
    2: ["de mon bureau", "de l'imprimante réseau", "du routeur local"],
    1: ["du câble RJ45", "de la prise murale", "du port réseau"]
}
INFRA_URGENCES = {
    4: ["a explosé et prend feu", "est totalement détruit par une inondation",
        "est en panne totale et bloque tout le monde"],
    3: ["est complètement HS", "est mort et urgent", "a craché de manière critique", "ne répond plus du tout"],
    2: ["est très lent aujourd'hui", "subit des ralentissements", "a un comportement bizarre", "affiche des erreurs"],
    1: ["nécessite une petite mise à jour", "clignote bizarrement", "a besoin d'une vérification de routine"]
}

# --- POLICE ---
POLICE_SUJETS = ["Je signale", "Nous avons un problème avec", "Intervention requise pour", "Au secours il y a"]
POLICE_IMPACTS = {
    4: ["un groupe armé", "un tireur fou", "des terroristes", "un braquage de banque avec otages"],
    3: ["un cambriolage en cours", "une violente agression", "une bagarre générale", "des violences conjugales"],
    2: ["un vol de voiture", "un pickpocket", "une personne suspecte", "un rôdeur"],
    1: ["du tapage nocturne", "une voiture mal garée", "un graffiti", "une incivilité"]
}
POLICE_URGENCES = {
    4: ["il y a des morts", "ça tire de partout", "c'est une question de vie ou de mort", "venez immédiatement !"],
    3: ["ils sont dangereux", "il y a des blessés", "ça dégénère vite", "faites vite !"],
    2: ["ils sont encore sur place", "ça vient de se passer", "j'ai les vidéos", "merci d'envoyer une patrouille"],
    1: ["quand vous aurez le temps", "pour information", "c'est pour signaler", "ce n'est pas urgent"]
}


# (Tu peux ajouter des dictionnaires similaires pour POMPIER, MATÉRIEL, ACCÈS, RH)
# Pour que le script tourne tout de suite, je vais utiliser une génération générique pour les autres.

# ==========================================
# 2. MOTEUR DE GÉNÉRATION
# ==========================================

def generer_phrase(domaine, impact, urgence):
    """Crée une phrase aléatoire en piochant dans les dictionnaires."""

    if domaine == "MÉDICAL":
        sujet = random.choice(MED_SUJETS)
        imp_phrase = random.choice(MED_IMPACTS[impact])
        urg_phrase = random.choice(MED_URGENCES[urgence])
        return f"{sujet} mal {imp_phrase} {urg_phrase}"

    elif domaine == "INFRA":
        sujet = random.choice(INFRA_SUJETS)
        imp_phrase = random.choice(INFRA_IMPACTS[impact])
        urg_phrase = random.choice(INFRA_URGENCES[urgence])
        return f"{sujet} {imp_phrase} {urg_phrase}"

    elif domaine == "POLICE":
        sujet = random.choice(POLICE_SUJETS)
        imp_phrase = random.choice(POLICE_IMPACTS[impact])
        urg_phrase = random.choice(POLICE_URGENCES[urgence])
        return f"{sujet} {imp_phrase} car {urg_phrase}"

    else:
        # Générateur générique pour les autres domaines pour atteindre tes 140 000 tickets
        mots_impact = {
            4: "critique", 3: "majeur", 2: "significatif", 1: "mineur"
        }
        mots_urgence = {
            4: "immédiat et bloquant", 3: "très urgent", 2: "gênant", 1: "pas pressé"
        }

        types = {
            "MATÉRIEL": ["Mon PC", "Mon écran", "Mon clavier", "L'ordinateur"],
            "ACCÈS": ["Mon mot de passe", "Mon compte", "Mon VPN", "L'accès au logiciel"],
            "RH": ["Ma paie", "Mon contrat", "Mes congés", "Mon arrêt maladie"],
            "POMPIER": ["Un incendie", "Un accident", "Un feu", "Une fuite de gaz"]
        }

        sujet = random.choice(types.get(domaine, ["Le problème"]))
        return f"{sujet} est un problème {mots_impact[impact]} et c'est {mots_urgence[urgence]}"


def creer_dataset_massif(tickets_par_domaine=20000):
    print(f"🚀 Début de la création de {tickets_par_domaine} tickets par domaine...")

    domaines = ["MÉDICAL", "INFRA", "POLICE", "POMPIER", "MATÉRIEL", "ACCÈS", "RH"]
    lignes = []

    for domaine in domaines:
        print(f"  -> Génération des données pour {domaine}...")
        for _ in range(tickets_par_domaine):
            # Choix aléatoire d'un impact et d'une urgence de 1 à 4
            impact = random.randint(1, 4)
            urgence = random.randint(1, 4)

            texte = generer_phrase(domaine, impact, urgence)
            lignes.append({
                "texte": texte,
                "domaine": domaine,
                "impact": impact,
                "urgence": urgence
            })

    # Création du DataFrame et sauvegarde
    df = pd.DataFrame(lignes)

    # On mélange toutes les lignes pour que l'IA ne lise pas tout le médical d'un coup
    df = df.sample(frac=1).reset_index(drop=True)

    fichier_sortie = "../datasets/nexus_massive_dataset.csv"
    df.to_csv(fichier_sortie, index=False, encoding='utf-8')

    print(f"\n✅ Terminé ! Dataset massif généré : {fichier_sortie}")
    print(f"📊 Volume total : {len(df)} tickets.")


if __name__ == "__main__":
    creer_dataset_massif()
