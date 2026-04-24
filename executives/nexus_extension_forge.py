# nexus_extension_forge.py
import sqlite3
import pandas as pd
import random
import os
from nexus_config import DB_PATH

print("🚀 INITIALISATION DE L'EXTENSION NEXUS : CAS EXTRÊMES ET INÉDITS...")

# --- NOUVEAUX CONTEXTES & LIEUX ---
EMOTIONS_EXTREMES = ["C'est la panique absolue, ", "Urgence vitale ! ", "Alerte maximale, ", "Je suis terrorisé, ",
                     "Faites très attention, ", "Mon Dieu, "]
LIEUX_COMPLEXES = ["à l'aéroport", "dans le métro ligne 4", "à l'usine chimique", "dans la forêt", "sur l'autoroute",
                   "au tribunal", "à l'école", "au bord du lac", "dans la zone industrielle"]
CONTEXTES = ["en pleine nuit", "sous une pluie battante", "il y a beaucoup de monde autour",
             "personne ne sait quoi faire"]

# --- 1. CAS MÉDICAUX INÉDITS ---
MED_EXTREMES = [
    ("est en train d'accoucher, la tête sort", 4, 4),
    ("a pris trop de médicaments, overdose", 4, 4),
    ("vient de s'électrocuter avec un câble à haute tension", 4, 4),
    ("fait une crise psychiatrique et menace de sauter", 4, 4),
    ("a mangé des arachides et gonfle, choc anaphylactique", 4, 4),
    ("s'est noyé et ne respire plus", 4, 4),
    ("a le doigt sectionné par une machine", 3, 4)
]


def gen_med_ext():
    act, imp, urg = random.choice(MED_EXTREMES)
    return (
        f"{random.choice(EMOTIONS_EXTREMES)}Une personne {act} {random.choice(LIEUX_COMPLEXES)} {random.choice(CONTEXTES)}",
        "MÉDICAL", imp, urg)


# --- 2. CAS POLICE INÉDITS ---
POL_EXTREMES = [
    ("prise d'otage en cours dans la banque", 4, 4),
    ("alerte à la bombe, un colis suspect", 4, 4),
    ("on vient d'enlever un enfant dans une camionnette", 4, 4),
    ("émeute urbaine avec des cocktails molotov", 4, 4),
    ("un chauffard a écrasé un piéton et a pris la fuite", 4, 4),
    ("on me fait du chantage à la webcam, cyberharcèlement", 2, 2)
]


def gen_pol_ext():
    act, imp, urg = random.choice(POL_EXTREMES)
    return (
        f"{random.choice(EMOTIONS_EXTREMES)}{act} {random.choice(LIEUX_COMPLEXES)}. {random.choice(['Envoyez le GIGN', 'Faites vite', 'Ils sont très dangereux'])}",
        "POLICE", imp, urg)


# --- 3. CAS POMPIER INÉDITS ---
POM_EXTREMES = [
    ("fuite de produit chimique toxique", 4, 4),
    ("déraillement d'un train de passagers", 4, 4),
    ("feu de forêt qui s'approche des maisons", 4, 4),
    ("effondrement du toit d'un supermarché", 4, 4),
    ("personne coincée sous un tracteur", 3, 4),
    ("fuite radioactive suspectée", 4, 4)
]


def gen_pom_ext():
    act, imp, urg = random.choice(POM_EXTREMES)
    return (f"{random.choice(EMOTIONS_EXTREMES)}{act} {random.choice(LIEUX_COMPLEXES)}. {random.choice(CONTEXTES)}",
            "POMPIER", imp, urg)


# --- 4. CAS TECH/CYBER INÉDITS ---
TECH_EXTREMES = [
    ("attaque par ransomware, toutes nos données sont cryptées", "INFRA", 4, 4),
    ("fuite de données sensibles des clients sur internet", "INFRA", 4, 4),
    ("coupure électrique totale du datacenter principal", "INFRA", 4, 4),
    ("piratage du compte du PDG avec usurpation d'identité", "ACCÈS", 4, 3),
    ("intrusion physique dans la salle des serveurs", "INFRA", 4, 4),
    ("le système d'alarme et les caméras ont été désactivés à distance", "MATÉRIEL", 3, 4)
]


def gen_tech_ext():
    act, dom, imp, urg = random.choice(TECH_EXTREMES)
    return (f"Alerte Sécurité IT : {act}. Intervention requise {random.choice(CONTEXTES)}.", dom, imp, urg)


# --- BOUCLE DE GÉNÉRATION ---
def run_extension():
    dataset = []
    print("⏳ Création de 120 000 tickets de Cas Extrêmes (30k par domaine)...")

    # On génère 30 000 de chaque pour bien "imprimer" ces nouveaux mots dans le cerveau de l'IA
    for _ in range(30000): dataset.append(gen_med_ext())
    for _ in range(30000): dataset.append(gen_pol_ext())
    for _ in range(30000): dataset.append(gen_pom_ext())
    for _ in range(30000): dataset.append(gen_tech_ext())

    df_complement = pd.DataFrame(dataset, columns=["texte", "domaine", "impact", "urgence"])

    # Nettoyage des doublons internes au complément
    df_complement = df_complement.drop_duplicates(subset=['texte'])
    print(f"✅ Extension générée : {len(df_complement)} tickets extrêmes uniques.")

    # Sauvegarde CSV
    os.makedirs("../datasets", exist_ok=True)
    df_complement.to_csv("../datasets/nexus_complement_dataset.csv", index=False)

    # INJECTION DANS LA BASE SQLITE EXISTANTE (APPEND)
    print("💾 Injection dans la base SQLite (sans effacer les données de la V15)...")
    with sqlite3.connect(DB_PATH) as conn:
        # L'argument if_exists="append" est crucial ici pour AJOUTER et non remplacer
        df_complement.to_sql("tickets_domaines", conn, if_exists="append", index=False)

    print(f"🎉 OPÉRATION TERMINÉE ! La base de données est maintenant enrichie avec des scénarios complexes.")


if __name__ == "__main__":
    run_extension()