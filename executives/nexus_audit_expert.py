# executives/nexus_audit_expert.py
import os
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


def generer_corrections_audit():
    print("==================================================")
    print("🔬 AUDIT EXPERT NEXUS - GÉNÉRATION DES CORRECTIONS")
    print("==================================================\n")

    # LA VÉRITÉ ABSOLUE (Ground Truth)
    # Tu définis ici exactement comment le modèle DOIT réagir face aux pièges.
    # Format : [texte, domaine, severite, impact, cible, friction]
    corrections_manuelles = [
        # --- 1. PIÈGES DE LA NÉGATION ET FICTION (Doivent être neutralisés) ---
        ["Il n'y a pas d'arme, c'est juste une dispute verbale", "POLICE", 2, 1, 0, "COMPLET"],
        ["Ce n'est pas urgent, je veux juste un renseignement", "NON_URGENT", 1, 1, 0, "COMPLET"],
        ["Je regarde un film où une bombe explose au centre commercial", "NON_URGENT", 1, 1, 0, "COMPLET"],
        ["Dans mon jeu vidéo, le mec s'est pris une balle", "NON_URGENT", 1, 1, 0, "COMPLET"],
        ["Ma pizza est froide, c'est un scandale absolu !", "NON_URGENT", 1, 1, 0, "COMPLET"],

        # --- 2. URGENCES ABSOLUES TROMPEUSES ---
        ["Un camion citerne d'essence a percuté le commissariat et prend feu", "POMPIER", 4, 3, 2, "MANQUE_LIEU"],
        ["Le serveur principal a pris feu à cause d'un court-circuit", "CYBERSÉCURITÉ", 4, 2, 2, "MANQUE_LIEU"],
        ["Attaque ransomware massive, on perd toutes les données bancaires", "CYBERSÉCURITÉ", 4, 4, 2, "MANQUE_LIEU"],
        ["Le bébé est tout bleu et ne respire plus du tout", "MÉDICAL", 4, 1, 0, "MANQUE_LIEU"],
        ["Un homme cagoulé tire sur la foule", "POLICE", 4, 4, 0, "MANQUE_LIEU"],

        # --- 3. TICKETS LACONIQUES EXTRÊMES (Le crash-test TF-IDF) ---
        ["Ça saigne beaucoup.", "MÉDICAL", 3, 1, 0, "MANQUE_LIEU"],
        ["On a piraté", "CYBERSÉCURITÉ", 3, 2, 0, "MANQUE_CONTEXTE"],
        ["Mon ordinateur.", "DIGITAL SUPPORT", 2, 1, 0, "MANQUE_SYMPTOMES"],
        ["Au feu !", "POMPIER", 4, 2, 0, "MANQUE_LIEU"],
        ["Vite police !", "POLICE", 4, 1, 0, "MANQUE_LIEU"],
        ["Aled", "MÉDICAL", 4, 1, 0, "MANQUE_CONTEXTE"],
        ["Accident grave", "TRANSPORT & MOBILITÉ", 4, 2, 0, "MANQUE_LIEU"]
    ]

    print("⚙️ Compilation des corrections manuelles...")
    df_corrections = pd.DataFrame(corrections_manuelles,
                                  columns=['texte', 'domaine', 'severite', 'impact', 'cible', 'friction'])

    os.makedirs("../audit", exist_ok=True)
    chemin_csv = "../audit/audit_corrections_expert.csv"
    df_corrections.to_csv(chemin_csv, index=False)

    print(f"✅ Fichier de corrections généré avec succès : {chemin_csv}")
    print(f"📊 {len(df_corrections)} cas extrêmes ont été formatés. Prêts pour l'injection Kaggle.")
    print("👉 Uploade ce fichier sur Kaggle en même temps que tes autres datasets.")


if __name__ == "__main__":
    generer_corrections_audit()