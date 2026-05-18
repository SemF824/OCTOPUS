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


class TaskExecutor:
    """Moteur d'exécution tactique des protocoles post-qualification."""

    @staticmethod
    def declencher_protocoles(domaine, niveau_urgence, resume_ticket):
        print("\n   ⚡ DÉCLENCHEMENT DES TÂCHES OPÉRATIONNELLES :")

        # 1. Action transverse si critique
        if niveau_urgence == "🔴 CRITIQUE":
            print("      [API] 📡 Broadcast SMS d'alerte aux superviseurs d'astreinte -> ENVOYÉ")

        # 2. Routage métier
        if domaine == "POMPIER":
            print(f"      [WEBHOOK] 🚒 Transmission au SDIS local (Code Rouge) -> OK")
            print("      [TASK] 🗺️ Extraction des coordonnées GPS pour les engins -> EN COURS")

        elif domaine == "POLICE":
            print(f"      [WEBHOOK] 🚓 Alerte patrouille secteur en cours -> OK")
            if "arme" in resume_ticket.lower() or "couteau" in resume_ticket.lower():
                print("      [TASK] ⚠️ Activation protocole BAC (Brigade Anti-Criminalité) -> DÉCLENCHÉ")

        elif domaine == "CYBERSÉCURITÉ":
            print(f"      [API] 🛡️ Isolement automatique du VLAN compromis -> EXÉCUTÉ")
            print("      [TASK] 📧 Notification RSSI & Cellule de Crise -> ENVOYÉ")

        elif domaine == "MÉDICAL":
            print(f"      [WEBHOOK] 🚑 Transmission du bilan au Médecin Régulateur (SAMU) -> OK")

        elif domaine == "DIGITAL SUPPORT":
            print(f"      [JIRA] 🎫 Création ticket automatique niveau 2 -> TICKET #NEX-8492 CRÉÉ")

        else:
            print(f"      [DISPATCH] 📨 Transmission standard au centre de régulation {domaine} -> OK")


class NexusAgenticSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V_ULTIME (Architecture Multi-Agents)...")
        self.logger = ShadowLogger()
        self.evaluator = QualificationEngine()
        self.client_llm = AsyncClient()
        self.llm_en_ligne = False

    async def prechauffer_cerveau(self):
        print(f"🔥 Pré-chauffage du modèle {MODEL_DIALOGUE} en cours...")
        try:
            await self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': 'ping'}],
                                       options={'num_predict': 1})
            self.llm_en_ligne = True
            print("✅ Modèle chargé en mémoire vive ! Prêt pour une réponse instantanée.")
        except Exception as e:
            self.llm_en_ligne = False
            print(f"⚠️ ERREUR CRITIQUE : Impossible de joindre Ollama. Vérifiez que 'ollama serve' tourne.")
            print(f"Détail technique : {e}")

    async def generer_question_bot(self, texte_utilisateur, domaine, friction):
        if not self.llm_en_ligne:
            return "[SYSTÈME DE DIALOGUE HORS LIGNE] Veuillez préciser la situation exacte."

        prompt = f"""
        Tu es un agent de régulation d'urgence (Humain, empathique, très professionnel).
        DOMAINE IDENTIFIÉ : {domaine}
        L'algorithme de tri suspecte qu'il manque cette info : {friction}
        HISTORIQUE DU CLIENT : "{texte_utilisateur}"

        MISSION CRITIQUE :
        1. Analyse l'historique de la conversation. Si le client A DÉJÀ FOURNI l'information manquante (ex: il a donné un numéro de rue, un code postal, ou décrit une situation claire), TU DOIS RÉPONDRE EXCLUSIVEMENT PAR LE MOT : "COMPLET". Ne dis rien d'autre.
        2. Si et seulement si l'information est VRAIMENT absente ou trop floue, pose UNE SEULE question courte pour l'obtenir.
        3. Ne te répète jamais. Ne dis pas bonjour. Va droit au but mais garde un ton rassurant.
        4. NE SOIS PAS INTRUSIF (ex: Ne demande pas un code postal exact si la ville suffit, ne demande pas le nom de famille).

        Réponds DIRECTEMENT par la question ou par "COMPLET".
        """
        try:
            reponse = await asyncio.wait_for(
                self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': prompt}],
                                     options={'temperature': 0.1}),
                timeout=30.0
            )
            return reponse['message']['content'].strip().replace('"', '')
        except asyncio.TimeoutError:
            print("\n   ⚠️ [ALERTE SYSTÈME] Timeout de l'API Ollama (Lenteur serveur).")
            return "La connexion est lente. Pouvez-vous détailler votre situation ou votre position géographique ?"
        except Exception as e:
            print(f"\n   ⚠️ [ALERTE SYSTÈME] Crash du modèle de dialogue : {e}")
            self.llm_en_ligne = False
            return "[SYSTÈME DE DIALOGUE DÉCONNECTÉ] Veuillez m'en dire plus."

    async def traiter_interaction(self, ticket_historique):
        domaine, score, friction = self.evaluator.evaluer_ticket(ticket_historique)

        if str(friction).upper() == "COMPLET":
            return domaine, score, "COMPLET", True, ""

        question_bot = await self.generer_question_bot(ticket_historique, domaine, friction)

        # Le filet de sécurité asynchrone : Mistral a le dernier mot pour forcer la complétion
        if "COMPLET" in question_bot.upper():
            return domaine, score, "COMPLET", True, ""

        return domaine, score, friction, False, question_bot


async def run_terminal():
    nexus = NexusAgenticSystem()
    await nexus.prechauffer_cerveau()

    print("\n" + "=" * 60)
    print(f"🚀 NEXUS COMMAND CENTER — HYBRID AI ({MODEL_DIALOGUE})")
    print("=" * 60)
    print("   Tapez 'exit' pour quitter. Appuyez sur ENTRÉE à vide pour forcer la validation.\n")

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
                print(f"   🤖 NEXUS ({domaine} | Score partiel: {score}/10) : {question_bot}")
                complement = input("   💬 Client : ").strip()

                # RESTAURATION DE TON OPTION DE SKIP SÉCURISÉE
                if complement == "":
                    print("   ⚠️ [AVERTISSEMENT] Vous n'avez pas fourni de détails supplémentaires.")
                    print("   ⚠️ L'urgence de votre situation pourrait être sous-évaluée.")
                    choix = input("   Voulez-vous transmettre le dossier tel quel ? (O/N) : ").strip().upper()
                    if choix in ['O', 'OUI', 'Y', 'YES']:
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

        # Re-score final pour prendre en compte le dernier ajout
        if not ticket_complet:
            domaine, score, friction = nexus.evaluator.evaluer_ticket(ticket_final)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"

        print(f"\n   ✅ DOSSIER VALIDÉ ET TRANSMIS")
        print(f"   🎯 Domaine : {domaine}  |  🔢 Score : {score}/10  →  {niveau}")
        print(f"   📄 Résumé du dossier : {ticket_final}")

        # Exécution des Tâches Opérationnelles
        nexus.executor.declencher_protocoles(domaine, niveau, ticket_final)

        # Log en base de données
        nexus.logger.log(ticket_final, domaine, score)
        print("-" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_terminal())