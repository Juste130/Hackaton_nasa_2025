# NASA Space Biology Knowledge Graph & AI Services

A comprehensive AI-powered system for analyzing NASA space biology publications using knowledge graphs, semantic search, and intelligent research assistance.

## Overview

This project provides intelligent analysis of NASA space biology research through:
- **Knowledge Graph**: Neo4j-based graph database for research relationships
- **Hybrid Search**: Semantic and keyword search capabilities  
- **AI Assistants**: Multiple specialized AI services for different research tasks
- **Data Pipeline**: Automated extraction and enrichment from NCBI/PubMed
- **REST API**: FastAPI-based web services with session management

## Project Structure

```
nasa_final/
├── src/                      # Main source code
│   ├── data_pipeline/        # Data extraction & enrichment
│   │   ├── extractors/       # NCBI, PubMed extractors
│   │   └── enrichment/       # Entity extraction, annotation
│   ├── ai/                   # AI services & agents
│   │   ├── agents/           # RAG, summarization, generation
│   │   └── models/           # DSPy models, compiled extractors
│   ├── api/                  # REST API endpoints
│   │   └── routers/          # FastAPI routers
│   ├── database/             # Database clients & queries
│   ├── services/             # Core services (search, sessions)
│   └── utils/                # Utilities (cache, config)
├── tests/                    # Test suite
├── scripts/                  # Deployment & utility scripts
├── data/                     # Data files & annotations
├── docs/                     # Documentation & guides
└── requirements.txt          # Dependencies
```

## Quick Start

##  Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL
- Neo4j  
- Redis

### Installation

**Using UV (recommended)**
```bash
git clone <repository>
cd nasa_final
uv venv
source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt
```

**Traditional installation**
```bash
git clone <repository>
cd nasa_final
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your API keys and database URLs
```

### Database Setup
Create required databases and start services:
- PostgreSQL: Create database 'nasa_publications'
- Neo4j: Start Neo4j server
- Redis: Start Redis server

### Running the System

**Start API Server**
```bash
cd src/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Alternative: Interactive Main Menu**
```bash
python src/main.py
```

**Direct Module Execution**
```bash
# Run Data Pipeline
python src/data_pipeline/main.py

# Test AI Agents  
python src/ai/main.py
```

## Components

### Data Pipeline
- **NCBI Extractor**: Fetches publications from PubMed Central
- **Entity Extraction**: DSPy-powered biological entity recognition  
- **Batch Processing**: Optimized large-scale data processing

### AI Services
- **RAG Assistant**: Research question answering
- **Summarizer**: Publication summarization
- **Abstract Generator**: AI-generated abstracts
- **Generic RAG**: Flexible RAG for any domain

### API Endpoints
- `/api/graph/*` - Knowledge graph operations
- `/api/ai/*` - AI assistant services
- `/api/search/*` - Hybrid search functionality

### Knowledge Graph
Neo4j-based graph database containing:
- Publications, authors, institutions
- Biological entities (organisms, phenomena, systems)
- Research relationships and gaps

## Features

### Research Gap Analysis
Identifies missing research combinations and critical gaps for Mars missions through:
- Completeness matrix by biological system
- Priority scoring for future research
- Gap visualization and recommendations

### Intelligent Search
Multi-modal search capabilities:
- Semantic similarity search using AI embeddings
- Keyword-based filtering and exact matching
- Graph traversal queries for related research
- Session-based interaction tracking

### AI-Powered Analysis
Advanced AI services for research assistance:
- Publication summarization with key findings extraction
- Entity extraction and normalization
- Research recommendation based on knowledge gaps
- Abstract generation for new research proposals

## Performance

- **Database**: 608 NASA publications indexed
- **Knowledge Graph**: 10k+ entities, 50k+ relationships  
- **Search**: Sub-second semantic search
- **AI**: GPT-4 powered with specialized prompts

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Test specific components:
```bash
python tests/test_api.py
python tests/test_database.py
python tests/test_rag.py
```

## API Usage

**Start research session:**
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"service_type": "rag_assistant"}'
```

**Ask research question:**
```bash
curl -X POST http://localhost:8000/api/rag/ask \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your_session_id" \
  -d '{"question": "What are the effects of microgravity on muscle atrophy?"}'
```

**Search publications:**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "muscle atrophy microgravity", "mode": "hybrid", "limit": 10}'
```

**Get graph data:**
```bash
curl http://localhost:8000/api/graph/filter \
  -G -d "organism=Mus musculus" -d "phenomenon=muscle atrophy"
```

##  Performance

- **Database**: 608 NASA publications indexed
- **Knowledge Graph**: 10k+ entities, 50k+ relationships
- **Search**: Sub-second semantic search
- **AI**: GPT-4 powered with specialized prompts

## Development

### Adding New AI Agents
1. Create agent class in `src/ai/agents/`
2. Implement required interface methods
3. Add to `src/ai/main.py` testing
4. Create API endpoint in `src/api/routers/`

### Extending Data Pipeline
1. Add new extractor to `src/data_pipeline/extractors/`
2. Implement enrichment in `src/data_pipeline/enrichment/`
3. Update pipeline main in `src/data_pipeline/main.py`

### Database Schema Changes
1. Update models in `src/database/client.py`
2. Create migration in `data/migrations/`
3. Update Neo4j schema in `src/database/neo4j_schema.py`

## License

This project is developed for NASA space biology research purposes.

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Submit pull request

## Support

For issues and questions:
- Check existing issues in repository
- Review documentation in `docs/`
- Contact development team

---

Built for NASA space biology research