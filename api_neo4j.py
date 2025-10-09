"""
Neo4j Graph API Router for Knowledge Graph Visualization
Exposes graph structure for frontend visualization
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from enum import Enum
import logging
from neo4j_client import Neo4jClient
from neo4j_queries import KnowledgeGraphAnalytics
from search_engine import HybridSearchEngine, SearchMode
from neo4j.time import DateTime as Neo4jDateTime
from datetime import datetime
import asyncio
from redis_cache import get_cache

logger = logging.getLogger(__name__)

# Initialize clients
neo4j_client = Neo4jClient()
analytics = KnowledgeGraphAnalytics(neo4j_client)
search_engine = HybridSearchEngine()
cache = get_cache()

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])


# === Helper Functions for Serialization ===

def serialize_neo4j_types(obj):
    """
    Convert Neo4j types to Python native types for JSON serialization
    Handles Neo4j DateTime, Date, Time, and other special types
    """
    if isinstance(obj, Neo4jDateTime):
        # Convert Neo4j DateTime to ISO format string
        return obj.iso_format()
    elif isinstance(obj, dict):
        return {k: serialize_neo4j_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_neo4j_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(serialize_neo4j_types(item) for item in obj)
    return obj


# === Pydantic Models ===

class NodeType(str, Enum):
    PUBLICATION = "Publication"
    ORGANISM = "Organism"
    PHENOMENON = "Phenomenon"
    FINDING = "Finding"
    PLATFORM = "Platform"
    STRESSOR = "Stressor"
    AUTHOR = "Author"


class RelationType(str, Enum):
    STUDIES = "STUDIES"
    INVESTIGATES = "INVESTIGATES"
    REPORTS = "REPORTS"
    CONDUCTED_ON = "CONDUCTED_ON"
    EXPOSES_TO = "EXPOSES_TO"
    AUTHORED_BY = "AUTHORED_BY"
    AFFECTS = "AFFECTS"
    CAUSES = "CAUSES"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    BUILDS_ON = "BUILDS_ON"


class GraphNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Node type/label")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    size: Optional[int] = Field(None, description="Node size for visualization")
    color: Optional[str] = Field(None, description="Node color")


class GraphEdge(BaseModel):
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    weight: Optional[float] = Field(None, description="Edge weight for visualization")


class GraphData(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)


class SearchGraphRequest(BaseModel):
    query: str = Field(..., description="Search query")
    search_mode: str = Field("hybrid", description="semantic | keyword | hybrid")
    limit: int = Field(10, description="Max publications to include")
    include_related: bool = Field(True, description="Include related entities")
    max_depth: int = Field(2, description="Max relationship depth")


class FilterRequest(BaseModel):
    node_types: Optional[List[NodeType]] = Field(None, description="Filter by node types")
    relation_types: Optional[List[RelationType]] = Field(None, description="Filter by relation types")
    organism: Optional[str] = Field(None, description="Filter by organism")
    phenomenon: Optional[str] = Field(None, description="Filter by phenomenon")
    platform: Optional[str] = Field(None, description="Filter by platform")
    date_from: Optional[str] = Field(None, description="Filter publications from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter publications to date (YYYY-MM-DD)")
    limit: int = Field(100, description="Max nodes to return")


# === Helper Functions ===

def get_node_color(label: str) -> str:
    """Get color for node type"""
    colors = {
        "Publication": "#3498db",  # Blue
        "Organism": "#27ae60",     # Green
        "Phenomenon": "#e74c3c",   # Red
        "Finding": "#f39c12",      # Orange
        "Platform": "#9b59b6",     # Purple
        "Stressor": "#e67e22",     # Dark orange
        "Author": "#34495e"        # Dark gray
    }
    return colors.get(label, "#95a5a6")


def get_node_size(label: str, degree: int = 1) -> int:
    """Calculate node size based on type and degree"""
    base_sizes = {
        "Publication": 20,
        "Organism": 15,
        "Phenomenon": 15,
        "Finding": 10,
        "Platform": 12,
        "Stressor": 12,
        "Author": 8
    }
    base = base_sizes.get(label, 10)
    return min(base + (degree * 2), 50)  # Max size 50


def format_node(record: Dict) -> GraphNode:
    """Format Neo4j node record to GraphNode"""
    node = record.get('n', record)
    node_id = str(node.get('id', node.get('pmcid', node.get('name', 'unknown'))))
    labels = node.get('labels', [])
    label = labels[0] if labels else 'Unknown'
    
    # Clean properties and serialize Neo4j types
    properties = serialize_neo4j_types(dict(node))
    properties.pop('id', None)
    properties.pop('labels', None)
    
    # Calculate degree if available
    degree = record.get('degree', 1)
    
    return GraphNode(
        id=node_id,
        label=label,
        properties=properties,
        size=get_node_size(label, degree),
        color=get_node_color(label)
    )


def format_edge(record: Dict) -> GraphEdge:
    """Format Neo4j relationship record to GraphEdge"""
    rel = record.get('r', record)
    source_id = str(record.get('source_id', 'unknown'))
    target_id = str(record.get('target_id', 'unknown'))
    rel_type = record.get('rel_type', rel.get('type', 'RELATED'))
    
    # Clean properties and serialize Neo4j types
    properties = serialize_neo4j_types(dict(rel) if isinstance(rel, dict) else {})
    properties.pop('type', None)
    
    edge_id = f"{source_id}_{rel_type}_{target_id}"
    weight = properties.get('similarity', properties.get('confidence', 1.0))
    
    return GraphEdge(
        id=edge_id,
        source=source_id,
        target=target_id,
        type=rel_type,
        properties=properties,
        weight=float(weight) if weight else 1.0
    )


def get_id_property(label: str) -> str:
    """Get the ID property for a node label"""
    id_properties = {
        "Publication": "pmcid",
        "Organism": "scientific_name",
        "Phenomenon": "name",
        "Platform": "name",
        "Stressor": "name",
        "Author": "name"
    }
    return id_properties.get(label, "name")


# === API Endpoints ===

@router.get("/full", response_model=GraphData)
async def get_full_graph(
    limit: int = Query(100, description="Max nodes to return"),
    include_isolated: bool = Query(False, description="Include isolated nodes")
):
    """Get full knowledge graph with optional limit"""
    try:
        # Cache pour 15 minutes (900 secondes)
        cache_key = cache._generate_key('api:graph:full', limit=limit, include_isolated=include_isolated)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f" Using cached full graph (limit={limit}, isolated={include_isolated})")
            return cached_result
        logger.info(f" Fetching full graph from Neo4j (limit={limit}, isolated={include_isolated})...")
        
        with neo4j_client.driver.session() as session:
            # Get nodes with their degree (connection count)
            isolation_filter = "WHERE degree > 0" if not include_isolated else ""
            
            node_query = f"""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as degree
                {isolation_filter}
                RETURN n, degree, labels(n) as labels
                ORDER BY degree DESC
                LIMIT $limit
            """
            
            node_result = session.run(node_query, limit=limit)
            nodes = []
            node_ids = set()
            
            for record in node_result:
                node_data = dict(record['n'])
                node_data['labels'] = record['labels']
                node_data['degree'] = record['degree']
                
                node = format_node({'n': node_data, 'degree': record['degree']})
                nodes.append(node)
                node_ids.add(node.id)
            
            # Get edges between these nodes
            if node_ids:
                # Convert node IDs for query - use elementId() instead of id()
                internal_node_ids = []
                id_mapping = {}
                for node in nodes:
                    try:
                        # Get internal Neo4j element ID
                        internal_id_result = session.run(
                            f"MATCH (n:{node.label}) WHERE n.{get_id_property(node.label)} = $value RETURN elementId(n) as internal_id",
                            value=node.id
                        )
                        internal_record = internal_id_result.single()
                        if internal_record:
                            internal_id = internal_record['internal_id']
                            internal_node_ids.append(internal_id)
                            id_mapping[internal_id] = node.id
                    except Exception as e:
                        logger.warning(f"Failed to get internal ID for {node.id}: {e}")
                        continue
                
                edge_query = """
                    MATCH (source)-[r]->(target)
                    WHERE elementId(source) IN $node_ids AND elementId(target) IN $node_ids
                    RETURN elementId(source) as source_id, elementId(target) as target_id, 
                           type(r) as rel_type, r, labels(source)[0] as source_label,
                           labels(target)[0] as target_label
                    LIMIT 500
                """
                
                edge_result = session.run(edge_query, node_ids=internal_node_ids)
                edges = []
                
                for record in edge_result:
                    source_internal = record['source_id']
                    target_internal = record['target_id']
                    
                    if source_internal in id_mapping and target_internal in id_mapping:
                        edge_data = {
                            'source_id': id_mapping[source_internal],
                            'target_id': id_mapping[target_internal],
                            'rel_type': record['rel_type'],
                            'r': dict(record['r']) if record['r'] else {}
                        }
                        edges.append(format_edge(edge_data))
            else:
                edges = []
            
            stats = {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'node_types': {},
                'edge_types': {}
            }
            
            # Calculate stats
            for node in nodes:
                stats['node_types'][node.label] = stats['node_types'].get(node.label, 0) + 1
            
            for edge in edges:
                stats['edge_types'][edge.type] = stats['edge_types'].get(edge.type, 0) + 1
            
            # Serialize the entire response
            result = GraphData(nodes=nodes, edges=edges, stats=stats)
            serialized_result = serialize_neo4j_types(result.dict())
            
            # Cache pour 15 minutes
            cache.set(cache_key, serialized_result, ttl=900)
            
            return serialized_result
    
    except Exception as e:
        logger.error(f"Full graph error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=GraphData)
async def search_graph(request: SearchGraphRequest):
    """Get graph based on semantic/hybrid search"""
    try:
        # Perform search to get relevant publications
        search_results = await search_engine.search(
            query=request.query,
            mode=SearchMode(request.search_mode),
            limit=request.limit
        )
        
        if not search_results['results']:
            return GraphData(nodes=[], edges=[], stats={})
        
        # Get PMCIDs from search results
        pmcids = [result.pmcid for result in search_results['results']]
        
        with neo4j_client.driver.session() as session:
            # Build the graph from these publications
            nodes = []
            edges = []
            node_ids = set()
            
            # Get publication nodes
            pub_query = """
                MATCH (p:Publication)
                WHERE p.pmcid IN $pmcids
                RETURN p, elementId(p) as internal_id, labels(p) as labels
            """
            
            pub_result = session.run(pub_query, pmcids=pmcids)
            pub_mapping = {}  # internal_id -> pmcid
            
            for record in pub_result:
                pub_data = dict(record['p'])
                pub_data['labels'] = record['labels']
                
                node = format_node({'n': pub_data})
                nodes.append(node)
                node_ids.add(node.id)
                pub_mapping[record['internal_id']] = node.id
            
            if request.include_related and pub_mapping:
                # Get related entities up to max_depth
                internal_pub_ids = list(pub_mapping.keys())
                
                related_query = f"""
                    MATCH (p:Publication)-[r*1..{request.max_depth}]-(related)
                    WHERE elementId(p) IN $pub_ids AND labels(related)[0] <> 'Publication'
                    RETURN DISTINCT related, elementId(related) as internal_id, labels(related) as labels
                    LIMIT 200
                """
                
                related_result = session.run(related_query, pub_ids=internal_pub_ids)
                related_mapping = {}
                
                for record in related_result:
                    related_data = dict(record['related'])
                    related_data['labels'] = record['labels']
                    
                    node = format_node({'n': related_data})
                    if node.id not in node_ids:
                        nodes.append(node)
                        node_ids.add(node.id)
                        related_mapping[record['internal_id']] = node.id
                
                # Get all relationships
                all_internal_ids = list(pub_mapping.keys()) + list(related_mapping.keys())
                all_mapping = {**pub_mapping, **related_mapping}
                
                edge_query = """
                    MATCH (source)-[r]->(target)
                    WHERE elementId(source) IN $node_ids AND elementId(target) IN $node_ids
                    RETURN elementId(source) as source_id, elementId(target) as target_id,
                           type(r) as rel_type, r
                    LIMIT 1000
                """
                
                edge_result = session.run(edge_query, node_ids=all_internal_ids)
                
                for record in edge_result:
                    source_internal = record['source_id']
                    target_internal = record['target_id']
                    
                    if source_internal in all_mapping and target_internal in all_mapping:
                        edge_data = {
                            'source_id': all_mapping[source_internal],
                            'target_id': all_mapping[target_internal],
                            'rel_type': record['rel_type'],
                            'r': dict(record['r']) if record['r'] else {}
                        }
                        edges.append(format_edge(edge_data))
            
            # Add search relevance to publication nodes
            for i, node in enumerate(nodes):
                if node.label == "Publication":
                    # Find matching search result
                    for result in search_results['results']:
                        if result.pmcid == node.id:
                            node.properties['search_score'] = result.score
                            node.properties['search_rank'] = i + 1
                            break
            
            stats = {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'search_query': request.query,
                'search_mode': request.search_mode,
                'publications_found': len(pmcids),
                'node_types': {},
                'edge_types': {}
            }
            
            for node in nodes:
                stats['node_types'][node.label] = stats['node_types'].get(node.label, 0) + 1
            
            for edge in edges:
                stats['edge_types'][edge.type] = stats['edge_types'].get(edge.type, 0) + 1
            
            result = GraphData(nodes=nodes, edges=edges, stats=stats)
            return serialize_neo4j_types(result.dict())
    
    except Exception as e:
        logger.error(f"Search graph error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter", response_model=GraphData)
async def filter_graph(request: FilterRequest):
    """Get filtered graph based on criteria"""
    try:
        with neo4j_client.driver.session() as session:
            # Build filter conditions
            where_conditions = []
            params = {}
            
            if request.node_types:
                node_labels = [nt.value for nt in request.node_types]
                label_conditions = " OR ".join([f"'{label}' IN labels(n)" for label in node_labels])
                where_conditions.append(f"({label_conditions})")
            
            if request.organism:
                where_conditions.append(
                    "(toLower(n.name) CONTAINS toLower($organism) OR "
                    "toLower(n.scientific_name) CONTAINS toLower($organism))"
                )
                params['organism'] = request.organism
            
            if request.phenomenon:
                where_conditions.append("toLower(n.name) CONTAINS toLower($phenomenon)")
                params['phenomenon'] = request.phenomenon
            
            if request.platform:
                where_conditions.append("toLower(n.name) CONTAINS toLower($platform)")
                params['platform'] = request.platform
            
            if request.date_from or request.date_to:
                if request.date_from:
                    where_conditions.append("n.publication_date >= $date_from")
                    params['date_from'] = request.date_from
                if request.date_to:
                    where_conditions.append("n.publication_date <= $date_to")
                    params['date_to'] = request.date_to
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get filtered nodes
            node_query = f"""
                MATCH (n)
                {where_clause}
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as degree
                RETURN n, degree, labels(n) as labels
                ORDER BY degree DESC
                LIMIT $limit
            """
            
            params['limit'] = request.limit
            node_result = session.run(node_query, **params)
            
            nodes = []
            node_ids = set()
            internal_to_external = {}
            
            for record in node_result:
                node_data = dict(record['n'])
                node_data['labels'] = record['labels']
                
                node = format_node({'n': node_data, 'degree': record['degree']})
                nodes.append(node)
                node_ids.add(node.id)
            
            # Get edges between filtered nodes
            if nodes:
                # Get internal IDs for edge query
                for node in nodes:
                    id_prop = get_id_property(node.label)
                    internal_id_query = f"""
                        MATCH (n:{node.label})
                        WHERE n.{id_prop} = $value
                        RETURN elementId(n) as internal_id
                    """
                    result = session.run(internal_id_query, value=node.id)
                    record = result.single()
                    if record:
                        internal_to_external[record['internal_id']] = node.id
                
                edge_query = """
                    MATCH (source)-[r]->(target)
                    WHERE elementId(source) IN $node_ids AND elementId(target) IN $node_ids
                    RETURN elementId(source) as source_id, elementId(target) as target_id,
                           type(r) as rel_type, r
                """
                
                edge_result = session.run(edge_query, node_ids=list(internal_to_external.keys()))
                edges = []
                
                for record in edge_result:
                    source_internal = record['source_id']
                    target_internal = record['target_id']
                    
                    if source_internal in internal_to_external and target_internal in internal_to_external:
                        edge_data = {
                            'source_id': internal_to_external[source_internal],
                            'target_id': internal_to_external[target_internal],
                            'rel_type': record['rel_type'],
                            'r': dict(record['r']) if record['r'] else {}
                        }
                        edges.append(format_edge(edge_data))
            else:
                edges = []
            
            # Additional filtering for relationships
            if request.relation_types:
                allowed_types = [rt.value for rt in request.relation_types]
                edges = [edge for edge in edges if edge.type in allowed_types]
            
            stats = {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'filters_applied': {
                    'node_types': [nt.value for nt in request.node_types] if request.node_types else None,
                    'relation_types': [rt.value for rt in request.relation_types] if request.relation_types else None,
                    'organism': request.organism,
                    'phenomenon': request.phenomenon,
                    'platform': request.platform,
                    'date_range': f"{request.date_from} to {request.date_to}" if request.date_from or request.date_to else None
                },
                'node_types': {},
                'edge_types': {}
            }
            
            for node in nodes:
                stats['node_types'][node.label] = stats['node_types'].get(node.label, 0) + 1
            
            for edge in edges:
                stats['edge_types'][edge.type] = stats['edge_types'].get(edge.type, 0) + 1
            
            result = GraphData(nodes=nodes, edges=edges, stats=stats)
            return serialize_neo4j_types(result.dict())
    
    except Exception as e:
        logger.error(f"Filter graph error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}")
async def get_node_details(
    node_id: str,
    include_neighbors: bool = Query(True, description="Include neighboring nodes"),
    max_neighbors: int = Query(20, description="Max neighbors to include")
):
    """Get detailed information about a specific node and its neighbors"""
    try:
        with neo4j_client.driver.session() as session:
            # Find the node by trying different ID properties
            node = None
            for label in NodeType:
                id_prop = get_id_property(label.value)
                node_query = f"""
                    MATCH (n:{label.value})
                    WHERE n.{id_prop} = $node_id
                    RETURN n, labels(n) as labels, elementId(n) as internal_id
                """
                result = session.run(node_query, node_id=node_id)
                record = result.single()
                if record:
                    node_data = dict(record['n'])
                    node_data['labels'] = record['labels']
                    node = {
                        'node': format_node({'n': node_data}),
                        'internal_id': record['internal_id']
                    }
                    break
            
            if not node:
                raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
            result_data = {
                'node': node['node'],
                'neighbors': [],
                'relationships': []
            }
            
            if include_neighbors:
                # Get neighbors
                neighbor_query = """
                    MATCH (center)-[r]-(neighbor)
                    WHERE elementId(center) = $internal_id
                    RETURN neighbor, r, labels(neighbor) as labels,
                           elementId(neighbor) as neighbor_internal_id,
                           type(r) as rel_type,
                           startNode(r) = center as is_outgoing
                    LIMIT $max_neighbors
                """
                
                neighbor_result = session.run(
                    neighbor_query,
                    internal_id=node['internal_id'],
                    max_neighbors=max_neighbors
                )
                
                for record in neighbor_result:
                    neighbor_data = dict(record['neighbor'])
                    neighbor_data['labels'] = record['labels']
                    
                    neighbor_node = format_node({'n': neighbor_data})
                    result_data['neighbors'].append(neighbor_node)
                    
                    # Add relationship info
                    rel_data = {
                        'source_id': node_id if record['is_outgoing'] else neighbor_node.id,
                        'target_id': neighbor_node.id if record['is_outgoing'] else node_id,
                        'rel_type': record['rel_type'],
                        'r': dict(record['r']) if record['r'] else {}
                    }
                    result_data['relationships'].append(format_edge(rel_data))
            
            return serialize_neo4j_types(result_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node details error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats():
    """Get comprehensive graph statistics"""
    try:
        # Cache pour 10 minutes (600 secondes)
        cache_key = cache._generate_key('api:graph:stats')
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(" Using cached graph stats")
            return cached_result
        
        stats = neo4j_client.get_stats()
        
        # Add analytics data
        top_organisms = analytics.top_studied_organisms(limit=5)
        top_phenomena = analytics.top_investigated_phenomena(limit=5)
        research_gaps = analytics.research_gaps_by_system()
        
        result = {
            'database_stats': stats,
            'analytics': {
                'top_organisms': top_organisms,
                'top_phenomena': top_phenomena,
                'research_gaps': research_gaps[:5]
            },
            'visualization_info': {
                'recommended_limits': {
                    'small_graph': 50,
                    'medium_graph': 200,
                    'large_graph': 500
                },
                'node_colors': {
                    'Publication': '#3498db',
                    'Organism': '#27ae60',
                    'Phenomenon': '#e74c3c',
                    'Finding': '#f39c12',
                    'Platform': '#9b59b6',
                    'Stressor': '#e67e22',
                    'Author': '#34495e'
                }
            }
        }
        
        serialized_result = serialize_neo4j_types(result)
        
        # Cache pour 10 minutes
        cache.set(cache_key, serialized_result, ttl=600)
        
        return serialized_result
    
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for Neo4j connection"""
    try:
        is_connected = neo4j_client.verify_connectivity()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "neo4j_connected": is_connected
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }