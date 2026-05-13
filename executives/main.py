# executives/main.py
import asyncio
import sqlite3
import datetime
import warnings
from ollama import AsyncClient

from nexus_config import DB_PATH, MODEL_DIALOGUE
from nexus_qualification import QualificationEngine

warnings.filterwarnings("ignore")


class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS interactions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date_log TEXT, ticket_complet TEXT,
            domaine TEXT, score REAL)''')
        self.conn.commit()

    def log(self, ticket_final, domaine, score):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''INSERT INTO interactions_log (date_log, ticket_complet, domaine, score)
            VALUES (?, ?, ?, ?)''', (date_now, ticket_final, domaine, score))
        self.conn.commit()


class NexusAgenticSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V_ULTIME (Architecture Multi-Agents)...")
        self.logger = ShadowLogger()
        self.evaluator = QualificationEngine()  # Le cerveau ML (Rapide)
        self.client_llm = AsyncClient()  # Le cerveau LLM (Empathique)

    async def generer_question_bot(self, texte_utilisateur, domaine, friction):
        """ Fait appel à Llama-3.1 pour générer une question fluide et contextuelle """
        prompt = f"""
        Tu es l'agent de triage du système d'urgence Nexus.
        DOMAINE : {domaine}
        INFORMATION MANQUANTE : {friction}
        MESSAGE DU CLIENT : "{texte_utilisateur}"

        MISSION : Pose UNE SEULE question polie, courte et empathique pour obtenir l'information manquante.
        Réponds DIRECTEMENT par la question, sans aucun autre texte ni introduction.
        """
        try:
            reponse = await self.client_llm.chat(
                model=MODEL_DIALOGUE,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.6}
            )
            return reponse['message']['content'].strip().replace('"', '')
        except Exception as e:
            return "Pouvez-vous me donner plus de précisions sur ce point ?"

    async def traiter_interaction(self, ticket_historique):
        # 1. Évaluation instantanée par le modèle Scikit-Learn
        domaine, score, friction = self.evaluator.evaluer_ticket(ticket_historique)

        # 2. Si le ticket est complet, on valide
        if str(friction).upper() == "COMPLET":
            return domaine, score, friction, True, ""

        # 3. Sinon, on demande à Llama-3.1 de formuler la question
        question_bot = await self.generer_question_bot(ticket_historique, domaine, friction)
        return domaine, score, friction, False, question_bot


async def run_terminal():
    nexus = NexusAgenticSystem()
    print("\n" + "=" * 52)
    print("🚀 NEXUS COMMAND CENTER — HYBRID AI (ML + LLM)")
    print("=" * 52)
    print("   Tapez 'exit' ou 'q' pour quitter.\n")

    while True:
        raw = input("📝 Client : ").strip()
        if not raw or raw.lower() in {"exit", "q", "quit"}: break

        ticket_final = raw
        ticket_complet = False
        tentatives = 0

        while not ticket_complet and tentatives < 5:
            # On traite le texte
            domaine, score, friction, ticket_complet, question_bot = await nexus.traiter_interaction(ticket_final)

            if not ticket_complet:
                print(f"   🤖 NEXUS ({domaine} | Score partiel: {score}/10) : {question_bot}")
                complement = input("   💬 Client : ").strip()
                if complement.lower() in {"exit", "q", "quit"}:
                    ticket_final = "exit"
                    break

                # On concatène l'historique
                ticket_final = ticket_final + ". " + complement
                tentatives += 1

        if ticket_final.lower() in {"exit", "q", "quit"}: break

        # Validation finale
        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"
        print(f"\n   ✅ DOSSIER VALIDÉ ET TRANSMIS")
        print(f"   🎯 Domaine : {domaine}  |  🔢 Score : {score}/10  →  {niveau}")
        print(f"   📄 Résumé du dossier : {ticket_final}\n")

        # Log dans la base de données
        nexus.logger.log(ticket_final, domaine, score)


if __name__ == "__main__":
    # Lancement de la boucle asynchrone (nécessaire pour Ollama)
    asyncio.run(run_terminal())