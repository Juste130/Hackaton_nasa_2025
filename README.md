# NASA Space Biology Knowledge Graph and AI Services

A comprehensive system for analyzing NASA space biology publications using knowledge graphs, semantic search, and AI-powered research assistance.

## Overview

This project provides intelligent analysis of NASA space biology research through:
- **Knowledge Graph**: Neo4j-based graph database for research relationships
- **Hybrid Search**: Semantic and keyword search capabilities
- **AI Assistants**: Multiple specialized AI services for different research tasks
- **Session Management**: Persistent conversation sessions
- **REST API**: FastAPI-based web services

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Neo4j       │    │   Vector DB     │
│  Publications   │    │ Knowledge Graph │    │   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              AI Services Layer                  │
         │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
         │  │ Summarizer  │ │ RAG Assistant│ │Generic RAG  ││
         │  └─────────────┘ └─────────────┘ └─────────────┘│
         └─────────────────────────────────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │                FastAPI                          │
         │              REST API                           │
         └─────────────────────────────────────────────────┘
```

## Components

### 1. Data Layer
- **PostgreSQL**: Stores publication metadata, authors, text sections
- **Neo4j**: Knowledge graph with entities and relationships
- **Vector Database**: Semantic embeddings for similarity search

### 2. AI Services
- **Summarizer**: Generates structured summaries of scientific articles
- **RAG Assistant**: Multi-hop reasoning with specified publications
- **Generic RAG**: Autonomous research assistant with tool selection

### 3. Search Engine
- **Hybrid Search**: Combines semantic similarity and keyword matching
- **Entity Search**: Find publications by organisms, phenomena, MeSH terms
- **Related Articles**: Semantic relationship discovery

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL
- Neo4j Database
- Virtual environment tool (venv or conda)

### Setup

1. **Clone repository**
```bash
git clone <repository-url>
cd nasa
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
Create `.env` file with:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/nasa_publications
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
MISTRAL_API_KEY=your-mistral-api-key
```



## API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
Most endpoints require API key or session management. Include session ID in headers when using sessions:
```
X-Session-ID: your-session-id
```

## Session Management

### Create Session
**POST** `/api/sessions`

Create a new conversation session for a specific AI service.

**Request Body:**
```json
{
  "service_type": "summarizer | rag_assistant | generic_rag",
  "metadata": {
    "user_id": "optional",
    "project": "optional"
  }
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "service_type": "generic_rag",
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Get Session History
**GET** `/api/sessions/{session_id}/history`

Retrieve conversation history for a session.

**Query Parameters:**
- `limit` (optional): Maximum number of messages to return

**Response:**
```json
{
  "session_id": "uuid-string",
  "service_type": "generic_rag",
  "message_count": 4,
  "messages": [
    {
      "role": "user",
      "content": "What are the effects of microgravity?",
      "timestamp": "2024-01-01T10:00:00Z",
      "metadata": {}
    },
    {
      "role": "assistant", 
      "content": "Microgravity has significant effects...",
      "timestamp": "2024-01-01T10:00:05Z",
      "metadata": {
        "citations": ["PMC123456"],
        "confidence": "high"
      }
    }
  ]
}
```

### List Sessions
**GET** `/api/sessions`

List all sessions with optional filtering.

**Query Parameters:**
- `service_type` (optional): Filter by service type
- `limit` (optional): Maximum sessions to return (default: 50)

### Delete Session
**DELETE** `/api/sessions/{session_id}`

Delete a session and its history.

## AI Services

### Article Summarizer
**POST** `/api/summarize`

Generate structured summary of a scientific article.

**Headers:**
```
X-Session-ID: optional-session-id
```

**Request Body:**
```json
{
  "pmcid": "PMC1234567"
}
```

**Response:**
```json
{
  "pmcid": "PMC1234567",
  "summary": {
    "executive_summary": "Brief overview...",
    "key_findings": [
      "Finding 1",
      "Finding 2"
    ],
    "methodology": "Research approach description",
    "implications": "Significance and impact",
    "limitations": "Study limitations"
  },
  "metadata": {
    "title": "Article Title",
    "authors": ["Author 1", "Author 2"],
    "journal": "Journal Name",
    "publication_date": "2024-01-01"
  }
}
```

### RAG Assistant
**POST** `/api/rag/ask`

Ask questions about specific publications with multi-hop reasoning.

**Headers:**
```
X-Session-ID: optional-session-id
```

**Request Body:**
```json
{
  "question": "What are the main findings about bone density?",
  "pmcids": ["PMC1234567", "PMC7890123"]
}
```

**Response:**
```json
{
  "answer": "Based on the studies, bone density...",
  "citations": ["PMC1234567", "PMC7890123"],
  "confidence": "high",
  "tools_used": ["get_section_content", "get_related_articles"],
  "reasoning_trace": [
    "I need to examine bone density findings",
    "Retrieved Methods section from PMC1234567",
    "Found related studies on bone loss"
  ]
}
```

### Generic RAG
**POST** `/api/rag/generic`

Ask any research question - AI autonomously searches and uses tools.

**Headers:**
```
X-Session-ID: optional-session-id
```

**Request Body:**
```json
{
  "question": "What do we know about microgravity effects on the cardiovascular system?"
}
```

**Response:**
```json
{
  "answer": "Research shows that microgravity causes...",
  "citations": ["PMC1111111", "PMC2222222", "PMC3333333"],
  "confidence": "high",
  "tools_used": ["search_publications", "get_section_content", "search_by_phenomenon"],
  "reasoning_trace": [
    "I need to search for cardiovascular microgravity studies",
    "Found 5 relevant articles",
    "Examining cardiovascular changes in detail"
  ]
}
```

## Available Tools

The AI assistants have access to these research tools:

### Publication Tools
- **get_article_metadata**: Get title, authors, journal, abstract
- **get_article_sections**: List available sections in a paper
- **get_section_content**: Retrieve specific section content
- **get_article_authors**: Get detailed author information
- **get_related_articles**: Find semantically similar papers

### Search Tools
- **search_publications**: Hybrid semantic + keyword search
- **search_by_organism**: Find studies on specific organisms
- **search_by_phenomenon**: Find studies on phenomena (e.g., "microgravity")
- **search_by_mesh_term**: Search using medical subject headings

## Health Check

### Health Status
**GET** `/health`

Check API health and service availability.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "summarizer": "available",
    "rag_assistant": "available",
    "generic_rag": "available"
  },
  "llm": "mistral-small-latest",
  "version": "2.0.0"
}
```

### Root Endpoint
**GET** `/`

Get API information and available endpoints.

## Usage Examples

### Python Client Example

```python
import requests

# Create session
session_response = requests.post("http://localhost:8000/api/sessions", 
    json={"service_type": "generic_rag"})
session_id = session_response.json()["session_id"]

# Ask question
question_response = requests.post("http://localhost:8000/api/rag/generic",
    headers={"X-Session-ID": session_id},
    json={"question": "What are the effects of microgravity on bones?"})

print(question_response.json()["answer"])
print("Citations:", question_response.json()["citations"])
```

### JavaScript Client Example

```javascript
// Create session
const sessionResponse = await fetch('http://localhost:8000/api/sessions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({service_type: 'generic_rag'})
});
const {session_id} = await sessionResponse.json();

// Ask question
const questionResponse = await fetch('http://localhost:8000/api/rag/generic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': session_id
  },
  body: JSON.stringify({
    question: 'What are the effects of microgravity on bones?'
  })
});

const result = await questionResponse.json();
console.log(result.answer);
console.log('Citations:', result.citations);
```

## Development

### Running the API
```bash
# Development mode with auto-reload
uvicorn api_ai:app --reload --port 8000

# Production mode
uvicorn api_ai:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run individual AI service tests
python test_generic_rag.py
python ai_rag_assistant.py
python ai_summarizer.py

# Test API endpoints
python test_api.py
```

### Adding New Tools

1. Create tool function in appropriate service file
2. Add citation tracking with `citation_tracker.add_pmcid()`
3. Register tool in ReAct agent tools list
4. Update documentation

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (session or resource)
- **500**: Internal Server Error

Error responses include details:
```json
{
  "detail": "Error description",
  "error_type": "validation_error"
}
```

## Performance

### Caching
- Services use singleton pattern for efficiency
- Database connections are pooled
- Embeddings are cached for repeated queries

### Scalability
- Stateless API design
- Session data stored in database
- Horizontal scaling supported

## Security

### API Security
- Environment variables for sensitive data
- Input validation on all endpoints
- Session-based access control

### Database Security
- Connection pooling with limits
- Prepared statements prevent SQL injection
- Neo4j authentication required

## Monitoring

### Logging
- Structured logging with timestamps
- Request/response tracking
- Error details and stack traces

### Metrics
- Response times logged
- Citation tracking
- Tool usage statistics

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

This project is developed for NASA space biology research analysis.