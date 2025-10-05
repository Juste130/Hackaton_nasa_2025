"""
Generate embeddings for publications using sentence-transformers
Vector store in PostgreSQL (pgvector) and Neo4j
"""
import asyncio
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import logging
from client import DatabaseClient, Publication, TextSection
from sqlalchemy.future import select
from sqlalchemy import update
import torch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingsGenerator:
    """Generate and store embeddings for semantic search"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        
        Models options:
        - all-MiniLM-L6-v2: Fast, 384 dims (RECOMMENDED for speed)
        - all-mpnet-base-v2: Better quality, 768 dims (current in DB schema)
        - multi-qa-mpnet-base-dot-v1: Optimized for Q&A
        """
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        logger.info(f" Loading model {model_name} on {self.device}...")
        self.model = SentenceTransformer(model_name)
        self.model.to(self.device)
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f" Model loaded with {self.embedding_dim} dimensions")
        
        # Get DATABASE_URL from environment
        database_url = os.getenv('POSTGRES_URL')
        if not database_url:
            raise ValueError("POSTGRES_URL not found in environment")
        
        # Convert to async URL
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif not database_url.startswith('postgresql+asyncpg://'):
            database_url = f"postgresql+asyncpg://{database_url}"
        
        logger.info(f" Connecting to database...")
        self.engine = create_async_engine(
            database_url,
            echo=False,
            connect_args={"prepared_statement_cache_size": 0}
        )
        self.async_session = async_sessionmaker(
            self.engine, 
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        # Keep reference for compatibility
        class DBWrapper:
            def __init__(self, session_maker, engine):
                self.async_session = session_maker
                self._engine = engine
            
            async def close(self):
                await self._engine.dispose()
        
        self.db_client = DBWrapper(self.async_session, self.engine)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding"""
        if not text or len(text.strip()) < 10:
            # Return zero vector for empty/too short texts
            logger.warning(" Text too short or empty, returning zero vector")
            return [0.0] * self.embedding_dim
        
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings in batches (faster)"""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_tensor=False
        )
        return embeddings.tolist()
    
    async def embed_publications(self, batch_size: int = 32):
        """
        Generate embeddings for all publications
        
        Strategy:
        1. Get all publications without embeddings
        2. Generate embeddings from title + abstract
        3. Store in PostgreSQL
        """
        async with self.db_client.async_session() as session:
            # Get publications without embeddings
            result = await session.execute(
                select(Publication)
                .where(Publication.embedding == None)  # NULL embeddings
                .limit(608)
            )
            publications = result.scalars().all()
            
            logger.info(f" Found {len(publications)} publications without embeddings")
            
            if not publications:
                logger.info(" All publications already have embeddings")
                return
            
            # Prepare texts for embedding
            texts = []
            pub_ids = []
            
            for pub in publications:
                # Combine title + abstract for rich semantic representation
                text = f"{pub.title or ''} {pub.abstract or ''}"
                texts.append(text.strip())
                pub_ids.append(pub.id)
            
            # Generate embeddings in batches
            logger.info(" Generating embeddings...")
            embeddings = self.generate_batch_embeddings(texts, batch_size=batch_size)
            
            # Update database
            logger.info(" Saving embeddings to database...")
            for pub_id, embedding in tqdm(zip(pub_ids, embeddings), total=len(pub_ids), desc="Saving"):
                await session.execute(
                    update(Publication)
                    .where(Publication.id == pub_id)
                    .values(embedding=embedding)
                )
            
            await session.commit()
            logger.info(f" Embedded {len(publications)} publications successfully")
    
    async def embed_text_sections(self, batch_size: int = 32):
        """
        Generate embeddings for individual text sections
        (for fine-grained semantic search)
        """
        async with self.db_client.async_session() as session:
            # Get text sections without embeddings
            result = await session.execute(
                select(TextSection)
                .where(TextSection.embedding == None)
            )
            sections = result.scalars().all()
            
            logger.info(f" Found {len(sections)} text sections without embeddings")
            
            if not sections:
                logger.info(" All sections already have embeddings")
                return
            
            # Prepare texts
            texts = [section.content for section in sections]
            section_ids = [section.id for section in sections]
            
            # Generate embeddings
            logger.info(" Generating section embeddings...")
            embeddings = self.generate_batch_embeddings(texts, batch_size=batch_size)
            
            # Update database
            logger.info(" Saving section embeddings...")
            for section_id, embedding in tqdm(zip(section_ids, embeddings), total=len(section_ids), desc="Saving sections"):
                await session.execute(
                    update(TextSection)
                    .where(TextSection.id == section_id)
                    .values(embedding=embedding)
                )
            
            await session.commit()
            logger.info(f" Embedded {len(sections)} text sections successfully")
    
    async def semantic_search_publications(
        self, 
        query: str, 
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Semantic search using cosine similarity
        
        Returns publications ranked by similarity to query
        """
        from sqlalchemy import text
        import json  # ← AJOUTEZ
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Convert to proper JSON format for pgvector
        embedding_json = json.dumps(query_embedding)  # ← FIX
        
        async with self.db_client.async_session() as session:
            # PostgreSQL pgvector similarity search
            result = await session.execute(
                text("""
                SELECT 
                    pmcid, title, abstract, journal, publication_date,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM publications
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> CAST(:query_embedding AS vector)) > :min_similarity
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :top_k
                """),
                {
                    "query_embedding": embedding_json,  # ← Utiliser JSON au lieu de str()
                    "min_similarity": min_similarity,
                    "top_k": top_k
                }
            )
            
            results = []
            for row in result:
                results.append({
                    'pmcid': row.pmcid,
                    'title': row.title,
                    'abstract': row.abstract[:200] + '...' if row.abstract else '',
                    'journal': row.journal,
                    'publication_date': row.publication_date.isoformat() if row.publication_date else None,
                    'similarity': round(row.similarity, 4)
                })
            
            return results
    
    async def find_similar_publications(
        self,
        pmcid: str,
        top_k: int = 5,
        exclude_self: bool = True
    ) -> List[Dict]:
        """
        Find publications similar to a given publication
        (useful for BUILDS_ON relationships)
        """
        from sqlalchemy import text
        import json  # ← AJOUTEZ cet import
        
        async with self.db_client.async_session() as session:
            # Get source publication embedding
            result = await session.execute(
                select(Publication).where(Publication.pmcid == pmcid)
            )
            source_pub = result.scalar_one_or_none()
            
            # Check if embedding exists properly
            if not source_pub:
                logger.warning(f"Publication {pmcid} not found")
                return []
            
            if source_pub.embedding is None or len(source_pub.embedding) == 0:
                logger.warning(f"Publication {pmcid} has no embedding")
                return []
            
            # FIX: Convert numpy array to proper JSON list format for pgvector
            # source_pub.embedding is a list, convert to JSON string without scientific notation
            embedding_list = [float(x) for x in source_pub.embedding]
            embedding_json = json.dumps(embedding_list)  # ← Format correct: "[0.123,0.456,...]"
            
            # Build query
            query_sql = """
            SELECT 
                pmcid, title, journal, publication_date,
                1 - (embedding <=> CAST(:source_embedding AS vector)) as similarity
            FROM publications
            WHERE embedding IS NOT NULL
            """
            
            params = {
                "source_embedding": embedding_json,  # ← Utiliser JSON au lieu de str()
                "top_k": top_k
            }
            
            if exclude_self:
                query_sql += " AND pmcid != :pmcid"
                params["pmcid"] = pmcid
            
            query_sql += """
            ORDER BY embedding <=> CAST(:source_embedding AS vector)
            LIMIT :top_k
            """
            
            result = await session.execute(text(query_sql), params)
            
            similar_pubs = []
            for row in result:
                similar_pubs.append({
                    'pmcid': row.pmcid,
                    'title': row.title,
                    'journal': row.journal,
                    'publication_date': row.publication_date.isoformat() if row.publication_date else None,
                    'similarity': round(row.similarity, 4)
                })
            
            return similar_pubs


async def main():
    """Generate embeddings for all publications"""
    generator = EmbeddingsGenerator()
    
    try:
        # Step 1: Embed publications
        logger.info("=== Step 1: Embedding Publications ===")
        await generator.embed_publications()
        
        # Step 2: Embed text sections (optional, takes longer)
        # logger.info("\n=== Step 2: Embedding Text Sections ===")
        # await generator.embed_text_sections()
        
        # Step 3: Test semantic search
        logger.info("\n=== Step 3: Testing Semantic Search ===")
        test_queries = [
            "bone loss in microgravity",
            "immune system changes during spaceflight",
            "muscle atrophy in astronauts"
        ]
        
        for query in test_queries:
            logger.info(f"\n Query: '{query}'")
            results = await generator.semantic_search_publications(query, top_k=3)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['title']}")
                print(f"   Similarity: {result['similarity']}")
                print(f"   PMCID: {result['pmcid']}")
        
    finally:
        await generator.db_client.close()


if __name__ == "__main__":
    asyncio.run(main())