# main.py — NEXUS V21 CORRIGÉ
# Corrections :
#   1. Bug affichage "📝 Ticket : 📝 Ticket :" — supprimé
#   2. LocationGuard — reconnaît maintenant les lieux nommés (via MOTS_LIEUX dans nexus_config)
#   3. NegationGuard — détecte les métaphores idiomatiques (via FICTION_MARKERS étendu)

import joblib
import os
import sqlite3
import warnings
import datetime
import random

from nexus_core import TextEncoder
from nexus_config import (
    DB_PATH, MODEL_PATH, MODEL_FRICTION_PATH,
    NEGATION_MARKERS, FICTION_MARKERS, SYNERGIES_URGENCE,
    MATRICE_PRIORITE, MOTS_LIEUX,
)

warnings.filterwarnings("ignore")


# ==============================================================================
# SHADOW LOGGER
# ==============================================================================

class ShadowLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                date_log      TEXT,
                ticket_original TEXT,
                ticket_final  TEXT,
                domaine_ia    TEXT,
                impact_ia     TEXT,
                urgence_ia    TEXT,
                confiance     TEXT,
                statut_humain TEXT DEFAULT 'A_VERIFIER'
            )
        ''')
        self.conn.commit()

    def log(self, t_orig, t_fin, dom, imp, urg, conf):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO interactions_log
                (date_log, ticket_original, ticket_final, domaine_ia, impact_ia, urgence_ia, confiance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date_now, t_orig, t_fin, dom, str(imp), str(urg), f"{conf:.1%}"))
        self.conn.commit()


# ==============================================================================
# NEGATION GUARD — détecte fiction, exercice, négations, métaphores
# ==============================================================================

class NegationGuard:
    """
    Retourne (is_neutralized: bool, raison: str).
    Si True, le ticket est une fausse alerte / fiction / métaphore.
    """

    def contient_negation(self, texte, mots_sensibles):
        t = texte.lower()

        # 1. Exercice / simulation
        mots_exercices = ["exercice", "test", "simulation", "entraînement"]
        if any(ex in t for ex in mots_exercices):
            return True, "Ceci est un exercice ou un test. Procédures d'urgence réelles annulées."

        # 2. Fiction étendue — inclut maintenant les métaphores idiomatiques
        #    (FICTION_MARKERS est importé depuis nexus_config, déjà enrichi)
        if any(f in t for f in FICTION_MARKERS):
            # Exception : "cinéma en feu" → vrai incendie même si le mot "film" est présent
            if "cinéma" in t and ("incendie" in t or "feu" in t or "brûle" in t):
                pass  # on laisse passer
            else:
                return True, "Contexte de fiction, simulation ou expression idiomatique détecté."

        # 3. Négation autour des mots sensibles
        mots_texte = t.split()
        for i, mot in enumerate(mots_texte):
            for sensible in mots_sensibles:
                if sensible[:3] in mot:
                    fenetre_avant = " ".join(mots_texte[max(0, i - 3):i])
                    if any(neg in fenetre_avant for neg in NEGATION_MARKERS):
                        return True, f"Négation détectée près du mot clé '{sensible}'."

        return False, ""


# ==============================================================================
# LOCATION GUARD — vérifie la présence d'un lieu dans le ticket
# ==============================================================================

class LocationGuard:
    """
    Vérifie si le texte contient un indice de localisation.
    Utilise MOTS_LIEUX depuis nexus_config (voirie + lieux nommés + villes).
    """

    def a_une_localisation(self, texte: str) -> bool:
        t = texte.lower()
        return any(lieu in t for lieu in MOTS_LIEUX)


# ==============================================================================
# SYSTEME PRINCIPAL NEXUS
# ==============================================================================

class NexusMainSystem:
    def __init__(self):
        print("🧠 Initialisation NEXUS V21 (Friction, Localisation & Métaphores)...")
        self.model_unified  = joblib.load(MODEL_PATH)
        self.model_friction = joblib.load(MODEL_FRICTION_PATH)
        self.guard          = NegationGuard()
        self.location_guard = LocationGuard()
        self.logger         = ShadowLogger()

    # ------------------------------------------------------------------
    def evaluer_ticket(self, texte_original: str, force_score: bool = False):
        """
        Retourne :
            domaine_final (str), score (float), raisons (list[str]),
            ticket_complet (bool),
            dom_brut (str), imp_brut (int), urg_brut (int), confiance (float)
        """
        pred_uni = self.model_unified.predict([texte_original])[0]
        domaine  = pred_uni[0]
        impact   = int(pred_uni[1])
        urgence  = int(pred_uni[2])

        probas    = self.model_unified.predict_proba([texte_original])
        confiance = max(probas[0][0]) if len(probas) > 0 else 0.5

        # ── 1. Filtre Fiction / Négation / Exercice ──────────────────
        is_negated, raison = self.guard.contient_negation(
            texte_original, ["arme", "feu", "urgence", "mort", "bless"]
        )
        if is_negated:
            return (
                "INFORMATION / SÉCURITÉ", 1.0,
                [f"⚠️ {raison}"],
                True, domaine, impact, urgence, confiance,
            )

        # ── 2. LocationGuard (uniquement pour urgences terrain) ──────
        DOMAINES_TERRAIN = {"MÉDICAL", "POLICE", "POMPIER"}
        if domaine in DOMAINES_TERRAIN and not force_score:
            if not self.location_guard.a_une_localisation(texte_original):
                return (
                    domaine, 0,
                    ["🚨 LOCALISATION MANQUANTE : À quelle adresse ou lieu exact se déroule l'incident ?"],
                    False, domaine, impact, urgence, confiance,
                )

        # ── 3. Friction ML (questions de précision) ──────────────────
        if not force_score:
            statut_friction = self.model_friction.predict([texte_original])[0]
            if statut_friction != "COMPLET":
                amorce = f"Je vois qu'il s'agit potentiellement d'un cas pour le service {domaine}."

                questions_par_label = {
                    "PRECISION_MED":  [
                        "Quels sont les symptômes exacts ?",
                        "La victime est-elle consciente et respire-t-elle ?",
                    ],
                    "PRECISION_POL":  [
                        "Y a-t-il des armes visibles ?",
                        "Combien d'individus sont impliqués ?",
                    ],
                    "PRECISION_POMP": [
                        "Y a-t-il des personnes coincées à l'intérieur ?",
                        "Voyez-vous des flammes ou seulement de la fumée ?",
                    ],
                }

                # Fallback : tech ou générique
                if statut_friction in questions_par_label:
                    questions = questions_par_label[statut_friction]
                elif "TECH" in statut_friction or domaine in {"INFRA", "MATÉRIEL", "ACCÈS"}:
                    questions = [
                        "Quel est le message d'erreur exact ?",
                        "Quel équipement ou logiciel est touché ?",
                    ]
                else:
                    questions = ["Pouvez-vous donner plus de détails sur la situation ?"]

                question = random.choice(questions)
                return (
                    domaine, 0,
                    [f"{amorce} {question}"],
                    False, domaine, impact, urgence, confiance,
                )

        # ── 4. Synergies multi-forces ────────────────────────────────
        texte_lower     = texte_original.lower()
        domaines_assignes = [domaine]
        synergie_raisons  = []

        for mot_cle, services in SYNERGIES_URGENCE.items():
            if mot_cle in texte_lower:
                for s in services:
                    if s not in domaines_assignes:
                        domaines_assignes.append(s)
                synergie_raisons.append(f"Mot-clé détecté : '{mot_cle.upper()}'")

        # ── 5. Calcul du score ───────────────────────────────────────
        score = (
            MATRICE_PRIORITE[impact - 1][urgence - 1]
            if 1 <= impact <= 4 and 1 <= urgence <= 4
            else 1.0
        )
        raisons = [
            f"Impact IA  : {impact}/4",
            f"Urgence IA : {urgence}/4",
            f"Confiance  : {confiance:.1%}",
        ]

        if len(domaines_assignes) > 1:
            score = max(score, 9.5)
            raisons.insert(0, f"🔥 SYNERGIE ACTIVÉE ({' + '.join(domaines_assignes)})")
            for sr in synergie_raisons:
                raisons.insert(1, f"   -> {sr}")
            domaine_final = " + ".join(domaines_assignes)
        else:
            domaine_final = domaine

        return (
            domaine_final, score, raisons, True,
            domaine, impact, urgence, confiance,
        )


# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================

if __name__ == "__main__":
    nexus = NexusMainSystem()
    print("\n" + "=" * 52)
    print("🚀  NEXUS V21 — COMMAND CENTER")
    print("=" * 52)
    print("   Tapez 'exit' ou 'q' pour quitter.\n")

    while True:
        # ── Saisie du ticket ─────────────────────────────────────────
        raw = input("📝 Ticket : ").strip()
        if not raw or raw.lower() in {"exit", "q", "quit"}:
            break

        ticket_final    = raw          # texte courant (s'enrichit si friction)
        ticket_complet  = False
        tentatives      = 0

        # ── Boucle de friction (max 2 questions) ────────────────────
        while not ticket_complet and tentatives < 2:
            (domaine, score, raisons,
             ticket_complet,
             dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=False
            )

            if not ticket_complet:
                print(f"\n   🎯 Domaine pressenti : {domaine}")
                print(f"   🛑 {raisons[0]}")
                # ✅ FIX : on n'affiche PAS "📝 Ticket :" ici pour éviter le doublon
                complement = input("   💬 Précisez SVP : ").strip()
                if complement.lower() in {"exit", "q", "quit"}:
                    ticket_final = "exit"
                    break
                ticket_final = ticket_final + ". " + complement
                tentatives  += 1

        if ticket_final.lower() in {"exit", "q", "quit"}:
            break

        # ── Si toujours incomplet après 2 questions → force le score ─
        if not ticket_complet:
            (domaine, score, raisons,
             ticket_complet,
             dom_brut, imp_brut, urg_brut, conf) = nexus.evaluer_ticket(
                ticket_final, force_score=True
            )

        # ── Affichage du résultat ────────────────────────────────────
        niveau = (
            "🔴 CRITIQUE" if score >= 8 else
            "🟠 HAUTE"    if score >= 5 else
            "🟢 BASSE"
        )
        print(f"\n   ✅ TICKET QUALIFIÉ")
        print(f"   🎯 {domaine}  |  🔢 {score}/10  →  {niveau}")
        for r in raisons:
            print(f"   💡 {r}")
        print()

        # ── Log en base ──────────────────────────────────────────────
        nexus.logger.log(raw, ticket_final, dom_brut, imp_brut, urg_brut, conf)