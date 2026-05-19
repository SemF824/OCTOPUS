# executives/nexus_audit_expert.py
import joblib
import os
import warnings
from nexus_config import MODEL_UNIFIED_PATH

warnings.filterwarnings("ignore")


def run_expert_audit():
    print("==================================================")
    print("🔬 AUDIT EXPERT NEXUS V33 (TESTS DE RUPTURE)")
    print("==================================================\n")

    if not os.path.exists(MODEL_UNIFIED_PATH):
        print(f"❌ Modèle introuvable: {MODEL_UNIFIED_PATH}")
        return

    print("🧠 Chargement du cerveau unifié V33...")
    model_unified = joblib.load(MODEL_UNIFIED_PATH)

    stress_tests = [
        # 1. PIÈGE DE LA NÉGATION
        "Il n'y a pas d'arme, c'est juste une dispute verbale",
        "Ce n'est pas urgent, je veux juste un renseignement",
        # 2. PIÈGE DE LA FICTION
        "Je regarde un film où une bombe explose au centre commercial",
        "Dans mon jeu vidéo, le mec s'est pris une balle",
        # 3. AMBIGUÏTÉ / SYNERGIES
        "Un camion d'essence a percuté le commissariat et prend feu",
        "Le serveur principal a pris feu à cause d'un court-circuit",
        # 4. TICKETS ULTRA-COURTS (Crash-Test TF-IDF)
        "Ça saigne beaucoup.",
        "On a piraté",
        "Mon ordinateur.",
        # 5. CAS EXTRÊMES
        "Le bébé est tout bleu et ne respire plus du tout",
        "Attaque ransomware massive, on perd toutes les données bancaires",
        "Un homme cagoulé tire sur la foule"
    ]

    print(f"\n{'TICKET SOUMIS':<60} | {'DOMAINE':<20} | {'SEV/IMP/CIB'} | {'FRICTION'}")
    print("-" * 125)

    for texte in stress_tests:
        pred_uni = model_unified.predict([texte])[0]
        # Décodage strict V33
        dom, sev, imp, cib, fric = pred_uni[0], pred_uni[1], pred_uni[2], pred_uni[3], pred_uni[4]

        texte_court = (texte[:57] + '...') if len(texte) > 57 else texte

        if fric == "COMPLET":
            fric_display = "🟢 COMPLET"
        else:
            fric_display = f"🟡 {fric}"

        print(f"{texte_court:<60} | {dom:<20} | {sev}/{imp}/{cib}       | {fric_display}")


if __name__ == "__main__":
    run_expert_audit()