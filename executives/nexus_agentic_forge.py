# executives/nexus_agentic_forge.py
import os
import random
import asyncio
import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from nexus_matrix import DOMAINES, PERSONAS, CONTRAINTES_ENVIRONNEMENT, SCENARIOS

# ==========================================
# 1. INITIALISATION SÉCURISÉE
# ==========================================
load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("❌ ERREUR : La clé GEMINI_API_KEY est introuvable. Vérifie ton fichier .env !")

client = genai.Client()
MODEL_ID = 'gemini-2.5-flash'


# ==========================================
# 2. SCHÉMA STRICT POUR LE JUGE (Anti-Hallucination)
# ==========================================
class EvaluationJuge(BaseModel):
    qualite_score: int = Field(description="Note de 1 à 10 sur le réalisme de la conversation.")
    texte: str = Field(description="La concaténation exacte des paroles de l'appelant uniquement.")
    domaine: str = Field(description="Le domaine PRINCIPAL de l'urgence (ex: POMPIER).")
    domaines_secondaires: list[str] = Field(
        description="Liste des autres domaines impliqués si la situation exige plusieurs services (ex: ['POLICE', 'ÉNERGIE & INFRASTRUCTURES']). Vide si mono-domaine.")
    severite: int = Field(description="Score de 1 à 4 (1=Banal, 4=Critique/Mortel).")
    impact: int = Field(description="Score de 1 à 4 (1=1 personne, 4=Ville entière).")
    cible: int = Field(description="0 (Citoyen), 2 (VIP/Entreprise), ou 4 (Hôpital/Infra vitale).")
    friction: str = Field(
        description="Valeur exacte parmi : MANQUE_LIEU, MANQUE_IDENTIFIANT, MANQUE_SYMPTOMES, MANQUE_MESSAGE_ERREUR, MANQUE_CONTEXTE, COMPLET.")


# ==========================================
# 3. MOTEUR ASYNCHRONE
# ==========================================
async def simuler_conversation(domaine_cible):
    persona = random.choice(PERSONAS)
    contrainte = random.choice(CONTRAINTES_ENVIRONNEMENT)
    scenario = random.choice(SCENARIOS.get(domaine_cible, SCENARIOS["MÉDICAL"]))

    system_appelant = f"""
    Tu es un appelant contactant les urgences ou un support IT.
    Ton problème réel : {scenario}
    Ton profil : {persona['profil']} ({persona['instruction']})
    Ton environnement : {contrainte}

    Règles :
    - Ne donne PAS toutes les informations d'un coup.
    - Fais des phrases courtes, adaptées à ton profil.
    - Attends que l'agent te pose des questions pour donner les détails (lieu, identité, contexte précis).
    - Remplace les vrais noms/adresses par des tags génériques comme <VILLE>, <ADRESSE_1>.
    """

    system_regulateur = f"""
    Tu es un expert du triage pour le domaine : {domaine_cible}.
    Ton but est d'obtenir : La nature exacte du problème, le lieu, et l'identité/codes.

    Règles :
    - Pose UNE SEULE question claire et précise à la fois.
    - Sois professionnel.
    - Si tu as toutes les informations vitales, termine en disant "COMPLET : [Résumé]".
    """

    historique_conversation = []

    # Appel 1 : L'appelant initie
    prompt_initial = f"Génère ta première phrase pour signaler ce problème : {scenario}"
    reponse_appelant = await client.aio.models.generate_content(
        model=MODEL_ID,
        contents=prompt_initial,
        config=types.GenerateContentConfig(system_instruction=system_appelant)
    )
    msg_appelant = reponse_appelant.text.strip()
    historique_conversation.append(f"Appelant: {msg_appelant}")

    conversation_terminee = False
    tours = 0
    max_tours = 4

    # Boucle de dialogue multi-agents (Vrai Asynchrone)
    while not conversation_terminee and tours < max_tours:
        # Tour du Régulateur
        prompt_regulateur = "\n".join(historique_conversation) + "\n\nQue réponds-tu/demandes-tu ?"
        reponse_reg = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt_regulateur,
            config=types.GenerateContentConfig(system_instruction=system_regulateur)
        )
        msg_reg = reponse_reg.text.strip()
        historique_conversation.append(f"Régulateur: {msg_reg}")

        if "COMPLET" in msg_reg:
            break

        # Tour de l'Appelant
        prompt_app = "\n".join(
            historique_conversation) + "\n\nRéponds à la dernière question du régulateur selon ton profil."
        reponse_app = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt_app,
            config=types.GenerateContentConfig(system_instruction=system_appelant)
        )
        msg_appelant = reponse_app.text.strip()
        historique_conversation.append(f"Appelant: {msg_appelant}")
        tours += 1

    texte_final = " ".join(
        [msg.replace("Appelant: ", "") for msg in historique_conversation if msg.startswith("Appelant:")])
    return historique_conversation, texte_final


async def evaluer_et_formatter_juge(historique, texte_appelant_concatene, domaine_initial):
    texte_conversation = "\n".join(historique)
    system_juge = "Tu es un Auditeur Qualité strict. Analyse la conversation et extrais les données selon le schéma JSON imposé. Gère les cas multi-domaines si la situation implique plusieurs services."

    try:
        # Utilisation du Structured Output (Pydantic) pour forcer le schéma
        reponse_juge = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=f"Conversation :\n{texte_conversation}\n\nTexte Appelant concaténé : {texte_appelant_concatene}",
            config=types.GenerateContentConfig(
                system_instruction=system_juge,
                response_mime_type="application/json",
                response_schema=EvaluationJuge,
                temperature=0.1
            )
        )
        # On parse directement le JSON certifié par Gemini
        import json
        return json.loads(reponse_juge.text)
    except Exception as e:
        return None


async def worker_generation(id_worker, nb_conversations, resultats):
    for i in range(nb_conversations):
        domaine = random.choice(DOMAINES)

        historique, texte_concat = await simuler_conversation(domaine)
        validation = await evaluer_et_formatter_juge(historique, texte_concat, domaine)

        if validation and validation.get("qualite_score", 0) >= 8:
            resultats.append(validation)
            print(f"✅ [Worker {id_worker}] Ticket {i + 1}/{nb_conversations} validé ({validation['domaine']}).")
        else:
            print(f"⚠️ [Worker {id_worker}] Ticket {i + 1}/{nb_conversations} rejeté par le Juge.")


async def main():
    print("🚀 Démarrage de la Forge Agentique NEXUS (Mode Asynchrone Strict)...")

    # Paramètres de production (modifiables selon tes besoins)
    NB_WORKERS = 8
    CONVS_PER_WORKER = 5

    resultats_valides = []
    taches = [worker_generation(i, CONVS_PER_WORKER, resultats_valides) for i in range(NB_WORKERS)]
    await asyncio.gather(*taches)

    if resultats_valides:
        df = pd.DataFrame(resultats_valides)
        # Colonnes strictement alignées pour le modèle Kaggle !
        colonnes_export = ['texte', 'domaine', 'severite', 'impact', 'cible', 'friction', 'domaines_secondaires']
        df = df[colonnes_export]

        os.makedirs("../datasets", exist_ok=True)
        path = "../datasets/nexus_agentic_dataset.csv"
        df.to_csv(path, index=False)
        print(f"\n🎯 OPÉRATION TERMINÉE ! {len(df)} tickets prêts pour le Machine Learning -> {path}")
    else:
        print("❌ Échec total. Aucune donnée n'a passé les filtres.")


if __name__ == "__main__":
    asyncio.run(main())