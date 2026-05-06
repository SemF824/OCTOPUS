# executives/nexus_dialogue_generator.py
import pandas as pd
import random
import os

print("🚀 Génération du Dataset Conversationnel (Entonnoir Clinique & Sécurité)...")

# --- Briques de la conversation ---
problemes_med = ["J'ai mal", "Il y a un blessé", "Je ne me sens pas bien", "Mon ami souffre", "Douleur intense"]
corps = ["à la tête", "au ventre", "à la poitrine", "au bras", "à la jambe", "au dos"]
symptomes = ["j'ai des vertiges", "il y a du sang", "je veux vomir", "j'ai du mal à respirer", "c'est gonflé",
             "je ne sens plus mes doigts"]
antecedents = ["25 ans aucun", "il a 50 ans et est diabétique", "je suis asthmatique", "aucun antécédent",
               "40 ans cardiaque"]
lieux = ["au 5 rue de la paix", "à Rennes", "chez moi", "devant la gare", "au cinéma"]

problemes_pol = ["Il y a un braquage", "On m'a agressé", "Des gens se battent", "Cambriolage en cours"]
armes = ["avec un couteau", "ils ont une arme", "armé d'un pistolet", "une batte de baseball", "je n'ai pas vu d'arme"]

donnees = []

# --- LES QUESTIONS CIBLES (LABELS) ---
Q_CORPS = "DEMANDE_CORPS"  # "À quelle partie du corps ?"
Q_SYMPTOMES = "DEMANDE_SYMPTOMES"  # "Quels sont les symptômes exacts (vertiges, saignements, etc.) ?"
Q_ANTECEDENTS = "DEMANDE_ANTECEDENTS"  # "Quel est l'âge et les antécédents médicaux ?"
Q_LIEU = "DEMANDE_LIEU"  # "À quelle adresse exacte vous trouvez-vous ?"
Q_ARME = "DEMANDE_ARME"  # "Y a-t-il des armes visibles ?"
Q_COMPLET = "COMPLET"  # "✅ Dossier complet."

# --- GÉNÉRATION DE L'ENTONNOIR MÉDICAL ---
for _ in range(3000):
    p = random.choice(problemes_med)
    c = random.choice(corps)
    s = random.choice(symptomes)
    a = random.choice(antecedents)
    l = random.choice(lieux)

    # Étape 1 : Juste le problème -> Demande le corps
    donnees.append([f"{p}", Q_CORPS])

    # Étape 2 : Problème + Corps -> Demande les symptômes
    donnees.append([f"{p}. {c}", Q_SYMPTOMES])

    # Étape 3 : Problème + Corps + Symptômes -> Demande les antécédents
    donnees.append([f"{p}. {c}. {s}", Q_ANTECEDENTS])

    # Étape 4 : Problème + Corps + Symptômes + Antécédents -> Demande le lieu
    donnees.append([f"{p}. {c}. {s}. {a}", Q_LIEU])

    # Étape 5 : Tout est là -> Complet
    donnees.append([f"{p}. {c}. {s}. {a}. {l}", Q_COMPLET])

    # Variantes : L'utilisateur donne le corps dès le début
    donnees.append([f"{p} {c}", Q_SYMPTOMES])

# --- GÉNÉRATION DE L'ENTONNOIR POLICE ---
for _ in range(2000):
    p = random.choice(problemes_pol)
    arm = random.choice(armes)
    l = random.choice(lieux)

    # Étape 1 : Problème -> Demande arme
    donnees.append([f"{p}", Q_ARME])

    # Étape 2 : Problème + Arme -> Demande lieu
    donnees.append([f"{p}. {arm}", Q_LIEU])

    # Étape 3 : Problème + Arme + Lieu -> Complet
    donnees.append([f"{p}. {arm}. {l}", Q_COMPLET])

df = pd.DataFrame(donnees, columns=["texte_conversation", "prochaine_question"])
df = df.drop_duplicates().sample(frac=1, random_state=42).reset_index(drop=True)

# Sauvegarde
os.makedirs("../datasets", exist_ok=True)
output_path = "../datasets/nexus_dialogue_funnel.csv"
df.to_csv(output_path, index=False, encoding='utf-8')
print(f"✅ Fichier généré avec succès ({len(df)} exemples purs) : {output_path}")