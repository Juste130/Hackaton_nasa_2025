"""
API Main Module - FastAPI Application Entry Point
"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src to Python path for absolute imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Create FastAPI app
app = FastAPI(
    title="NASA Bioscience Publications API",
    description="AI-powered knowledge graph and research assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers correctly
try:
    from api.routers.api_neo4j import router as neo4j_router
    app.include_router(neo4j_router)
    print(" Neo4j router loaded")
except ImportError as e:
    print(f" Neo4j router not found: {e}")

try:
    from api.routers.api_ai import router as ai_router
    app.include_router(ai_router)
    print(" AI router loaded")
except ImportError as e:
    print(f" AI router not found: {e}")
