"""
Hybrid Search Engine for NASA Space Biology Publications
Combines semantic search (embeddings) + full-text search (PostgreSQL)
"""
import asyncio
from typing import List, Dict, Optional, Literal, Any
from enum import Enum
from dataclasses import dataclass
from embeddings_generator import EmbeddingsGenerator
from client import DatabaseClient, Publication
from sqlalchemy import text, select, func, or_
from sqlalchemy.dialects.postgresql import TSVECTOR
import logging
import json  # ← AJOUTEZ

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """Search strategy"""
    SEMANTIC = "semantic"           # Embedding similarity
    FULLTEXT = "fulltext"          # PostgreSQL tsvector
    HYBRID = "hybrid"              # Both combined


@dataclass
class SearchResult:
    """Unified search result"""
    pmcid: str
    title: str
    abstract: str
    journal: Optional[str]
    publication_date: Optional[str]
    score: float                    # Similarity or rank score
    search_method: str              # "semantic", "fulltext", or "hybrid"
    full_text_snippet: Optional[str] = None  # For fulltext results
    match_type: Optional[str] = None  # "exact", "similar", "related"
    doi: Optional[str] = None
    authors: Optional[str] = None
    first_affiliation: Optional[str] = None
    sections_count: Optional[int] = None
    keywords_text: Optional[str] = None
    mesh_terms_text: Optional[str] = None
    has_full_text: Optional[bool] = None
    matching_sections: Optional[int] = None
    organisms: Optional[List[str]] = None
    phenomena: Optional[List[str]] = None
    platforms: Optional[List[str]] = None


class HybridSearchEngine:
    """
    Advanced search engine with multiple strategies
    
    Features:
    - Semantic search via embeddings
    - Full-text search via PostgreSQL
    - Hybrid mode with score fusion
    - Pagination support
    - Filter by date, journal, organism, etc.
    """
    
    def __init__(self):
        self.embeddings_gen = EmbeddingsGenerator()
        self.db_client = DatabaseClient()
        self._should_close = True
    
    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        limit: int = 10,
        offset: int = 0,
        min_similarity: float = 0.3,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        journal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified search interface with input validation
        """
        # Validate query length
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "mode": mode.value,
                "results": [],
                "total_count": 0,
                "page": 1,
                "total_pages": 0,
                "has_next": False
            }
        
        query = query.strip()
        logger.info(f" Searching: '{query}' (mode={mode.value}, limit={limit}, offset={offset})")
        
        if mode == SearchMode.SEMANTIC:
            results = await self._semantic_search(
                query, limit, offset, min_similarity, year_from, year_to, journal
            )
        
        elif mode == SearchMode.FULLTEXT:
            results = await self._fulltext_search(
                query, limit, offset, year_from, year_to, journal
            )
        
        elif mode == SearchMode.HYBRID:
            results = await self._hybrid_search(
                query, limit, offset, min_similarity, year_from, year_to, journal
            )
        
        else:
            raise ValueError(f"Invalid search mode: {mode}")
        
        # Calculate pagination
        total_count = len(results)  # In real impl, count separately
        page = (offset // limit) + 1
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "query": query,
            "mode": mode.value,
            "results": results,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "has_next": offset + limit < total_count
        }
    
    async def _semantic_search(
        self,
        query: str,
        limit: int,
        offset: int,
        min_similarity: float,
        year_from: Optional[int],
        year_to: Optional[int],
        journal: Optional[str]
    ) -> List[SearchResult]:
        """
        Enhanced semantic search with corrected database schema
        """
        # Generate query embedding
        query_embedding = self.embeddings_gen.generate_embedding(query)
        embedding_json = json.dumps(query_embedding)
        
        async with self.db_client.async_session() as session:
            # Fixed SQL query - removed DISTINCT and fixed GROUP BY/ORDER BY mismatch
            sql = """
            SELECT
                p.pmcid, p.title, p.abstract, p.journal, p.publication_date,
                p.doi, p.full_text_content,
                1 - (p.embedding <=> CAST(:query_embedding AS vector)) as similarity,
                
                -- Authors (aggregated)
                COALESCE(
                    STRING_AGG(CONCAT(a.firstname, ' ', a.lastname), ', ') 
                    FILTER (WHERE a.lastname IS NOT NULL), 
                    ''
                ) as authors,
                
                -- First affiliation from publication_authors
                (SELECT pa2.affiliation 
                 FROM publication_authors pa2 
                 WHERE pa2.publication_id = p.id AND pa2.affiliation IS NOT NULL 
                 LIMIT 1) as first_affiliation,
                
                -- Text sections count
                (SELECT COUNT(*) FROM text_sections ts WHERE ts.publication_id = p.id) as sections_count,
                
                -- Keywords aggregated from related table
                COALESCE(
                    (SELECT STRING_AGG(k.keyword, ', ')
                     FROM publication_keywords pk
                     JOIN keywords k ON pk.keyword_id = k.id
                     WHERE pk.publication_id = p.id), 
                    ''
                ) as keywords_text,
                
                -- MeSH terms aggregated from related table
                COALESCE(
                    (SELECT STRING_AGG(mt.term, ', ')
                     FROM publication_mesh_terms pmt
                     JOIN mesh_terms mt ON pmt.mesh_term_id = mt.id
                     WHERE pmt.publication_id = p.id), 
                    ''
                ) as mesh_terms_text
                
            FROM publications p
            LEFT JOIN publication_authors pa ON p.id = pa.publication_id
            LEFT JOIN authors a ON pa.author_id = a.id
            WHERE p.embedding IS NOT NULL
              AND 1 - (p.embedding <=> CAST(:query_embedding AS vector)) > :min_similarity
            """
            
            params = {
                "query_embedding": embedding_json,
                "min_similarity": min_similarity,
                "limit": limit,
                "offset": offset
            }
            
            # Add filters
            if year_from:
                sql += " AND EXTRACT(YEAR FROM p.publication_date) >= :year_from"
                params["year_from"] = year_from
            
            if year_to:
                sql += " AND EXTRACT(YEAR FROM p.publication_date) <= :year_to"
                params["year_to"] = year_to
            
            if journal:
                sql += " AND LOWER(p.journal) LIKE LOWER(:journal)"
                params["journal"] = f"%{journal}%"
            
            sql += """
            GROUP BY p.id, p.pmcid, p.title, p.abstract, p.journal, p.publication_date,
                     p.doi, p.full_text_content, p.embedding
            ORDER BY 1 - (p.embedding <=> CAST(:query_embedding AS vector)) DESC
            LIMIT :limit OFFSET :offset
            """
            
            result = await session.execute(text(sql), params)
            
            search_results = []
            for row in result:
                # Enhanced SearchResult with more metadata
                search_result = SearchResult(
                    pmcid=row.pmcid,
                    title=row.title,
                    abstract=row.abstract[:300] + '...' if row.abstract and len(row.abstract) > 300 else row.abstract,
                    journal=row.journal,
                    publication_date=row.publication_date.isoformat() if row.publication_date else None,
                    score=round(row.similarity, 4),
                    search_method="semantic",
                    match_type="similar" if row.similarity < 0.7 else "highly_similar"
                )
                
                # Add extra metadata
                search_result.doi = row.doi
                search_result.authors = row.authors
                search_result.first_affiliation = row.first_affiliation
                search_result.sections_count = row.sections_count
                search_result.keywords_text = row.keywords_text
                search_result.mesh_terms_text = row.mesh_terms_text
                search_result.has_full_text = bool(row.full_text_content and len(row.full_text_content) > 100)
                
                search_results.append(search_result)
            
            return search_results
    
    async def _fulltext_search(
        self,
        query: str,
        limit: int,
        offset: int,
        year_from: Optional[int],
        year_to: Optional[int],
        journal: Optional[str]
    ) -> List[SearchResult]:
        """
        Enhanced full-text search with corrected database schema
        """
        async with self.db_client.async_session() as session:
            # Create tsquery from user input
            tsquery = ' & '.join(query.split())
            
            sql = """
            SELECT
                p.pmcid, p.title, p.abstract, p.journal, p.publication_date,
                p.doi, p.full_text_content,
                
                -- Full-text ranking across title, abstract, text sections, keywords, and mesh terms
                ts_rank(
                    to_tsvector('english', 
                        COALESCE(p.title, '') || ' ' || 
                        COALESCE(p.abstract, '') || ' ' ||
                        COALESCE(p.full_text_content, '') || ' ' ||
                        COALESCE((
                            SELECT STRING_AGG(ts.content, ' ') 
                            FROM text_sections ts 
                            WHERE ts.publication_id = p.id
                        ), '') || ' ' ||
                        COALESCE((
                            SELECT STRING_AGG(k.keyword, ' ')
                            FROM publication_keywords pk
                            JOIN keywords k ON pk.keyword_id = k.id
                            WHERE pk.publication_id = p.id
                        ), '') || ' ' ||
                        COALESCE((
                            SELECT STRING_AGG(mt.term, ' ')
                            FROM publication_mesh_terms pmt
                            JOIN mesh_terms mt ON pmt.mesh_term_id = mt.id
                            WHERE pmt.publication_id = p.id
                        ), '')
                    ),
                    to_tsquery('english', :tsquery)
                ) AS rank,
                
                -- Enhanced snippet from multiple sources
                CASE 
                    WHEN to_tsvector('english', COALESCE(p.abstract, '')) @@ to_tsquery('english', :tsquery)
                    THEN ts_headline('english', p.abstract, to_tsquery('english', :tsquery), 'MaxWords=50, MinWords=20')
                    WHEN to_tsvector('english', COALESCE(p.title, '')) @@ to_tsquery('english', :tsquery)
                    THEN ts_headline('english', p.title, to_tsquery('english', :tsquery), 'MaxWords=30')
                    ELSE ts_headline('english', 
                        COALESCE(p.full_text_content, p.abstract, p.title), 
                        to_tsquery('english', :tsquery),
                        'MaxWords=50, MinWords=20'
                    )
                END AS snippet,
                
                -- Authors
                COALESCE(
                    STRING_AGG(CONCAT(a.firstname, ' ', a.lastname), ', ') 
                    FILTER (WHERE a.lastname IS NOT NULL), 
                    ''
                ) as authors,
                
                -- Sections that match
                (SELECT COUNT(*) 
                 FROM text_sections ts2 
                 WHERE ts2.publication_id = p.id 
                   AND to_tsvector('english', ts2.content) @@ to_tsquery('english', :tsquery)
                ) as matching_sections,
                
                -- Keywords aggregated
                COALESCE(
                    (SELECT STRING_AGG(k.keyword, ', ')
                     FROM publication_keywords pk
                     JOIN keywords k ON pk.keyword_id = k.id
                     WHERE pk.publication_id = p.id), 
                    ''
                ) as keywords_text,
                
                -- MeSH terms aggregated
                COALESCE(
                    (SELECT STRING_AGG(mt.term, ', ')
                     FROM publication_mesh_terms pmt
                     JOIN mesh_terms mt ON pmt.mesh_term_id = mt.id
                     WHERE pmt.publication_id = p.id), 
                    ''
                ) as mesh_terms_text
                
            FROM publications p
            LEFT JOIN publication_authors pa ON p.id = pa.publication_id
            LEFT JOIN authors a ON pa.author_id = a.id
            WHERE (
                to_tsvector('english', COALESCE(p.title, '') || ' ' || COALESCE(p.abstract, ''))
                @@ to_tsquery('english', :tsquery)
                OR 
                to_tsvector('english', COALESCE(p.full_text_content, ''))
                @@ to_tsquery('english', :tsquery)
                OR 
                EXISTS (
                    SELECT 1 FROM text_sections ts 
                    WHERE ts.publication_id = p.id 
                      AND to_tsvector('english', ts.content) @@ to_tsquery('english', :tsquery)
                )
                OR
                EXISTS (
                    SELECT 1 FROM publication_keywords pk
                    JOIN keywords k ON pk.keyword_id = k.id
                    WHERE pk.publication_id = p.id 
                      AND to_tsvector('english', k.keyword) @@ to_tsquery('english', :tsquery)
                )
                OR
                EXISTS (
                    SELECT 1 FROM publication_mesh_terms pmt
                    JOIN mesh_terms mt ON pmt.mesh_term_id = mt.id
                    WHERE pmt.publication_id = p.id 
                      AND to_tsvector('english', mt.term) @@ to_tsquery('english', :tsquery)
                )
            )
            """
            
            params = {
                "tsquery": tsquery,
                "limit": limit,
                "offset": offset
            }
            
            # Add filters
            if year_from:
                sql += " AND EXTRACT(YEAR FROM p.publication_date) >= :year_from"
                params["year_from"] = year_from
            
            if year_to:
                sql += " AND EXTRACT(YEAR FROM p.publication_date) <= :year_to"
                params["year_to"] = year_to
            
            if journal:
                sql += " AND LOWER(p.journal) LIKE LOWER(:journal)"
                params["journal"] = f"%{journal}%"
            
            sql += """
            GROUP BY p.id, p.pmcid, p.title, p.abstract, p.journal, p.publication_date,
                     p.doi, p.full_text_content
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
            """
            
            result = await session.execute(text(sql), params)
            
            search_results = []
            for row in result:
                search_result = SearchResult(
                    pmcid=row.pmcid,
                    title=row.title,
                    abstract=row.abstract[:300] + '...' if row.abstract and len(row.abstract) > 300 else row.abstract,
                    journal=row.journal,
                    publication_date=row.publication_date.isoformat() if row.publication_date else None,
                    score=round(float(row.rank), 4),
                    search_method="fulltext",
                    full_text_snippet=row.snippet,
                    match_type="exact_match"
                )
                
                # Enhanced metadata
                search_result.doi = row.doi
                search_result.authors = row.authors
                search_result.matching_sections = row.matching_sections
                search_result.keywords_text = row.keywords_text
                search_result.mesh_terms_text = row.mesh_terms_text
                search_result.has_full_text = bool(row.full_text_content and len(row.full_text_content) > 100)
                
                search_results.append(search_result)
            
            return search_results
    
    async def _hybrid_search(
        self,
        query: str,
        limit: int,
        offset: int,
        min_similarity: float,
        year_from: Optional[int],
        year_to: Optional[int],
        journal: Optional[str]
    ) -> List[SearchResult]:
        """
        Hybrid search: Combine semantic + fulltext
        Uses Reciprocal Rank Fusion (RRF) for score merging
        """
        # Get results from both methods
        semantic_results = await self._semantic_search(
            query, limit * 2, 0, min_similarity, year_from, year_to, journal
        )
        
        fulltext_results = await self._fulltext_search(
            query, limit * 2, 0, year_from, year_to, journal
        )
        
        # Reciprocal Rank Fusion (RRF)
        # Score = 1 / (k + rank), k=60 is standard
        k = 60
        rrf_scores = {}
        
        # Add semantic scores
        for rank, result in enumerate(semantic_results, 1):
            pmcid = result.pmcid
            rrf_scores[pmcid] = rrf_scores.get(pmcid, 0) + 1 / (k + rank)
        
        # Add fulltext scores
        for rank, result in enumerate(fulltext_results, 1):
            pmcid = result.pmcid
            rrf_scores[pmcid] = rrf_scores.get(pmcid, 0) + 1 / (k + rank)
        
        # Merge results and sort by RRF score
        merged = {}
        for result in semantic_results + fulltext_results:
            if result.pmcid not in merged:
                merged[result.pmcid] = result
                # Update score to RRF score
                merged[result.pmcid].score = round(rrf_scores[result.pmcid], 4)
                merged[result.pmcid].search_method = "hybrid"
        
        # Sort by RRF score and paginate
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_results[offset:offset + limit]
    
    async def search_with_graph_context(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        limit: int = 10,
        include_related: bool = True
    ) -> Dict:
        """
        Search with Neo4j graph context
        Returns results + related entities from knowledge graph
        """
        # Get search results
        search_response = await self.search(query, mode, limit)
        
        if not include_related:
            return search_response
        
        # For each result, fetch related entities from Neo4j
        from neo4j_client import Neo4jClient
        neo4j_client = Neo4jClient()
        
        try:
            for result in search_response["results"]:
                pmcid = result.pmcid
                
                # Get related entities
                with neo4j_client.driver.session() as session:
                    cypher = """
                    MATCH (p:Publication {pmcid: $pmcid})
                    OPTIONAL MATCH (p)-[:STUDIES]->(o:Organism)
                    OPTIONAL MATCH (p)-[:INVESTIGATES]->(ph:Phenomenon)
                    OPTIONAL MATCH (p)-[:CONDUCTED_ON]->(pl:Platform)
                    RETURN 
                        collect(DISTINCT o.scientific_name) AS organisms,
                        collect(DISTINCT ph.name) AS phenomena,
                        collect(DISTINCT pl.name) AS platforms
                    """
                    
                    graph_result = session.run(cypher, pmcid=pmcid).single()
                    
                    if graph_result:
                        result.organisms = graph_result["organisms"]
                        result.phenomena = graph_result["phenomena"]
                        result.platforms = graph_result["platforms"]
        
        finally:
            neo4j_client.close()
        
        return search_response
    
    async def close(self):
        """Cleanup connections - but avoid aggressive closing in Streamlit"""
        try:
            # Only close if we're not in a cached context
            if hasattr(self, '_should_close') and self._should_close:
                await self.db_client.close()
                await self.embeddings_gen.db_client.close()
        except Exception as e:
            # Silently ignore cleanup errors in interactive contexts
            pass


async def demo_search():
    """Demo of all search modes"""
    engine = HybridSearchEngine()
    
    try:
        test_queries = [
            "bone density loss in microgravity",
            "immune system changes",
            "muscle atrophy"
        ]
        
        for query in test_queries:
            print(f"\n{'='*70}")
            print(f" Query: '{query}'")
            print(f"{'='*70}\n")
            
            # 1. Semantic Search
            print(" SEMANTIC SEARCH (embedding similarity)")
            print("-" * 70)
            results = await engine.search(query, mode=SearchMode.SEMANTIC, limit=3)
            for i, result in enumerate(results["results"], 1):
                print(f"{i}. {result.title[:60]}...")
                print(f"   Score: {result.score} | PMCID: {result.pmcid}")
            
            # 2. Full-Text Search
            print("\n FULL-TEXT SEARCH (keyword matching)")
            print("-" * 70)
            results = await engine.search(query, mode=SearchMode.FULLTEXT, limit=3)
            for i, result in enumerate(results["results"], 1):
                print(f"{i}. {result.title[:60]}...")
                print(f"   Score: {result.score} | Snippet: {result.full_text_snippet[:80]}...")
            
            # 3. Hybrid Search
            print("\n HYBRID SEARCH (combined)")
            print("-" * 70)
            results = await engine.search(query, mode=SearchMode.HYBRID, limit=3)
            for i, result in enumerate(results["results"], 1):
                print(f"{i}. {result.title[:60]}...")
                print(f"   Score: {result.score} | Method: {result.search_method}")
            
            print()
    
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(demo_search())