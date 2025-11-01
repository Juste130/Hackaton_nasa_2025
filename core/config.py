"""
Configuration module for DSPy, Neo4j, PostgreSQL, and API keys.
"""
import os
from dotenv import load_dotenv

load_dotenv("./.env")


# === DSPy Configuration ===
DSPY_MODEL = os.getenv("DSPY_MODEL", "openrouter/x-ai/grok-4-fast")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# === Neo4j Configuration ===
NEO4J_URI = os.getenv("NEO4J_URI")  # Ex: "neo4j+s://xxxxx.databases.neo4j.io"
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# === PostgreSQL  ===
POSTGRES_URL = os.getenv("POSTGRES_URL")

# === API Keys ===
NCBI_API_KEY = os.getenv("NCBI_API_KEY")


