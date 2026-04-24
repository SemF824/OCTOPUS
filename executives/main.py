# main.py
import joblib
import os
import warnings
import numpy as np
from nexus_config import MATRICE_PRIORITE, MODEL_PATH, CONFIDENCE_THRESHOLD
from nexus_core import TextEncoder

warnings.filterwarnings("ignore")


class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V9 (Multi-Output)...")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Modèle absent à {MODEL_PATH}. Lancez la Forge.")
            exit()
        self.model = joblib.load(MODEL_PATH)

    def evaluer_ticket(self, texte):
        # 1. Analyse IA (Domaine, Impact, Urgence)
        pred = self.model.predict([texte])[0]
        domaine, impact, urgence = pred[0], int(pred[1]), int(pred[2])

        # 2. Vérification Confiance (Auto-Qualification)
        probas = self.model.predict_proba([texte])
        confiance = np.max(probas[0][0])  # Confiance sur le domaine

        # 3. Logique d'Auto-Qualification
        if len(texte.split()) < 3 or confiance < CONFIDENCE_THRESHOLD:
            return domaine, 0.0, [f"⚠️ Précision requise (Confiance: {confiance:.1%})"]

        # 4. Calcul Score via Matrice
        score = MATRICE_PRIORITE[impact - 1][urgence - 1]
        raisons = [f"Impact IA: {impact}/4", f"Urgence IA: {urgence}/4", f"Confiance: {confiance:.1%}"]

        return domaine, score, raisons


if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n🚀 NEXUS V9 PRÊT")
    while True:
        ticket = input("\n📝 Ticket : ").strip()
        if not ticket or ticket.lower() == 'exit': break

        dom, sco, rai = nexus.evaluer_ticket(ticket)

        if sco == 0.0:
            print(f"🛑 AUTO-QUALIFICATION : {rai[0]}")
        else:
            prio = "🔴 CRITIQUE" if sco >= 8 else ("🟠 HAUTE" if sco >= 5 else "🟢 BASSE")
            print(f"🎯 {dom} | 🔢 {sco}/10 -> {prio}")
            print(f"💡 {', '.join(rai)}")