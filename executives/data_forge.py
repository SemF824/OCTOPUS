# data_forge.py
import sqlite3
import pandas as pd
import random
import os
from nexus_config import DB_PATH, SYNERGIES_URGENCE, MOTS_LIEUX

PREFIXES_EMPATHIE = ["", "Au secours, ", "Aidez-moi vite, ", "Je panique, "]


def assign_impact_urgence(domaine, texte):
    """Attribue des scores nuancés pour ne pas bloquer à 3/3 (8/10)"""
    t = texte.lower()
    if domaine == "MÉDICAL":
        if any(m in t for m in ["doigt", "ongle", "égratignure", "picotement"]): return "1", "1"
        if any(m in t for m in ["nez", "dent", "entorse", "mal au ventre"]): return "2", "2"
        if any(m in t for m in ["cassé", "fracture", "saigne", "jambe", "bras"]): return "3", "3"
        if any(m in t for m in ["coeur", "cœur", "sang", "hémorragie", "inconscient"]): return "4", "4"
        return "2", "2"
    elif domaine == "POLICE":
        if any(m in t for m in ["bruit", "voisin", "rodéo"]): return "1", "2"
        if any(m in t for m in ["vol", "cambriolage", "effraction"]): return "2", "2"
        if any(m in t for m in ["frappe", "agression", "menace"]): return "3", "3"
        if any(m in t for m in ["arme", "couteau", "fusil", "tueur", "braquage", "tireur"]): return "4", "4"
        return "3", "3"
    elif domaine == "INFRA":
        if "panne totale" in t or "serveur principal" in t: return "4", "4"
        return "3", "2"
    elif domaine == "MATÉRIEL":
        return "1", "1"

    return "2", "2"


def generer_friction_etiquettes(texte_complet, domaine):
    """Découpe le texte et assigne la QUESTION exacte à poser au lieu de 0 ou 1"""
    mots = texte_complet.split()
    if len(mots) <= 3: return [(texte_complet, "DEMANDE_DETAILS_GENERAUX")]

    v1 = " ".join(mots[:len(mots) // 2])  # Garde le début, coupe la fin
    v2 = " ".join(mots[len(mots) // 2:])  # Garde la fin, coupe le début

    labels = []
    if domaine == "MÉDICAL":
        labels = [(v1, "DEMANDE_SYMPTOME_MED"), (v2, "DEMANDE_LIEU_CORPS"), (texte_complet, "COMPLET")]
    elif domaine == "POLICE":
        labels = [(v1, "DEMANDE_ACTION_POLICE"), (v2, "DEMANDE_LIEU_POLICE"), (texte_complet, "COMPLET")]
    elif domaine == "POMPIER":
        labels = [(v1, "DEMANDE_ETAT_POMPIER"), (v2, "DEMANDE_LIEU_POMPIER"), (texte_complet, "COMPLET")]
    elif domaine in ["INFRA", "MATÉRIEL", "ACCÈS"]:
        labels = [(v1, "DEMANDE_PANNE_TECH"), (v2, "DEMANDE_MATERIEL_TECH"), (texte_complet, "COMPLET")]
    else:
        labels = [(v1, "DEMANDE_DETAILS_GENERAUX"), (texte_complet, "COMPLET")]

    return labels


def generer_donnees_v12():
    print("🛠️ GÉNÉRATION FORGE V12 (Nuances de Scores & Questions ML)...")
    domaines_data, friction_data = [], []

    for mot_cle, labels in SYNERGIES_URGENCE.items():
        dom_str = labels[0]
        for _ in range(150):
            texte = f"{random.choice(PREFIXES_EMPATHIE)}il y a une {mot_cle} {random.choice(MOTS_LIEUX)}"
            imp, urg = assign_impact_urgence(dom_str, texte)
            domaines_data.append((texte, dom_str, imp, urg))
            for v, lbl in generer_friction_etiquettes(texte, dom_str): friction_data.append((v, lbl))

    dossier_datasets = "../datasets/"
    if os.path.exists(dossier_datasets):
        for fichier in os.listdir(dossier_datasets):
            if fichier.endswith(".csv"):
                try:
                    df = pd.read_csv(os.path.join(dossier_datasets, fichier))
                    if 'texte' in df.columns and 'domaine' in df.columns:
                        for _, row in df.iterrows():
                            t = str(row['texte'])
                            d = str(row['domaine']).upper()
                            imp, urg = assign_impact_urgence(d, t)
                            domaines_data.append((t, d, imp, urg))
                            for v, lbl in generer_friction_etiquettes(t, d): friction_data.append((v, lbl))
                    elif 'Demande' in df.columns and 'Domaine' in df.columns:
                        for _, row in df.iterrows():
                            t = str(row['Demande'])
                            d = str(row['Domaine']).upper()
                            if "POLICE" in d:
                                d = "POLICE"
                            elif "POMPIER" in d or "INCENDIE" in d:
                                d = "POMPIER"
                            elif "CIRCULATION" in d:
                                d = "POLICE"
                            imp, urg = assign_impact_urgence(d, t)
                            domaines_data.append((t, d, imp, urg))
                            for v, lbl in generer_friction_etiquettes(t, d): friction_data.append((v, lbl))
                except Exception:
                    pass

    df_domaines = pd.DataFrame(domaines_data, columns=["texte", "domaine", "impact", "urgence"]).drop_duplicates()
    df_friction = pd.DataFrame(friction_data, columns=["texte", "label"]).drop_duplicates()

    with sqlite3.connect(DB_PATH) as conn:
        df_domaines.to_sql("tickets_domaines", conn, if_exists="replace", index=False)
        df_friction.to_sql("tickets_friction", conn, if_exists="replace", index=False)

    print(
        f"✅ Forge V12 terminée: {len(df_domaines)} tickets domaine, {len(df_friction)} tickets friction (Questions ML).")


if __name__ == "__main__":
    generer_donnees_v12()