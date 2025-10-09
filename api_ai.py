"""
FastAPI endpoints for AI services with session management
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import dspy
import os
import logging
from dotenv import load_dotenv

# Import correct modules
from ai_summarizer import SummaryService
from ai_rag_assistant import RAGService
from ai_generic_rag import GenericRAGService
from session_manager import SessionManager

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


class MessageResponse(BaseModel):
    role: str
    content: str
    metadata: Optional[dict] = None
    timestamp: str


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
        
        # Validate session if provided
        if session_id:
            session_manager = get_session_manager()
            info = session_manager.get_session_info(session_id)
            if not info:
                raise HTTPException(status_code=404, detail="Session not found")
            if info['service_type'] != 'summarizer':
                raise HTTPException(status_code=400, detail="Wrong service type for this session")
        
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


@app.post("/api/rag/ask")
async def ask_rag_assistant(
    request: RAGQuestionRequest,
    session_id: str = Header(None, alias="X-Session-ID")
):
    """Ask RAG assistant with specific PMCIDs"""
    try:
        logger.info(f"🤖 RAG question: {request.question[:100]}...")
        
        # Validate session if provided
        if session_id:
            session_manager = get_session_manager()
            info = session_manager.get_session_info(session_id)
            if not info:
                raise HTTPException(status_code=404, detail="Session not found")
            if info['service_type'] != 'rag_assistant':
                raise HTTPException(status_code=400, detail="Wrong service type for this session")
        
        # Get answer
        rag_service = get_rag_service()
        answer = await rag_service.ask(request.question, request.pmcids)
        
        # Save to session if provided
        if session_id:
            session_manager.add_message(
                session_id=session_id,
                role='user',
                content=request.question,
                metadata={'pmcids': request.pmcids}
            )
            
            session_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=answer['answer'],
                metadata={
                    'citations': answer.get('citations', []),
                    'confidence': answer.get('confidence'),
                    'tools_used': answer.get('tools_used', [])
                }
            )
        
        logger.info(f" RAG answer generated with {len(answer.get('citations', []))} citations")
        return answer
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/generic")
async def ask_generic_rag(
    request: GenericRAGRequest,
    session_id: str = Header(None, alias="X-Session-ID")
):
    """Ask generic RAG (AI autonomously searches and uses tools)"""
    try:
        logger.info(f" Generic RAG question: {request.question[:100]}...")
        
        # Validate session if provided
        if session_id:
            session_manager = get_session_manager()
            info = session_manager.get_session_info(session_id)
            if not info:
                raise HTTPException(status_code=404, detail="Session not found")
            if info['service_type'] != 'generic_rag':
                raise HTTPException(status_code=400, detail="Wrong service type for this session")
        
        # Just pass the question - AI handles the rest!
        generic_rag_service = get_generic_rag_service()
        answer = await generic_rag_service.ask(request.question)
        
        # Save to session if provided
        if session_id:
            session_manager.add_message(
                session_id=session_id,
                role='user',
                content=request.question,
                metadata={}
            )
            
            session_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=answer['answer'],
                metadata={
                    'citations': answer.get('citations', []),
                    'tools_used': answer.get('tools_used', []),
                    'reasoning_trace': answer.get('reasoning_trace', []),
                    'confidence': answer.get('confidence')
                }
            )
        
        logger.info(f" Generic RAG answer generated with {len(answer.get('citations', []))} citations")
        return answer
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Generic RAG error: {e}")
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
            "generic_rag": "/api/rag/generic"
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