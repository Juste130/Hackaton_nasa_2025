# NASA Space Biology Knowledge Graph and AI Services

A comprehensive system for analyzing NASA space biology publications using knowledge graphs, semantic search, and AI-powered research assistance.

## Overview

This project provides intelligent analysis of NASA space biology research through:
- **Knowledge Graph**: Neo4j-based graph database for research relationships
- **Hybrid Search**: Semantic and keyword search capabilities
- **AI Assistants**: Multiple specialized AI services for different research tasks
- **Session Management**: Persistent conversation sessions
- **REST API**: FastAPI-based web services
- **Interactive Visualization**: D3.js-based graph explorer frontend

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
                                 │
         ┌─────────────────────────────────────────────────┐
         │              Frontend                           │
         │           D3.js Visualization                   │
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

### 4. Knowledge Graph API
- **Full Graph Export**: Retrieve complete or filtered graph data
- **Search-Based Graphs**: Generate graphs from semantic search results
- **Interactive Filtering**: Node types, organisms, phenomena, date ranges
- **Node Details**: Detailed information with neighbor exploration

### 5. Interactive Frontend
- **D3.js Visualization**: Force-directed graph with physics simulation
- **Drag & Drop**: Interactive node positioning with mouse
- **Zoom & Pan**: Navigate large graphs with smooth transitions
- **Real-time Filtering**: Dynamic graph updates based on search/filters
- **Node Details**: Tooltips and expandable information panels

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Neo4j Database (AuraDB or local instance)
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
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/nasa_publications
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
MISTRAL_API_KEY=your-mistral-api-key
```


## Running the Application

### Backend API Server
```bash
# Development mode with auto-reload
uvicorn api_ai:app --reload --port 8000

# Production mode
uvicorn api_ai:app --host 0.0.0.0 --port 8000
```

### Frontend Visualization
```bash
# Serve the frontend (separate terminal)
python serve_frontend.py

# Or with custom port
python serve_frontend.py --port 3001
```

### Access Points
- **API Documentation**: http://localhost:8000/docs
- **Graph Visualization**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
Include session ID in headers when using sessions:
```
X-Session-ID: your-session-id
```

## Knowledge Graph API

### Get Full Graph
**GET** `/api/graph/full`

Retrieve the complete knowledge graph with optional filtering.

**Query Parameters:**
- `limit` (int): Maximum nodes to return (default: 100)
- `include_isolated` (bool): Include nodes with no connections (default: false)

**Response:**
```json
{
  "nodes": [
    {
      "id": "PMC123456",
      "label": "Publication",
      "properties": {
        "title": "Effects of Microgravity on Bone Density",
        "journal": "Space Medicine",
        "publication_date": "2023-01-15"
      },
      "size": 25,
      "color": "#3498db"
    }
  ],
  "edges": [
    {
      "id": "PMC123456_STUDIES_mouse",
      "source": "PMC123456",
      "target": "mouse",
      "type": "STUDIES",
      "properties": {},
      "weight": 1.0
    }
  ],
  "stats": {
    "total_nodes": 150,
    "total_edges": 300,
    "node_types": {
      "Publication": 50,
      "Organism": 25,
      "Phenomenon": 30
    },
    "edge_types": {
      "STUDIES": 75,
      "INVESTIGATES": 60
    }
  }
}
```

### Search-Based Graph
**POST** `/api/graph/search`

Generate graph from semantic search results.

**Request Body:**
```json
{
  "query": "bone loss microgravity",
  "search_mode": "hybrid",
  "limit": 10,
  "include_related": true,
  "max_depth": 2
}
```

### Filter Graph
**POST** `/api/graph/filter`

Get filtered graph based on multiple criteria.

**Request Body:**
```json
{
  "node_types": ["Publication", "Organism"],
  "organism": "mouse",
  "phenomenon": "bone loss",
  "date_from": "2020-01-01",
  "date_to": "2023-12-31",
  "limit": 100
}
```

### Node Details
**GET** `/api/graph/node/{node_id}`

Get detailed information about a specific node and its neighbors.

**Query Parameters:**
- `include_neighbors` (bool): Include connected nodes (default: true)
- `max_neighbors` (int): Maximum neighbors to return (default: 20)

### Graph Statistics
**GET** `/api/graph/stats`

Get comprehensive graph statistics and analytics.

**Response:**
```json
{
  "database_stats": {
    "total_nodes": 1250,
    "total_relationships": 3400,
    "node_types": {
      "Publication": 500,
      "Organism": 150,
      "Phenomenon": 200
    }
  },
  "analytics": {
    "top_organisms": [
      {"name": "Mus musculus", "count": 45},
      {"name": "Rattus rattus", "count": 32}
    ],
    "top_phenomena": [
      {"name": "bone loss", "count": 28},
      {"name": "muscle atrophy", "count": 22}
    ],
    "research_gaps": [
      {"system": "cardiovascular", "gap_score": 0.85}
    ]
  },
  "visualization_info": {
    "recommended_limits": {
      "small_graph": 50,
      "medium_graph": 200,
      "large_graph": 500
    },
    "node_colors": {
      "Publication": "#3498db",
      "Organism": "#27ae60"
    }
  }
}
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

## Frontend Visualization

### Interactive Features

#### Graph Navigation
- **Mouse Controls**: Drag nodes to reposition, scroll to zoom
- **Keyboard Shortcuts**:
  - `Ctrl+F`: Focus search input
  - `Ctrl+R`: Reload full graph
  - `Ctrl+C`: Center view

#### Search & Filtering
- **Semantic Search**: Natural language queries like "bone loss in microgravity"
- **Search Modes**: Hybrid (default), Semantic only, Keyword only
- **Node Type Filters**: Publications, Organisms, Phenomena, Platforms
- **Text Filters**: Filter by organism name, phenomenon, platform
- **Date Filters**: Limit publications by date range

#### Visual Elements
- **Node Colors**: Color-coded by type (Publications: blue, Organisms: green, etc.)
- **Node Sizes**: Based on connection degree and node type
- **Edge Weights**: Relationship strength affects line thickness
- **Labels**: Smart labeling with truncation for readability
- **Tooltips**: Detailed information on hover
- **Legend**: Interactive color guide

#### Real-time Updates
- **Dynamic Loading**: Graphs update without page refresh
- **Statistics Panel**: Live node/edge counts and type distribution
- **Loading Indicators**: Progress feedback during data fetch
- **Error Handling**: User-friendly error messages

### Configuration

The frontend connects to the API at `http://localhost:8000` by default. To change this, modify the `API_BASE` constant in `frontend/index.html`:

```javascript
const API_BASE = 'http://your-api-server:8000/api/graph';
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

### Graph Tools
- **get_node_details**: Detailed node information with neighbors
- **filter_graph**: Apply complex filters to graph data
- **search_graph**: Generate graphs from search queries

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

# Get graph data
graph_response = requests.get("http://localhost:8000/api/graph/full?limit=50")
graph_data = graph_response.json()
print(f"Graph has {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
```

### JavaScript Client Example

```javascript
// Search and visualize graph
async function searchAndVisualize(query) {
  const searchResponse = await fetch('http://localhost:8000/api/graph/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      query: query,
      search_mode: 'hybrid',
      limit: 15,
      include_related: true
    })
  });
  
  const graphData = await searchResponse.json();
  
  // graphData contains nodes and edges ready for D3.js visualization
  console.log(`Found ${graphData.nodes.length} nodes`);
  console.log(`Search query: ${graphData.stats.search_query}`);
  
  return graphData;
}

// Use with D3.js
searchAndVisualize("cardiovascular effects of spaceflight")
  .then(data => renderGraph(data));
```

## Development

### Project Structure
```
nasa/
├── api_ai.py              # Main API with AI services
├── api_neo4j.py           # Knowledge graph API router
├── session_manager.py     # Session management
├── ai_summarizer.py       # Article summarization service
├── ai_rag_assistant.py    # RAG with specific PMCIDs
├── ai_generic_rag.py      # Autonomous RAG service
├── search_engine.py       # Hybrid search engine
├── neo4j_client.py        # Neo4j database client
├── neo4j_queries.py       # Analytics and complex queries
├── frontend/
│   └── index.html         # D3.js visualization interface
├── serve_frontend.py      # Frontend development server
├── requirements.txt       # Python dependencies
└── README.md
```

### Testing

```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/graph/stats

# Test graph endpoints
curl -X POST http://localhost:8000/api/graph/search \
  -H "Content-Type: application/json" \
  -d '{"query": "bone loss", "limit": 5}'

# Test AI services
curl -X POST http://localhost:8000/api/rag/generic \
  -H "Content-Type: application/json" \
  -d '{"question": "What causes bone loss in space?"}'
```

### Adding New Features

#### New Graph Filters
1. Add filter parameters to `FilterRequest` model in `api_neo4j.py`
2. Update filter logic in `filter_graph()` endpoint
3. Add corresponding UI controls in `frontend/index.html`

#### New Visualization Types
1. Extend the D3.js code in `frontend/index.html`
2. Add new rendering functions for different graph layouts
3. Update the stats and legend systems

#### New AI Tools
1. Create tool function in appropriate service file
2. Add citation tracking with `citation_tracker.add_pmcid()`
3. Register tool in ReAct agent tools list
4. Update API documentation

## Performance Optimization

### Backend
- **Connection Pooling**: Database connections are pooled and reused
- **Caching**: LLM responses and embeddings are cached
- **Async Operations**: Non-blocking I/O for better concurrency
- **Query Optimization**: Efficient Neo4j queries with proper indexing

### Frontend
- **Progressive Loading**: Large graphs load incrementally
- **Viewport Culling**: Only render visible nodes/edges
- **Throttled Updates**: Smooth animations without performance drops
- **Smart Labeling**: Labels appear/disappear based on zoom level

### Scalability
- **Stateless API**: Horizontal scaling supported
- **Session Storage**: Database-backed session management
- **Modular Services**: Individual components can be scaled independently

## Error Handling

### API Errors
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (session or resource)
- **500**: Internal Server Error
- **503**: Service Unavailable (AI services down)

### Frontend Errors
- **Network Errors**: Graceful fallback with retry options
- **Data Validation**: Client-side validation before API calls
- **User Feedback**: Clear error messages and loading states

## Security

### API Security
- **Environment Variables**: Sensitive data stored securely
- **Input Validation**: All endpoints validate input parameters
- **CORS Configuration**: Proper cross-origin request handling
- **Rate Limiting**: Planned feature for production deployment

### Data Security
- **Database Security**: Connection pooling with authentication
- **No Data Logging**: Sensitive query content not logged
- **Session Isolation**: User sessions are properly isolated

## Deployment

### Production Deployment
```bash
# Build production container
docker build -t nasa-ai-api .

# Run with production settings
docker run -p 8000:8000 --env-file .env nasa-ai-api

# Serve frontend with nginx
nginx -c /path/to/nginx.conf
```

### Environment Variables
Required for production:
```env
DATABASE_URL=postgresql://...
NEO4J_URI=neo4j+s://...
NEO4J_USERNAME=...
NEO4J_PASSWORD=...
MISTRAL_API_KEY=...
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes with proper testing
4. Update documentation and examples
5. Submit pull request with detailed description

### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **JavaScript**: Use modern ES6+ syntax
- **Documentation**: Update README for new features
- **Testing**: Add tests for new functionality

### Issue Reporting
- Use GitHub issues for bugs and feature requests
- Include reproduction steps and environment details
- Tag issues appropriately (bug, enhancement, documentation)

## License

This project is developed for NASA space biology research analysis.

## Acknowledgments

- NASA Space Biology Program for research data
- Neo4j for graph database technology
- D3.js community for visualization tools
- OpenAI and Mistral for AI capabilities