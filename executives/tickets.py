import pandas as pd
import random
import csv

# ==========================================
# 1. PARAMÈTRES DE SAUVEGARDE
# ==========================================
NOM_FICHIER_SORTIE = "dataset_classification_medical_enrichi.csv"
NOMBRE_DE_TICKETS = 10000

# ==========================================
# 2. DICTIONNAIRES : DOMAINE MÉDICAL (Triage SAMU / 15)
# ==========================================
intents = {

    # ---------------------------------------------------------
    # CATÉGORIE 1 : URGENCE VITALE ABSOLUE (SMUR)
    # ---------------------------------------------------------
    "Medical_Urgence_Vitale": {
        "domaine": "Urgence Vitale Absolue (SMUR)",
        "fr": {
            "subjects": [
                "Suspicion d'AVC", "Arrêt cardio-respiratoire", "Douleur thoracique intense",
                "Étouffement total", "Choc anaphylactique", "Hémorragie massive",
                "Inconscience soudaine", "Intoxication médicamenteuse grave",
                "Difficulté respiratoire extrême", "Malaise cardiaque suspecté",
                "Perte de connaissance prolongée", "Convulsions continues",
                "Visage paralysé et mutisme", "Plaie saignante artérielle", "Asphyxie en cours"
            ],
            "salutations": ["Vite, à l'aide !", "Allô le 15 ?", "Urgence médicale,", "Vite, venez !", "Au secours,"],
            "problemes": [
                "mon père vient de s'effondrer au sol, il est inconscient et ne respire plus.",
                "mon mari a une douleur écrasante dans la poitrine qui irradie dans le bras gauche.",
                "ma femme a soudainement le visage paralysé d'un côté et n'arrive plus à parler.",
                "mon ami a mangé une cacahuète, il gonfle de partout et s'étouffe.",
                "mon grand-père vomit beaucoup de sang, c'est une hémorragie terrible.",
                "j'ai trouvé ma colocataire inconsciente avec des boîtes de somnifères vides autour d'elle.",
                "le patient s'est effondré, il n'a plus de pouls et ses lèvres sont bleues.",
                "il a avalé un gros morceau de viande et ne peut plus ni tousser ni respirer."
            ],
            "contextes": [
                "C'est au <adresse>, s'il vous plaît faites très vite !",
                "Le patient a 60 ans et a des antécédents cardiaques.",
                "Je suis paniqué, dites-moi ce que je dois faire en attendant l'ambulance.",
                "J'ai commencé le massage cardiaque, dépêchez-vous !",
                "Mon numéro est le <tel_num>, le portail est grand ouvert."
            ]
        }
    },

    # ---------------------------------------------------------
    # CATÉGORIE 2 : TRAUMATOLOGIE (Blessures, Chutes)
    # ---------------------------------------------------------
    "Medical_Traumatologie": {
        "domaine": "Traumatologie & Blessures",
        "fr": {
            "subjects": [
                "Chute dans les escaliers", "Coupure profonde", "Brûlure thermique étendue",
                "Suspicion de fracture ouverte", "Morsure de chien", "Accident de bricolage",
                "Traumatisme crânien", "Corps étranger dans l'œil", "Entorse grave de la cheville",
                "Écrasement du doigt", "Chute de grande hauteur", "Plaie ouverte au crâne",
                "Luxation de l'épaule", "Brûlure chimique", "Accident de trottinette"
            ],
            "salutations": ["Bonjour le SAMU,", "Allô,", "Bonjour,", "Besoin d'une ambulance,"],
            "problemes": [
                "mon fils est tombé de vélo à vive allure et son avant-bras a une forme anormale.",
                "je me suis coupé très profondément avec une scie circulaire, ça saigne en jet.",
                "je viens de me renverser une friteuse d'huile bouillante sur les jambes.",
                "ma mère de 85 ans a glissé dans la salle de bain et sa jambe est tordue.",
                "mon voisin s'est fait mordre violemment au mollet par un gros chien.",
                "je me suis pris un éclat métallique dans l'œil, je ne vois plus rien.",
                "il a pris un gros coup sur la tête, il a vomi et semble confus.",
                "un ouvrier est tombé d'un échafaudage de 3 mètres, il a très mal au dos."
            ],
            "contextes": [
                "Nous sommes au <adresse>.",
                "J'ai fait un point de compression avec une serviette propre.",
                "La personne est consciente mais hurle de douleur.",
                "Il ne faut surtout pas le bouger, n'est-ce pas ?",
                "Est-ce que je dois l'emmener aux urgences moi-même ?"
            ]
        }
    },

    # ---------------------------------------------------------
    # CATÉGORIE 3 : MÉDECINE DE GARDE & CONSEIL
    # ---------------------------------------------------------
    "Medical_Conseil_Garde": {
        "domaine": "Médecine de Garde & Conseil",
        "fr": {
            "subjects": [
                "Forte fièvre adulte", "Gastro-entérite sévère", "Crise de colique néphrétique",
                "Besoin d'un médecin de garde", "Otite très douloureuse", "Lumbago foudroyant",
                "Crise d'asthme modérée", "Vertiges intenses", "Éruption cutanée généralisée",
                "Migraine insupportable", "Infection urinaire douloureuse", "Angine blanche très forte",
                "Douleur abdominale persistante", "Grosse réaction allergique", "Douleur dentaire aiguë"
            ],
            "salutations": ["Bonjour,", "Allô un médecin ?", "Bonjour le 15,"],
            "problemes": [
                "je vomis en continu depuis cette nuit et je ne tiens plus du tout debout.",
                "j'ai une douleur atroce dans le bas du dos qui irradie vers le ventre.",
                "mon mari a 40 de fièvre et des frissons intenses depuis hier soir.",
                "je suis complètement bloqué du dos, je ne peux même plus me lever du lit.",
                "j'ai des vertiges horribles dès que je tourne la tête et des nausées.",
                "je fais une petite crise d'asthme, j'ai pris ma Ventoline mais ça siffle encore.",
                "j'ai une douleur insupportable à l'oreille droite, comme des coups de poignard.",
                "j'ai des migraines extrêmement fortes que les cachets ne calment pas."
            ],
            "contextes": [
                "Je n'arrive pas à avoir de rendez-vous sur Doctolib aujourd'hui.",
                "Est-ce que SOS Médecins peut venir à domicile au <adresse> ?",
                "C'est pour avoir un avis médical, je ne sais pas si je dois m'inquiéter.",
                "Mon médecin traitant m'a dit de faire le 15 en cas d'aggravation."
            ]
        }
    },

    # ---------------------------------------------------------
    # CATÉGORIE 4 : OBSTÉTRIQUE & PÉDIATRIE
    # ---------------------------------------------------------
    "Medical_Maternite_Pediatrie": {
        "domaine": "Obstétrique & Pédiatrie",
        "fr": {
            "subjects": [
                "Contractions très rapprochées", "Perte des eaux", "Convulsions du nourrisson",
                "Fièvre bébé 3 mois", "Saignement grossesse", "Bébé amorphe", "Ingestion accidentelle",
                "Chute de la table à langer", "Bébé qui respire mal", "Pleurs incessants nourrisson",
                "Accouchement imminent", "Toux très grasse enfant", "Bébé refuse de s'alimenter",
                "Plaque rouge sur bébé", "Vomissements répétés enfant"
            ],
            "salutations": ["Allô les pompiers,", "Bonjour, c'est pour un bébé,", "Urgence maternité,"],
            "problemes": [
                "ma femme est enceinte de 8 mois et elle vient de perdre les eaux d'un coup.",
                "les contractions sont espacées de 3 minutes et on n'aura pas le temps d'aller à la clinique.",
                "mon bébé de 1 an fait des convulsions, il tremble de partout et a les yeux révulsés.",
                "mon nourrisson de 2 mois a 39.5°C de fièvre et refuse de boire son biberon.",
                "je suis enceinte de 4 mois et je viens de perdre beaucoup de sang.",
                "ma fille de 3 ans vient de boire une gorgée de produit d'entretien pour le sol.",
                "le bébé est très pâle, tout mou et il a du mal à se réveiller."
            ],
            "contextes": [
                "La maternité m'a dit de vous appeler pour avoir une ambulance.",
                "Nous sommes au <adresse>, au 4ème étage sans ascenseur.",
                "Est-ce que je dois faire baisser sa fièvre avec un bain ?",
                "Je garde le flacon du produit chimique pour vous donner la composition."
            ]
        }
    },

    # ---------------------------------------------------------
    # CATÉGORIE 5 : DÉTRESSE PSYCHOLOGIQUE
    # ---------------------------------------------------------
    "Medical_Psychiatrie": {
        "domaine": "Psychiatrie & Détresse",
        "fr": {
            "subjects": [
                "Crise d'angoisse", "Idées suicidaires", "Agitation extrême", "Attaque de panique",
                "Syndrome de sevrage", "Délire et hallucinations", "Comportement agressif",
                "Propos incohérents", "Mise en danger de soi", "Crise de larmes incontrôlable",
                "Paranoïa soudaine", "Hyperventilation sévère", "Détresse psychologique grave",
                "Menace de passage à l'acte", "Désorientation totale"
            ],
            "salutations": ["Aidez-moi,", "Allô les urgences,", "Bonjour le 15,"],
            "problemes": [
                "je n'arrive plus à respirer, mon cœur bat à 100 à l'heure, je crois que je fais une crise de panique.",
                "mon frère est dans un état d'agitation extrême, il casse tout dans l'appartement.",
                "je suis à bout, j'ai envie d'en finir et j'ai une lame dans les mains.",
                "mon ami tremble beaucoup, transpire et semble en plein syndrome de manque.",
                "ma voisine hurle dans le couloir, elle tient des propos incohérents et voit des choses.",
                "je fais une énorme crise d'angoisse et je sens que je vais m'évanouir."
            ],
            "contextes": [
                "Il est suivi en psychiatrie habituellement à l'hôpital.",
                "Pouvez-vous m'envoyer quelqu'un ou me passer un psychiatre au téléphone ?",
                "C'est au <adresse>. J'ai peur pour sa sécurité et la mienne."
            ]
        }
    }
}


# ==========================================
# 3. MOTEUR DE GÉNÉRATION INTELLIGENT
# ==========================================
def generate_medical_tickets(num_tickets):
    data = []

    for _ in range(num_tickets):
        intent_key = random.choice(list(intents.keys()))
        intent = intents[intent_key]

        lang = "fr"
        content = intent[lang]

        # Tirage au sort combinatoire massif
        salutation = random.choice(content["salutations"])
        probleme = random.choice(content["problemes"])
        contexte = random.choice(content["contextes"])
        body_text = f"{salutation} {probleme} {contexte}".strip()

        subject_text = random.choice(content["subjects"])

        # Gestion des priorités cliniques en Français
        if intent_key == "Medical_Urgence_Vitale":
            priority = "Haute"  # SMUR immédiat
        elif intent_key in ["Medical_Traumatologie", "Medical_Maternite_Pediatrie"]:
            priority = random.choice(["Moyenne", "Haute"])  # Dépend de la gravité clinique
        elif intent_key == "Medical_Psychiatrie":
            priority = random.choice(["Moyenne", "Haute"])  # Risque suicidaire / Dangerosité
        else:
            priority = random.choice(["Basse", "Moyenne"])  # Conseil médical (SOS Médecins)

        # Création du ticket au format CLASSIFICATION (4 colonnes)
        ticket = {
            'Sujets': subject_text,
            'Demande': body_text,
            'Domaine': intent["domaine"],
            'Niveau de priority': priority
        }
        data.append(ticket)

    return pd.DataFrame(data)


# ==========================================
# 4. LANCEMENT ET SAUVEGARDE
# ==========================================
print(f"Génération de {NOMBRE_DE_TICKETS} tickets Médicaux (Dataset hyper-varié) en cours...")
df_tickets = generate_medical_tickets(NOMBRE_DE_TICKETS)

df_tickets.to_csv(NOM_FICHIER_SORTIE, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
print(f"Terminé ! Le fichier '{NOM_FICHIER_SORTIE}' a bien été créé avec une très grande diversité de sujets.")