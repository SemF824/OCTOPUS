import sqlite3
import pandas as pd
import random

DB_PATH = "nexus_bionexus.db"


def generer_usine_monde_reel():
    print(">>> DÉMARRAGE DE LA DATA FACTORY V4 (SIMULATEUR MONDE RÉEL)...")
    donnees = []
    titres = ["Ticket", "Demande", "Incident", "Problème", "Assistance", "Urgence", "Besoin"]

    # Le "bruit" simule le langage humain pour habituer le vectorizer (TF-IDF baissera leur poids)
    bruit = ["", "bonjour", "svp", "il y a un", "mon", "le", "la", "avec", "pour", "je n'arrive pas à",
             "problème avec la touche"]

    # Vérité métier absolue (Liste de mots -> Domaine, Score Réel de base, Veto)
    concepts = [
        # MÉDICAL (4000)
        (["jambe", "bras", "doigt", "tête", "ventre", "coupure", "douleur"], "MÉDICAL", 2.0, "NON"),
        (["cœur", "poitrine", "respire plus", "malaise", "sang", "inconscient"], "MÉDICAL", 10.0, "OUI (Veto)"),

        # --- LE CONCEPT DE LA FRACTURE ---
        (["cassé", "fracture", "os", "entorse", "entorse grave", "déchirure", "luxation"], "MÉDICAL", 7.5, "NON"),

        # INFRA (4000)
        (["câble", "wifi", "lenteur réseau", "latence", "débranché", "internet"], "INFRA", 3.0, "NON"),
        (["datacenter", "feu", "ransomware", "cyberattaque", "serveurs down"], "INFRA", 10.0, "OUI (Veto)"),

        # MATÉRIEL (4000)
        (["clavier", "souris", "écran", "ordinateur", "imprimante", "casque", "espace"], "MATÉRIEL", 2.5, "NON"),
        (["batterie gonflée", "étincelles ordinateur", "fumée écran"], "MATÉRIEL", 8.0, "NON"),

        # RH (4000)
        (["salaire", "paie", "congés", "fiche", "contrat", "absence", "mutuelle"], "RH", 4.0, "NON"),
        (["harcèlement", "burnout", "conflit grave", "inspection du travail"], "RH", 9.0, "NON"),

        # ACCÈS (4000)
        (["mot de passe", "session", "badge", "portique", "vpn", "accès refusé"], "ACCÈS", 3.5, "NON"),
        (["vol de badge", "usurpation d'identité", "compte admin piraté"], "ACCÈS", 9.5, "OUI (Veto)")
    ]

    # Le comportement humain est chaotique et menteur : total aléatoire pour décorréler l'IA
    def etat_user():
        return random.choice(["NORMAL", "URGENT"])

    def rang_user():
        return random.randint(1, 5)

    # 2000 tickets par concept = 20 000 tickets au total (4000 par domaine strict)
    for mots, domaine, score_base, veto in concepts:
        for _ in range(2000):
            texte = f"{random.choice(bruit)} {random.choice(mots)} {random.choice(bruit)}".strip()
            # Le score cible varie légèrement autour de sa vérité métier pour éviter le surapprentissage absolu
            score_final = min(max(random.uniform(score_base - 1.0, score_base + 1.0), 1.0), 10.0)
            if veto == "OUI (Veto)": score_final = 10.0

            donnees.append((rang_user(), etat_user(), random.choice(titres), texte, domaine, score_final, veto))

    df = pd.DataFrame(donnees,
                      columns=['rang_priorite', 'etat_declare', 'titre_ticket', 'details_ticket', 'domaine_cible',
                               'score_cible', 'ethique_veto'])
    df = df.sample(frac=1).reset_index(drop=True)
    df.insert(0, 'id_ticket', [f"TKT-FAC{i:04d}" for i in range(len(df))])

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql('tickets', conn, if_exists='replace', index=False)
        print(f"✅ Usine V4 terminée : {len(df)} tickets générés (Équilibre et Chaos activés).")


if __name__ == "__main__":
    generer_usine_monde_reel()
