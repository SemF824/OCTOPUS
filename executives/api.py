# api.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from main import NexusMainSystem  # On importe ton chef-d'oeuvre !

# 1. Initialisation de l'application Web et de l'IA
app = FastAPI(title="NEXUS Prime API", description="Moteur de triage d'urgence", version="28.0")
nexus = NexusMainSystem()

# 2. Autoriser ton futur site web à communiquer avec cette API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Plus tard, tu mettras l'URL de ton site ici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. Définition du format de données attendu depuis le site web
class TicketRequest(BaseModel):
    texte: str
    force_score: bool = False


# 4. La route principale (L'URL que ton site va appeler)
@app.post("/api/evaluer")
def evaluer_ticket_api(request: TicketRequest):
    # On passe le texte à ton moteur existant
    (domaine, score, raisons, ticket_complet,
     dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(request.texte, request.force_score)

    # Détermination de l'alerte visuelle
    niveau = "🔴 CRITIQUE" if score >= 8 else "🟠 HAUTE" if score >= 5 else "🟢 BASSE"

    # On renvoie une belle structure JSON au site web
    if not ticket_complet:
        return {
            "statut": "INCOMPLET",
            "domaine_pressenti": domaine,
            "question_ia": raisons[0],  # La question que le site devra afficher dans le chat
            "donnees_brutes": {"confiance": conf}
        }
    else:
        # On logge en BDD car le ticket est fini
        nexus.logger.log(request.texte, request.texte, dom_brut, imp_brut, urg_brut, conf)
        return {
            "statut": "COMPLET",
            "resultat": {
                "domaine_final": domaine,
                "score_sur_10": score,
                "niveau_alerte": niveau,
                "explications": raisons
            }
        }