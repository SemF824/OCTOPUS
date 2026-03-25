"""
DATA FORGE V8.1 — Données Synthétiques Tone-Varied + Neuro/Trauma
Correctifs V8.1 :
  • Ajout de termes neurologiques (neurones, picotements, vertiges, migraine)
    et traumatiques (renversé, crâne, fracture) dans le domaine MÉDICAL
  • Cas de négation étendus (negation_guard coverage)
  • Tons "confus" et "atypique" pour entraîner la robustesse aux fautes
"""
import sqlite3
import pandas as pd
import random

DB_PATH = "nexus_bionexus.db"

TEMPLATES = {
    "MATÉRIEL": {
        "mots_cles": [
            "clavier", "souris", "ordinateur", "écran", "imprimante",
            "laptop", "câble USB", "périphérique", "batterie", "dalle"
        ],
        "tons": {
            "calme":       ["{k} ne fonctionne pas", "problème avec le {k}", "mon {k} est en panne"],
            "urgent":      ["URGENT {k} HS réunion dans 10min !!!", "besoin aide immédiate {k} mort", "CATASTROPHE mon {k} a lâché"],
            "désespéré":   ["je vais perdre tout mon travail {k} cassé", "SOS {k} mort impossible de travailler"],
            "sarcastique": ["encore le {k} qui décide de mourir", "bien sûr c'est le {k} qui flanche auj"],
            "technique":   ["défaillance hardware {k} diagnostic requis", "{k} panne intermittente port USB"],
            "confus":      ["je sais pas pourquoi mais {k} marche plus", "quelque chose cloche avec {k} aidez moi"],
        }
    },
    "INFRA": {
        "mots_cles": [
            "wifi", "internet", "réseau", "VPN", "serveur",
            "connexion", "fibre", "routeur", "datacenter", "proxy"
        ],
        "tons": {
            "calme":   ["problème de {k}", "le {k} est instable", "coupure {k} signalée"],
            "urgent":  ["RÉSEAU DOWN URGENT {k}", "plus de {k} réunion client dans 5 min !!!", "panne totale {k} site bloqué"],
            "désespéré": ["sans {k} depuis 2h réunion annulée clients perdus", "je perds des contrats à cause du {k}"],
            "sarcastique": ["le {k} en vacances comme d'habitude", "encore et toujours le {k} qui plante"],
            "technique": ["latence élevée {k} traceroute KO MTU mismatch", "{k} gateway timeout 504 BGP flap"],
            "panique":   ["tout est DOWN {k} plus rien ne répond urgence absolue !!!"],
        }
    },
    "ACCÈS": {
        "mots_cles": [
            "mot de passe", "badge", "session", "compte",
            "authentification", "accès", "token", "certificat"
        ],
        "tons": {
            "calme":   ["réinitialisation {k} requise", "problème de {k}", "bloqué sur {k}"],
            "urgent":  ["BLOQUÉ DEHORS réunion dans 2min {k} expiré !!!!", "impossible accès {k} rendez-vous critique"],
            "désespéré": ["enfermé dehors depuis 1h {k} ne marche plus", "bloqué sans {k} travail paralysé"],
            "sarcastique": ["encore le {k} magique qui refuse de fonctionner", "splendide {k} expiré sans prévenir merci"],
            "technique": ["SSO {k} timeout Kerberos ticket invalide", "{k} LDAP sync failure AD forest"],
        }
    },
    "MÉDICAL": {
        "mots_cles": [
            # Douleur générale
            "douleur", "fièvre", "nausée", "malaise", "blessure",
            "saignement", "brûlure", "vertiges", "choc",
            # NEURO (FIX V8.1) — termes souvent mal classifiés en MATÉRIEL
            "picotements", "picotements dans la tête", "picotements des neurones",
            "maux de tête", "migraine", "céphalées",
            "vertiges soudains", "perte de connaissance",
            "engourdissements", "paralysie partielle",
            "tremblements", "convulsions", "épilepsie",
            # CARDIO étendu
            "douleur à la poitrine", "douleur thoracique", "trou dans le coeur",
            "palpitations", "essoufflement",
            # TRAUMA (FIX V8.1)
            "accident de voiture", "renversé par une voiture",
            "chute grave", "crâne fracturé", "crâne ouvert",
            "traumatisme crânien", "fracture du bras", "fracture de la jambe",
        ],
        "tons": {
            "calme":       ["j'ai des {k}", "petits {k} depuis ce matin", "ressens des {k} légères"],
            "urgent":      ["URGENCE {k} forte !!!", "{k} intense depuis 1h besoin aide"],
            "grave":       ["collègue inconscient après {k}", "victime d'un {k} grave appelez les secours"],
            "panique":     ["je souffre de {k} appelez le 15", "{k} bras gauche douleur irradiante"],
            "descriptif":  ["symptômes de {k} depuis hier pas amélioré", "{k} récurrentes besoin consultation"],
            # Tons atypiques pour robustesse (FIX V8.1)
            "confus":      ["je sais pas c'est quoi mais j'ai des {k}", "truc bizarre des {k} depuis hier"],
            "avec_fautes": ["j'ai des {k} depuis ce matin", "des {k} dans la tete depuis hier"],
        }
    },
    "RH": {
        "mots_cles": [
            "salaire", "congés", "contrat", "mutuelle", "paie",
            "fiche de paie", "entretien", "prime", "arrêt maladie"
        ],
        "tons": {
            "calme":    ["question sur mon {k}", "information sur le {k}", "clarification {k} svp"],
            "urgent":   ["URGENT {k} non reçu fin de mois !!!", "délai dépassé pour mon {k}"],
            "désespéré":["toujours pas mon {k} 3ème mois consécutif", "sans {k} impossible de payer mon loyer"],
            "furieux":  ["SCANDALEUX {k} introuvable encore une fois !!!", "inadmissible {k} absent je suis furieux"],
            "ironique": ["félicitations encore un {k} oublié", "bravo pour le {k} aux abonnés absents"],
        }
    },
}

# ── Cas de négation médicale (anti-faux-positifs) ─────────────────────────────
NEGATIONS_CRITIQUES = [
    ("je n'ai pas de douleur mais mon ordinateur est cassé",                  "MATÉRIEL"),
    ("pas de fièvre mais le réseau est en panne",                             "INFRA"),
    ("sans douleur toutefois mon salaire est manquant",                       "RH"),
    ("je ne suis pas blessé mais mon compte est bloqué",                      "ACCÈS"),
    ("aucune douleur à la poitrine mais je ne reçois plus mes fiches de paie","RH"),
    ("je ne souffre pas mais le wifi ne marche plus",                         "INFRA"),
    ("pas de malaise mais mon badge a expiré",                                "ACCÈS"),
    ("je n'ai pas mal mais l'imprimante fume",                                "MATÉRIEL"),
    ("aucun saignement juste un écran cassé",                                 "MATÉRIEL"),
    ("pas d'AVC pas d'infarctus juste un problème de salaire",                "RH"),
    ("pas de douleur thoracique mais je suis furieux sans mes fiches de paie","RH"),
    ("aucune douleur mais la situation est catastrophique réseau down",        "INFRA"),
    # FIX V8.1 : négations neuro
    ("je n'ai pas de picotements juste un bug réseau",                        "INFRA"),
    ("pas de maux de tête c'est mon clavier qui déconne",                     "MATÉRIEL"),
    ("aucun vertige mais mon accès est bloqué",                               "ACCÈS"),
]


def generer_master_data_v8():
    print(">>> 🛠️  DÉMARRAGE DE LA FORGE V8.1 (NEURO + TRAUMA + NÉGATIONS)...")
    donnees = []

    NB_PAR_TON     = 600
    NB_NEGATION    = 300

    for domaine, data in TEMPLATES.items():
        mots = data["mots_cles"]
        for ton, phrases in data["tons"].items():
            for _ in range(NB_PAR_TON):
                mot      = random.choice(mots)
                template = random.choice(phrases)
                phrase   = template.replace("{k}", mot)
                donnees.append((phrase, domaine))

    for phrase, domaine in NEGATIONS_CRITIQUES:
        for _ in range(NB_NEGATION):
            donnees.append((phrase, domaine))

    df = pd.DataFrame(donnees, columns=["details_ticket", "domaine_cible"])
    df = df.sample(frac=1).reset_index(drop=True)

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("tickets", conn, if_exists="replace", index=False)

    print(f"✅ Forge V8.1 terminée : {len(df)} tickets injectés.\n")
    print(df["domaine_cible"].value_counts().to_string())
    return df


if __name__ == "__main__":
    generer_master_data_v8()
