# main.py
import joblib
import os
import torch
import warnings
from sentence_transformers import util
from nexus_core import TextEncoder
from nexus_config import *

warnings.filterwarnings("ignore")


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V8 (100% IA Sémantique)...")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ {MODEL_PATH} absent. Lancez la Forge.")
            exit()

        self.domain_model = joblib.load(MODEL_PATH)
        self.semantic_model = self.domain_model.named_steps['vectorizer']._get_encoder()

        # --- Chargement des Ancres d'IMPACT dans l'IA ---
        self.phrases_impact = []
        self.ancre_to_impact = {}
        for zone, data in LOCALISATIONS.items():
            for phrase in data["phrases"]:
                self.phrases_impact.append(phrase)
                self.ancre_to_impact[phrase] = (zone, data["impact"])
        self.emb_impact = self.semantic_model.encode(self.phrases_impact, convert_to_tensor=True)

        # --- Chargement des Ancres d'URGENCE dans l'IA ---
        self.phrases_urgence = []
        self.ancre_to_urgence = {}
        for niv, data in URGENCES.items():
            for phrase in data["phrases"]:
                self.phrases_urgence.append(phrase)
                self.ancre_to_urgence[phrase] = (niv, data["urgence"])
        self.emb_urgence = self.semantic_model.encode(self.phrases_urgence, convert_to_tensor=True)

    def calculer_priorite_medicale(self, texte):
        raisons = []
        query_emb = self.semantic_model.encode(texte, convert_to_tensor=True)

        # 1. IA : ÉVALUATION DE L'IMPACT (X)
        sims_impact = util.cos_sim(query_emb, self.emb_impact)[0]
        best_idx_imp = torch.argmax(sims_impact).item()
        phrase_match_imp = self.phrases_impact[best_idx_imp]
        zone, impact_val = self.ancre_to_impact[phrase_match_imp]

        raisons.append(f"Impact : {zone} (Ancre: '{phrase_match_imp}')")

        # 2. IA : ÉVALUATION DE L'URGENCE (Y)
        sims_urg = util.cos_sim(query_emb, self.emb_urgence)[0]
        best_idx_urg = torch.argmax(sims_urg).item()
        phrase_match_urg = self.phrases_urgence[best_idx_urg]
        niveau_urg, urgence_val = self.ancre_to_urgence[phrase_match_urg]

        raisons.append(f"Urgence : {niveau_urg} (Ancre: '{phrase_match_urg}')")

        # 3. LECTURE MATRICIELLE
        score_final = MATRICE_PRIORITE[impact_val - 1][urgence_val - 1]

        return score_final, raisons

    def evaluer_ticket(self, texte):
        t_lower = texte.lower()

        # Alerte Technique Critique
        if any(k in t_lower for k in CRITICAL_TECH_KEYWORDS):
            return "INFRA/SÉCURITÉ", 10.0, ["ALERTE CRITIQUE : Risque physique ou matériel"]

        # Classification du Domaine (Kaggle)
        domaine = self.domain_model.predict([texte])[0]

        # Notation
        if domaine == "MÉDICAL":
            score, raisons = self.calculer_priorite_medicale(texte)
        else:
            impact_map = {"INFRA": 4, "ACCÈS": 3, "RH": 2, "MATÉRIEL": 1}
            imp_val = impact_map.get(domaine, 1)
            urg_val = 4 if any(m in t_lower for m in ["urgent", "bloqué", "panne", "mort"]) else 1
            score = MATRICE_PRIORITE[imp_val - 1][urg_val - 1]
            raisons = [f"Standard {domaine} (Imp:{imp_val}/Urg:{urg_val})"]

        return domaine, round(score, 1), raisons


if __name__ == "__main__":
    system = NexusMainSystem()
    print("\n🚀 NEXUS V8 PRO (Full IA) - PRÊT")
    while True:
        ticket = input("\n📝 Description : ").strip()
        if ticket.lower() == 'exit': break

        dom, sco, rai = system.evaluer_ticket(ticket)
        prio = "🔴 CRITIQUE" if sco >= 8 else ("🟠 HAUTE" if sco >= 5 else "🟢 BASSE")

        print(f"🎯 Domaine : {dom} | 🔢 Score : {sco}/10 -> {prio}")
        print(f"💡 Analyse : {' | '.join(rai)}")