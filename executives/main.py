#main.py
import textwrap
import asyncio
import sqlite3
import datetime
import warnings
import sys
import re
from ollama import AsyncClient

from nexus_config import DB_PATH, MODEL_DIALOGUE
from nexus_qualification import QualificationEngine
from nexus_matrix import DOMAINES

warnings.filterwarnings("ignore")


# =====================================================================
# MODULE 1 : BASE DE DONNÉES & LOGGING
# =====================================================================
class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS interactions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date_log TEXT, ticket_complet TEXT,
            domaine_principal TEXT, domaines_secondaires TEXT, score REAL, statut TEXT)''')
        self.conn.commit()

    def log(self, ticket_final, domaine_principal, sec_list, score, statut="CLOS"):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sec_str = ", ".join(sec_list) if sec_list else "AUCUN"
        try:
            self.cursor.execute('''INSERT INTO interactions_log (date_log, ticket_complet, domaine_principal, domaines_secondaires, score, statut)
                VALUES (?, ?, ?, ?, ?, ?)''', (date_now, ticket_final, domaine_principal, sec_str, score, statut))
            self.conn.commit()
        except sqlite3.OperationalError:
            self.cursor.execute('DROP TABLE IF EXISTS interactions_log')
            self.cursor.execute('''CREATE TABLE interactions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, date_log TEXT, ticket_complet TEXT,
                domaine_principal TEXT, domaines_secondaires TEXT, score REAL, statut TEXT)''')
            self.cursor.execute('''INSERT INTO interactions_log (date_log, ticket_complet, domaine_principal, domaines_secondaires, score, statut)
                VALUES (?, ?, ?, ?, ?, ?)''', (date_now, ticket_final, domaine_principal, sec_str, score, statut))
            self.conn.commit()


# =====================================================================
# MODULE 2 : EXÉCUTION TACTIQUE
# =====================================================================
class TaskExecutor:
    @staticmethod
    def declencher_protocoles(domaines_impliques, niveau_urgence, resume_ticket, motif_cloture="STANDARD"):
        print("\n   ⚡ DÉCLENCHEMENT DES TÂCHES OPÉRATIONNELLES (MULTI-SERVICES) :")

        if motif_cloture == "SILENCE_CRITIQUE":
            print("      [ALERTE] 🚨 RUPTURE DE LIAISON DÉTECTÉE - PROTOCOLE D'URGENCE ABSOLUE ACTIVÉ")
        elif motif_cloture == "CRI_DETECTE":
            print("      [ALERTE] 🚨 PANIQUE ACOUSTIQUE DÉTECTÉE - INTERVENTION MAXIMUM IMMÉDIATE")

        if niveau_urgence == "🔴 CRITIQUE":
            print("      [API] 📡 Broadcast SMS d'alerte aux superviseurs d'astreinte -> ENVOYÉ")

        for domaine in domaines_impliques:
            print(f"\n      --- Unité En Alerte : {domaine} ---")
            if domaine == "POMPIER":
                print("      [WEBHOOK] 🚒 Transmission au SDIS local (Code Rouge) -> OK")
                print("      [TASK] 🗺️ Extraction des coordonnées GPS pour les engins -> EN COURS")
            elif domaine == "POLICE":
                print("      [WEBHOOK] 🚓 Alerte patrouille secteur en cours (Sécurisation) -> OK")
            elif domaine == "ÉNERGIE & INFRASTRUCTURES" or domaine == "CYBERSÉCURITÉ":
                print("      [WEBHOOK] ⚡ Alerte Cellule de Crise Infrastructure -> OK")
            elif domaine == "MÉDICAL":
                print("      [WEBHOOK] 🚑 Transmission du bilan au SAMU (Régulation 15) -> OK")
            elif domaine == "EN_ATTENTE":
                print("      [DISPATCH] 🗑️ Appel fantôme / Erreur de ligne -> ARCHIVÉ SANS SUITE")
            else:
                print(f"      [DISPATCH] 📨 Transmission standard au centre {domaine} -> OK")


# =====================================================================
# MODULE 3 : MOTEUR COGNITIF & TEMPOREL
# =====================================================================
class NexusAgenticSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V_ULTIME (Architecture Temps Réel)...")
        self.logger = ShadowLogger()
        self.evaluator = QualificationEngine()
        self.client_llm = AsyncClient()
        self.executor = TaskExecutor()
        self.llm_en_ligne = False

    async def prechauffer_cerveau(self):
        print(f"🔥 Pré-chauffage du modèle {MODEL_DIALOGUE} en cours...")
        try:
            await self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': 'ping'}],
                                       options={'num_predict': 1})
            self.llm_en_ligne = True
            print("✅ Système paré. Écoute asynchrone activée.")
        except Exception as e:
            self.llm_en_ligne = False
            print(f"⚠️ ERREUR CRITIQUE : Impossible de joindre Ollama. {e}")

    def est_salutation_basique(self, texte):
        t_clean = texte.strip().lower()
        t_clean = re.sub(r'[^\w\s]', '', t_clean)
        return t_clean in ["bonjour", "salut", "allo", "allô", "bonsoir", "oui", "non", "ok"]

    def detecter_choc_acoustique(self, texte):
        t = texte.upper()
        mots_chocs = ["AU SECOURS", "AIDEZ-MOI", "ÇA EXPLOSE", "AU FEU", "JE MEURS", "AAAA", "VITE VITE"]
        if any(mot in t for mot in mots_chocs):
            return True
        if len(t) > 5 and sum(1 for c in texte if c.isupper()) / len(texte) > 0.6:
            return True
        return False

    def verifier_presence_localisation(self, texte):
        t = texte.lower()
        indicateurs_forts = ["gare", "aéroport", "hôpital", "clinique", "mairie", "préfecture"]
        if any(ind in t for ind in indicateurs_forts): return True

        voirie = r'\b(rue|avenue|boulevard|impasse|allée|chemin|route|place|square|pont)\b'
        if re.search(voirie, t): return True

        if re.search(r'\b\d{5}\b', t): return True

        return False

    async def generer_question_bot(self, transcript, texte_utilisateur, domaine, score_actuel):
        if self.est_salutation_basique(texte_utilisateur):
            return "EN_COURS", "Ici les urgences. Quel est votre problème et où vous trouvez-vous ?"

        if not self.llm_en_ligne:
            return "EN_COURS", "Décrivez votre urgence et votre adresse."

        # LE CERVEAU RECALIBRÉ : Few-Shot + Style Militaire + Exigence d'Accès
        prompt = f"""Rôle : Régulateur des urgences (SAMU/112). Ton ton est MILITAIRE, SEC et DIRECT.
Domaine : {domaine}

TRANSCRIPTION DE L'APPEL :
{transcript}

MISSION : Le dossier est validé uniquement si les 3 informations suivantes sont obtenues :
1. LE DANGER : Nature de l'urgence (symptôme, blessure).
2. LA RUE / LE LIEU : Rue, avenue, ou repère majeur (Gare).
3. L'ACCÈS EXACT : Étage, appartement, digicode (ou précision si lieu public).

INSTRUCTIONS STRICTES :
- AUCUNE POLITESSE. N'utilise JAMAIS "Monsieur", "Veuillez", "Pour nous aider".
- Phrase de 15 mots maximum. Va à l'essentiel.
- Si le client a donné la rue (ex: 19 place de Serbie) MAIS pas l'étage/code, EXIGE l'accès direct.
- Si les 3 éléments (Danger + Rue + Accès) sont validés, écris UNIQUEMENT la balise : ###CLOS###

EXEMPLES DE COMPORTEMENT ATTENDU :
Client : "J'ai mal au coeur, je suis au 12 rue de Paris."
Ta réponse : Êtes-vous en maison ou appartement ? Quel étage et quel code ?

Client : "Au 3ème étage, code 1234."
Ta réponse : ###CLOS###

Génère uniquement ta réplique parlée ou ###CLOS### :"""

        try:
            # Rallongement du timeout à 25 secondes pour éviter le crash sur les longs transcripts
            reponse = await asyncio.wait_for(
                self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': prompt}],
                                     options={'temperature': 0.15}),
                timeout=25.0
            )
            contenu = reponse['message']['content'].strip()

            if "###CLOS###" in contenu:
                if domaine in ["MÉDICAL", "POLICE", "POMPIER"]:
                    if not self.verifier_presence_localisation(texte_utilisateur):
                        return "EN_COURS", "Donnez-moi un nom de rue ou un repère physique clair pour l'ambulance."
                return "COMPLET", ""

            contenu = contenu.replace("###CLOS###", "").strip()
            contenu = re.sub(r'^(Régulateur\s*:|Ta réponse\s*:|Réponse\s*:|:\s*|"\s*)', '', contenu, flags=re.IGNORECASE).strip('" ')
            contenu = re.sub(r'\(.*?\)', '', contenu).strip()

            return "EN_COURS", contenu

        except asyncio.TimeoutError:
            print("\n   [SYSTEM WARN] ⚠️ Timeout du LLM (Temps de réponse > 25s).")
            return "EN_COURS", "Liaison instable. Répétez votre position et la situation."
        except Exception as e:
            print(f"\n   [SYSTEM ERROR] ⚠️ Crash LLM : {e}")
            return "EN_COURS", "Liaison instable. Répétez votre position et la situation."

    async def extraire_domaines_secondaires(self, texte_utilisateur, domaine_principal):
        if not self.llm_en_ligne or domaine_principal in ["NON_URGENT", "EN_ATTENTE"]: return []
        prompt = f"Analyse : '{texte_utilisateur}'. Principal : {domaine_principal}. Besoins de renforts ? Choix : {', '.join(DOMAINES)}. Règles : Pas le principal. Si rien : AUCUN. Si plusieurs, sépare par virgules. Aucun autre texte."
        try:
            reponse = await asyncio.wait_for(
                self.client_llm.chat(model=MODEL_DIALOGUE, messages=[{'role': 'user', 'content': prompt}],
                                     options={'temperature': 0.0}), timeout=10.0)
            res = reponse['message']['content'].strip().upper()
            return [] if "AUCUN" in res else list(
                set([d.strip() for d in res.split(',') if d.strip() in DOMAINES and d.strip() != domaine_principal]))
        except Exception:
            return []


# =====================================================================
# SOUS-ROUTINE ASYNCHRONE OPTIMISÉE (UNIX/MAC)
# =====================================================================
async def async_input(prompt: str, timeout: float):
    loop = asyncio.get_event_loop()
    print(prompt, end="", flush=True)

    queue = asyncio.Queue()

    def got_input():
        line = sys.stdin.readline()
        loop.call_soon_threadsafe(queue.put_nowait, line)

    loop.add_reader(sys.stdin.fileno(), got_input)
    try:
        ligne = await asyncio.wait_for(queue.get(), timeout)
        return ligne.strip()
    except asyncio.TimeoutError:
        print()
        return ""
    finally:
        loop.remove_reader(sys.stdin.fileno())


# =====================================================================
# BOUCLE PRINCIPALE (HYPERVISEUR)
# =====================================================================
async def run_terminal():
    nexus = NexusAgenticSystem()
    await nexus.prechauffer_cerveau()

    print("\n" + "=" * 70)
    print(f"🚀 NEXUS COMMAND CENTER — PIPELINE TEMPS RÉEL (T+20s/40s)")
    print("=" * 70 + "\n")

    while True:
        raw = await async_input("📝 Client (Début d'appel) : ", timeout=86400)
        if raw.lower() in {"exit", "q", "quit"}: break
        if not raw: continue

        ticket_final = raw
        transcript = f"Client : {raw}\n"
        ticket_complet = False
        silence_count = 0
        motif_fermeture = "STANDARD"
        skip_generation = False

        if nexus.est_salutation_basique(ticket_final):
            domaine_maitre, score_maitre = "EN_ATTENTE", 0.0
        else:
            domaine_maitre, score_maitre, _ = nexus.evaluator.evaluer_ticket(ticket_final)

        while not ticket_complet:
            if nexus.detecter_choc_acoustique(ticket_final):
                print("   [ALERTE] 💥 PANIQUE DÉTECTÉE - BASCULE MULTI-FORCES")
                domaine_maitre = "MÉDICAL"
                score_maitre = 10.0
                motif_fermeture = "CRI_DETECTE"
                if silence_count > 0:
                    ticket_complet = True
                    break

            if not nexus.est_salutation_basique(ticket_final):
                domaine_courant, score_courant, friction = nexus.evaluator.evaluer_ticket(ticket_final)
                if score_courant > score_maitre:
                    score_maitre = score_courant
                    domaine_maitre = domaine_courant

            if not skip_generation:
                statut, question_bot = await nexus.generer_question_bot(transcript, ticket_final, domaine_maitre, score_maitre)
                if statut == "COMPLET":
                    ticket_complet = True
                    break
                print(f"   🤖 NEXUS ({domaine_maitre} | Score: {score_maitre}/10) : {question_bot}")

            skip_generation = False

            complement = await async_input("   💬 Client : ", timeout=20.0)

            if complement == "":
                silence_count += 1

                if domaine_maitre in ["MÉDICAL", "POLICE", "POMPIER"]:
                    if silence_count == 1:
                        print("   🤖 NEXUS (RELANCE URGENCE) : Allô ? Répondez-moi si vous m'entendez !")
                        skip_generation = True
                        continue
                    else:
                        motif_fermeture = "SILENCE_CRITIQUE"
                        ticket_complet = True
                        break

                elif domaine_maitre in ["CYBERSÉCURITÉ", "ÉNERGIE & INFRASTRUCTURES", "TRANSPORT & MOBILITÉ"] and score_maitre >= 5:
                    if silence_count == 1:
                        print("   🤖 NEXUS (RELANCE TECHNIQUE) : Liaison instable. Êtes-vous en ligne ?")
                        skip_generation = True
                        continue
                    else:
                        motif_fermeture = "SILENCE_CRITIQUE"
                        ticket_complet = True
                        break

                else:
                    if silence_count == 1:
                        print("   🤖 NEXUS (RELANCE) : Êtes-vous toujours là ?")
                        skip_generation = True
                        continue
                    elif silence_count == 2:
                        print("   🤖 NEXUS (AVERTISSEMENT) : Sans réponse de votre part, je raccroche.")
                        skip_generation = True
                        continue
                    else:
                        print("   ⚠️ APPEL ABANDONNÉ PAR L'UTILISATEUR (Aucun secours déclenché).")
                        nexus.logger.log(ticket_final, domaine_maitre, [], score_maitre, statut="ABANDON")
                        break

            silence_count = 0

            if complement.lower() in {"exit", "q", "quit"}:
                ticket_final = "exit"
                break

            ticket_final += " " + complement
            transcript += f"Régulateur : {question_bot}\nClient : {complement}\n"

        if ticket_final == "exit": break

        if silence_count >= 3 and domaine_maitre not in ["MÉDICAL", "POLICE", "POMPIER", "CYBERSÉCURITÉ", "ÉNERGIE & INFRASTRUCTURES"]:
            print("-" * 70 + "\n📝 En attente du prochain appelant...\n")
            continue

        niveau = "🔴 CRITIQUE" if score_maitre >= 8 else "🟠 HAUTE" if score_maitre >= 5 else "🟢 BASSE"

        print(f"\n   ✅ APPEL CLOS — TRANSMISSION AUX UNITÉS")
        print(f"   🎯 Service Principal : {domaine_maitre}  |  🔢 Score Tactique : {score_maitre}/10  →  {niveau}")

        domaines_secondaires = await nexus.extraire_domaines_secondaires(ticket_final, domaine_maitre)
        if motif_fermeture == "CRI_DETECTE":
            domaines_secondaires = list(set(domaines_secondaires + ["POLICE", "POMPIER"]))
            domaines_secondaires = [d for d in domaines_secondaires if d != domaine_maitre]

        if domaines_secondaires:
            print(f"   🚨 Renforts requis identifiés : {', '.join(domaines_secondaires)}")

        domaines_impliques = [domaine_maitre] + domaines_secondaires

        nexus.executor.declencher_protocoles(domaines_impliques, niveau, ticket_final, motif_fermeture)
        nexus.logger.log(ticket_final, domaine_maitre, domaines_secondaires, score_maitre, statut=motif_fermeture)

        print("-" * 70 + "\n📝 En attente du prochain appelant...\n")


if __name__ == "__main__":
    asyncio.run(run_terminal())
