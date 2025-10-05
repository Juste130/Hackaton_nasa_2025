"""
Configuration centralisée pour le projet NASA Knowledge Graph
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === DSPy Configuration ===
DSPY_MODEL = os.getenv("DSPY_MODEL", "openrouter/x-ai/grok-4-fast")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# === Neo4j Configuration ===
NEO4J_URI = os.getenv("NEO4J_URI")  # Ex: "neo4j+s://xxxxx.databases.neo4j.io"
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# === PostgreSQL (déjà configuré dans client.py) ===
DATABASE_URL = os.getenv("POSTGRES_URL")

# === API Keys ===
NCBI_API_KEY = os.getenv("NCBI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Pour embeddings

# === Validation ===
def validate_config():
    """Valider que toutes les variables critiques sont présentes"""
    required = {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
    }
    
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing)}")
    
    print(" Configuration validée")

if __name__ == "__main__":
    validate_config()