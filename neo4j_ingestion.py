"""
Ingest extracted entities into Neo4j Knowledge Graph
Now with semantic embeddings for BUILDS_ON relationships
"""
import json
from typing import List, Dict, Optional
from neo4j_client import Neo4jClient
from embeddings_generator import EmbeddingsGenerator
from tqdm import tqdm
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jIngestion:
    """Ingest publications and entities into Neo4j"""
    
    def __init__(self, neo4j_client: Neo4jClient, embeddings_gen: Optional[EmbeddingsGenerator] = None):
        self.client = neo4j_client
        self.embeddings_gen = embeddings_gen
    
    async def ingest_publications(self, extracted_file: str = "extracted_entities_all.json"):
        """
        Ingest all publications and their entities
        
        Pipeline:
        1. Create Publication nodes
        2. Create Organism nodes (merge duplicates)
        3. Create Phenomenon nodes (merge duplicates)
        4. Create Platform/Stressor nodes
        5. Create relationships (STUDIES, INVESTIGATES, CONDUCTED_ON, EXPOSES_TO)
        6. Create BUILDS_ON relationships using semantic similarity
        """
        # Load extracted entities
        with open(extracted_file, 'r') as f:
            data = json.load(f)
        
        logger.info(f" Loading {len(data)} publications from {extracted_file}")
        
        # Statistics
        stats = {
            'publications': 0,
            'organisms': set(),
            'phenomena': set(),
            'platforms': set(),
            'stressors': set(),
            'studies_relations': 0,
            'investigates_relations': 0,
            'conducted_on_relations': 0,
            'exposes_to_relations': 0,
            'builds_on_relations': 0
        }
        
        with self.client.driver.session() as session:
            for entry in tqdm(data, desc="Ingesting publications"):
                pmcid = entry['pmcid']
                entities = entry['entities']
                
                try:
                    # 1. Create Publication node
                    self._create_publication_node(session, pmcid, entities)
                    stats['publications'] += 1
                    
                    # 2. Create and link Organisms
                    for organism in entities.get('organisms', []):
                        self._create_organism_node(session, organism)
                        self._create_studies_relation(session, pmcid, organism)
                        stats['organisms'].add(organism['scientific_name'])
                        stats['studies_relations'] += 1
                    
                    # 3. Create and link Phenomena
                    for phenomenon in entities.get('phenomena', []):
                        self._create_phenomenon_node(session, phenomenon)
                        self._create_investigates_relation(session, pmcid, phenomenon)
                        stats['phenomena'].add(phenomenon['name'])
                        stats['investigates_relations'] += 1
                    
                    # 4. Create and link Platform
                    platform = entities.get('platform')
                    if platform:
                        self._create_platform_node(session, platform)
                        self._create_conducted_on_relation(session, pmcid, platform)
                        stats['platforms'].add(platform)
                        stats['conducted_on_relations'] += 1
                    
                    # 5. Create and link Stressors
                    for stressor in entities.get('stressors', []):
                        self._create_stressor_node(session, stressor)
                        self._create_exposes_to_relation(session, pmcid, stressor)
                        stats['stressors'].add(stressor)
                        stats['exposes_to_relations'] += 1
                    
                except Exception as e:
                    logger.error(f" Error ingesting {pmcid}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # 6. Create BUILDS_ON relationships using embeddings
        if self.embeddings_gen:
            logger.info("\n Creating BUILDS_ON relationships using semantic similarity...")
            builds_on_count = await self._create_builds_on_relationships(data)
            stats['builds_on_relations'] = builds_on_count
        
        # Convert sets to counts
        stats['organisms'] = len(stats['organisms'])
        stats['phenomena'] = len(stats['phenomena'])
        stats['platforms'] = len(stats['platforms'])
        stats['stressors'] = len(stats['stressors'])
        
        logger.info(" Ingestion complete!")
        self._print_ingestion_stats(stats)
        
        return stats
    
    async def _create_builds_on_relationships(self, data: List[Dict], similarity_threshold: float = 0.6, max_links_per_pub: int = 3):
        """Create BUILDS_ON relationships based on embedding similarity"""
        builds_on_count = 0
        
        with self.client.driver.session() as session:
            for entry in tqdm(data[:50], desc="Creating BUILDS_ON links"):  # Limit to 50 for speed
                pmcid = entry['pmcid']
                
                # Find similar publications
                similar_pubs = await self.embeddings_gen.find_similar_publications(
                    pmcid, 
                    top_k=max_links_per_pub,
                    exclude_self=True
                )
                
                for similar_pub in similar_pubs:
                    if similar_pub['similarity'] >= similarity_threshold:
                        # Create BUILDS_ON relationship
                        query = """
                        MATCH (p1:Publication {pmcid: $pmcid1})
                        MATCH (p2:Publication {pmcid: $pmcid2})
                        MERGE (p1)-[r:BUILDS_ON]->(p2)
                        SET r.similarity = $similarity,
                            r.relationship_type = 'semantic_similarity',
                            r.created_at = datetime()
                        RETURN r
                        """
                        
                        session.run(query,
                            pmcid1=pmcid,
                            pmcid2=similar_pub['pmcid'],
                            similarity=similar_pub['similarity']
                        )
                        builds_on_count += 1
        
        return builds_on_count
    
    def _create_publication_node(self, session, pmcid: str, entities: Dict):
        """Create or update Publication node"""
        query = """
        MERGE (p:Publication {pmcid: $pmcid})
        SET p.experimental_context = $experimental_context,
            p.extraction_confidence = $extraction_confidence,
            p.updated_at = datetime()
        RETURN p
        """
        
        session.run(query, 
            pmcid=pmcid,
            experimental_context=entities.get('experimental_context', 'unknown'),
            extraction_confidence=entities.get('extraction_confidence', 0.0)
        )
    
    def _create_organism_node(self, session, organism: Dict):
        """Create or merge Organism node"""
        query = """
        MERGE (o:Organism {scientific_name: $scientific_name})
        SET o.name = $name,
            o.category = $category,
            o.updated_at = datetime()
        RETURN o
        """
        
        session.run(query,
            scientific_name=organism['scientific_name'],
            name=organism.get('name', organism['scientific_name']),
            category=organism.get('category', 'unknown')
        )
    
    def _create_phenomenon_node(self, session, phenomenon: Dict):
        """Create or merge Phenomenon node"""
        query = """
        MERGE (ph:Phenomenon {name: $name})
        SET ph.description = $description,
            ph.system = $system,
            ph.updated_at = datetime()
        RETURN ph
        """
        
        session.run(query,
            name=phenomenon['name'],
            description=phenomenon.get('description', ''),
            system=phenomenon.get('system', 'other')
        )
    
    def _create_platform_node(self, session, platform_name: str):
        """Create or merge Platform node"""
        query = """
        MERGE (pl:Platform {name: $name})
        SET pl.updated_at = datetime()
        RETURN pl
        """
        
        session.run(query, name=platform_name)
    
    def _create_stressor_node(self, session, stressor_name: str):
        """Create or merge Stressor node"""
        query = """
        MERGE (s:Stressor {name: $name})
        SET s.updated_at = datetime()
        RETURN s
        """
        
        session.run(query, name=stressor_name)
    
    def _create_studies_relation(self, session, pmcid: str, organism: Dict):
        """Create STUDIES relationship"""
        query = """
        MATCH (p:Publication {pmcid: $pmcid})
        MATCH (o:Organism {scientific_name: $scientific_name})
        MERGE (p)-[r:STUDIES]->(o)
        SET r.created_at = datetime()
        RETURN r
        """
        
        session.run(query,
            pmcid=pmcid,
            scientific_name=organism['scientific_name']
        )
    
    def _create_investigates_relation(self, session, pmcid: str, phenomenon: Dict):
        """Create INVESTIGATES relationship"""
        query = """
        MATCH (p:Publication {pmcid: $pmcid})
        MATCH (ph:Phenomenon {name: $name})
        MERGE (p)-[r:INVESTIGATES]->(ph)
        SET r.confidence = $confidence,
            r.created_at = datetime()
        RETURN r
        """
        
        session.run(query,
            pmcid=pmcid,
            name=phenomenon['name'],
            confidence=0.8
        )
    
    def _create_conducted_on_relation(self, session, pmcid: str, platform: str):
        """Create CONDUCTED_ON relationship"""
        query = """
        MATCH (p:Publication {pmcid: $pmcid})
        MATCH (pl:Platform {name: $platform})
        MERGE (p)-[r:CONDUCTED_ON]->(pl)
        SET r.created_at = datetime()
        RETURN r
        """
        
        session.run(query, pmcid=pmcid, platform=platform)
    
    def _create_exposes_to_relation(self, session, pmcid: str, stressor: str):
        """Create EXPOSES_TO relationship"""
        query = """
        MATCH (p:Publication {pmcid: $pmcid})
        MATCH (s:Stressor {name: $stressor})
        MERGE (p)-[r:EXPOSES_TO]->(s)
        SET r.created_at = datetime()
        RETURN r
        """
        
        session.run(query, pmcid=pmcid, stressor=stressor)
    
    def _print_ingestion_stats(self, stats: Dict):
        """Pretty print ingestion statistics"""
        logger.info(f"""
 Ingestion Statistics:
   Publications: {stats['publications']}
   Unique Organisms: {stats['organisms']}
   Unique Phenomena: {stats['phenomena']}
   Unique Platforms: {stats['platforms']}
   Unique Stressors: {stats['stressors']}
   
   STUDIES relations: {stats['studies_relations']}
   INVESTIGATES relations: {stats['investigates_relations']}
   CONDUCTED_ON relations: {stats['conducted_on_relations']}
   EXPOSES_TO relations: {stats['exposes_to_relations']}
   BUILDS_ON relations: {stats['builds_on_relations']}
        """)


async def main():
    """Run ingestion"""
    neo4j_client = Neo4jClient()
    embeddings_gen = EmbeddingsGenerator()
    
    try:
        # Verify connectivity
        if not neo4j_client.verify_connectivity():
            logger.error(" Cannot connect to Neo4j")
            return
        
        # Run ingestion
        ingestion = Neo4jIngestion(neo4j_client, embeddings_gen)
        stats = await ingestion.ingest_publications()
        
        # Print final graph stats
        logger.info("\n=== Final Graph Statistics ===")
        neo4j_client.print_stats()
        
    finally:
        neo4j_client.close()
        await embeddings_gen.db_client.close()


if __name__ == "__main__":
    asyncio.run(main())