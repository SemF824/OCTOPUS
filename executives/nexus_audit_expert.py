# nexus_audit_expert.py
import joblib
import os
import warnings
import pandas as pd
from nexus_core import TextEncoder
from nexus_config import MODEL_PATH, MODEL_FRICTION_PATH

warnings.filterwarnings("ignore")


def run_expert_audit():
    print("==================================================")
    print("🔬 AUDIT EXPERT NEXUS V12 (TESTS DE RUPTURE)")
    print("==================================================\n")

    if not os.path.exists(MODEL_PATH) or not os.path.exists(MODEL_FRICTION_PATH):
        print("❌ Modèles introuvables. Vérifiez les chemins.")
        return

    print("🧠 Chargement des cerveaux...")
    model_unified = joblib.load(MODEL_PATH)
    model_friction = joblib.load(MODEL_FRICTION_PATH)

    # ==========================================
    # BATTERIE DE TESTS INÉDITS (Pièges absolus)
    # ==========================================
    stress_tests = [
        # 1. PIÈGE DE LA NÉGATION
        ("Il n'y a pas d'arme, c'est juste une dispute verbale", "POLICE (Faible)"),
        ("Ce n'est pas urgent, je veux juste un renseignement", "Bas/Neutralisé"),

        # 2. PIÈGE DE LA FICTION
        ("Je regarde un film où une bombe explose au centre commercial", "Neutralisé/Bas"),
        ("Dans mon jeu vidéo, le mec s'est pris une balle", "Neutralisé/Bas"),

        # 3. AMBIGUÏTÉ / SYNERGIES
        ("Un camion d'essence a percuté le commissariat et prend feu", "POMPIER + POLICE"),
        ("Le serveur principal a pris feu à cause d'un court-circuit", "INFRA + POMPIER"),

        # 4. FRICTION (Manque d'infos - doit déclencher une question)
        ("Ça saigne beaucoup.", "Doit poser question"),
        ("On a piraté", "Doit poser question"),
        ("Mon ordinateur.", "Doit poser question"),

        # 5. CAS EXTRÊMES (Impact 4 / Urgence 4)
        ("Le bébé est tout bleu et ne respire plus du tout", "MÉDICAL 4/4"),
        ("Attaque ransomware massive, on perd toutes les données bancaires", "INFRA 4/4"),
        ("Un homme cagoulé tire sur la foule", "POLICE 4/4")
    ]

    print(f"\n{'TICKET SOUMIS (Inédit)':<60} | {'DOM.'} | {'I/U'} | {'STATUT FRICTION'}")
    print("-" * 105)

    for texte, attente in stress_tests:
        # 1. Test du modèle Friction (Phrase complète ou non ?)
        pred_fric = model_friction.predict([texte])[0]

        # 2. Test du modèle Principal (Domaine, Impact, Urgence)
        pred_uni = model_unified.predict([texte])[0]
        dom, imp, urg = pred_uni[0], pred_uni[1], pred_uni[2]

        # Formatage visuel du statut de Friction
        if pred_fric == "COMPLET":
            statut_fric = "🟢 TICKET COMPLET"
        else:
            statut_fric = f"🟡 QUESTION REQUISE"

        # Raccourcir le texte pour l'affichage
        texte_court = (texte[:57] + '...') if len(texte) > 57 else texte

        print(f"{texte_court:<60} | {dom[:4]:<4} | {imp}/{urg} | {statut_fric}")

    print("-" * 105)
    print("✅ Audit terminé. Observez comment l'IA réagit aux pièges ci-dessus.")
    print("👉 Note : Si un ticket court est marqué 'TICKET COMPLET', le modèle Friction manque de données courtes.")


if __name__ == "__main__":
    run_expert_audit()