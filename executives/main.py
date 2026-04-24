# main.py
import joblib
import os
import torch
import warnings
from sentence_transformers import util
from nexus_core import TextEncoder
from nexus_config import *  # Importation de toute la partie notation

# Désactivation des warnings
warnings.filterwarnings("ignore")


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V7 PRO (Notation Découplée)...")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ {MODEL_PATH} absent. Lancez la Forge.")
            exit()

        self.domain_model = joblib.load(MODEL_PATH)
        self.semantic_model = self.domain_model.named_steps['vectorizer']._get_encoder()

        # Préparation des ancres sémantiques à partir de la config
        self.phrases_ancres = []
        self.ancre_to_impact = {}
        for zone, data in LOCALISATIONS.items():
            for phrase in data["phrases"]:
                self.phrases_ancres.append(phrase)
                self.ancre_to_impact[phrase] = (zone, data["impact"])

        self.ancre_embeddings = self.semantic_model.encode(self.phrases_ancres, convert_to_tensor=True)

    def calculer_priorite_medicale(self, texte):
        t_lower = texte.lower()
        raisons = []

        # 1. ÉVALUATION DE L'IMPACT (Axe X) via Similarité Sémantique
        query_emb = self.semantic_model.encode(texte, convert_to_tensor=True)
        sims = util.cos_sim(query_emb, self.ancre_embeddings)[0]
        best_idx = torch.argmax(sims).item()
        phrase_match = self.phrases_ancres[best_idx]
        zone, impact_val = self.ancre_to_impact[phrase_match]

        raisons.append(f"Impact : {zone} (Niveau {impact_val}/4)")

        # 2. ÉVALUATION DE L'URGENCE (Axe Y) via Analyse de Signes
        urgence_val = 1  # Niveau de base (Faible)

        # Check Hémorragie
        if any(k in t_lower for k in ["sang", "saigne", "hemorr", "hemero"]):
            if any(m in t_lower for m in ["beaucoup", "gicle", "massive", "s'arrête pas"]):
                urgence_val = max(urgence_val, 4)
                raisons.append("Urgence : Hémorragie active (Niveau 4/4)")
            else:
                urgence_val = max(urgence_val, 2)
                raisons.append("Urgence : Saignement simple (Niveau 2/4)")

        # Check Red Flags Cliniques
        for alerte, infos in RED_FLAGS.items():
            if any(m in t_lower for m in infos["mots"]):
                urgence_val = max(urgence_val, infos["urgence"])
                raisons.append(f"Urgence : Signe {alerte.upper()} (Niveau {infos['urgence']}/4)")

        # 3. CROISEMENT DANS LA MATRICE (config)
        # On soustrait 1 pour l'indexation Python (0-3)
        score_final = MATRICE_PRIORITE[impact_val - 1][urgence_val - 1]

        return score_final, raisons

    def evaluer_ticket(self, texte):
        t_lower = texte.lower()

        # Sécurité : Incidents techniques majeurs (Feu/Explosion)
        if any(k in t_lower for k in CRITICAL_TECH_KEYWORDS):
            return "INFRA/SÉCURITÉ", 10.0, ["ALERTE CRITIQUE : Risque physique ou matériel majeur"]

        # A. Classification du Domaine (IA)
        domaine = self.domain_model.predict([texte])[0]

        # B. Notation via la Matrice
        if domaine == "MÉDICAL":
            score, raisons = self.calculer_priorite_medicale(texte)
        else:
            # Notation technique simplifiée Impact x Urgence
            impact_map = {"INFRA": 4, "ACCÈS": 3, "RH": 2, "MATÉRIEL": 1}
            imp_val = impact_map.get(domaine, 1)

            urg_val = 4 if any(m in t_lower for m in ["urgent", "bloqué", "panne", "mort"]) else 1

            score = MATRICE_PRIORITE[imp_val - 1][urg_val - 1]
            raisons = [f"Standard {domaine} (Imp:{imp_val}/Urg:{urg_val})"]

        return domaine, round(score, 1), raisons


if __name__ == "__main__":
    system = NexusMainSystem()
    print("\n🚀 NEXUS V7 PRO - PRÊT")
    while True:
        ticket = input("\n📝 Description : ").strip()
        if ticket.lower() == 'exit': break

        dom, sco, rai = system.evaluer_ticket(ticket)
        prio = "🔴 CRITIQUE" if sco >= 8 else ("🟠 HAUTE" if sco >= 5 else "🟢 BASSE")

        print(f"🎯 Domaine : {dom} | 🔢 Score : {sco}/10 -> {prio}")
        print(f"💡 Analyse : {' | '.join(rai)}")