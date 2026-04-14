# data_forge.py
import sqlite3
import pandas as pd
import random
from nexus_config import DB_PATH


def generer_donnees_v7():
    print("🛠️ Génération de la Forge V7...")
    # (Tes générateurs de base ici...)

    # Injection des correctifs (Vaccins)
    vaccins = [
        ("ACCÈS", ["connexion VPN", "token MFA", "accès refusé", "mot de passe oublié"]),
        ("INFRA", ["serveur en panne", "routeur HS", "latence réseau", "coupure fibre"]),
        ("POMPIER", [
            "incendie dans l'immeuble",
            "feu de forêt signalé",
            "fumée dans le couloir",
            "explosion au rez-de-chaussée",
            "fuite de gaz détectée",
            "départ de feu en cuisine",
            "voiture en feu sur l'autoroute",
            "flammes visibles au 3ème étage",
        ]),
        ("POLICE", [
            "agression dans la rue",
            "cambriolage à mon domicile",
            "vol de voiture signalé",
            "violences conjugales",
            "menaces de mort reçues",
            "bagarre devant le bar",
            "vol à l'arrachée",
            "braquage signalé", "agression", "cambriolage", "vol de voiture", "violences", "braquage", "arme", "rodéo"
        ]),
    ]

    rows = []
    for domaine, phrases in vaccins:
        for p in phrases:
            for _ in range(150):  # Poids fort
                rows.append((p, domaine))

    df = pd.DataFrame(rows, columns=["details_ticket", "domaine_cible"])
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("tickets", conn, if_exists="append", index=False)
    print("✅ Base de données prête pour Kaggle.")


if __name__ == "__main__":
    generer_donnees_v7()
