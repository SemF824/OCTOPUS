import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier


# --- 1. CONFIGURATION CLIENTS (Fixe) ---
def generer_clients_fixes():
    data = [
        {"ID_Client": "CLI-102", "Nom_Organisation": "Hôpital de Paris", "Niveau_Importance": 5},  # VIP
        {"ID_Client": "CLI-140", "Nom_Organisation": "PME Tech Solutions", "Niveau_Importance": 2},  # Petit client
        {"ID_Client": "CLI-71", "Nom_Organisation": "Société Générale", "Niveau_Importance": 5},  # VIP
        {"ID_Client": "CLI-999", "Nom_Organisation": "Inconnu", "Niveau_Importance": 1}
    ]
    pd.DataFrame(data).to_csv('base_clients_v8.csv', index=False)


# --- 2. ENTRAÎNEMENT DE BASE (Pour le filet de sécurité) ---
def generer_historique_v8():
    data = []
    # On garde un historique minimal pour que le RandomForest ne plante pas
    for _ in range(100):
        data.append({"Texte": "Serveur HS", "Categorie": "Infra", "Gravite_Reelle": 10})
        data.append({"Texte": "Souris cassée", "Categorie": "Matériel", "Gravite_Reelle": 1})
    pd.DataFrame(data).to_csv('historique_v8.csv', index=False)


# INITIALISATION
generer_clients_fixes()
generer_historique_v8()
df_clients = pd.read_csv('base_clients_v8.csv')
df_hist = pd.read_csv('historique_v8.csv')

# IA "Backup" (Sert uniquement à deviner la catégorie : Infra, Santé, Matériel...)
vectorizer = TfidfVectorizer(stop_words=['le', 'la', 'de', 'pour', 'est', 'une', 'un'])
X = vectorizer.fit_transform(df_hist['Texte'])
model_cat = RandomForestClassifier(n_estimators=10, random_state=42).fit(X, df_hist['Categorie'])

# --- 3. LE CŒUR DU SYSTÈME : LA MATRICE SÉMANTIQUE ---

# Dictionnaire des OBJETS (Valeur intrinsèque)
SCORES_OBJETS = {
    # IT VITAL (10)
    'serveur': 10, 'datacenter': 10, 'backbone': 10, 'réanimation': 10, 'cœur': 10,
    # IT BLOQUANT / SANTÉ SÉRIEUSE (7-8)
    'ordinateur': 8, 'pc': 8, 'mac': 8, 'intranet': 7, 'crm': 7, 'jambe': 8, 'cheville': 7, 'bras': 7,
    # CONFORT / SANTÉ BÉNINE (1-2)
    'souris': 1, 'clavier': 1, 'écran': 2, 'café': 0, 'nez': 1, 'doigt': 2, 'stylo': 0
}

# Dictionnaire des ÉTATS (Multiplicateur de gravité)
SCORES_ETATS = {
    # CATASTROPHE (x 1.5 -> Plafond à 10)
    'feu': 1.5, 'mort': 1.5, 'arrêt': 1.5, 'danger': 1.5, 'incendie': 1.5,
    # PROBLÈME CONFIRMÉ (x 1.0)
    'hs': 1.0, 'panne': 1.0, 'cassé': 1.0, 'cassée': 1.0, 'fracture': 1.0, 'bloqué': 1.0, 'impossible': 1.0,
    # PROBLÈME MINEUR / DOUTEUX (x 0.5)
    'manque': 0.5, 'perdu': 0.5, 'lent': 0.5, 'saigne': 0.5, 'bruit': 0.3, 'couleur': 0.1
}


def calculer_score_semantique(texte):
    """Analyse chaque mot pour trouver le pire scénario Objet + État"""
    words = texte.lower().replace("'", " ").split()

    # 1. On cherche l'objet le plus précieux dans la phrase
    max_objet_score = 0
    objet_trouve = "Aucun"
    for word in words:
        if word in SCORES_OBJETS:
            if SCORES_OBJETS[word] > max_objet_score:
                max_objet_score = SCORES_OBJETS[word]
                objet_trouve = word

    # 2. On cherche l'état le plus grave
    max_etat_mult = 0.5  # Par défaut, si on ne sait pas, c'est une gêne (0.5)
    etat_trouve = "Inconnu"

    # Si aucun état n'est précisé mais qu'il y a un objet, on suppose une panne standard (1.0)
    if max_objet_score > 0:
        max_etat_mult = 1.0

    for word in words:
        if word in SCORES_ETATS:
            if SCORES_ETATS[word] > max_etat_mult:
                max_etat_mult = SCORES_ETATS[word]
                etat_trouve = word

    # CALCUL DU SCORE TECHNIQUE
    score_tech = max_objet_score * max_etat_mult

    return min(10, score_tech), objet_trouve, etat_trouve


# --- 4. MOTEUR DE DÉCISION V8 ---
def traiter_ticket(texte, id_client):
    # A. Analyse IA (Juste pour la catégorie)
    try:
        v_texte = vectorizer.transform([texte])
        categorie = model_cat.predict(v_texte)[0]
    except:
        categorie = "Général"

    # B. Client
    client_row = df_clients[df_clients['ID_Client'] == id_client]
    if not client_row.empty:
        nom = client_row.iloc[0]['Nom_Organisation']
        imp = client_row.iloc[0]['Niveau_Importance']
    else:
        nom = "Inconnu"
        imp = 1

    # C. ANALYSE MATRICIELLE (La nouveauté)
    gravite_tech, obj, etat = calculer_score_semantique(texte)

    # D. FORMULE FINALE
    # Si la gravité technique est très faible (< 2), l'importance client ne compte presque pas.
    # Si la gravité est haute, l'importance client sert de boost.

    if gravite_tech < 2:
        # Cas de la Souris : Score Tech (0.5) + Petit Bonus Client (Imp * 0.2)
        score_final = gravite_tech + (imp * 0.2)
    else:
        # Cas Sérieux : 70% Tech + 30% Client
        score_final = (gravite_tech * 0.7) + (imp * 2 * 0.3)

    return {
        "Ticket": texte,
        "Client": f"{nom} (Imp {imp})",
        "Détails": f"Objet: {obj} ({SCORES_OBJETS.get(obj, 0)}) | État: {etat} (x{SCORES_ETATS.get(etat, 1.0)})",
        "Gravité_Tech": f"{gravite_tech:.1f}/10",
        "SCORE_FINAL": f"{min(10, score_final):.1f}/10"
    }


# --- 5. LE COMPARATIF FINAL (TES DEMANDES) ---
print("\n" + "=" * 80)
print(" RÉSULTATS V8 : LE TRIOMPHE DU SENS COMMUN")
print("=" * 80)

scenarios = [
    # CAS 1 : Matériel (PME vs SG)
    ("Mon ordinateur est en panne bloqué", "CLI-140"),  # PME (Imp 2) + PC (8) * Panne (1.0) = Tech 8
    ("Il me manque une souris sans fil", "CLI-71"),  # SG (Imp 5) + Souris (1) * Manque (0.5) = Tech 0.5

    # CAS 2 : Santé (Urgence vs Bobo)
    ("Je me suis cassé la cheville", "CLI-102"),  # Hôpital + Cheville (7) * Cassé (1.0) = Tech 7
    ("J'ai le nez qui saigne", "CLI-102"),  # Hôpital + Nez (1) * Saigne (0.5) = Tech 0.5

    # CAS 3 : Vital
    ("Le serveur est HS arrêt total", "CLI-999")  # Inconnu + Serveur (10) * HS (1.0) = Tech 10
]

for t, id_c in scenarios:
    res = traiter_ticket(t, id_c)
    print(f"[Ticket] : {res['Ticket']}")
    print(f"   -> {res['Client']}")
    print(f"   -> ⚙️  {res['Détails']}")
    print(f"   -> 🎯 PRIORITÉ : {res['SCORE_FINAL']}")
    print("-" * 40)