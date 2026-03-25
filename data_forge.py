"""
DATA FORGE V8 — Données Synthétiques Tone-Varied
Remplace la génération brute par des variations tonales (urgent, désespéré,
sarcastique, technique...) et injecte des cas de NÉGATION pour entraîner
le modèle à gérer les faux positifs médicaux.
"""
import sqlite3
import pandas as pd
import random

DB_PATH = "nexus_bionexus.db"

# ── TEMPLATES PAR DOMAINE ET TON ──────────────────────────────────────────────
# Chaque {k} est remplacé par un mot-clé aléatoire du domaine.
# L'objectif : produire des phrases naturellement diversifiées en style ET urgence.

TEMPLATES = {
    "MATÉRIEL": {
        "mots_cles": [
            "clavier", "souris", "ordinateur", "écran", "imprimante",
            "laptop", "câble USB", "périphérique", "batterie", "dalle"
        ],
        "tons": {
            "calme":      ["{k} ne fonctionne pas", "problème avec le {k}", "mon {k} est en panne"],
            "urgent":     ["URGENT {k} HS réunion dans 10min !!!", "besoin aide immédiate {k} mort", "CATASTROPHE mon {k} a lâché"],
            "désespéré":  ["je vais perdre tout mon travail {k} cassé", "SOS {k} mort impossible de travailler", "3ème {k} en panne ce mois"],
            "sarcastique":["encore le {k} qui décide de mourir", "bien sûr c'est le {k} qui flanche auj", "bravo le {k} parfait timing"],
            "technique":  ["défaillance hardware {k} diagnostic requis", "{k} panne intermittente port USB", "{k} IRQ conflict BSOD"],
            "confus":     ["je sais pas pourquoi mais {k} marche plus", "quelque chose cloche avec {k} aidez moi"],
        }
    },
    "INFRA": {
        "mots_cles": [
            "wifi", "internet", "réseau", "VPN", "serveur",
            "connexion", "fibre", "routeur", "datacenter", "proxy"
        ],
        "tons": {
            "calme":      ["problème de {k}", "le {k} est instable", "coupure {k} signalée"],
            "urgent":     ["RÉSEAU DOWN URGENT {k}", "plus de {k} réunion client dans 5 min !!!", "panne totale {k} site bloqué"],
            "désespéré":  ["sans {k} depuis 2h réunion annulée clients perdus", "je perds des contrats à cause du {k}"],
            "sarcastique":["le {k} en vacances comme d'habitude", "encore et toujours le {k} qui plante"],
            "technique":  ["latence élevée {k} traceroute KO MTU mismatch", "{k} gateway timeout 504 BGP flap"],
            "panique":    ["tout est DOWN {k} plus rien ne répond urgence absolue !!!"],
        }
    },
    "ACCÈS": {
        "mots_cles": [
            "mot de passe", "badge", "session", "compte",
            "authentification", "accès", "token", "certificat"
        ],
        "tons": {
            "calme":      ["réinitialisation {k} requise", "problème de {k}", "bloqué sur {k}"],
            "urgent":     ["BLOQUÉ DEHORS réunion dans 2min {k} expiré !!!!", "impossible accès {k} rendez-vous critique"],
            "désespéré":  ["enfermé dehors depuis 1h {k} ne marche plus", "bloqué sans {k} travail paralysé"],
            "sarcastique":["encore le {k} magique qui refuse de fonctionner", "splendide {k} expiré sans prévenir merci"],
            "technique":  ["SSO {k} timeout Kerberos ticket invalide", "{k} LDAP sync failure AD forest"],
        }
    },
    "MÉDICAL": {
        "mots_cles": [
            "douleur", "fièvre", "nausée", "malaise", "blessure",
            "saignement", "brûlure", "vertiges", "choc"
        ],
        "tons": {
            "calme":      ["j'ai une légère {k}", "petite {k} depuis ce matin", "ressens une {k} modérée"],
            "urgent":     ["URGENCE {k} forte !!!", "{k} intense depuis 1h besoin aide", "forte {k} besoin intervention"],
            "grave":      ["collègue inconscient après {k}", "AVC suspecté {k} appelez les secours", "hémorragie {k} grave"],
            "panique":    ["je {k} appeler le 15 maintenant", "{k} bras gauche douleur irradiante", "victime d'un malaise {k}"],
            "descriptif": ["symptômes {k} depuis hier pas amélioré", "{k} récurrente besoin consultation"],
        }
    },
    "RH": {
        "mots_cles": [
            "salaire", "congés", "contrat", "mutuelle", "paie",
            "fiche de paie", "entretien", "prime", "arrêt maladie"
        ],
        "tons": {
            "calme":      ["question sur mon {k}", "information sur le {k}", "clarification {k} svp"],
            "urgent":     ["URGENT {k} non reçu fin de mois !!!", "délai dépassé pour mon {k}"],
            "désespéré":  ["toujours pas mon {k} 3ème mois consécutif", "sans {k} impossible de payer mon loyer"],
            "furieux":    ["SCANDALEUX {k} introuvable encore une fois !!!", "inadmissible {k} absent je suis furieux"],
            "ironique":   ["félicitations encore un {k} oublié", "bravo pour le {k} aux abonnés absents"],
        }
    },
}

# ── CAS DE NÉGATION (critiques pour éviter faux positifs médicaux) ─────────────
# Ces phrases contiennent des mots médicaux sous négation → domaine NON-MÉDICAL
NEGATIONS_CRITIQUES = [
    # Médical nié → autre domaine
    ("je n'ai pas de douleur mais mon ordinateur est cassé",        "MATÉRIEL"),
    ("pas de fièvre mais le réseau est en panne",                   "INFRA"),
    ("sans douleur toutefois mon salaire est manquant",             "RH"),
    ("je ne suis pas blessé mais mon compte est bloqué",            "ACCÈS"),
    ("aucune douleur à la poitrine mais je ne reçois plus mes fiches de paie", "RH"),
    ("je ne souffre pas mais le wifi ne marche plus",               "INFRA"),
    ("pas de malaise mais mon badge a expiré",                      "ACCÈS"),
    ("je n'ai pas mal mais l'imprimante fume",                      "MATÉRIEL"),
    ("aucun saignement juste un écran cassé",                       "MATÉRIEL"),
    ("pas d'AVC pas d'infarctus juste un problème de salaire",      "RH"),
    # Furieux + médical nié (le crash-test original)
    ("pas de douleur thoracique mais je suis furieux sans mes fiches de paie", "RH"),
    ("aucune douleur mais la situation est catastrophique réseau down", "INFRA"),
]

# ── GÉNÉRATEUR PRINCIPAL ──────────────────────────────────────────────────────

def generer_master_data_v8():
    print(">>> 🛠️  DÉMARRAGE DE LA FORGE V8 (TONE-VARIED + NÉGATION CRITIQUE)...")
    donnees = []

    # 1. Données tone-varied (600 exemples par ton par domaine)
    NB_PAR_TON = 600
    for domaine, data in TEMPLATES.items():
        mots = data["mots_cles"]
        for ton, phrases in data["tons"].items():
            for _ in range(NB_PAR_TON):
                mot = random.choice(mots)
                template = random.choice(phrases)
                phrase = template.replace("{k}", mot)
                donnees.append((phrase, domaine))

    # 2. Cas de négation (répétés pour que le modèle les mémorise)
    NB_NEGATION = 300
    for phrase, domaine in NEGATIONS_CRITIQUES:
        for _ in range(NB_NEGATION):
            donnees.append((phrase, domaine))

    df = pd.DataFrame(donnees, columns=["details_ticket", "domaine_cible"])
    df = df.sample(frac=1).reset_index(drop=True)

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("tickets", conn, if_exists="replace", index=False)

    total = len(df)
    print(f"✅ Forge V8 terminée : {total} tickets injectés.\n")
    print(df["domaine_cible"].value_counts().to_string())
    return df


if __name__ == "__main__":
    generer_master_data_v8()
