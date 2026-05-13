# executives/nexus_config.py
import os

# Chemins des bases de données et modèles ML
DB_PATH = "../nexus_bionexus.db"
# Le futur modèle Scikit-Learn que tu vas entraîner sur ton Golden Dataset :
MODEL_UNIFIED_PATH = "../pickle_result/nexus_v32_unified.pkl"

# Configurations des Modèles LLM (Ollama)
MODEL_EVALUATOR = "qwen2.5-coder" # Utilisé en arrière-plan pour la forge/logique
MODEL_DIALOGUE = "llama3.1"       # Le petit cerveau empathique pour parler au client

CONFIDENCE_THRESHOLD = 0.50