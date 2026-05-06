# executives/nexus_agentic_forge.py
import os
import random
import asyncio
import pandas as pd
from google import genai
from google.genai import types
from nexus_matrix import DOMAINES, PERSONAS, CONTRAINTES_ENVIRONNEMENT, SCENARIOS

from dotenv import load_dotenv  # <-- 1. NOUVEL IMPORT

from nexus_matrix import DOMAINES, PERSONAS, CONTRAINTES_ENVIRONNEMENT, SCENARIOS

# <-- 2. CHARGEMENT DU FICHIER .env
load_dotenv()

# Petite vérification de sécurité pour être sûr que le .env a bien été lu
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("❌ ERREUR : La clé GEMINI_API_KEY est introuvable. Vérifie ton fichier .env !")

# <-- 3. INITIALISATION DU CLIENT (Il trouve la clé tout seul maintenant !)
client = genai.Client()
MODEL_ID = 'gemini-2.5-flash'  # Parfait pour le volume, rapide et intelligent

async def simuler_conversation(domaine_cible):
    """
    Simule une conversation complète entre l'Appelant et le Régulateur.
    """
    # 1. PIOCHE ALÉATOIRE DANS LA MATRICE
    persona = random.choice(PERSONAS)
    contrainte = random.choice(CONTRAINTES_ENVIRONNEMENT)
    scenario = random.choice(SCENARIOS.get(domaine_cible, SCENARIOS["MÉDICAL"]))

    # 2. INITIALISATION DES AGENTS (Prompts Système)
    system_appelant = f"""
    Tu es un appelant contactant les urgences ou un support IT.
    Ton problème réel : {scenario}
    Ton profil : {persona['profil']} ({persona['instruction']})
    Ton environnement : {contrainte}

    Règles :
    - Ne donne PAS toutes les informations d'un coup.
    - Fais des phrases courtes, adaptées à ton profil.
    - Attends que l'agent te pose des questions pour donner les détails (lieu, identité, contexte précis).
    - Remplace les vrais noms, adresses ou téléphones par des tags génériques comme <VILLE>, <ADRESSE_1>, <TEL_X>.
    """

    system_regulateur = f"""
    Tu es un expert du triage pour le domaine : {domaine_cible}.
    Ton but est d'obtenir : La nature exacte du problème, les symptômes/codes d'erreur, le lieu, et l'identité.

    Règles :
    - Pose UNE SEULE question claire et précise à la fois.
    - Sois professionnel, concis, et applique les protocoles de ton domaine.
    - Si tu as toutes les informations vitales, termine la conversation en disant "COMPLET : [Résumé de l'action]".
    """

    historique_conversation = []

    # Premier message : l'appelant lance l'alerte (il génère la phrase sans contexte préalable)
    prompt_initial = f"Génère ta première phrase pour signaler ce problème : {scenario}"
    reponse_appelant = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt_initial,
        config=types.GenerateContentConfig(system_instruction=system_appelant)
    )
    msg_appelant = reponse_appelant.text.strip()
    historique_conversation.append(f"Appelant: {msg_appelant}")

    conversation_terminee = False
    tours = 0
    max_tours = 5

    # 3. BOUCLE DE DIALOGUE (Multi-Agent Debate)
    while not conversation_terminee and tours < max_tours:
        # --- Tour du Régulateur ---
        prompt_regulateur = "\n".join(historique_conversation) + "\n\nQue réponds-tu/demandes-tu ?"
        reponse_reg = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt_regulateur,
            config=types.GenerateContentConfig(system_instruction=system_regulateur)
        )
        msg_reg = reponse_reg.text.strip()
        historique_conversation.append(f"Régulateur: {msg_reg}")

        if "COMPLET" in msg_reg:
            break

        # --- Tour de l'Appelant ---
        prompt_app = "\n".join(
            historique_conversation) + "\n\nRéponds à la dernière question du régulateur selon ton profil."
        reponse_app = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt_app,
            config=types.GenerateContentConfig(system_instruction=system_appelant)
        )
        msg_appelant = reponse_app.text.strip()
        historique_conversation.append(f"Appelant: {msg_appelant}")

        tours += 1

    texte_final = " ".join([msg for msg in historique_conversation if msg.startswith("Appelant:")])
    texte_final = texte_final.replace("Appelant: ", "")

    return historique_conversation, texte_final


def evaluer_et_formatter_juge(historique, texte_appelant_concatene, domaine):
    """
    Le LLM-as-a-Judge évalue la conversation et formate le JSON pour notre dataset.
    """
    texte_conversation = "\n".join(historique)

    system_juge = """
    Tu es un Auditeur Qualité strict. Tu dois analyser la conversation fournie.
    Extrais l'évolution du triage pour le mettre au format JSON.

    Format attendu (STRICTEMENT CE JSON, RIEN D'AUTRE) :
    {
        "qualite_score": 9,
        "texte_historique": "la concaténation des paroles de l'appelant",
        "impact": 4,
        "urgence": 4,
        "domaine": "MÉDICAL",
        "statut_friction_final": "COMPLET"
    }
    Note : Si la conversation n'a pas atteint son but, statut = MANQUE_LIEU, MANQUE_ARME, etc.
    """

    try:
        reponse_juge = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Conversation à analyser :\n{texte_conversation}\n\nTexte Appelant concaténé : {texte_appelant_concatene}\nDomaine visé : {domaine}",
            config=types.GenerateContentConfig(
                system_instruction=system_juge,
                response_mime_type="application/json"
            )
        )
        # Gemini renvoie un JSON propre grâce à response_mime_type
        import json
        resultat = json.loads(reponse_juge.text)
        return resultat
    except Exception as e:
        print(f"Erreur du juge : {e}")
        return None


async def worker_generation(id_worker, nb_conversations, resultats):
    """Un worker asynchrone pour générer en parallèle."""
    for i in range(nb_conversations):
        domaine = random.choice(DOMAINES)
        print(f"Worker {id_worker} | Génération {i + 1}/{nb_conversations} | Domaine: {domaine}...")

        # Phase 2 : Dialogue
        historique, texte_concat = await simuler_conversation(domaine)

        # Phase 3 : Jugement et Extraction
        validation = evaluer_et_formatter_juge(historique, texte_concat, domaine)

        if validation and validation.get("qualite_score", 0) >= 8:
            resultats.append(validation)
        else:
            print(f"Worker {id_worker} | Rejeté par le Juge (score trop bas ou erreur).")


async def main():
    print("🚀 Démarrage de la Forge Agentique NEXUS...")

    # PARAMÈTRES POUR LE PASSAGE À L'ÉCHELLE
    NB_WORKERS = 5  # Nombre de discussions en simultané
    CONVS_PER_WORKER = 2  # Augmente ceci (ex: 1000) pour générer massivement

    resultats_valides = []

    # Création des tâches asynchrones
    taches = [worker_generation(i, CONVS_PER_WORKER, resultats_valides) for i in range(NB_WORKERS)]
    await asyncio.gather(*taches)

    # Phase 5 : Exportation
    if resultats_valides:
        df = pd.DataFrame(resultats_valides)
        # On ne garde que les colonnes utiles pour ton .pkl
        df = df[['texte_historique', 'domaine', 'impact', 'urgence', 'statut_friction_final']]
        df.to_csv("../datasets/nexus_agentic_dataset.csv", index=False)
        print(f"✅ Terminé ! {len(df)} conversations expertes générées et validées.")
    else:
        print("❌ Aucune conversation n'a passé les critères du Juge.")


if __name__ == "__main__":
    asyncio.run(main())