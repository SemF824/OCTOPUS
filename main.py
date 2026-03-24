import sqlite3
import joblib
import warnings
from scipy.sparse import hstack, csr_matrix

warnings.filterwarnings("ignore")

# CONSTANTES
DB_PATH = "nexus_bionexus.db"
MODEL_DOMAIN_PATH = "nexus_modele_domaine_v3.pkl"
MODEL_SCORE_PATH = "nexus_modele_score_v3.pkl"
VECTORIZER_PATH = "nexus_vectorizer_v3.pkl"


def rechercher_client(saisie: str):
    """
    Tente de trouver un client par son ID exact ou par une partie de son nom.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # On cherche soit une correspondance exacte de l'ID, soit le nom
            query = """
                SELECT id_client, nom_organisation 
                FROM clients 
                WHERE id_client = ? OR nom_organisation LIKE ?
            """
            cursor.execute(query, (saisie, f"%{saisie}%"))
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def run_terminal_interface() -> None:
    """Lance l'interface en ligne de commande avec résolution d'identité."""
    print("\n" + "=" * 60)
    print(" 🧠 NEXUS BIONEXUS - MODE TERMINAL (MONDE RÉEL)")
    print("=" * 60)

    try:
        vectorizer = joblib.load(VECTORIZER_PATH)
        domain_model = joblib.load(MODEL_DOMAIN_PATH)
        score_model = joblib.load(MODEL_SCORE_PATH)
        print("✅ Cerveaux connectés. Prêt pour l'analyse.\n")
    except Exception as e:
        print(f"❌ Erreur critique lors du chargement des modèles : {e}")
        return

    while True:
        print("-" * 60)
        ticket_text = input("📝 Description : ").strip()

        if ticket_text.lower() == 'exit':
            print("Fermeture du système.")
            break

        # --- RÉSOLUTION DU CLIENT ---
        saisie_client = input("👤 Client (Nom ou ID) : ").strip()
        resultats = rechercher_client(saisie_client)

        if len(resultats) == 1:
            client_id = resultats[0][0]
            nom_client = resultats[0][1]
            print(f"✅ Client identifié : {nom_client} ({client_id})")
        elif len(resultats) > 1:
            print("❓ Plusieurs correspondances trouvées :")
            for i, res in enumerate(resultats):
                print(f"  {i + 1}. {res[0]} - {res[1]}")
            choix = input("Sélectionnez l'ID exact (ou Entrée pour ignorer) : ").strip()
            client_id = choix if choix else "CLI-GENERIC"
        else:
            print("⚠️ Aucun client trouvé. Utilisation de 'CLI-GENERIC'.")
            client_id = "CLI-GENERIC"

        # --- PARAMÈTRES D'URGENCE ---
        urgency_input = input("🚨 Urgence (1-5) : ").strip()
        urgency_level = int(urgency_input) if urgency_input.isdigit() else 3

        # 1. Extraction des features
        X_text = vectorizer.transform([ticket_text])

        # Le modèle attend [rang_priorite, etat_num]
        etat_num = 1 if urgency_level >= 4 else 0
        X_metadata = csr_matrix([[urgency_level, etat_num]])
        X_final = hstack([X_text, X_metadata])

        # 2. Prédictions
        predicted_domain = domain_model.predict(X_text)[0]
        raw_score = score_model.predict(X_final)[0]
        final_score = round(raw_score, 1)

        print(f"\n[ RÉSULTAT ] Domaine: {predicted_domain} | Score: {final_score}/10")

        # 3. Log SQL
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO prediction_logs 
                    (texte_ticket, id_client, domaine_predit, score_brut_ia)
                    VALUES (?, ?, ?, ?)
                """, (ticket_text, client_id, predicted_domain, float(raw_score)))
                print("💾 Décision mémorisée en SQL.")
        except sqlite3.Error as e:
            print(f"⚠️ Erreur lors de l'écriture des logs : {e}")


if __name__ == "__main__":
    run_terminal_interface()
