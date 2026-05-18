# executives/nexus_config.py
import os

# Chemins des bases de données et modèles ML
DB_PATH = "../nexus_bionexus.db"

# Ton futur modèle Kaggle
MODEL_UNIFIED_PATH = "../pickle_result/nexus_v32_unified.pkl"

# Configurations des Modèles LLM (Ollama)
MODEL_EVALUATOR = "qwen2.5-coder" # Utilisé sur Kaggle
MODEL_DIALOGUE = "mistral"        # Le modèle français léger et naturel

CONFIDENCE_THRESHOLD = 0.50