# ==============================================================================
# NEXUS - KAGGLE MASTER V21 - SCRIPT D'ENTRAÎNEMENT CORRIGÉ
# ==============================================================================
# CORRECTIONS PAR RAPPORT AU V20 :
#   1. Utilisation de nexus_massive_dataset.csv comme base (déjà équilibré)
#   2. Normalisation correcte des domaines et priorités de tous les CSV
#   3. Fausses alertes isolées et bien labellisées
#   4. Génération de données intermédiaires (scores 2/4, 3/4)
#   5. nexus_complement_dataset.csv IGNORÉ (84% de 4/4 → poison)
#   6. nexus_dataset_8000.csv IGNORÉ (tickets clients hors domaine)
# ==============================================================================
# INSTRUCTIONS KAGGLE :
#   1. Uploade tous tes CSV comme un dataset Kaggle (ex: "nexus-datasets")
#   2. Uploade le dossier executives/ comme un autre dataset (ex: "nexus-ghali")
#   3. Modifie CSV_FOLDER ci-dessous selon le nom de ton dataset Kaggle
# ==============================================================================

import os, sys, sqlite3, random, joblib, warnings
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
warnings.filterwarnings("ignore")

# --- CHEMINS ---
KAGGLE_WORKING   = "/kaggle/working"
CSV_FOLDER       = "/kaggle/input/nexus-datasets"   # ← adapter si besoin
EXEC_FOLDER      = "/kaggle/input/nexus-ghali/executives"
DB_PATH          = f"{KAGGLE_WORKING}/nexus_bionexus.db"
MODEL_PATH       = f"{KAGGLE_WORKING}/pickle_result/nexus_v21_unified.pkl"
MODEL_FRIC_PATH  = f"{KAGGLE_WORKING}/pickle_result/nexus_v21_friction.pkl"

os.makedirs(f"{KAGGLE_WORKING}/pickle_result", exist_ok=True)
sys.path.append(EXEC_FOLDER)
from nexus_core import TextEncoder

RF_PARAMS = {
    'n_estimators': 400,
    'max_depth': 35,
    'class_weight': 'balanced',
    'random_state': 42,
    'n_jobs': -1
}

# ==============================================================================
# ÉTAPE 1 — TABLES DE NORMALISATION
# ==============================================================================

# Mapping des sous-domaines bruts → domaine NEXUS standard
DOMAIN_MAP = {
    # MÉDICAL
    "Urgence Vitale Absolue (SMUR)":   "MÉDICAL",
    "Psychiatrie & Détresse":           "MÉDICAL",
    "Traumatologie & Blessures":        "MÉDICAL",
    "Obstétrique & Pédiatrie":          "MÉDICAL",
    "Médecine de Garde & Conseil":      "MÉDICAL",
    # POLICE
    "Police Secours (Crimes & Délits)": "POLICE",
    "Ordre Public & Nuisances":         "POLICE",
    "Sécurité Routière & Circulation":  "POLICE",
    # POMPIER
    "Opérations Diverses":              "POMPIER",
    # INFRA
    "Infra - Serveurs & Datacenter":    "INFRA",
    "Infra - Matériel Réseau (LAN)":    "INFRA",
    "Infra - Connectivité & Télécom":   "INFRA",
    # MATÉRIEL
    "Matériel - Bureautique & IT":      "MATÉRIEL",
    "Services Généraux - Plomberie":    "MATÉRIEL",
    "Services Généraux - Mobilier":     "MATÉRIEL",
    "Flotte & Mobilité":                "MATÉRIEL",
    # ACCÈS
    "Gestion des Comptes & Droits":     "ACCÈS",
    "Sécurité & Double Authentification": "ACCÈS",
    "Accès Distant & VPN":              "ACCÈS",
    "ACCÈS":                            "ACCÈS",
}

# Sous-domaines toujours critiques → score forcé à 4/4 peu importe la priorité
TOUJOURS_CRITIQUE = {"Urgence Vitale Absolue (SMUR)", "Police Secours (Crimes & Délits)"}

# Mapping priorité → (impact, urgence)
# On utilise 3/3 pour Haute (et non 4/4) pour éviter l'écrasement
PRIORITY_MAP = {
    "Haute":   (3, 3),
    "HAUTE":   (3, 3),
    "Moyenne": (2, 2),
    "MOYENNE": (2, 2),
    "Basse":   (1, 1),
    "BASSE":   (1, 1),
}


def normalize_row(raw_domain, raw_priority):
    """Renvoie (domaine_nexus, impact, urgence)."""
    domaine = DOMAIN_MAP.get(raw_domain, raw_domain.upper().strip())

    if raw_domain in TOUJOURS_CRITIQUE:
        return domaine, 4, 4

    imp, urg = PRIORITY_MAP.get(str(raw_priority).strip(), (2, 2))
    return domaine, imp, urg


# ==============================================================================
# ÉTAPE 2 — CHARGEMENT ET NORMALISATION DE CHAQUE CSV
# ==============================================================================

def load_csv_safe(filename):
    path = os.path.join(CSV_FOLDER, filename)
    if not os.path.exists(path):
        print(f"  ⚠️  Fichier manquant : {filename}")
        return None
    return pd.read_csv(path)


def charger_tous_les_csv():
    frames = []
    print("\n--- CHARGEMENT DES DATASETS CSV ---")

    # ── 1. nexus_massive_dataset.csv  (base principale – déjà équilibrée) ──
    df = load_csv_safe("nexus_massive_dataset.csv")
    if df is not None:
        df = df[['texte', 'domaine', 'impact', 'urgence']].dropna()
        df['domaine'] = df['domaine'].str.strip().str.upper()
        frames.append(df)
        print(f"  ✅ massive_dataset         : {len(df):>7} lignes")

    # ── 2. dataset_tickets_medical.csv ──
    df = load_csv_safe("dataset_tickets_medical.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            dom, imp, urg = normalize_row(r['Domaine'], r['Niveau de priorité'])
            rows.append((str(r['Demande']), dom, imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_medical         : {len(tmp):>7} lignes")

    # ── 3. dataset_tickets_PoliceNationale.csv ──
    df = load_csv_safe("dataset_tickets_PoliceNationale.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            dom, imp, urg = normalize_row(r['Domaine'], r['Niveau de priorité'])
            rows.append((str(r['Demande']), dom, imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_PoliceNationale : {len(tmp):>7} lignes")

    # ── 4. dataset_tickets_pompiers.csv ──
    df = load_csv_safe("dataset_tickets_pompiers.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            dom, imp, urg = normalize_row(r['Domaine'], r['Niveau de priorité'])
            rows.append((str(r['Demande']), dom, imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_pompiers        : {len(tmp):>7} lignes")

    # ── 5. dataset_tickets_Infra.csv ──
    df = load_csv_safe("dataset_tickets_Infra.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            dom, imp, urg = normalize_row(r['Domaine'], r['Niveau de priorité'])
            rows.append((str(r['Demande']), dom, imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_Infra           : {len(tmp):>7} lignes")

    # ── 6. dataset_tickets_Materiel.csv ──
    df = load_csv_safe("dataset_tickets_Materiel.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            dom, imp, urg = normalize_row(r['Domaine'], r['Niveau de priorité'])
            rows.append((str(r['Demande']), dom, imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_Materiel        : {len(tmp):>7} lignes")

    # ── 7. dataset_tickets_acces.csv ──
    df = load_csv_safe("dataset_tickets_acces.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            imp, urg = PRIORITY_MAP.get(str(r['Niveau de priorité']).strip(), (2, 2))
            rows.append((str(r['Demande']), 'ACCÈS', imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_acces           : {len(tmp):>7} lignes")

    # ── 8. dataset_tickets_acceslogin.csv ──
    df = load_csv_safe("dataset_tickets_acceslogin.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            dom, imp, urg = normalize_row(r['Domaine'], r['Niveau de priorité'])
            rows.append((str(r['Demande']), dom, imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ tickets_acceslogin      : {len(tmp):>7} lignes")

    # ── 9. nexus_renfort_15000_complet.csv ──
    df = load_csv_safe("nexus_renfort_15000_complet.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            imp, urg = PRIORITY_MAP.get(str(r['priorite']).strip(), (2, 2))
            rows.append((str(r['texte']), str(r['domaine']).strip().upper(), imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ renfort_15000           : {len(tmp):>7} lignes")

    # ── 10. nexus_stress_test_15000.csv (pas d'impact/urgence → défaut Moyenne) ──
    df = load_csv_safe("nexus_stress_test_15000.csv")
    if df is not None:
        df = df[['texte','domaine']].dropna()
        df['domaine'] = df['domaine'].str.strip().str.upper()
        df['impact']  = 2
        df['urgence'] = 2
        frames.append(df)
        print(f"  ✅ stress_test_15000       : {len(df):>7} lignes (impact/urgence=2/2 par défaut)")

    # ── 11. nexus_urgences_priorises.csv ──
    df = load_csv_safe("nexus_urgences_priorises.csv")
    if df is not None:
        rows = []
        for _, r in df.iterrows():
            imp, urg = PRIORITY_MAP.get(str(r['priorite']).strip(), (2, 2))
            rows.append((str(r['texte']), str(r['label']).strip().upper(), imp, urg))
        tmp = pd.DataFrame(rows, columns=['texte','domaine','impact','urgence'])
        frames.append(tmp)
        print(f"  ✅ urgences_priorises      : {len(tmp):>7} lignes")

    # ── 12. medDataset_processed.csv (FAQ médicale → informatif, score bas) ──
    df = load_csv_safe("medDataset_processed.csv")
    if df is not None:
        df = df[['texte','domaine']].dropna()
        df['domaine'] = "MÉDICAL"
        df['impact']  = 1
        df['urgence'] = 1
        frames.append(df)
        print(f"  ✅ medDataset_processed    : {len(df):>7} lignes (FAQ médicale, score 1/1)")

    # ── 13. nexus_medical_3000.csv (même type FAQ) ──
    df = load_csv_safe("nexus_medical_3000.csv")
    if df is not None:
        df = df.rename(columns={'ticket_fr': 'texte', 'domaine_cible': 'domaine'})
        df = df[['texte','domaine']].dropna().drop_duplicates()
        df['domaine'] = "MÉDICAL"
        df['impact']  = 1
        df['urgence'] = 1
        frames.append(df)
        print(f"  ✅ nexus_medical_3000      : {len(df):>7} lignes (FAQ médicale, score 1/1)")

    # ── IGNORÉS VOLONTAIREMENT ──
    print("  ⏭️  nexus_complement_dataset.csv IGNORÉ (84% impact=4 → biais)")
    print("  ⏭️  nexus_dataset_8000.csv      IGNORÉ (tickets SAV hors domaine)")

    return frames


# ==============================================================================
# ÉTAPE 3 — GÉNÉRATION DES FAUSSES ALERTES ET CAS NUANCÉS
# ==============================================================================

def generer_donnees_complementaires():
    print("\n--- GÉNÉRATION DES DONNÉES COMPLÉMENTAIRES ---")
    data = []

    # ── Fausses alertes (score très bas) ──
    FAUSSES_ALERTES = [
        "Ceci est un exercice d'évacuation",
        "Test de l'alarme incendie programmé",
        "Simulation de piratage en cours",
        "Exercice attentat dans l'école",
        "C'est pour un jeu de rôle grandeur nature",
        "Je regarde un film où une bombe explose",
        "Dans mon jeu vidéo le personnage est blessé",
        "Je lis un manga où le héros se bat",
        "Un Titan attaque dans L'Attaque des Titans",
        "Mon personnage Minecraft est mort",
        "C'est une blague, tout va bien",
        "Fausse alerte, désolé pour le dérangement",
        "C'était juste une simulation de crise",
        "Le braquage dans le film était très réaliste",
        "Drôle d'histoire : mon pote a fait semblant d'être mort",
    ]
    RUES = [f"rue {i}" for i in range(1, 200)]
    for texte in FAUSSES_ALERTES:
        for _ in range(800):  # 800 × 15 = 12 000 fausses alertes
            variante = texte if random.random() < 0.4 else f"{texte} au {random.randint(1,99)} {random.choice(RUES)}"
            data.append((variante, "INFORMATION / SÉCURITÉ", "1", "1"))

    # ── Cas intermédiaires manquants (score 2/4 et 3/4) ──
    CAS_INTERMEDIAIRES = [
        # Médical
        ("MÉDICAL", [
            ("J'ai mal à la tête depuis ce matin", 1, 2),
            ("Mon enfant a de la fièvre à 39°C", 2, 2),
            ("Je me suis tordu la cheville en courant", 1, 2),
            ("J'ai une grosse entorse au genou", 2, 2),
            ("Mon père a vomi plusieurs fois", 2, 3),
            ("J'ai une douleur au dos très forte", 2, 2),
            ("Mon bras saigne, j'ai besoin de points", 3, 3),
            ("Elle a une fracture, l'os ne dépasse pas", 3, 3),
            ("Il a perdu connaissance mais respire", 3, 4),
        ]),
        # Police
        ("POLICE", [
            ("On a tagué ma façade cette nuit", 1, 1),
            ("Mon voisin fait du bruit toute la nuit", 1, 2),
            ("J'ai retrouvé ma voiture rayée", 2, 1),
            ("On m'a volé mon vélo ce matin", 2, 2),
            ("Un individu rode autour de chez moi", 2, 3),
            ("Je me suis fait voler mon téléphone", 2, 3),
            ("Mon voisin me menace verbalement", 3, 3),
            ("Des individus se bagarrent dans la rue", 3, 4),
        ]),
        # INFRA
        ("INFRA", [
            ("Mon mot de passe VPN est expiré", 1, 1),
            ("L'internet est lent sur mon poste", 1, 2),
            ("Plusieurs postes n'arrivent plus à imprimer", 2, 2),
            ("Le réseau est instable depuis 1h", 2, 3),
            ("Le serveur de fichiers répond lentement", 3, 2),
            ("Impossible d'accéder à l'ERP depuis ce matin", 3, 3),
            ("Panne totale du serveur de messagerie", 4, 3),
        ]),
        # MATÉRIEL
        ("MATÉRIEL", [
            ("Mon clavier a quelques touches qui ne marchent plus", 1, 1),
            ("L'écran de mon laptop clignote", 2, 2),
            ("Mon PC ne démarre plus depuis ce matin", 2, 3),
            ("Le vidéoprojecteur de la salle est mort", 2, 2),
        ]),
        # ACCÈS
        ("ACCÈS", [
            ("J'ai oublié mon mot de passe Windows", 1, 2),
            ("Mon compte est bloqué après trop de tentatives", 2, 2),
            ("Je n'arrive plus à me connecter au VPN depuis hier", 2, 3),
            ("Mon badge d'accès ne fonctionne plus", 2, 2),
        ]),
    ]

    for domaine, cas in CAS_INTERMEDIAIRES:
        for texte, imp, urg in cas:
            for _ in range(2000):  # 2000 × cas = bon volume
                variante = f"{texte} au {random.randint(1,99)} {random.choice(RUES)}"
                data.append((variante, domaine, str(imp), str(urg)))
                data.append((texte, domaine, str(imp), str(urg)))  # sans lieu aussi

    df = pd.DataFrame(data, columns=["texte", "domaine", "impact", "urgence"])
    print(f"  ✅ Données générées : {len(df):>7} lignes")
    return df


# ==============================================================================
# ÉTAPE 4 — GÉNÉRATION DES DONNÉES DE FRICTION (QUESTIONS)
# ==============================================================================

def generer_friction(df_domaines):
    print("\n--- GÉNÉRATION DES DONNÉES DE FRICTION ---")
    data = []

    PHRASES_INCOMPLETES = {
        "PRECISION_MED": [
            "Ça saigne", "J'ai mal", "Au secours", "Il est tombé", "Je me sens mal",
            "Vite un médecin", "Il respire bizarrement", "Elle a perdu connaissance",
            "Mon fils", "Ma mère", "Il ne bouge plus", "Ça fait très mal",
        ],
        "PRECISION_POL": [
            "On m'a volé", "Je suis suivi", "Il y a un homme bizarre", "Bagarre",
            "Ils ont une arme", "Au voleur", "Vite la police", "Il me menace",
            "Quelqu'un est entré", "Des coups de feu",
        ],
        "PRECISION_POMP": [
            "Ça brûle", "Il y a le feu", "Accident", "Fumée partout",
            "Ça a explosé", "Odeur de gaz", "L'eau monte",
        ],
        "PRECISION_TECH": [
            "Le serveur est en panne", "Plus d'internet", "Mot de passe perdu",
            "Mon ordinateur", "Ça marche pas", "Bug", "Erreur",
            "Je n'arrive plus à me connecter", "Le réseau",
        ],
    }

    for label, phrases in PHRASES_INCOMPLETES.items():
        for phrase in phrases:
            for _ in range(800):  # Volume suffisant
                data.append((phrase, label))
                data.append((phrase.lower(), label))
                # Variantes avec fautes d'orthographe légères
                data.append((phrase + ".", label))
                data.append((phrase + "!!", label))

    # Tickets complets : on pioche dans le dataset domaine
    n_complets = min(50000, len(df_domaines))
    for texte in df_domaines['texte'].sample(n_complets, random_state=42):
        data.append((str(texte), "COMPLET"))

    df = pd.DataFrame(data, columns=["texte", "label"]).drop_duplicates()
    print(f"  ✅ Données friction : {len(df):>7} lignes")
    return df


# ==============================================================================
# ÉTAPE 5 — VÉRIFICATION DE L'ÉQUILIBRE DES DONNÉES
# ==============================================================================

def afficher_bilan(df):
    print("\n📊 BILAN DES DONNÉES D'ENTRAÎNEMENT :")
    print(f"  Total lignes : {len(df):,}")
    print("\n  Distribution domaines :")
    for dom, cnt in df['domaine'].value_counts().items():
        pct = cnt / len(df) * 100
        print(f"    {dom:<30} {cnt:>8,}  ({pct:4.1f}%)")
    print("\n  Distribution impact :")
    for val, cnt in df['impact'].value_counts().sort_index().items():
        pct = cnt / len(df) * 100
        print(f"    Impact {val}  {cnt:>8,}  ({pct:4.1f}%)")
    print("\n  Distribution urgence :")
    for val, cnt in df['urgence'].value_counts().sort_index().items():
        pct = cnt / len(df) * 100
        print(f"    Urgence {val} {cnt:>8,}  ({pct:4.1f}%)")


# ==============================================================================
# PROGRAMME PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 NEXUS MASTER V21 — DÉMARRAGE DE L'ENTRAÎNEMENT")
    print("=" * 60)

    # ── 1. Chargement de tous les CSV ──
    frames = charger_tous_les_csv()

    # ── 2. Génération des données complémentaires ──
    df_complement = generer_donnees_complementaires()
    frames.append(df_complement)

    # ── 3. Fusion et nettoyage ──
    print("\n--- FUSION ET NETTOYAGE ---")
    df_domaines = pd.concat(frames, ignore_index=True)

    # Normalisation finale des colonnes
    df_domaines['domaine'] = df_domaines['domaine'].str.strip().str.upper()
    df_domaines['impact']  = df_domaines['impact'].astype(str).str.strip()
    df_domaines['urgence'] = df_domaines['urgence'].astype(str).str.strip()

    # Suppression des domaines inconnus ou vides
    DOMAINES_VALIDES = {"MÉDICAL", "POLICE", "POMPIER", "INFRA", "MATÉRIEL", "ACCÈS", "INFORMATION / SÉCURITÉ"}
    df_domaines = df_domaines[df_domaines['domaine'].isin(DOMAINES_VALIDES)]

    # Suppression des doublons
    avant = len(df_domaines)
    df_domaines = df_domaines.drop_duplicates(subset=['texte'])
    print(f"  ✅ Doublons supprimés : {avant - len(df_domaines):,}")
    print(f"  ✅ Total final        : {len(df_domaines):,} lignes uniques")

    afficher_bilan(df_domaines)

    # ── 4. Génération des données friction ──
    df_friction = generer_friction(df_domaines)

    # ── 5. Sauvegarde SQLite ──
    print("\n--- SAUVEGARDE BASE DE DONNÉES ---")
    with sqlite3.connect(DB_PATH) as conn:
        df_domaines.to_sql("tickets_domaines", conn, if_exists="replace", index=False)
        df_friction.to_sql("tickets_friction",  conn, if_exists="replace", index=False)
    print(f"  ✅ Base SQLite sauvegardée : {DB_PATH}")

    # ── 6. Entraînement Modèle Principal ──
    print("\n--- ENTRAÎNEMENT MODÈLE PRINCIPAL (domaine + impact + urgence) ---")
    y_multi = df_domaines[['domaine', 'impact', 'urgence']].astype(str).values

    pipeline_dom = Pipeline([
        ('vec', TextEncoder()),
        ('clf', MultiOutputClassifier(RandomForestClassifier(**RF_PARAMS)))
    ])

    print(f"  ⚙️  Entraînement sur {len(df_domaines):,} tickets...")
    pipeline_dom.fit(df_domaines['texte'], y_multi)
    joblib.dump(pipeline_dom, MODEL_PATH)
    print(f"  ✅ Modèle principal sauvegardé : {MODEL_PATH}")

    # ── 7. Entraînement Modèle Friction ──
    print("\n--- ENTRAÎNEMENT MODÈLE FRICTION (questions) ---")
    pipeline_fric = Pipeline([
        ('vec', TextEncoder()),
        ('clf', RandomForestClassifier(**RF_PARAMS))
    ])

    print(f"  ⚙️  Entraînement sur {len(df_friction):,} tickets...")
    pipeline_fric.fit(df_friction['texte'], df_friction['label'].astype(str))
    joblib.dump(pipeline_fric, MODEL_FRIC_PATH)
    print(f"  ✅ Modèle friction sauvegardé : {MODEL_FRIC_PATH}")

    print("\n" + "=" * 60)
    print("🎉 NEXUS V21 PRÊT ! Télécharge nexus_v21_unified.pkl et nexus_v21_friction.pkl")
    print("=" * 60)