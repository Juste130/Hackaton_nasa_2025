"""
FastAPI endpoints for AI services with session management
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import dspy
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import text
from enum import Enum
from datetime import datetime

# Import correct modules
from ai_summarizer import SummaryService
from ai_rag_assistant import RAGService
from ai_generic_rag import GenericRAGService
from session_manager import SessionManager
from search_engine import HybridSearchEngine, SearchMode
from redis_cache import cache_neo4j_query

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NASA AI Services API",
    description="AI-powered research assistant with sessions",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services - initialize only once
_llm = None
_summary_service = None
_rag_service = None
_generic_rag_service = None
_session_manager = None
_search_engine = None


def get_llm():
    """Get or create LLM instance"""
    global _llm
    if _llm is None:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        
        try:
            _llm = dspy.LM(
                "openai/mistral-small-latest",
                api_key=os.environ.get("MISTRAL_API_KEY"),
                api_base="https://api.mistral.ai/v1",
                max_tokens=20000
            )
            logger.info(" LLM initialized with OpenAI interface")
        except Exception as e:
            logger.warning(f"OpenAI interface failed: {e}")
            try:
                _llm = dspy.LM(
                    "openai/mistral-small-latest",
                    api_key=os.environ.get("MISTRAL_API_KEY"),
                    api_base="https://api.mistral.ai/v1",
                    max_tokens=20000
                )
                logger.info(" LLM initialized with LiteLLM interface")
            except Exception as e2:
                logger.error(f"LiteLLM failed: {e2}")
                raise
        
        # Configure DSPy settings ONCE, globally
        dspy.settings.configure(lm=_llm)
        logger.info(" DSPy settings configured globally")
    
    return _llm


def get_summary_service():
    """Get or create summary service"""
    global _summary_service
    if _summary_service is None:
        _summary_service = SummaryService(get_llm())
        logger.info(" Summary service initialized")
    return _summary_service


def get_rag_service():
    """Get or create RAG service"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(get_llm())
        logger.info(" RAG service initialized")
    return _rag_service


def get_generic_rag_service():
    """Get or create Generic RAG service"""
    global _generic_rag_service
    if _generic_rag_service is None:
        _generic_rag_service = GenericRAGService(get_llm())
        logger.info(" Generic RAG service initialized")
    return _generic_rag_service


def get_session_manager():
    """Get or create session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
        logger.info(" Session manager initialized")
    return _session_manager


def get_search_engine():
    """Get or create search engine"""
    global _search_engine
    if _search_engine is None:
        _search_engine = HybridSearchEngine()
        logger.info(" Search engine initialized")
    return _search_engine


# === Pydantic Models avec Enums pour dropdowns ===

class SearchModeEnum(str, Enum):
    """Search mode options for dropdown"""
    semantic = "semantic"
    fulltext = "fulltext"
    hybrid = "hybrid"

# === Pydantic Models ===

class SessionCreate(BaseModel):
    service_type: str = Field(..., description="summarizer | rag_assistant | generic_rag")
    metadata: Optional[dict] = None


class SessionResponse(BaseModel):
    session_id: str
    service_type: str
    created_at: str


class SummarizeRequest(BaseModel):
    pmcid: str = Field(..., description="PMC ID of the article to summarize")


class RAGQuestionRequest(BaseModel):
    question: str = Field(..., description="Question to ask")
    pmcids: Optional[List[str]] = Field(None, description="Optional list of PMC IDs to focus on")


class GenericRAGRequest(BaseModel):
    question: str = Field(..., description="Question - AI will autonomously search")


class RAGResponse(BaseModel):
    """Response for RAG services"""
    answer: str
    citations: List[str] = Field(default_factory=list)
    confidence: Union[float,str] = "low"
    reasoning: Optional[str] = None
    tools_used: List[str] = Field(default_factory=list)
    metadata: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MessageResponse(BaseModel):
    """Response for chat-style interactions"""
    role: str = Field(default="assistant")
    content: str
    metadata: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    mode: SearchModeEnum = Field(SearchModeEnum.hybrid, description="Search mode")
    limit: int = Field(10, ge=1, le=100, description="Number of results per page")
    page: int = Field(1, ge=1, description="Page number (1-based)")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity for semantic search")
    year_from: Optional[int] = Field(None, description="Filter publications from year")
    year_to: Optional[int] = Field(None, description="Filter publications to year")
    journal: Optional[str] = Field(None, description="Filter by journal name (free text)")
    include_graph_context: bool = Field(False, description="Include Neo4j graph relationships")


class SearchResponse(BaseModel):
    query: str
    mode: str
    results: List[dict]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_previous: bool
    filters_applied: dict


# === Session Endpoints ===

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create new conversation session"""
    try:
        # Validate service type
        valid_types = ['summarizer', 'rag_assistant', 'generic_rag']
        if request.service_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid service_type. Must be one of: {valid_types}"
            )
        
        session_manager = get_session_manager()
        session_id = session_manager.create_session(
            service_type=request.service_type,
            metadata=request.metadata
        )

        info = session_manager.get_session_info(session_id)

        return SessionResponse(
            session_id=session_id,
            service_type=info['service_type'],
            created_at=info['created_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Session creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: Optional[int] = None
):
    """Get conversation history for session"""
    try:
        session_manager = get_session_manager()
        info = session_manager.get_session_info(session_id)
        
        if not info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = session_manager.get_history(session_id, limit=limit)
        
        return {
            "session_id": session_id,
            "service_type": info['service_type'],
            "message_count": len(history),
            "messages": history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions(
    service_type: Optional[str] = None,
    limit: int = 50
):
    """List all sessions"""
    try:
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions(
            service_type=service_type,
            limit=limit
        )
        
        return {
            "count": len(sessions),
            "sessions": sessions
        }
    
    except Exception as e:
        logger.error(f" Session listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        session_manager = get_session_manager()
        info = session_manager.get_session_info(session_id)
        
        if not info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_manager.delete_session(session_id)
        
        return {"message": f"Session {session_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Session deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === AI Service Endpoints ===

@app.post("/api/summarize")
async def summarize_article(
    request: SummarizeRequest,
    session_id: str = Header(None, alias="X-Session-ID")
):
    """Generate summary for an article"""
    try:
        logger.info(f" Summarizing {request.pmcid}")
        
        # Get or create session if provided
        session_manager = get_session_manager() if session_id else None
        session_info = None
        
        if session_id:
            session_info = session_manager.get_or_create_session(
                session_id=session_id,
                service_type='summarizer',
                metadata={'created_via': 'summarize_endpoint'}
            )
            
            # Validate service type for existing sessions
            if session_info['existed'] and session_info['service_type'] != 'summarizer':
                raise HTTPException(
                    status_code=400, 
                    detail=f"Session is for {session_info['service_type']}, not summarizer"
                )
        
        # Generate summary
        summary_service = get_summary_service()
        summary = await summary_service.summarize_by_pmcid(request.pmcid)
        
        # Save to session if provided
        if session_id:
            session_manager.add_message(
                session_id=session_id,
                role='user',
                content=f"Summarize {request.pmcid}",
                metadata={'pmcid': request.pmcid}
            )
            
            session_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=summary['summary']['executive_summary'],
                metadata=summary
            )
        
        logger.info(f" Summary generated for {request.pmcid}")
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/ask", response_model=RAGResponse)
async def ask_rag_assistant(
    request: RAGQuestionRequest,
    session_id: str = Header(None, alias="X-Session-ID")
):
    """Ask question to RAG assistant"""
    try:
        logger.info(f"🤖 RAG question: {request.question[:50]}...")
        
        # Get or create session if provided
        session_manager = get_session_manager() if session_id else None
        session_info = None
        
        if session_id:
            session_info = session_manager.get_or_create_session(
                session_id=session_id,
                service_type='rag_assistant',
                metadata={'created_via': 'rag_endpoint'}
            )
            
            # Validate service type for existing sessions
            if session_info['existed'] and session_info['service_type'] != 'rag_assistant':
                raise HTTPException(
                    status_code=400, 
                    detail=f"Session is for {session_info['service_type']}, not rag_assistant"
                )
        
        # Get RAG service and ask question
        rag_service = get_rag_service()
        result = await rag_service.ask(request.question, pmcids=request.pmcids)
        
        # Save to session if provided
        if session_id:
            session_manager.add_message(
                session_id=session_id,
                role='user',
                content=request.question,
                metadata={'question_type': 'rag_assistant'}
            )
            
            session_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=result.get('answer', result.get('message', '')),
                metadata={
                    'citations': result.get('citations', []),
                    'confidence': result.get('confidence', 0.0)
                }
            )
        
        logger.info(f" RAG response generated")
        
        # Return structured RAG response
        return RAGResponse(
            answer=result.get('answer', result.get('message', '')),
            citations=result.get('citations', []),
            confidence=result.get('confidence'),
            reasoning=result.get('reasoning'),
            tools_used=result.get('tools_used', []),
            metadata=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/generic", response_model=RAGResponse)
async def ask_generic_rag(
    request: GenericRAGRequest,
    session_id: str = Header(None, alias="X-Session-ID")
):
    """Ask question to generic RAG system"""
    try:
        logger.info(f" Generic RAG: {request.question[:50]}...")
        
        # Get or create session if provided
        session_manager = get_session_manager() if session_id else None
        session_info = None
        
        if session_id:
            session_info = session_manager.get_or_create_session(
                session_id=session_id,
                service_type='generic_rag',
                metadata={'created_via': 'generic_rag_endpoint'}
            )
            
            # Validate service type for existing sessions
            if session_info['existed'] and session_info['service_type'] != 'generic_rag':
                raise HTTPException(
                    status_code=400, 
                    detail=f"Session is for {session_info['service_type']}, not generic_rag"
                )
        
        # Get generic RAG service
        rag_service = get_generic_rag_service()
        result = await rag_service.ask(request.question)
        
        # Save to session if provided
        if session_id:
            session_manager.add_message(
                session_id=session_id,
                role='user',
                content=request.question,
                metadata={'question_type': 'generic_rag'}
            )
            
            session_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=result.get('answer', result.get('message', '')),
                metadata={
                    'citations': result.get('citations', []),
                    'reasoning': result.get('reasoning', ''),
                    'tools_used': result.get('tools_used', [])
                }
            )
        
        logger.info(f" Generic RAG response generated")
        
        # Return structured RAG response
        return RAGResponse(
            answer=result.get('answer', result.get('message', '')),
            citations=result.get('citations', []),
            confidence=result.get('confidence'),
            reasoning=result.get('reasoning'),
            tools_used=result.get('tools_used', []),
            metadata=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Generic RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@cache_neo4j_query('search:hybrid', ttl=1800)
@app.post("/api/search", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    session_id: str = Header(None, alias="X-Session-ID")
):
    """
    Hybrid search across publications with multiple modes and filters
    
    Search Modes:
    - semantic: Find conceptually similar content using AI embeddings
    - fulltext: Exact keyword matching in text
    - hybrid: Combined semantic + keyword search (recommended)
    
    Filters:
    - year_from/year_to: Filter by publication date range
    - journal: Filter by journal name (partial matching)
    - min_similarity: Minimum similarity threshold for semantic search
    - include_graph_context: Add related entities from knowledge graph
    
    Pagination:
    - Use `page` and `limit` for pagination
    - Response includes `total_pages`, `has_next`, `has_previous`
    """
    try:
        logger.info(f" Search: '{request.query[:50]}...' (mode={request.mode}, page={request.page})")
        
        # Get or create session if provided
        session_manager = get_session_manager() if session_id else None
        session_info = None
        
        if session_id:
            session_info = session_manager.get_or_create_session(
                session_id=session_id,
                service_type='search',
                metadata={'created_via': 'search_endpoint'}
            )
        
        # Convert page to offset
        offset = (request.page - 1) * request.limit
        
        # Get search engine and perform search
        search_engine = get_search_engine()
        
        # Convert enum to SearchMode enum
        mode_enum = SearchMode(request.mode.value)
        
        if request.include_graph_context:
            search_result = await search_engine.search_with_graph_context(
                query=request.query,
                mode=mode_enum,
                limit=request.limit,
                include_related=True
            )
        else:
            search_result = await search_engine.search(
                query=request.query,
                mode=mode_enum,
                limit=request.limit,
                offset=offset,
                min_similarity=request.min_similarity,
                year_from=request.year_from,
                year_to=request.year_to,
                journal=request.journal
            )
        
        # Convert SearchResult objects to dicts for JSON serialization
        results_as_dicts = []
        for result in search_result["results"]:
            result_dict = {
                "pmcid": result.pmcid,
                "title": result.title,
                "abstract": result.abstract,
                "journal": result.journal,
                "publication_date": result.publication_date,
                "score": result.score,
                "search_method": result.search_method,
                "match_type": result.match_type,
                "full_text_snippet": result.full_text_snippet,
                "doi": getattr(result, 'doi', None),
                "authors": getattr(result, 'authors', None),
                "keywords_text": getattr(result, 'keywords_text', None),
                "mesh_terms_text": getattr(result, 'mesh_terms_text', None),
                "has_full_text": getattr(result, 'has_full_text', None),
                "sections_count": getattr(result, 'sections_count', None)
            }
            
            # Add graph context if available
            if hasattr(result, 'organisms'):
                result_dict["organisms"] = result.organisms
                result_dict["phenomena"] = result.phenomena
                result_dict["platforms"] = result.platforms
            
            results_as_dicts.append(result_dict)
        
        # Calculate pagination info
        total_count = search_result.get("total_count", len(results_as_dicts))
        total_pages = (total_count + request.limit - 1) // request.limit
        has_next = request.page < total_pages
        has_previous = request.page > 1
        
        # Track filters applied
        filters_applied = {}
        if request.year_from:
            filters_applied["year_from"] = request.year_from
        if request.year_to:
            filters_applied["year_to"] = request.year_to
        if request.journal:
            filters_applied["journal"] = request.journal
        if request.min_similarity != 0.3:
            filters_applied["min_similarity"] = request.min_similarity
        
        # Save to session if provided
        if session_id:
            session_manager.add_message(
                session_id=session_id,
                role='user',
                content=f"Search: {request.query}",
                metadata={
                    'search_mode': request.mode.value,
                    'filters': filters_applied,
                    'results_count': len(results_as_dicts)
                }
            )
            
            session_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=f"Found {len(results_as_dicts)} results",
                metadata={
                    'search_result': search_result,
                    'total_count': total_count
                }
            )
        
        response = SearchResponse(
            query=request.query,
            mode=request.mode.value,  # Convert back to string
            results=results_as_dicts,
            total_count=total_count,
            page=request.page,
            limit=request.limit,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            filters_applied=filters_applied
        )
        
        logger.info(f" Search completed: {len(results_as_dicts)} results, page {request.page}/{total_pages}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/filters")
async def get_search_filters():
    """Get available filter options for search"""
    try:
        search_engine = get_search_engine()
        
        async with search_engine.db_client.async_session() as session:
            # Get available journals
            journals_result = await session.execute(text("""
                SELECT DISTINCT journal, COUNT(*) as count
                FROM publications 
                WHERE journal IS NOT NULL AND journal != ''
                GROUP BY journal 
                ORDER BY count DESC 
                LIMIT 50
            """))
            journals = [{"name": row.journal, "count": row.count} for row in journals_result]
            
            # Get year range
            year_range_result = await session.execute(text("""
                SELECT 
                    MIN(EXTRACT(YEAR FROM publication_date)) as min_year,
                    MAX(EXTRACT(YEAR FROM publication_date)) as max_year
                FROM publications 
                WHERE publication_date IS NOT NULL
            """))
            year_range = year_range_result.first()
            
            # Get publication stats by year
            yearly_stats_result = await session.execute(text("""
                SELECT 
                    EXTRACT(YEAR FROM publication_date) as year,
                    COUNT(*) as count
                FROM publications 
                WHERE publication_date IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM publication_date)
                ORDER BY year DESC
                LIMIT 20
            """))
            yearly_stats = [{"year": int(row.year), "count": row.count} for row in yearly_stats_result]
            
            # Get top keywords
            keywords_result = await session.execute(text("""
                SELECT k.keyword, COUNT(*) as count
                FROM keywords k
                JOIN publication_keywords pk ON k.id = pk.keyword_id
                GROUP BY k.keyword
                ORDER BY count DESC
                LIMIT 20
            """))
            top_keywords = [{"keyword": row.keyword, "count": row.count} for row in keywords_result]
            
            # Get top MeSH terms
            mesh_result = await session.execute(text("""
                SELECT mt.term, COUNT(*) as count
                FROM mesh_terms mt
                JOIN publication_mesh_terms pmt ON mt.id = pmt.mesh_term_id
                GROUP BY mt.term
                ORDER BY count DESC
                LIMIT 20
            """))
            top_mesh_terms = [{"term": row.term, "count": row.count} for row in mesh_result]
            
            return {
                "journals": journals,
                "year_range": {
                    "min_year": int(year_range.min_year) if year_range.min_year else None,
                    "max_year": int(year_range.max_year) if year_range.max_year else None
                },
                "yearly_distribution": yearly_stats,
                "top_keywords": top_keywords,
                "top_mesh_terms": top_mesh_terms,
                "search_modes": [
                    {"value": "semantic", "name": "Semantic Search", "description": "Find conceptually similar content"},
                    {"value": "fulltext", "name": "Full-Text Search", "description": "Exact keyword matching"},
                    {"value": "hybrid", "name": "Hybrid Search", "description": "Combined semantic + keyword search"}
                ]
            }
    
    except Exception as e:
        logger.error(f" Filters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Health Check ===

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        llm = get_llm()
        
        return {
            "status": "healthy",
            "services": {
                "summarizer": "available",
                "rag_assistant": "available", 
                "generic_rag": "available"
            },
            "llm": "mistral-small-latest",
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f" Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NASA AI Services API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "sessions": "/api/sessions",
            "summarize": "/api/summarize", 
            "rag": "/api/rag/ask",
            "generic_rag": "/api/rag/generic",
            "search": "/api/search",
            "search_filters": "/api/search/filters"
        }
    }


# Proper shutdown handling
@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    try:
        if _summary_service:
            await _summary_service.close()
        if _rag_service:
            await _rag_service.close()
        if _generic_rag_service:
            await _generic_rag_service.close()
        if _search_engine:
            await _search_engine.close()
        logger.info(" Services closed gracefully")
    except Exception as e:
        logger.error(f" Shutdown error: {e}")


# Startup event
@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    try:
        logger.info(" Starting NASA AI Services API...")
        
        # Test initialization - but don't fail if LLM setup fails
        try:
            get_llm()
            logger.info(" LLM initialized successfully")
        except Exception as e:
            logger.error(f" LLM initialization failed: {e}")
            logger.info(" API will start but AI services may not work")
        
        # Initialize session manager (doesn't depend on LLM)
        get_session_manager()
        
        logger.info(" API ready!")
    except Exception as e:
        logger.error(f" Startup failed: {e}")
        # Don't raise - let the API start anyway


# Add Neo4j router import
try:
    from api_neo4j import router as neo4j_router
    app.include_router(neo4j_router)
    logger.info(" Neo4j router included")
except Exception as e:
    logger.error(f" Failed to include Neo4j router: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)