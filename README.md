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
REDIS_URL=redis://localhost:6379/0
```


## Running the Application

### Backend API Server
```bash
# Development mode with auto-reload
uvicorn api_ai:app --reload --port 8000

# Production mode
uvicorn api_ai:app --host 0.0.0.0 --port 8000

# Alternative: using main.py
python main.py
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
- **Interactive API**: http://localhost:8000/redoc
- **Graph Visualization**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## Complete API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
Include session ID in headers when using sessions:
```
X-Session-ID: your-session-id
```

---

## 📊 Core API Routes

### Root & Health
```bash
# API information and available endpoints
GET /

# Health check for all services
GET /health
```

**Example Response:**
```json
{
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
```

---

## 💬 Session Management Routes

### Create Session
**POST** `/api/sessions`

Create a new conversation session for a specific AI service.

**Request Body:**
```json
{
  "service_type": "summarizer | rag_assistant | generic_rag | search",
  "metadata": {
    "user_id": "optional",
    "project": "optional"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "generic_rag",
    "metadata": {"project": "bone_research"}
  }'
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "service_type": "generic_rag",
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Get Session History
**GET** `/api/sessions/{session_id}/history`

**Query Parameters:**
- `limit` (optional): Maximum messages to return

**cURL Example:**
```bash
curl "http://localhost:8000/api/sessions/550e8400-e29b-41d4-a716-446655440000/history?limit=10"
```

### List All Sessions
**GET** `/api/sessions`

**Query Parameters:**
- `service_type` (optional): Filter by service type
- `limit` (optional, default: 50): Maximum sessions to return

**cURL Example:**
```bash
curl "http://localhost:8000/api/sessions?service_type=generic_rag&limit=20"
```

### Delete Session
**DELETE** `/api/sessions/{session_id}`

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/sessions/550e8400-e29b-41d4-a716-446655440000"
```

---

## 📄 AI Services Routes

### Article Summarizer
**POST** `/api/summarize`

Generate structured summary of a scientific article.

**Request Body:**
```json
{
  "pmcid": "PMC1234567"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id" \
  -d '{"pmcid": "PMC1234567"}'
```

**Response:**
```json
{
  "pmcid": "PMC1234567",
  "summary": {
    "executive_summary": "This study investigates the effects of microgravity...",
    "key_findings": [
      "Bone density decreased by 15% after 6 months",
      "Calcium metabolism significantly altered"
    ],
    "methodology": "Longitudinal study with 20 astronauts over 12 months",
    "organisms_studied": "Human subjects",
    "space_relevance": "Directly applicable to long-duration spaceflight",
    "future_directions": "Investigate countermeasures and prevention strategies"
  },
  "metadata": {
    "title": "Bone Loss in Long-Duration Spaceflight",
    "authors": ["Smith, J.", "Johnson, M."],
    "journal": "Space Medicine & Biology",
    "publication_date": "2024-01-01"
  }
}
```

### RAG Assistant (Specific Publications)
**POST** `/api/rag/ask`

Ask questions about specific publications with multi-hop reasoning.

**Request Body:**
```json
{
  "question": "What are the main findings about bone density changes?",
  "pmcids": ["PMC1234567", "PMC7890123"]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id" \
  -d '{
    "question": "What are the protective mechanisms against radiation?",
    "pmcids": ["PMC1234567", "PMC2345678"]
  }'
```

### Generic RAG (Autonomous Research)
**POST** `/api/rag/generic`

Ask any research question - AI autonomously searches and uses tools.

**Request Body:**
```json
{
  "question": "What do we know about cardiovascular changes in microgravity?"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/rag/generic" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id" \
  -d '{
    "question": "How does microgravity affect the immune system in mice?"
  }'
```

**Response (both RAG endpoints):**
```json
{
  "role": "assistant",
  "content": "Based on multiple studies, cardiovascular changes in microgravity include...",
  "metadata": {
    "citations": ["PMC1111111", "PMC222222"],
    "confidence": "high",
    "tools_used": ["search_publications", "get_section_content"],
    "reasoning_trace": [
      "Searching for cardiovascular microgravity studies",
      "Found 8 relevant publications",
      "Analyzing cardiovascular adaptation mechanisms"
    ]
  },
  "timestamp": "2024-01-01T10:05:30Z"
}
```

---

## 🔍 Search Engine Routes

### Hybrid Search
**POST** `/api/search`

Advanced search with semantic understanding, keyword matching, and filtering.

**Request Body:**
```json
{
  "query": "bone loss in microgravity",
  "mode": "hybrid",
  "limit": 10,
  "page": 1,
  "min_similarity": 0.3,
  "year_from": 2020,
  "year_to": 2024,
  "journal": "Space Medicine",
  "include_graph_context": false
}
```

**Search Modes (dropdown in Swagger UI):**
- `semantic`: Conceptual similarity using AI embeddings
- `fulltext`: Exact keyword matching
- `hybrid`: Combined approach (recommended)

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id" \
  -d '{
    "query": "muscle atrophy countermeasures",
    "mode": "hybrid",
    "limit": 15,
    "page": 1,
    "min_similarity": 0.4,
    "year_from": 2018
  }'
```

**Response:**
```json
{
  "query": "bone loss in microgravity",
  "mode": "hybrid",
  "results": [
    {
      "pmcid": "PMC1234567",
      "title": "Effects of Microgravity on Bone Density",
      "abstract": "This study examines changes in bone mineral density...",
      "journal": "Space Medicine & Biology",
      "publication_date": "2023-06-15",
      "score": 0.85,
      "search_method": "hybrid",
      "match_type": "highly_similar",
      "doi": "10.1000/space.2023.001",
      "authors": "Smith, J., Johnson, M., Brown, K.",
      "keywords_text": "microgravity, bone loss, calcium metabolism",
      "mesh_terms_text": "Bone Density, Weightlessness, Space Flight",
      "has_full_text": true,
      "sections_count": 8,
      "full_text_snippet": "Results showed significant <b>bone loss</b> in <b>microgravity</b> conditions..."
    }
  ],
  "total_count": 45,
  "page": 1,
  "limit": 10,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false,
  "filters_applied": {
    "year_from": 2020,
    "min_similarity": 0.3
  }
}
```

### Search Filters
**GET** `/api/search/filters`

Get available filter options and statistics for search interface.

**cURL Example:**
```bash
curl "http://localhost:8000/api/search/filters"
```

**Response:**
```json
{
  "journals": [
    {"name": "Space Medicine & Biology", "count": 45},
    {"name": "Microgravity Science", "count": 32}
  ],
  "year_range": {
    "min_year": 2010,
    "max_year": 2024
  },
  "yearly_distribution": [
    {"year": 2024, "count": 12},
    {"year": 2023, "count": 28}
  ],
  "top_keywords": [
    {"keyword": "microgravity", "count": 156},
    {"keyword": "bone loss", "count": 89}
  ],
  "top_mesh_terms": [
    {"term": "Weightlessness", "count": 134},
    {"term": "Space Flight", "count": 98}
  ],
  "search_modes": [
    {"value": "semantic", "name": "Semantic Search", "description": "Find conceptually similar content"},
    {"value": "fulltext", "name": "Full-Text Search", "description": "Exact keyword matching"},
    {"value": "hybrid", "name": "Hybrid Search", "description": "Combined semantic + keyword search"}
  ]
}
```

---

## 🕸️ Knowledge Graph Routes

### Get Full Graph
**GET** `/api/graph/full`

Retrieve complete knowledge graph with optional filtering.

**Query Parameters:**
- `limit` (int, default: 100): Maximum nodes to return
- `include_isolated` (bool, default: false): Include nodes with no connections

**cURL Example:**
```bash
curl "http://localhost:8000/api/graph/full?limit=50&include_isolated=false"
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

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/graph/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cardiovascular adaptation space",
    "search_mode": "semantic",
    "limit": 8,
    "include_related": true,
    "max_depth": 1
  }'
```

### Filter Graph
**POST** `/api/graph/filter`

Get filtered graph based on multiple criteria.

**Available Node Types (dropdown):**
- `Publication`
- `Organism` 
- `Phenomenon`
- `Finding`
- `Platform`
- `Stressor`
- `Author`

**Available Relation Types (dropdown):**
- `STUDIES`
- `INVESTIGATES`
- `REPORTS`
- `CONDUCTED_ON`
- `EXPOSES_TO`
- `AUTHORED_BY`
- `AFFECTS`
- `CAUSES`

**Request Body:**
```json
{
  "node_types": ["Publication", "Organism"],
  "relation_types": ["STUDIES", "INVESTIGATES"],
  "organism": "mouse",
  "phenomenon": "bone loss",
  "platform": "International Space Station",
  "date_from": "2020-01-01",
  "date_to": "2023-12-31",
  "limit": 100
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/graph/filter" \
  -H "Content-Type: application/json" \
  -d '{
    "node_types": ["Publication", "Organism"],
    "organism": "rat",
    "date_from": "2019-01-01",
    "limit": 75
  }'
```

### Node Details
**GET** `/api/graph/node/{node_id}`

Get detailed information about a specific node and its neighbors.

**Query Parameters:**
- `include_neighbors` (bool, default: true): Include connected nodes
- `max_neighbors` (int, default: 20): Maximum neighbors to return

**cURL Example:**
```bash
curl "http://localhost:8000/api/graph/node/PMC1234567?include_neighbors=true&max_neighbors=15"
```

### Graph Statistics
**GET** `/api/graph/stats`

Get comprehensive graph statistics and analytics.

**cURL Example:**
```bash
curl "http://localhost:8000/api/graph/stats"
```

**Response:**
```json
{
  "database_stats": {
    "Publication": 608,
    "Organism": 145,
    "Phenomenon": 89,
    "Platform": 23,
    "Stressor": 45,
    "Author": 1250
  },
  "analytics": {
    "top_organisms": [
      {"name": "Mus musculus", "count": 85},
      {"name": "Rattus rattus", "count": 67}
    ],
    "top_phenomena": [
      {"name": "bone loss", "count": 45},
      {"name": "muscle atrophy", "count": 38}
    ],
    "research_gaps": [
      {"system": "cardiovascular", "gap_score": 0.75},
      {"system": "neurological", "gap_score": 0.68}
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
      "Organism": "#27ae60",
      "Phenomenon": "#e74c3c"
    }
  }
}
```

### Graph Health Check
**GET** `/api/graph/health`

Health check for Neo4j connection.

**cURL Example:**
```bash
curl "http://localhost:8000/api/graph/health"
```

---

## 🧰 Available AI Tools

The AI assistants automatically use these tools:

### Publication Analysis Tools
- **get_article_metadata**: Get title, authors, journal, abstract
- **get_article_sections**: List available sections in a paper
- **get_section_content**: Retrieve specific section content (Methods, Results, etc.)
- **get_article_authors**: Get detailed author information with affiliations
- **get_related_articles**: Find semantically similar papers

### Search & Discovery Tools
- **search_publications**: Hybrid semantic + keyword search across all content
- **search_by_organism**: Find studies on specific organisms (mouse, rat, human, etc.)
- **search_by_phenomenon**: Find studies on specific phenomena (bone loss, muscle atrophy, etc.)
- **search_by_mesh_term**: Search using medical subject headings

### Graph Analysis Tools
- **get_node_details**: Detailed node information with neighbor exploration
- **filter_graph**: Apply complex filters to graph data
- **search_graph**: Generate focused graphs from search queries

---

## 🌐 Frontend Visualization

### Access Frontend
```bash
# Start frontend server
python serve_frontend.py

# Open in browser
http://localhost:3000
```

### Interactive Features

#### Graph Navigation
- **Mouse Controls**: 
  - Drag nodes to reposition
  - Scroll to zoom in/out
  - Click and drag background to pan
- **Keyboard Shortcuts**:
  - `Ctrl+F`: Focus search input
  - `Ctrl+R`: Reload full graph
  - `Ctrl+C`: Center view
  - `Space`: Pause/resume physics simulation

#### Search & Filtering
- **Search Modes**: Hybrid (default), Semantic only, Keyword only
- **Node Type Filters**: Filter by Publications, Organisms, Phenomena, etc.
- **Text Filters**: Search by organism name, phenomenon, platform
- **Date Range**: Limit publications by publication date
- **Live Updates**: Graph updates in real-time without page refresh

#### Visual Elements
- **Color Coding**: 
  - Publications: Blue (#3498db)
  - Organisms: Green (#27ae60)
  - Phenomena: Red (#e74c3c)
  - Platforms: Purple (#9b59b6)
  - Authors: Gray (#34495e)
- **Node Sizing**: Based on connection degree and importance
- **Edge Thickness**: Relationship strength affects line weight
- **Smart Labels**: Show/hide based on zoom level
- **Tooltips**: Hover for detailed information

### Frontend Configuration

Modify API endpoint in `frontend/index.html`:
```javascript
const API_BASE = 'http://your-api-server:8000/api/graph';
```

---

## 📋 Usage Examples

### Complete Workflow Example

```bash
# 1. Create a research session
SESSION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{"service_type": "generic_rag", "metadata": {"project": "cardiovascular_research"}}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r .session_id)
echo "Session ID: $SESSION_ID"

# 2. Ask a research question
curl -X POST "http://localhost:8000/api/rag/generic" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{
    "question": "What are the main cardiovascular adaptations to long-duration spaceflight and what countermeasures have been tested?"
  }' | jq .

# 3. Search for related publications
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{
    "query": "cardiovascular countermeasures exercise",
    "mode": "hybrid",
    "limit": 5,
    "year_from": 2018
  }' | jq .

# 4. Get graph visualization for the topic
curl -X POST "http://localhost:8000/api/graph/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cardiovascular exercise countermeasures",
    "search_mode": "hybrid",
    "limit": 10,
    "include_related": true
  }' | jq .

# 5. Review session history
curl "http://localhost:8000/api/sessions/$SESSION_ID/history" | jq .
```

### Python Client Example

```python
import requests
import json

class NASAResearchClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def create_session(self, service_type="generic_rag", metadata=None):
        """Create a new research session"""
        response = requests.post(f"{self.base_url}/api/sessions", 
            json={"service_type": service_type, "metadata": metadata or {}})
        response.raise_for_status()
        self.session_id = response.json()["session_id"]
        return self.session_id
    
    def ask_question(self, question):
        """Ask a research question"""
        headers = {"X-Session-ID": self.session_id} if self.session_id else {}
        response = requests.post(f"{self.base_url}/api/rag/generic",
            headers=headers, json={"question": question})
        response.raise_for_status()
        return response.json()
    
    def search_publications(self, query, mode="hybrid", **kwargs):
        """Search publications with filters"""
        data = {"query": query, "mode": mode, **kwargs}
        response = requests.post(f"{self.base_url}/api/search", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_graph(self, query=None, limit=50):
        """Get graph visualization data"""
        if query:
            data = {"query": query, "limit": limit, "include_related": True}
            response = requests.post(f"{self.base_url}/api/graph/search", json=data)
        else:
            response = requests.get(f"{self.base_url}/api/graph/full?limit={limit}")
        response.raise_for_status()
        return response.json()

# Usage example
client = NASAResearchClient()
session_id = client.create_session(metadata={"researcher": "Dr. Smith"})

# Ask a research question
result = client.ask_question("What are the effects of microgravity on bone metabolism?")
print("Answer:", result["content"])
print("Citations:", result["metadata"]["citations"])

# Search for related papers
search_results = client.search_publications(
    "bone metabolism microgravity",
    mode="hybrid",
    year_from=2020,
    limit=10
)
print(f"Found {search_results['total_count']} publications")

# Get visualization data
graph_data = client.get_graph("bone metabolism")
print(f"Graph has {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
```

### JavaScript Frontend Integration

```javascript
class NASAGraphVisualizer {
    constructor(apiBase = 'http://localhost:8000/api/graph') {
        this.apiBase = apiBase;
    }
    
    async searchAndVisualize(query, mode = 'hybrid') {
        const response = await fetch(`${this.apiBase}/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: query,
                search_mode: mode,
                limit: 20,
                include_related: true,
                max_depth: 2
            })
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        const graphData = await response.json();
        this.renderGraph(graphData);
        return graphData;
    }
    
    async filterGraph(filters) {
        const response = await fetch(`${this.apiBase}/filter`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(filters)
        });
        
        const graphData = await response.json();
        this.renderGraph(graphData);
        return graphData;
    }
    
    async getNodeDetails(nodeId) {
        const response = await fetch(`${this.apiBase}/node/${nodeId}`);
        return await response.json();
    }
    
    renderGraph(data) {
        // D3.js rendering code here
        console.log(`Rendering ${data.nodes.length} nodes and ${data.edges.length} edges`);
        // Implementation details in frontend/index.html
    }
}

// Usage
const visualizer = new NASAGraphVisualizer();

// Search and visualize
visualizer.searchAndVisualize('cardiovascular microgravity')
    .then(data => console.log('Graph rendered:', data.stats));

// Filter by organism
visualizer.filterGraph({
    node_types: ['Publication', 'Organism'],
    organism: 'mouse',
    date_from: '2020-01-01'
});
```

---

## 🔧 Development & Testing

### API Testing Commands

```bash
# Test all endpoints quickly
./test_api.sh  # If you create this script

# Or manually test each endpoint:

# 1. Health check
curl http://localhost:8000/health

# 2. Create session
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{"service_type": "generic_rag"}'

# 3. Test search
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "bone loss", "mode": "hybrid", "limit": 3}'

# 4. Test AI service
curl -X POST "http://localhost:8000/api/rag/generic" \
  -H "Content-Type: application/json" \
  -d '{"question": "What causes bone loss in space?"}'

# 5. Test graph endpoints
curl "http://localhost:8000/api/graph/stats"
curl "http://localhost:8000/api/graph/full?limit=10"

# 6. Test summarizer
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{"pmcid": "PMC1234567"}'
```

### Environment Variables for Development

```bash
# .env file for development
DATABASE_URL=postgresql://user:pass@localhost:5432/nasa_dev
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
MISTRAL_API_KEY=your_dev_key
REDIS_URL=redis://localhost:6379/1
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Production Configuration

```bash
# .env file for production
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/nasa_prod
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=secure_password
MISTRAL_API_KEY=your_production_key
REDIS_URL=redis://prod_redis:6379/0
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 📈 Performance & Scaling

### Rate Limits (Production)
- Search endpoints: 100 requests/minute per IP
- AI services: 50 requests/minute per session
- Graph endpoints: 200 requests/minute per IP

### Caching Strategy
- **Search results**: 30 minutes
- **Graph data**: 15 minutes
- **Node details**: 10 minutes
- **Statistics**: 10 minutes

### Optimization Tips
- Use pagination for large result sets
- Enable graph context only when needed
- Cache session IDs for multiple requests
- Use appropriate search modes (semantic for concepts, fulltext for exact terms)

---

## 🐛 Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (session, publication, or node)
- **429**: Too Many Requests (rate limited)
- **500**: Internal Server Error
- **503**: Service Unavailable (AI services down)

### Common Error Responses

```json
{
  "detail": "Session not found",
  "status_code": 404
}
```

```json
{
  "detail": "Invalid search mode. Must be one of: semantic, fulltext, hybrid",
  "status_code": 400
}
```

---

## 🔐 Security Notes

### API Security
- No authentication required for read operations
- Session isolation prevents data leakage
- Input validation on all endpoints
- CORS enabled for frontend integration

### Data Privacy
- Sessions automatically expire after 30 days
- No personal data stored beyond session metadata
- Query content not logged in production

---