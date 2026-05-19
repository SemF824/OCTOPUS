# executives/main.py
import asyncio
import sqlite3
import datetime
import warnings
from ollama import AsyncClient

from nexus_config import DB_PATH, MODEL_DIALOGUE
from nexus_qualification import QualificationEngine
from nexus_matrix import DOMAINES  # On importe la liste officielle des services

warnings.filterwarnings("ignore")


class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS interactions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date_log TEXT, ticket_complet TEXT,
            domaine_principal TEXT, domaines_secondaires TEXT, score REAL)''')
        self.conn.commit()

    def log(self, ticket_final, domaine_principal, sec_list, score):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sec_str = ", ".join(sec_list) if sec_list else "AUCUN"
        self.cursor.execute('''INSERT INTO interactions_log (date_log, ticket_complet, domaine_principal, domaines_secondaires, score)
            VALUES (?, ?, ?, ?, ?)''', (date_now, ticket_final, domaine_principal, sec_str, score))
        self.conn.commit()


class TaskExecutor:
    """Moteur d'exécution tactique des protocoles post-qualification."""

    @staticmethod
    def declencher_protocoles(domaines_impliques, niveau_urgence, resume_ticket):
        print("\n   ⚡ DÉCLENCHEMENT DES TÂCHES OPÉRATIONNELLES (MULTI-SERVICES) :")

        # 1. Action transverse si critique
        if niveau_urgence == "🔴 CRITIQUE":
            print("      [API] 📡 Broadcast SMS d'alerte aux superviseurs d'astreinte -> ENVOYÉ")

        # 2. Routage métier dynamique pour CHAQUE domaine identifié
        for domaine in domaines_impliques:
            print(f"\n      --- Unité : {domaine} ---")
            if domaine == "POMPIER":
                print(f"      [WEBHOOK] 🚒 Transmission au SDIS local -> OK")
                print("      [TASK] 🗺️ Extraction des coordonnées GPS pour les engins -> EN COURS")

            elif domaine == "POLICE":
                print(f"      [WEBHOOK] 🚓 Alerte patrouille secteur en cours -> OK")
                if "arme" in resume_ticket.lower() or "couteau" in resume_ticket.lower():
                    print("      [TASK] ⚠️ Activation protocole BAC (Brigade Anti-Criminalité) -> DÉCLENCHÉ")

            elif domaine == "CYBERSÉCURITÉ":
                print(f"      [API] 🛡️ Isolement automatique du VLAN compromis -> EXÉCUTÉ")

            elif domaine == "ÉNERGIE & INFRASTRUCTURES":
                print(f"      [WEBHOOK] ⚡ Alerte ERDF/RTE pour coupure préventive réseau -> OK")

            elif domaine == "MÉDICAL":
                print(f"      [WEBHOOK] 🚑 Transmission du bilan au Médecin Régulateur (SAMU) -> OK")

            elif domaine == "DIGITAL SUPPORT":
                print(f"      [JIRA] 🎫 Création ticket automatique niveau 2 -> CRÉÉ")

            elif domaine == "NON_URGENT":
                print(f"      [DISPATCH] 🗑️ Rejet du ticket (Faux Numéro / Troll) -> ARCHIVÉ")

            else:
                print(f"      [DISPATCH] 📨 Transmission standard au centre {domaine} -> OK")


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
            print("✅ Modèle chargé ! Prêt pour le multithreading.")
        except Exception as e:
            self.llm_en_ligne = False
            print(f"⚠️ ERREUR CRITIQUE : Impossible de joindre Ollama.")

    async def generer_question_bot(self, texte_utilisateur, domaine, friction):
        if not self.llm_en_ligne:
            return "[SYSTÈME HORS LIGNE] Veuillez préciser la situation."

        prompt = f"""
        Tu es un agent de régulation d'urgence (Humain, empathique, très professionnel).
        DOMAINE IDENTIFIÉ : {domaine}
        INFO MANQUANTE SUSPECTÉE : {friction}
        HISTORIQUE : "{texte_utilisateur}"

        MISSION :
        1. Si le client A DÉJÀ FOURNI l'info manquante, réponds UNIQUEMENT le mot : "COMPLET".
        2. Sinon, pose UNE SEULE question courte, directe et ciblée. Ne dis pas bonjour.
        """
        try:
            reponse = await asyncio.wait_for(
                self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': prompt}],
                                     options={'temperature': 0.1}), timeout=15.0)
            return reponse['message']['content'].strip().replace('"', '')
        except Exception:
            return "Pouvez-vous m'en dire plus ?"

    async def extraire_domaines_secondaires(self, texte_utilisateur, domaine_principal):
        """Demande à Mistral d'analyser le besoin de renforts transverses."""
        if not self.llm_en_ligne or domaine_principal == "NON_URGENT":
            return []

        prompt = f"""
        Analyse cette urgence : "{texte_utilisateur}"
        Le service principal assigné est : {domaine_principal}.

        Cette situation nécessite-t-elle l'intervention d'AUTRES services en renfort (pour sécuriser le périmètre, soigner, ou réparer des dégâts annexes) ?

        Choisis EXCLUSIVEMENT parmi cette liste : {", ".join(DOMAINES)}.

        RÈGLES :
        - Ne réponds PAS le service principal ({domaine_principal}).
        - Si aucun autre service n'est nécessaire, réponds EXACTEMENT : "AUCUN".
        - Si plusieurs, sépare-les par des virgules (ex: POLICE, MÉDICAL).
        - NE FAIS AUCUNE PHRASE. JUSTE LES MOTS-CLÉS.
        """
        try:
            reponse = await asyncio.wait_for(
                self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': prompt}],
                                     options={'temperature': 0.0}), timeout=10.0)

            resultat_brut = reponse['message']['content'].strip().upper()
            if "AUCUN" in resultat_brut:
                return []

            # Nettoyage et extraction stricte
            domaines_trouves = [d.strip() for d in resultat_brut.split(',') if
                                d.strip() in DOMAINES and d.strip() != domaine_principal]
            return list(set(domaines_trouves))
        except Exception:
            return []

    async def traiter_interaction(self, ticket_historique):
        domaine, score, friction = self.evaluator.evaluer_ticket(ticket_historique)
        if str(friction).upper() == "COMPLET":
            return domaine, score, "COMPLET", True, ""
        question_bot = await self.generer_question_bot(ticket_historique, domaine, friction)
        if "COMPLET" in question_bot.upper():
            return domaine, score, "COMPLET", True, ""
        return domaine, score, friction, False, question_bot


async def run_terminal():
    nexus = NexusAgenticSystem()
    await nexus.prechauffer_cerveau()

    print("\n" + "=" * 60)
    print(f"🚀 NEXUS COMMAND CENTER — HYBRID AI MULTI-SERVICES ({MODEL_DIALOGUE})")
    print("=" * 60)
    print("   Tapez 'exit' pour quitter.\\n")

    while True:
        raw = input("📝 Appelant : ").strip()
        if raw.lower() in {"exit", "q", "quit"}: break
        if not raw: continue

        ticket_final = raw
        ticket_complet = False
        tentatives = 0

        while not ticket_complet and tentatives < 3:
            domaine, score, friction, ticket_complet, question_bot = await nexus.traiter_interaction(ticket_final)

            if not ticket_complet:
                print(f"   🤖 NEXUS ({domaine} | Score partiel: {score}/10) : {question_bot}")
                complement = input("   💬 Appelant : ").strip()

                if complement == "":
                    choix = input("   ⚠️ Détails manquants. Transmettre tel quel ? (O/N) : ").strip().upper()
                    if choix in ['O', 'OUI', 'Y']:
                        break
                    else:
                        continue

                if complement.lower() in {"exit", "q", "quit"}:
                    ticket_final = "exit"
                    break

                ticket_final += " " + complement
                tentatives += 1

        if ticket_final == "exit": break

        # Évaluation finale du domaine primaire
        if not ticket_complet:
            domaine, score, friction = nexus.evaluator.evaluer_ticket(ticket_final)

        niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"

        print(f"\n   ✅ DOSSIER VALIDÉ")
        print(f"   🎯 Primaire : {domaine}  |  🔢 Score : {score}/10  →  {niveau}")

        # --- L'ANALYSE MULTI-SERVICES DE MISTRAL ---
        print("   🔍 Analyse des renforts tactiques en cours...")
        domaines_secondaires = await nexus.extraire_domaines_secondaires(ticket_final, domaine)

        if domaines_secondaires:
            print(f"   🚨 Renforts requis identifiés : {', '.join(domaines_secondaires)}")
        else:
            print("   🛡️ Incident isolé. Aucun renfort croisé requis.")

        # Consolidation des domaines pour l'exécution
        domaines_impliques = [domaine] + domaines_secondaires

        print(f"   📄 Résumé du dossier : {ticket_final}")

        # Exécution en boucle sur TOUS les services identifiés
        nexus.executor.declencher_protocoles(domaines_impliques, niveau, ticket_final)

        # Log de l'intégralité des opérations
        nexus.logger.log(ticket_final, domaine, domaines_secondaires, score)
        print("-" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_terminal())