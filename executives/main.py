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
        self.evaluator = QualificationEngine()
        self.client_llm = AsyncClient()

    async def prechauffer_cerveau(self):
        print(f"🔥 Pré-chauffage du modèle {MODEL_DIALOGUE} en cours...")
        try:
            await self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': 'ping'}],
                                       options={'num_predict': 1})
            print("✅ Modèle chargé en mémoire vive ! Prêt pour une réponse instantanée.")
        except Exception as e:
            print(f"⚠️ Impossible de pré-chauffer le modèle. Erreur: {e}")

    async def generer_question_bot(self, texte_utilisateur, domaine, friction):
        prompt = f"""
        Tu es un agent de triage d'urgence (Humain, empathique, très professionnel).
        DOMAINE IDENTIFIÉ : {domaine}
        INFORMATION MANQUANTE : {friction}
        HISTORIQUE DU CLIENT : "{texte_utilisateur}"

        RÈGLES STRICTES :
        1. Pose UNE SEULE question courte pour obtenir l'information manquante (ex: Demande l'adresse si c'est MANQUE_LIEU).
        2. NE SOIS PAS INTRUSIF.
        3. Ne te répète pas.
        4. Va droit au but sans dire bonjour.

        Réponds DIRECTEMENT par la question.
        """
        try:
            reponse = await asyncio.wait_for(
                self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': prompt}],
                                     options={'temperature': 0.4}),
                timeout=30.0
            )
            return reponse['message']['content'].strip().replace('"', '')
        except:
            return "Pouvez-vous me donner plus de précisions, notamment sur le lieu ou la situation ?"

    async def traiter_interaction(self, ticket_historique):
        domaine, score, friction = self.evaluator.evaluer_ticket(ticket_historique)
        if str(friction).upper() == "COMPLET":
            return domaine, score, friction, True, ""
        question_bot = await self.generer_question_bot(ticket_historique, domaine, friction)
        return domaine, score, friction, False, question_bot


async def run_terminal():
    nexus = NexusAgenticSystem()
    await nexus.prechauffer_cerveau()

    print("\n" + "=" * 52)
    print(f"🚀 NEXUS COMMAND CENTER — HYBRID AI ({MODEL_DIALOGUE})")
    print("=" * 52)
    print("   Tapez 'exit' pour quitter. Appuyez sur ENTRÉE à vide pour passer une question.\n")

    while True:
        raw = input("📝 Client : ").strip()
        if raw.lower() in {"exit", "q", "quit"}: break
        if not raw: continue

        ticket_final = raw
        ticket_complet = False
        tentatives = 0

        while not ticket_complet and tentatives < 3:
            domaine, score, friction, ticket_complet, question_bot = await nexus.traiter_interaction(ticket_final)

            if not ticket_complet:
                print(f"   🤖 NEXUS ({domaine} | Score: {score}/10) : {question_bot}")
                complement = input("   💬 Client : ").strip()

                # OPTION DE SKIP (Entrée à vide)
                if complement == "":
                    print(
                        "   ⚠️ [AVERTISSEMENT] Sans plus de détails, l'urgence de votre situation pourrait être sous-évaluée.")
                    choix = input("   Voulez-vous transmettre le dossier tel quel ? (O/N) : ").strip().upper()
                    if choix in ['O', 'OUI']:
                        print("   ⏩ Transmission forcée...")
                        break
                    else:
                        print("   ↩️ Retour à la question.")
                        continue

                if complement.lower() in {"exit", "q", "quit"}:
                    ticket_final = "exit"
                    break

                ticket_final += " " + complement
                tentatives += 1

        if ticket_final == "exit": break

        if not ticket_complet:
            domaine, score, friction = nexus.evaluator.evaluer_ticket(ticket_final)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"
        print(f"\n   ✅ DOSSIER VALIDÉ ET TRANSMIS")
        print(f"   🎯 Domaine : {domaine}  |  🔢 Score : {score}/10  →  {niveau}")
        print(f"   📄 Résumé du dossier : {ticket_final}\n")

        nexus.logger.log(ticket_final, domaine, score)


if __name__ == "__main__":
    asyncio.run(run_terminal())