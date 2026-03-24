import sqlite3
import pandas as pd
import random

DB_PATH = "nexus_bionexus.db"


def generer_usine_massive():
    print(">>> DÉMARRAGE DE LA DATA FACTORY V2 (COMBINATOIRE)...")
    donnees = []

    # --- DICTIONNAIRES DE MOTS ---

    # 1. MÉDICAL
    med_bobo_sujets = ["jambe", "jambes", "bras", "doigt", "tête", "ventre", "pied", "dos"]
    med_bobo_verbes = ["j'ai mal au", "j'ai mal aux", "douleur légère", "je me suis coupé le", "ampoule au", "petit problème au"]

    med_grave_sujets = ["cœur", "poitrine", "collègue", "visiteur", "sang", "respiration"]
    med_grave_verbes = ["ne respire plus", "malaise", "crise cardiaque", "hémorragie", "inconscient", "arrêt"]

    # 2. INFRA
    infra_mineur_mots = ["câble", "wifi", "lenteur réseau", "latence", "débranché", "internet lent"]
    infra_grave_mots = ["datacenter", "feu", "ransomware", "cyberattaque", "piratage", "serveurs down", "intrusion"]

    # 3. MATÉRIEL
    mat_mots = ["clavier", "souris", "écran", "ordinateur", "laptop", "imprimante", "toner", "chargeur", "casque"]
    mat_verbes = ["cassé", "ne marche plus", "hs", "bloqué", "plus de batterie", "bouton cassé"]

    # 4. RH
    rh_mots = ["salaire", "paie", "congés", "fiche", "contrat", "manager", "harcèlement", "absence", "mutuelle"]

    # 5. ACCÈS
    acc_mots = ["mot de passe", "session", "badge", "portique", "vpn", "authentification", "compte bloqué",
                "accès refusé"]

    # --- GÉNÉRATION DES TICKETS ---

    for _ in range(1500):
        # MÉDICAL BÉNIN (Score bas, Urgence aléatoire)
        texte = f"{random.choice(med_bobo_verbes)} {random.choice(med_bobo_sujets)}"
        donnees.append((random.randint(1, 5), "NORMAL", "Bobo", texte, "MÉDICAL", random.uniform(1.0, 3.5), "NON"))

        # MÉDICAL GRAVE (Score 10, Urgence aléatoire)
        texte = f"{random.choice(med_grave_sujets)} {random.choice(med_grave_verbes)}"
        donnees.append((random.randint(1, 5), "URGENT", "Urgence Vitale", texte, "MÉDICAL", 10.0, "OUI (Veto)"))

        # INFRA MINEUR (Score bas)
        donnees.append((random.randint(1, 5), "NORMAL", "Réseau", random.choice(infra_mineur_mots), "INFRA",
                        random.uniform(2.0, 4.0), "NON"))

        # INFRA GRAVE (Score 10)
        donnees.append(
            (random.randint(3, 5), "URGENT", "Incident Majeur", random.choice(infra_grave_mots), "INFRA", 10.0,
             "OUI (Veto)"))

        # MATÉRIEL (Score bas, toujours)
        texte = f"{random.choice(mat_mots)} {random.choice(mat_verbes)}"
        donnees.append((random.randint(1, 5), "NORMAL", "Hardware", texte, "MATÉRIEL", random.uniform(1.0, 4.0), "NON"))

        # RH
        donnees.append(
            (random.randint(1, 4), "NORMAL", "Admin", random.choice(rh_mots), "RH", random.uniform(2.0, 5.0), "NON"))

        # ACCÈS
        donnees.append(
            (random.randint(1, 5), "NORMAL", "Auth", random.choice(acc_mots), "ACCÈS", random.uniform(2.0, 6.0), "NON"))

    # Création du DataFrame et mélange (shuffle) pour ne pas fausser l'entraînement
    df = pd.DataFrame(donnees,
                      columns=['rang_priorite', 'etat_declare', 'titre_ticket', 'details_ticket', 'domaine_cible',
                               'score_cible', 'ethique_veto'])
    df = df.sample(frac=1).reset_index(drop=True)
    df.insert(0, 'id_ticket', [f"TKT-FAC{i:04d}" for i in range(len(df))])

    # Injection SQL
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df.to_sql('tickets', conn, if_exists='replace', index=False)
            print(f"✅ Usine terminée : {len(df)} tickets avec variance linguistique générés.")
    except Exception as e:
        print(f"❌ Erreur : {e}")


if __name__ == "__main__":
    generer_usine_massive()